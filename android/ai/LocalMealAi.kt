package fr.monevolution.app

import android.app.Activity
import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.StatFs
import android.webkit.WebView
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Content
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** Optional local AI; model is never packed into APK or sent over the network. */
class LocalMealAi(private val activity: Activity, private val web: WebView) {
    companion object {
        private const val MODEL_NAME = "gemma-4-E4B-it.litertlm"
        private const val MODEL_BYTES = 3659530240L
        private const val MODEL_SHA256 = "0b2a8980ce155fd97673d8e820b4d29d9c7d99b8fa6806f425d969b145bd52e0"
        private const val MODEL_URL =
            "https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm/resolve/2eee7ac325f20eb8c9ac1d0e972f7c84663062da/gemma-4-E4B-it.litertlm"
    }
    private val prefs = activity.getSharedPreferences("imc_local_ai_e4b", Context.MODE_PRIVATE)
    private val worker = Executors.newSingleThreadExecutor()
    private val checking = AtomicBoolean(false)
    private val analyzing = AtomicBoolean(false)
    private val directory: File? = activity.getExternalFilesDir(null)?.let { File(it, "models") }
    private val model: File? = directory?.let { File(it, MODEL_NAME) }
    private val downloadManager = activity.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
    private var engine: Engine? = null

    private fun response(state: String, detail: String = "", percent: Int = -1): String =
        JSONObject().put("state", state).put("detail", detail).put("percent", percent)
            .put("model", "Gemma 4 E4B").toString()

