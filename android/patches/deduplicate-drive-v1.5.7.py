#!/usr/bin/env python3
"""Mon Evolution IMC v1.5.7 - avoid duplicate Google Drive documents.

Use the v1.5.6 source code as input in /tmp/mon-evolution-src.
The Android Storage Access Framework is used to preserve users' Drive access
and file permissions. No existing document is deleted automatically.
"""
from pathlib import Path

base=Path("/tmp/mon-evolution-src/app")
java=base/"src/main/java/fr/monevolution/app/MainActivity.java"
html=base/"src/main/assets/index.html"
manifest=base/"src/main/AndroidManifest.xml"
gradle=base/"build.gradle"

def rep(path, old, new):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    assert n==1, f"{path}: expected exactly one occurrence ({n} found) of {old[:100]!r}"
    path.write_text(s.replace(old,new),encoding="utf-8")

rep(manifest,'android:versionCode="12" android:versionName="1.5.6"',
             'android:versionCode="13" android:versionName="1.5.7"')
rep(gradle,'versionCode 12','versionCode 13')
rep(gradle,"versionName '1.5.6'","versionName '1.5.7'")
rep(html,"const installed='1.5.6';","const installed='1.5.7';")
rep(html,'Version installée : <strong>1.5.6</strong>','Version installée : <strong>1.5.7</strong>')
rep(html,'Version installée : 1.5.6. Vérifie sur GitHub','Version installée : 1.5.7. Vérifie sur GitHub')

# 1. Create once, then update the same Drive file for the selected profile.
rep(java,
    'private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44, SHARE_CREATE = 45, SHARE_OPEN = 46;',
    'private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44, SHARE_CREATE = 45, SHARE_OPEN = 46, SHARE_RELINK = 47, BACKUP_RELINK = 48;')
rep(java,'    private String pendingShareId;',
         '    private String pendingShareId;\n    private String pendingShareName;')
rep(java,
'''                    new JSONObject(json).getJSONObject("profile").getJSONArray("entries");
                    pendingShareId=profileId;''',
'''                    JSONObject sharedProfile=new JSONObject(json).getJSONObject("profile");
                    sharedProfile.getJSONArray("entries");
                    String linked=getPreferences(MODE_PRIVATE).getString("share_uri_"+profileId,null);
                    if(linked!=null) {
                        // IMPORTANT: never invoke CREATE_DOCUMENT for an already linked profile.
                        final String payload=makeSharedDocument(profileId,sharedProfile);
                        io.execute(() -> {
                            try {
                                writeShared(Uri.parse(linked), payload);
                                runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));
                            } catch(Exception error) {
                                runOnUiThread(() -> web.evaluateJavascript("sharedUpdateFailed()",null));
                            }
                        });
                        return;
                    }
                    pendingShareId=profileId;''')
# 2. Reconnect an existing share without writing over it immediately.
rep(java,
'''        @JavascriptInterface public String sharedStatus(String id) {''',
'''        @JavascriptInterface public void linkExistingShare(String profileId, String profileName) {
            if(profileId==null || !profileId.matches("[a-zA-Z0-9_-]{1,75}")
                    || profileName==null || profileName.length()>100) return;
            runOnUiThread(() -> {
                pendingShareId=profileId;
                pendingShareName=profileName;
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, SHARE_RELINK);
            });
        }
        @JavascriptInterface public String sharedStatus(String id) {''')
# 3. Backup button reuses existing URI; separately offer a link-existing workflow.
rep(java,
'''        @JavascriptInterface public void save(String json) {
            runOnUiThread(() -> {
                pendingJson = json;''',
'''        @JavascriptInterface public void save(String json) {
            if(json==null || json.length()>50_000_000) {
                runOnUiThread(() -> web.evaluateJavascript("backupFailed()",null));
                return;
            }
            // The manual "save" button must never create a second Drive document
            // while a writable backup is linked. Reuse autoSave's conflict guard.
            if(getPreferences(MODE_PRIVATE).contains(BACKUP_URI)) {
                autoSave(json);
                return;
            }
            runOnUiThread(() -> {
                pendingJson = json;''')
rep(java,
'''        @JavascriptInterface public void load() {
            runOnUiThread(() -> {''',
'''        @JavascriptInterface public void linkExistingBackup() {
            runOnUiThread(() -> {
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent,BACKUP_RELINK);
            });
        }
        @JavascriptInterface public void load() {
            runOnUiThread(() -> {''')
