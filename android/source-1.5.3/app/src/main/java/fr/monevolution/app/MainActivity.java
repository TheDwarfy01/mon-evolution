package fr.monevolution.app;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.graphics.pdf.PdfDocument;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.RectF;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.List;
import java.security.MessageDigest;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import android.content.SharedPreferences;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44;
    private WebView web;
    private String pendingJson;
    private String pendingPdfJson;
    private String pendingPhotoToken;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private static final String PREFS = "drive_backup";
    private static final String BACKUP_URI = "backup_uri";
    private static final String BACKUP_HASH = "backup_hash";
    private static final String BACKUP_TIME = "backup_time";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        // Android 15 (SDK 35) draws apps edge-to-edge. A WebView's own
        // setPadding() does not reliably inset its HTML viewport on all devices.
        // Apply system-bar insets to a native parent instead.
        android.widget.FrameLayout content = new android.widget.FrameLayout(this);
        content.setBackgroundColor(android.graphics.Color.rgb(9, 24, 39));
        web = new WebView(this);
        content.addView(web, new android.widget.FrameLayout.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(content);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        if (android.os.Build.VERSION.SDK_INT >= 35) {
            content.setOnApplyWindowInsetsListener((view, insets) -> {
                android.graphics.Insets bars = insets.getInsets(
                        android.view.WindowInsets.Type.systemBars()
                        | android.view.WindowInsets.Type.displayCutout());
                // Inset the FrameLayout, not the WebView's internal viewport.
                // This keeps the header below the notification/status bar.
                if (view.getPaddingLeft() != bars.left || view.getPaddingTop() != bars.top
                        || view.getPaddingRight() != bars.right
                        || view.getPaddingBottom() != bars.bottom) {
                    view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                }
                return insets;
            });
            content.requestApplyInsets();
            android.view.View decor = getWindow().getDecorView();
            decor.setSystemUiVisibility(decor.getSystemUiVisibility()
                    & ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        }
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        web.addJavascriptInterface(new Bridge(), "AndroidBackup");
        web.loadUrl("file:///android_asset/index.html");
    }

    public class Bridge {
        @JavascriptInterface public String reminderSettings() {
            SharedPreferences p=getSharedPreferences("reminders",MODE_PRIVATE);
            JSONObject result=new JSONObject();
            try {
                for(String type:new String[]{"weight","meals"}){
                    JSONObject item=new JSONObject();
                    item.put("enabled",p.getBoolean(type+"_enabled",false));
                    item.put("hour",p.getInt(type+"_hour",type.equals("weight")?9:20));
                    item.put("minute",p.getInt(type+"_minute",0));
                    item.put("weekday",p.getInt(type+"_weekday",1));
                    result.put(type,item);
                }
            } catch(Exception ignored){}
            return result.toString();
        }
        @JavascriptInterface public void setReminder(String type, boolean enabled, int hour, int minute, int weekday) {
            runOnUiThread(() -> {
                ReminderReceiver.configure(MainActivity.this,type,enabled,hour,minute,weekday);
                if(enabled&&android.os.Build.VERSION.SDK_INT>=33
                    &&checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
                    requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},72);
            });
        }
        @JavascriptInterface public String loadLocal() {
            File file = new File(getFilesDir(), "mon-evolution-data.json");
            if (!file.exists() || file.length() > 50_000_000) return null;
            try (FileInputStream input = new FileInputStream(file)) {
                java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                return new String(output.toByteArray(), StandardCharsets.UTF_8);
            } catch (Exception ignored) { return null; }
        }
        @JavascriptInterface public boolean saveLocal(String json) {
            if (json == null || json.length() > 50_000_000) return false;
            File target = new File(getFilesDir(), "mon-evolution-data.json");
            File temporary = new File(getFilesDir(), "mon-evolution-data.tmp");
            try (FileOutputStream output = new FileOutputStream(temporary)) {
                output.write(json.getBytes(StandardCharsets.UTF_8));
                output.getFD().sync();
            } catch (Exception e) { return false; }
            return temporary.renameTo(target);
        }
        @JavascriptInterface public boolean isLinked() {
            return getPreferences(MODE_PRIVATE).contains(BACKUP_URI);
        }
        @JavascriptInterface public String backupStatus() {
            SharedPreferences prefs = getPreferences(MODE_PRIVATE);
            return (prefs.contains(BACKUP_URI) ? "1" : "0") + "|" + prefs.getLong(BACKUP_TIME, 0);
        }
        @JavascriptInterface public void autoSave(String json) {
            String value = getPreferences(MODE_PRIVATE).getString(BACKUP_URI, null);
            if (value == null) return;
            io.execute(() -> {
                try {
                    Uri uri = Uri.parse(value);
                    String knownHash = getPreferences(MODE_PRIVATE).getString(BACKUP_HASH, null);
                    String actualHash = fileHash(uri);
                    if (knownHash != null && !knownHash.equals(actualHash)) {
                        runOnUiThread(() -> web.evaluateJavascript("backupConflict()", null));
                        return;
                    }
                    try (OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                        if (out == null) throw new Exception("Destination inaccessible");
                        out.write(json.getBytes(StandardCharsets.UTF_8));
                    }
                    getPreferences(MODE_PRIVATE).edit().putString(BACKUP_HASH, stringHash(json)).putLong(BACKUP_TIME, System.currentTimeMillis()).apply();
                    runOnUiThread(() -> web.evaluateJavascript("refreshDriveState()", null));
                } catch (Exception e) {
                    runOnUiThread(() -> web.evaluateJavascript("backupFailed()", null));
                }
            });
        }
        @JavascriptInterface public void disconnect() {
            getPreferences(MODE_PRIVATE).edit().remove(BACKUP_URI).remove(BACKUP_HASH).remove(BACKUP_TIME).apply();
        }
        @JavascriptInterface public void save(String json) {
            runOnUiThread(() -> {
                pendingJson = json;
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                i.putExtra(Intent.EXTRA_TITLE, "mon-evolution-profils.json");
                startActivityForResult(i, SAVE);
            });
        }
        @JavascriptInterface public void load() {
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                startActivityForResult(i, LOAD);
            });
        }
        @JavascriptInterface public void exportMealsPdf(String reportJson) {
            if (reportJson == null || reportJson.length() > 1_000_000) return;
            runOnUiThread(() -> {
                try {
                    JSONObject report = new JSONObject(reportJson);
                    String month = report.getString("month");
                    if (!month.matches("\\d{4}-\\d{2}")) throw new Exception("Mois invalide");
                    pendingPdfJson = reportJson;
                    Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("application/pdf");
                    intent.putExtra(Intent.EXTRA_TITLE, "repas-" + month + ".pdf");
                    startActivityForResult(intent, PDF);
                } catch (Exception e) {
                    web.evaluateJavascript("showMessage('Compte rendu invalide')", null);
                }
            });
        }
        @JavascriptInterface public void pickPhoto(String token) {
            if (token == null || token.length() > 150) return;
            runOnUiThread(() -> {
                pendingPhotoToken = token;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.setType("image/*");
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(intent, PHOTO);
            });
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try {
            if (request == PHOTO) {
                String photo = compressedPhoto(uri);
                web.evaluateJavascript("photoPicked(" + JSONObject.quote(pendingPhotoToken) + "," + JSONObject.quote(photo) + ")", null);
            } else if (request == PDF) {
                createMealsPdf(uri, pendingPdfJson);
                web.evaluateJavascript("pdfCompleted()", null);
            } else if (request == SAVE) {
                boolean persistent = false;
                try {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    persistent = true;
                } catch (SecurityException ignored) {
                    try {
                        getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                        persistent = true;
                    } catch (SecurityException ignoredAgain) {}
                }
                try (OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                    if (out == null) throw new Exception("Destination inaccessible");
                    out.write(pendingJson.getBytes(StandardCharsets.UTF_8));
                }
                if (persistent) {
                    getPreferences(MODE_PRIVATE).edit().putString(BACKUP_URI, uri.toString()).putString(BACKUP_HASH, stringHash(pendingJson)).putLong(BACKUP_TIME, System.currentTimeMillis()).apply();
                }
                web.evaluateJavascript("backupCompleted(" + persistent + ")", null);
            } else if (request == LOAD) {
                byte[] bytes;
                try (InputStream in = getContentResolver().openInputStream(uri)) {
                    if (in == null) throw new Exception("Fichier inaccessible");
                    java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
                    byte[] buffer = new byte[4096];
                    int count;
                    while ((count = in.read(buffer)) != -1) {
                        out.write(buffer, 0, count);
                        if (out.size() > 40_000_000) throw new Exception("Sauvegarde trop volumineuse");
                    }
                    bytes = out.toByteArray();
                }
                String json = new String(bytes, StandardCharsets.UTF_8);
                String encoded = android.util.Base64.encodeToString(json.getBytes(StandardCharsets.UTF_8), android.util.Base64.NO_WRAP);
                web.evaluateJavascript("restoreBase64('" + encoded + "')", null);
            }
        } catch (Exception e) {
            web.evaluateJavascript("showMessage('Opération impossible : vérifie le fichier ou Google Drive')", null);
        } finally {
            pendingJson = null;
            pendingPdfJson = null;
            pendingPhotoToken = null;
        }
    }
    private String stringHash(String value) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
        return android.util.Base64.encodeToString(hash, android.util.Base64.NO_WRAP);
    }
    private String fileHash(Uri uri) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = getContentResolver().openInputStream(uri)) {
            if (input == null) throw new Exception("Sauvegarde inaccessible");
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        return android.util.Base64.encodeToString(digest.digest(), android.util.Base64.NO_WRAP);
    }
    private String compressedPhoto(Uri uri) throws Exception {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        try (InputStream input = getContentResolver().openInputStream(uri)) {
            if (input == null) throw new Exception("Photo inaccessible");
            BitmapFactory.decodeStream(input, null, bounds);
        }
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) throw new Exception("Format d'image non reconnu");
        int sample = 1;
        while (Math.max(bounds.outWidth, bounds.outHeight) / sample > 1000) sample *= 2;
        BitmapFactory.Options opts = new BitmapFactory.Options();
        opts.inSampleSize = sample;
        Bitmap decoded;
        try (InputStream input = getContentResolver().openInputStream(uri)) {
            if (input == null) throw new Exception("Photo inaccessible");
            decoded = BitmapFactory.decodeStream(input, null, opts);
        }
        if (decoded == null) throw new Exception("Photo non décodable");
        int longest = Math.max(decoded.getWidth(), decoded.getHeight());
        float scale = Math.min(1f, 600f / longest);
        Bitmap small = Bitmap.createScaledBitmap(decoded, Math.max(1,(int)(decoded.getWidth()*scale)), Math.max(1,(int)(decoded.getHeight()*scale)), true);
        java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
        small.compress(Bitmap.CompressFormat.JPEG, 55, output);
        if (output.size() > 130_000) {
            output.reset();
            small.compress(Bitmap.CompressFormat.JPEG, 35, output);
        }
        if (small != decoded) small.recycle();
        decoded.recycle();
        if (output.size() > 180_000) throw new Exception("Photo trop volumineuse");
        return "data:image/jpeg;base64," + android.util.Base64.encodeToString(output.toByteArray(), android.util.Base64.NO_WRAP);
    }
    private void createMealsPdf(Uri uri, String reportJson) throws Exception {
        JSONObject report = new JSONObject(reportJson);
        String name = report.optString("name", "Profil");
        String month = report.getString("month");
        JSONArray days = report.getJSONArray("days");
        JSONArray weights = report.optJSONArray("weights");
        double goal = report.optDouble("goal", 0);
        List<String> rows = new ArrayList<>();
        List<String> photos = new ArrayList<>();
        rows.add("Bilan mensuel - " + name);
        rows.add("Mois : " + month.substring(5) + "/" + month.substring(0, 4));
        rows.add("Jours renseignés : " + days.length());
        if (weights != null && weights.length() > 0) {
            double first = weights.getJSONObject(0).getDouble("weight");
            double last = weights.getJSONObject(weights.length()-1).getDouble("weight");
            rows.add("# Poids et progression");
            rows.add("Pesées du mois : " + weights.length());
            rows.add("Première pesée : " + String.format(java.util.Locale.FRANCE,"%.1f kg",first));
            rows.add("Dernière pesée : " + String.format(java.util.Locale.FRANCE,"%.1f kg",last));
            rows.add("Évolution : " + String.format(java.util.Locale.FRANCE,"%+.1f kg",last-first));
            rows.add("Objectif : " + String.format(java.util.Locale.FRANCE,"%.1f kg",goal));
            rows.add("@chart");
        }
        rows.add("# Journal alimentaire");
        rows.add("");
        if (days.length() == 0) rows.add("Aucun repas enregistré pour ce mois.");
        for (int i = 0; i < days.length(); i++) {
            JSONObject day = days.getJSONObject(i);
            String date = day.getString("date");
            rows.add("# " + date.substring(8) + "/" + date.substring(5, 7) + "/" + date.substring(0, 4));
            JSONArray meals = day.getJSONArray("meals");
            for (int j = 0; j < meals.length(); j++) {
                JSONObject meal = meals.getJSONObject(j);
                rows.add(meal.getString("label") + " : " + meal.getString("text"));
                String photo = meal.optString("photo", "");
                if (photo.startsWith("data:image/jpeg;base64,")) {
                    photos.add(photo.substring("data:image/jpeg;base64,".length()));
                    rows.add("@photo:"+(photos.size()-1));
                }
            }
            rows.add("");
        }
        PdfDocument document = new PdfDocument();
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setTextSize(12f);
        paint.setColor(Color.rgb(28, 45, 59));
        int pageNumber = 0;
        PdfDocument.Page page = null;
        Canvas canvas = null;
        float y = 0f;
        try {
            for (String row : rows) {
                if (row.equals("@chart") || row.startsWith("@photo:")) {
                    if (page == null || y > 620f) {
                        if (page != null) document.finishPage(page);
                        page = document.startPage(new PdfDocument.PageInfo.Builder(595, 842, ++pageNumber).create());
                        canvas = page.getCanvas();
                        canvas.drawColor(Color.WHITE);
                        paint.setColor(Color.rgb(80, 110, 128));
                        paint.setTextSize(10f);
                        canvas.drawText("Mon Évolution  |  Bilan mensuel", 45f, 32f, paint);
                        canvas.drawText("Page " + pageNumber, 505f, 815f, paint);
                        y = 64f;
                    }
                    if (row.equals("@chart")) {
                        drawWeightChart(canvas, weights, goal, y);
                        y += 170f;
                    } else {
                        int index = Integer.parseInt(row.substring(7));
                        if (index >= 0 && index < photos.size()) y += drawPdfPhoto(canvas, photos.get(index), y);
                    }
                    paint.setColor(Color.rgb(28, 45, 59));
                    continue;
                }
                boolean heading = row.startsWith("# ");
                String clean = heading ? row.substring(2) : row;
                paint.setTypeface(heading ? Typeface.create(Typeface.DEFAULT, Typeface.BOLD) : Typeface.DEFAULT);
                paint.setTextSize(heading ? 14f : 12f);
                List<String> wrapped = wrapPdfText(clean, paint, 495f);
                for (String line : wrapped) {
                    if (page == null || y > 780f) {
                        if (page != null) document.finishPage(page);
                        page = document.startPage(new PdfDocument.PageInfo.Builder(595, 842, ++pageNumber).create());
                        canvas = page.getCanvas();
                        canvas.drawColor(Color.WHITE);
                        paint.setColor(Color.rgb(80, 110, 128));
                        paint.setTextSize(10f);
                        canvas.drawText("Mon Évolution  |  Bilan mensuel", 45f, 32f, paint);
                        canvas.drawText("Page " + pageNumber, 505f, 815f, paint);
                        paint.setColor(Color.rgb(28, 45, 59));
                        paint.setTextSize(heading ? 14f : 12f);
                        y = 64f;
                    }
                    canvas.drawText(line, 45f, y, paint);
                    y += heading ? 21f : 18f;
                }
            }
            if (page != null) document.finishPage(page);
            try (OutputStream output = getContentResolver().openOutputStream(uri, "wt")) {
                if (output == null) throw new Exception("Destination PDF inaccessible");
                document.writeTo(output);
            }
        } finally {
            document.close();
        }
    }
    private float drawPdfPhoto(Canvas canvas, String encoded, float y) {
        try {
            byte[] bytes = android.util.Base64.decode(encoded, android.util.Base64.DEFAULT);
            Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (bitmap == null) return 0f;
            float height = Math.min(125f, 250f * bitmap.getHeight() / Math.max(1,bitmap.getWidth()));
            float width = height * bitmap.getWidth() / Math.max(1,bitmap.getHeight());
            Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
            canvas.drawBitmap(bitmap, null, new RectF(55f, y+4f, 55f+width, y+4f+height), paint);
            bitmap.recycle();
            return height + 17f;
        } catch (Exception e) { return 0f; }
    }
    private void drawWeightChart(Canvas canvas, JSONArray weights, double goal, float y) throws Exception {
        if (weights == null || weights.length()==0) return;
        double min=goal,max=goal;
        for (int i=0;i<weights.length();i++){
            double w=weights.getJSONObject(i).getDouble("weight");
            min=Math.min(min,w);max=Math.max(max,w);
        }
        min-=1.5;max+=1.5;
        float left=65f,right=525f,top=y+15f,bottom=y+130f;
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setStrokeWidth(1f);paint.setColor(Color.rgb(202,212,220));
        for(int i=0;i<=3;i++){
            float yy=top+(bottom-top)*i/3f;
            canvas.drawLine(left,yy,right,yy,paint);
        }
        float gy=(float)(bottom-(goal-min)/(max-min)*(bottom-top));
        paint.setColor(Color.rgb(204,155,70));paint.setStrokeWidth(1.5f);
        canvas.drawLine(left,gy,right,gy,paint);
        paint.setColor(Color.rgb(29,139,126));paint.setStrokeWidth(3f);
        float lastX=0,lastY=0;
        for(int i=0;i<weights.length();i++){
            float xx=weights.length()==1?(left+right)/2:left+(right-left)*i/(weights.length()-1);
            float yy=(float)(bottom-(weights.getJSONObject(i).getDouble("weight")-min)/(max-min)*(bottom-top));
            if(i>0)canvas.drawLine(lastX,lastY,xx,yy,paint);
            canvas.drawCircle(xx,yy,3.5f,paint);
            lastX=xx;lastY=yy;
        }
        paint.setTextSize(10f);paint.setColor(Color.rgb(75,97,113));
        canvas.drawText("Évolution des pesées",left,y+155f,paint);
        canvas.drawText("Objectif",right-45f,gy-6f,paint);
    }
    private List<String> wrapPdfText(String value, Paint paint, float maxWidth) {
        List<String> lines = new ArrayList<>();
        String[] paragraphs = value.split("\\n", -1);
        for (String paragraph : paragraphs) {
            String rest = paragraph.trim();
            if (rest.isEmpty()) { lines.add(""); continue; }
            while (!rest.isEmpty()) {
                int count = paint.breakText(rest, true, maxWidth, null);
                if (count >= rest.length()) { lines.add(rest); break; }
                int split = rest.lastIndexOf(' ', count);
                if (split <= 0) split = Math.max(1, count);
                lines.add(rest.substring(0, split).trim());
                rest = rest.substring(split).trim();
            }
        }
        return lines;
    }
    @Override public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        io.shutdown();
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