    fun status(): String {
        if (Build.SUPPORTED_ABIS.none { it == "arm64-v8a" }) {
            return response("incompatible", "Android ARM64 requis.")
        }
        val file = model ?: return response("incompatible", "Stockage indisponible.")
        if (prefs.getBoolean("verified", false) && file.length() == MODEL_BYTES) {
            return response(if (analyzing.get()) "analyzing" else "ready", "Analyse hors ligne disponible.")
        }
        if (checking.get()) return response("checking", "Vérification de l'intégrité du modèle...")
        val id = prefs.getLong("download_id", -1L)
        if (id > 0L) {
            try {
                downloadManager.query(DownloadManager.Query().setFilterById(id))?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val state = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
                        if (state == DownloadManager.STATUS_RUNNING || state == DownloadManager.STATUS_PENDING ||
                            state == DownloadManager.STATUS_PAUSED) {
                            val total = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
                            val read = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
                            val percent = if (total > 0) (read * 100 / total).toInt().coerceIn(0, 100) else -1
                            return response("downloading", "Téléchargement Wi-Fi recommandé (3,66 Go).", percent)
                        }
                        if (state == DownloadManager.STATUS_FAILED)
                            return response("error", "Échec du téléchargement. Réessayez.")
                        if (state == DownloadManager.STATUS_SUCCESSFUL) {
                            if (file.length() != MODEL_BYTES)
                                return response("error", "Fichier incomplet. Supprimez et réessayez.")
                            verifyInBackground(file)
                            return response("checking", "Vérification de l'intégrité du modèle...")
                        }
                    }
                }
            } catch (_: Exception) {
                return response("error", "Impossible de vérifier le téléchargement.")
            }
        }
        if (file.exists() && file.length() == MODEL_BYTES) {
            verifyInBackground(file)
            return response("checking", "Vérification de l'intégrité du modèle...")
        }
        return response("not_installed", "Installation facultative, environ 3,66 Go.")
    }

    fun download(): String {
        val file = model ?: return response("incompatible", "Stockage indisponible.")
        val state = JSONObject(status()).optString("state")
        if (state in setOf("ready", "analyzing", "checking", "downloading", "removing")) return status()
        try {
            directory?.mkdirs()
            if (StatFs(directory!!.absolutePath).availableBytes < MODEL_BYTES + 650_000_000L)
                return response("error", "Il faut environ 4,3 Go d'espace libre.")
            if (file.exists()) file.delete()
            val request = DownloadManager.Request(Uri.parse(MODEL_URL))
                .setTitle("IMC — IA alimentaire Gemma")
                .setDescription("Modèle local à télécharger une seule fois")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setAllowedOverMetered(false)
                .setAllowedOverRoaming(false)
                .setDestinationUri(Uri.fromFile(file))
            val id = downloadManager.enqueue(request)
            prefs.edit().putLong("download_id", id).putBoolean("verified", false).apply()
            return response("downloading", "Téléchargement en cours via Wi-Fi.")
        } catch (ex: Exception) {
            return response("error", "Téléchargement impossible : " + (ex.message ?: "erreur Android"))
        }
    }

    private fun verifyInBackground(file: File) {
        if (!checking.compareAndSet(false, true)) return
        worker.execute {
            try {
                val digest = MessageDigest.getInstance("SHA-256")
                FileInputStream(file).use { input ->
                    val buffer = ByteArray(1024 * 1024)
                    while (true) {
                        val n = input.read(buffer)
                        if (n < 0) break
                        digest.update(buffer, 0, n)
                    }
                }
                val checksum = digest.digest().joinToString("") { "%02x".format(it) }
                val valid = checksum.equals(MODEL_SHA256, true)
                prefs.edit().putBoolean("verified", valid).apply()
                if (!valid) prefs.edit().putLong("download_id", -1L).apply()
            } catch (_: Exception) {
                prefs.edit().putBoolean("verified", false).apply()
            } finally {
                checking.set(false)
            }
        }
    }

    fun remove(): String {
        if (analyzing.get() || checking.get()) return response("error", "Attendez la fin de l'opération IA.")
        val id = prefs.getLong("download_id", -1L)
        if (id > 0) try { downloadManager.remove(id) } catch (_: Exception) { }
        worker.execute {
            try { engine?.close() } catch (_: Exception) { }
            engine = null
            model?.delete()
            prefs.edit().clear().apply()
        }
        return response("removing", "Suppression du modèle seulement, sans toucher aux repas.")
    }

    fun analyze(token: String, base64DataUrl: String, description: String) {
        val hasPhoto = base64DataUrl.isNotEmpty()
        if (token.length > 150 || (!hasPhoto && description.isBlank()) ||
            (hasPhoto && (!base64DataUrl.startsWith("data:image/jpeg;base64,") ||
            base64DataUrl.length > 600_000))) {
            notifyResult(token, JSONObject().put("error", "Ajoutez une photo ou une description du repas.").toString())
            return
        }
        if (!analyzing.compareAndSet(false, true)) {
            notifyResult(token, JSONObject().put("error", "Une analyse est déjà en cours.").toString())
            return
        }
        worker.execute {
            try {
                val file = model ?: throw IllegalStateException("Modèle introuvable.")
                if (!prefs.getBoolean("verified", false) || file.length() != MODEL_BYTES)
                    throw IllegalStateException("Installez et vérifiez le modèle IA avant l'analyse.")
                val bytes = if (hasPhoto) android.util.Base64.decode(
                    base64DataUrl.substringAfter(','), android.util.Base64.DEFAULT
                ) else null
                val e = engine ?: Engine(EngineConfig(
                    modelPath = file.absolutePath,
                    backend = Backend.CPU(),
                    visionBackend = Backend.CPU(),
                    cacheDir = activity.cacheDir.absolutePath
                )).also { fresh ->
                    fresh.initialize()
                    engine = fresh
                }
                val mode = if (hasPhoto)
                    "Analyse la photo. Si elle est floue ou ne montre pas clairement les aliments, " +
                    "utilise la description saisie pour estimer le repas si elle identifie un aliment."
                else
                    "Analyse UNIQUEMENT le texte saisi, sans image. " +
                    "Une description courte suffit dès qu'un aliment est reconnaissable."
                val prompt = """
Tu es un estimateur nutritionnel pour un journal alimentaire en français. """ + mode + """
Texte du repas : """ + description.take(800) + """
Tout aliment nommé, même une collation et même sans poids précis, est identifiable :
« 1 morceau de camembert », « 1 assiette de carbonara », « 1 carré de chocolat »,
« bol de céréales et 2 craquottes à la fraise » sont des exemples de descriptions analysables.
Estime une portion française habituelle en cas de quantité imprécise.
Pour un plat cuisiné dont la recette est inconnue, utilise une estimation générique du plat,
sans prétendre connaître précisément ses ingrédients.
Ne refuse pas un aliment reconnu sous prétexte de quantités inconnues.
Réponds EXCLUSIVEMENT avec un objet JSON valide, sans commentaire ni Markdown :
{"description":"riz et poulet, portion moyenne","kcal":500,"protein":25,"carbs":40,"fat":18}
Le champ description a au maximum 12 mots.
kcal = kilocalories par portion, protein/carbs/fat = grammes de macronutriments.
Ces valeurs sont des estimations approximatives et ne constituent pas un diagnostic.
Réponds {"error":"Repas non identifiable"} UNIQUEMENT si ni la photo ni le texte
ne permettent de reconnaître un aliment (par exemple un objet non alimentaire).
""".trimIndent()
                val content = if (hasPhoto) {
                    Contents.of(Content.ImageBytes(bytes!!), Content.Text(prompt))
                } else {
                    Contents.of(Content.Text(prompt))
                }
                val answer = e.createConversation().use { conversation ->
                    conversation.sendMessage(content).toString()
                }
                val start = answer.indexOf('{')
                val end = answer.lastIndexOf('}')
                if (start < 0 || end <= start) throw IllegalStateException("Réponse IA non exploitable.")
                var parsed = JSONObject(answer.substring(start, end + 1))
                // Some model responses incorrectly reject short but clear descriptions.
                // Retry once with a simpler text-only request; never add an invented result.
                if (parsed.optString("error").contains("non identifiable", ignoreCase = true)
                    && description.isNotBlank()) {
                    val retryPrompt = """
Le texte suivant décrit un aliment ou un repas consommé en France :
""" + description.take(800) + """
Estime sa portion habituelle et ses calories, protéines, glucides, lipides.
Un morceau de fromage, un carré de chocolat ou une assiette de pâtes sont identifiables.
Une quantité imprécise n'est pas une raison de refuser une estimation.
Écris uniquement ce JSON avec les 5 champs demandés, sans aucun autre texte :
{"description":"portion de camembert","kcal":95,"protein":6,"carbs":0.1,"fat":7.5}
Les nombres de l'exemple sont indicatifs : adapte-les à l'aliment réellement indiqué.
""".trimIndent()
                    val candidate = runCatching {
                        val retryAnswer = e.createConversation().use { conversation ->
                            conversation.sendMessage(Contents.of(Content.Text(retryPrompt))).toString()
                        }
                        val from = retryAnswer.indexOf('{')
                        val to = retryAnswer.lastIndexOf('}')
                        if (from < 0 || to <= from) null
                        else JSONObject(retryAnswer.substring(from, to + 1))
                    }.getOrNull()
                    if (candidate != null && !candidate.has("error")) parsed = candidate
                }
                if (!parsed.has("error") && (!parsed.has("kcal") || !parsed.has("protein") ||
                            !parsed.has("carbs") || !parsed.has("fat")))
                    throw IllegalStateException("Valeurs nutritionnelles manquantes.")
                notifyResult(token, parsed.toString())
            } catch (ex: Throwable) {
                val msg = (ex.message ?: ex.javaClass.simpleName).take(300)
                notifyResult(token, JSONObject().put("error", "Analyse indisponible : " + msg).toString())
            } finally {
                analyzing.set(false)
            }
        }
    }

    private fun notifyResult(token: String, result: String) {
        activity.runOnUiThread {
            web.evaluateJavascript(
                "window.localAiMealResult && window.localAiMealResult(" +
                    JSONObject.quote(token) + "," + JSONObject.quote(result) + ")", null)
        }
    }
}