# 4. Link existing documents after checking their content and persistent write rights.
rep(java,
'''            } else if (request == SHARE_OPEN) {
                persistUri(uri, false);''',
'''            } else if (request == SHARE_RELINK) {
                if(pendingShareId==null || pendingShareName==null)
                    throw new Exception("Profil introuvable");
                JSONObject document=new JSONObject(readSafJson(uri,40_000_000));
                if(!"mon-evolution-lecture-seule".equals(document.optString("format"))
                    || document.optInt("version")!=1)
                    throw new Exception("Format du partage invalide");
                JSONObject existing=document.getJSONObject("profile");
                if(!pendingShareName.equalsIgnoreCase(existing.getString("name")))
                    throw new Exception("Ce fichier correspond à un autre profil");
                existing.getJSONArray("entries");
                if(!persistUri(uri,true))
                    throw new Exception("Impossible de conserver les droits d'écriture Drive");
                getPreferences(MODE_PRIVATE).edit()
                    .putString("share_uri_"+pendingShareId,uri.toString()).apply();
                web.evaluateJavascript("shareRelinked()",null);
            } else if (request == BACKUP_RELINK) {
                String raw=readSafJson(uri,40_000_000);
                JSONObject existing=new JSONObject(raw);
                if(!"mon-evolution".equals(existing.optString("format"))
                    || existing.optInt("version")!=1)
                    throw new Exception("Sauvegarde incompatible");
                existing.getJSONObject("data").getJSONArray("profiles");
                if(!persistUri(uri,true))
                    throw new Exception("Impossible de conserver les droits d'écriture Drive");
                getPreferences(MODE_PRIVATE).edit()
                    .putString(BACKUP_URI,uri.toString())
                    .putString(BACKUP_HASH,stringHash(raw))
                    .putLong(BACKUP_TIME,System.currentTimeMillis()).apply();
                web.evaluateJavascript("backupRelinked()",null);
            } else if (request == SHARE_OPEN) {
                persistUri(uri, false);''')
rep(java,
'''            if (request == SHARE_CREATE) {
                web.evaluateJavascript("sharedUpdateFailed()", null);
            } else if (request == SHARE_OPEN) {''',
'''            if (request == SHARE_CREATE || request == SHARE_RELINK) {
                web.evaluateJavascript("sharedUpdateFailed()", null);
            } else if (request == BACKUP_RELINK) {
                web.evaluateJavascript("backupRelinkFailed()", null);
            } else if (request == SHARE_OPEN) {''')
rep(java,
'''            pendingShareId = null;
            pendingShareJson = null;''',
'''            pendingShareId = null;
            pendingShareName = null;
            pendingShareJson = null;''')
rep(java,
'''    // Documents are created/selected using Android SAF; no Google password or OAuth token.
    private boolean persistUri(Uri uri, boolean writable) {''',
'''    // Read an existing SAF document with a strict size cap, before linking.
    private String readSafJson(Uri uri,int cap) throws Exception {
        try(InputStream in=getContentResolver().openInputStream(uri)) {
            if(in==null)throw new Exception("Document Drive inaccessible");
            java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
            byte[] buf=new byte[8192];
            int n;
            while((n=in.read(buf))!=-1) {
                out.write(buf,0,n);
                if(out.size()>cap) throw new Exception("Document trop volumineux");
            }
            return new String(out.toByteArray(),StandardCharsets.UTF_8);
        }
    }

    // Documents are created/selected using Android SAF; no Google password or OAuth token.
    private boolean persistUri(Uri uri, boolean writable) {''')

# Backup UI: create only once, then update, or explicitly relink older file.
rep(html,
    '<button class="primary" id="backup">☁ Relier / enregistrer sur Drive</button>',
    '<button class="primary" id="backup">☁ Relier / enregistrer sur Drive</button><button class="secondary" style="width:100%;margin-top:12px" id="backup-relink">↗ Relier une sauvegarde déjà présente sur Drive</button>')
rep(html,
'''  document.getElementById('disconnect').style.display = linked ? 'block' : 'none';
}''',
'''  document.getElementById('disconnect').style.display = linked ? 'block' : 'none';
  document.getElementById('backup-relink').style.display = linked ? 'none' : 'block';
  document.getElementById('backup').textContent = linked
    ? '↻ Mettre à jour la sauvegarde Drive'
    : '☁ Créer une sauvegarde (une seule fois)';
}''')
rep(html,
'''document.getElementById('backup').onclick = () => {
  if (window.AndroidBackup) AndroidBackup.save(backupPayload());
  else message('Cette option nécessite l’application Android');
};''',
'''document.getElementById('backup').onclick = () => {
  if (!window.AndroidBackup) return message('Cette option nécessite l’application Android');
  if (AndroidBackup.isLinked()) message('Mise à jour du fichier Drive existant…');
  else if (!confirm('Un fichier mon-evolution-profils.json existe-t-il déjà sur Drive ? Si oui, annule et utilise « Relier une sauvegarde déjà présente » pour éviter un doublon.')) return;
  AndroidBackup.save(backupPayload());
};
document.getElementById('backup-relink').onclick = () => {
  if (!window.AndroidBackup?.linkExistingBackup) return message('Liaison Drive indisponible');
  if (!confirm('Choisir la sauvegarde existante à réutiliser ? Le fichier ne sera pas modifié immédiatement. Les prochaines modifications synchronisées pourront remplacer son contenu.')) return;
  AndroidBackup.linkExistingBackup();
};
function backupRelinked(){
  refreshDriveState();
  message('Sauvegarde existante reliée ✓ Aucun nouveau fichier créé.');
}
function backupRelinkFailed(){
  alert('Impossible de relier cette sauvegarde. Sélectionne un fichier mon-evolution-profils.json dont tu possèdes les droits de modification.');
}''')

# Sharing UI: update existing file, or relink a prior file. Never delete remote files.
rep(html,
    '<button class="primary" id="create-share">Créer le fichier partagé sur Drive</button>',
    '<button class="primary" id="create-share">Créer le fichier partagé sur Drive</button><button class="secondary" style="width:100%;margin-top:10px" id="share-relink">↗ Relier un fichier partagé existant</button>')
rep(html,
''' $('stop-share').style.display=linked?'block':'none';
 $('share-photos').checked=!!window.AndroidBackup?.sharePhotosEnabled?.(id);''',
''' $('stop-share').style.display=linked?'block':'none';
 $('create-share').textContent=linked?'↻ Mettre à jour le partage Drive':'Créer le fichier partagé sur Drive';
 $('share-relink').textContent=linked?'Changer de fichier partagé relié':'↗ Relier un fichier partagé existant';
 $('share-photos').checked=!!window.AndroidBackup?.sharePhotosEnabled?.(id);''')
rep(html,
'''$('create-share').onclick=()=>{
 if(!window.AndroidBackup?.createShare)return message('Partage disponible dans l’application Android');
 const p=profile();
 AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));
};''',
'''$('create-share').onclick=()=>{
 if(!window.AndroidBackup?.createShare)return message('Partage disponible dans l’application Android');
 const p=profile();
 const linked=window.AndroidBackup?.sharedStatus?.(p.id)==='1';
 if(!linked && !confirm('Un fichier de partage existe-t-il déjà pour ce profil ? Si oui, annule et utilise « Relier un fichier partagé existant » pour éviter un doublon.'))return;
 AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));
 if(linked)message('Actualisation du fichier partagé existant…');
};
$('share-relink').onclick=()=>{
 if(!window.AndroidBackup?.linkExistingShare)return message('Liaison du partage indisponible');
 const p=profile();
 if(!confirm('Relier un fichier partagé existant correspondant à '+p.name+' ? Le fichier sélectionné ne sera pas écrasé immédiatement.'))return;
 AndroidBackup.linkExistingShare(p.id,p.name);
};
function shareRelinked(){
 shareStatus();
 message('Fichier de partage existant relié ✓');
}''')
rep(html,
'''function sharedUpdateFailed(){message('Échec de mise à jour du partage : vérifie Google Drive')}''',
'''function sharedUpdateFailed(){alert('Impossible de créer, relier ou modifier le fichier partagé. Vérifie les droits Google Drive. N’en crée pas un nouveau avant d’avoir essayé « Relier un fichier partagé existant ».');}''')

s=html.read_text(encoding="utf-8")
assert "const installed='1.5.7';" in s
assert 'id="setup-screen"' in s
assert "name:'Mario',height:181" not in s and '119,9' not in s
assert "id=\"update-page-open\"" in s and "id=\"update-direct-open\"" in s
assert 'android:icon="@drawable/ic_launcher"' in manifest.read_text()
j=java.read_text()
assert "SHARE_RELINK = 47, BACKUP_RELINK = 48" in j
assert 'linkExistingShare' in j and 'linkExistingBackup' in j
assert "String linked=getPreferences(MODE_PRIVATE).getString(\"share_uri_\"+profileId,null);" in j
print("v1.5.7 - linked files updated, existing documents relinkable, duplicate creation guarded.")
