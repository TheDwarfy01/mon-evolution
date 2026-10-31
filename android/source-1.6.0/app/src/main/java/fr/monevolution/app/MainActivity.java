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
    private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44, SHARE_CREATE = 45, SHARE_OPEN = 46, SHARE_RELINK = 47, BACKUP_RELINK = 48, EXPORT_CSV = 49, EXPORT_PROFILE = 50, PROGRESS_PDF = 51;
    private WebView web;
    private String pendingJson;
    private String pendingPdfJson;
    private String pendingPhotoToken;
    private String pendingShareId;
    private String pendingShareName;
    private String pendingShareJson;
    private String pendingExport;
    private String pendingProgressJson;
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
        web.setWebViewClient(new WebViewClient() {
            private boolean handleUri(Uri uri) {
                if ("file".equalsIgnoreCase(uri.getScheme())
                        && uri.getPath()!=null && uri.getPath().startsWith("/android_asset/")) return false;
                if ("https".equalsIgnoreCase(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW,uri)); }
                    catch(Exception ignored) { }
                }
                return true;
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                return handleUri(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleUri(Uri.parse(url));
            }
        });
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
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        web.addJavascriptInterface(new Bridge(), "AndroidBackup");
        web.loadUrl("file:///android_asset/index.html");
    }

    public class Bridge {
        @JavascriptInterface public void openOfficialUrl(String url) {
            if (url == null) return;
            String prefix = "https://github.com/TheDwarfy01/mon-evolution/releases";
            boolean valid = prefix.equals(url)
                || url.matches("https://github\\.com/TheDwarfy01/mon-evolution/releases/tag/v[0-9]+(\\.[0-9]+){1,3}")
                || url.matches("https://github\\.com/TheDwarfy01/mon-evolution/releases/download/v[0-9]+(\\.[0-9]+){1,3}/Mon_Evolution_IMC_v[0-9]+(\\.[0-9]+){1,3}\\.apk");
            if (!valid) return;
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    intent.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(intent);
                } catch (android.content.ActivityNotFoundException ignored) { }
            });
        }
        @JavascriptInterface public void createShare(String profileId, String json) {
            if (profileId == null || !profileId.matches("[a-zA-Z0-9_-]{1,75}")
                    || json == null || json.length() > 40_000_000) {
                runOnUiThread(() -> web.evaluateJavascript("sharedUpdateFailed()", null));
                return;
            }
            runOnUiThread(() -> {
                try {
                    JSONObject sharedProfile=new JSONObject(json).getJSONObject("profile");
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
                    pendingShareId=profileId;
                    pendingShareJson=json;
                    Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("application/json");
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                        | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                        | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                    intent.putExtra(Intent.EXTRA_TITLE, "mon-evolution-partage-" + profileId + ".json");
                    startActivityForResult(intent, SHARE_CREATE);
                } catch (Exception e) {
                    web.evaluateJavascript("sharedUpdateFailed()", null);
                }
            });
        }
        @JavascriptInterface public void linkExistingShare(String profileId, String profileName) {
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
        @JavascriptInterface public String sharedStatus(String id) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return "0";
            return getPreferences(MODE_PRIVATE).contains("share_uri_" + id) ? "1" : "0";
        }
        @JavascriptInterface public boolean sharePhotosEnabled(String id) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return false;
            return getPreferences(MODE_PRIVATE).getBoolean("share_photos_" + id, false);
        }
        @JavascriptInterface public void setSharePhotos(String id, boolean enabled) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return;
            getPreferences(MODE_PRIVATE).edit().putBoolean("share_photos_" + id, enabled).apply();
        }
        @JavascriptInterface public void stopShare(String id) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return;
            getPreferences(MODE_PRIVATE).edit()
                .remove("share_uri_" + id).remove("share_link_" + id).apply();
        }
        @JavascriptInterface public String getShareLink(String id) {
            if (id==null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return "";
            if (!getPreferences(MODE_PRIVATE).contains("share_uri_"+id)) return "";
            return getPreferences(MODE_PRIVATE).getString("share_link_"+id,"");
        }
        @JavascriptInterface public boolean saveShareLink(String id,String url) {
            if (id==null || !id.matches("[a-zA-Z0-9_-]{1,75}")
                    || !getPreferences(MODE_PRIVATE).contains("share_uri_"+id)
                    || url==null || url.length()>1500) return false;
            String value=url.trim();
            if (!validDriveShareLink(value)) return false;
            getPreferences(MODE_PRIVATE).edit().putString("share_link_"+id,value).apply();
            return true;
        }
        @JavascriptInterface public void copyShareLink(String id) {
            final String url=getShareLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Colle d’abord le lien obtenu dans Google Drive')",null);
                    return;
                }
                android.content.ClipboardManager clipboard=
                    (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Lien du profil partagé",url));
                web.evaluateJavascript("showMessage('Lien Google Drive copié ✓')",null);
            });
        }
        @JavascriptInterface public void sendShareLink(String id) {
            final String url=getShareLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Enregistre d’abord le lien Google Drive')",null);
                    return;
                }
                try {
                    Intent send=new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_SUBJECT,"Profil Mon Évolution IMC en lecture seule");
                    send.putExtra(Intent.EXTRA_TEXT,"Voici mon profil Mon Évolution IMC en lecture seule :\n"+url);
                    startActivity(Intent.createChooser(send,"Partager le lien du profil"));
                } catch(Exception e) {
                    web.evaluateJavascript("showMessage('Impossible d’ouvrir le partage Android')",null);
                }
            });
        }
        @JavascriptInterface public void openDrive() {
            runOnUiThread(() -> {
                try {
                    Intent open=new Intent(Intent.ACTION_VIEW,
                        Uri.parse("https://drive.google.com/drive/my-drive"));
                    open.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(open);
                } catch(Exception e){
                    web.evaluateJavascript("showMessage('Ouvre Google Drive depuis ton téléphone')",null);
                }
            });
        }

        @JavascriptInterface public void checkLatestVersion() {
            io.execute(() -> {
                try {
                    String raw = httpRead("https://api.github.com/repos/TheDwarfy01/mon-evolution/releases/latest", 200_000);
                    JSONObject release = new JSONObject(raw);
                    String version = release.getString("tag_name");
                    if(!version.matches("v[0-9]+(\\.[0-9]+){1,3}"))
                        throw new Exception("Invalid release tag");
                    String ver=version.substring(1);
                    runOnUiThread(() -> web.evaluateJavascript("receiveUpdateVersion("+JSONObject.quote(ver)+")",null));
                }catch(Exception e){
                    runOnUiThread(() -> web.evaluateJavascript("updateVersionFailed()",null));
                }
            });
        }
        @JavascriptInterface public void deleteActiveShare(String id) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            String value=getPreferences(MODE_PRIVATE).getString("share_uri_"+id,null);
            if(value==null) {
                js("shareDeleteFailed()");
                return;
            }
            io.execute(() -> {
                try {
                    if(!android.provider.DocumentsContract.deleteDocument(getContentResolver(),Uri.parse(value)))
                        throw new Exception("Provider refused deletion");
                    getPreferences(MODE_PRIVATE).edit()
                        .remove("share_uri_"+id).remove("share_link_"+id).apply();
                    js("shareDeleted()");
                }catch(Exception e){js("shareDeleteFailed()");}
            });
        }
        @JavascriptInterface public void deleteProfileOnDrive(String id) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            String value=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            String known=getPreferences(MODE_PRIVATE).getString(BACKUP_HASH,null);
            if(value==null || known==null){js("driveProfileRemoveFailed()");return;}
            io.execute(() -> {
                try {
                    Uri uri=Uri.parse(value);
                    if(!known.equals(fileHash(uri))) throw new Exception("Drive changed: conflict");
                    JSONObject doc=new JSONObject(readSafJson(uri,40_000_000));
                    if(!"mon-evolution".equals(doc.optString("format"))
                        || doc.optInt("version")!=1)throw new Exception("Wrong backup");
                    JSONObject body=doc.getJSONObject("data");
                    JSONArray profiles=body.getJSONArray("profiles"),remaining=new JSONArray();
                    boolean found=false;
                    for(int i=0;i<profiles.length();i++){
                        JSONObject p=profiles.getJSONObject(i);
                        if(id.equals(p.optString("id")))found=true;
                        else remaining.put(p);
                    }
                    if(!found)throw new Exception("Profile missing");
                    if(remaining.length()==0){
                        if(!android.provider.DocumentsContract.deleteDocument(getContentResolver(),uri))
                            throw new Exception("Cannot delete last backup");
                    }else{
                        body.put("profiles",remaining);
                        if(id.equals(body.optString("active")))
                            body.put("active",remaining.getJSONObject(0).getString("id"));
                        doc.put("data",body);
                        try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                            if(out==null)throw new Exception("Drive is read-only");
                            out.write(doc.toString().getBytes(StandardCharsets.UTF_8));
                        }
                    }
                    // Deliberately disconnect the active backup to prevent an
                    // existing local copy of this profile being re-uploaded.
                    getPreferences(MODE_PRIVATE).edit().remove(BACKUP_URI)
                        .remove(BACKUP_HASH).remove(BACKUP_TIME).apply();
                    js("driveProfileRemoved()");
                }catch(Exception e){js("driveProfileRemoveFailed()");}
            });
        }
        @JavascriptInterface public void loadSharedPublic(String url) {
            String id=driveFileId(url);
            if(id==null){js("sharedPublicFailed()");return;}
            io.execute(() -> {
                try {
                    byte[] body=fetchPublicProfile(id);
                    JSONObject doc=new JSONObject(new String(body,StandardCharsets.UTF_8));
                    if(!"mon-evolution-lecture-seule".equals(doc.optString("format"))
                        || doc.optInt("version")!=1)
                        throw new Exception("Not an app share");
                    doc.getJSONObject("profile").getJSONArray("entries");
                    String b64=android.util.Base64.encodeToString(body,android.util.Base64.NO_WRAP);
                    getPreferences(MODE_PRIVATE).edit()
                        .putString("received_public_url","https://drive.google.com/file/d/"+id+"/view")
                        .remove("received_share_uri").apply();
                    js("sharedLoaded("+JSONObject.quote(b64)+")");
                }catch(Exception e){js("sharedPublicFailed()");}
            });
        }
        @JavascriptInterface public void exportProgressPdf(String content) {
            if(content==null || content.length()>4_000_000){js("exportFailed()");return;}
            runOnUiThread(() -> {
                try {
                    JSONObject doc=new JSONObject(content);
                    if(doc.getJSONArray("weights").length()<1)throw new Exception("No weights");
                    pendingProgressJson=content;
                    Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("application/pdf");
                    i.putExtra(Intent.EXTRA_TITLE,"mon-evolution-bilan-global.pdf");
                    startActivityForResult(i,PROGRESS_PDF);
                }catch(Exception e){js("exportFailed()");}
            });
        }
        @JavascriptInterface public void exportCsv(String content) {
            if(content==null || content.length()>15_000_000){js("exportFailed()");return;}
            runOnUiThread(() -> {
                pendingExport=content;
                Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("text/csv");
                i.putExtra(Intent.EXTRA_TITLE,"mon-evolution-pesees.csv");
                startActivityForResult(i,EXPORT_CSV);
            });
        }
        @JavascriptInterface public void exportSingleProfile(String content) {
            if(content==null || content.length()>40_000_000){js("exportFailed()");return;}
            runOnUiThread(() -> {
                pendingExport=content;
                Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                i.putExtra(Intent.EXTRA_TITLE,"mon-evolution-profil.json");
                startActivityForResult(i,EXPORT_PROFILE);
            });
        }
        @JavascriptInterface public void openShared() {
            runOnUiThread(() -> {
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, SHARE_OPEN);
            });
        }
        @JavascriptInterface public void refreshShared() {
            String publicUrl=getPreferences(MODE_PRIVATE).getString("received_public_url",null);
            if(publicUrl!=null) {loadSharedPublic(publicUrl);return;}
            String value=getPreferences(MODE_PRIVATE).getString("received_share_uri", null);
            if(value!=null)loadShared(Uri.parse(value));
        }
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
            updateSharedFiles(json);
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
                pendingJson = json;
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                i.putExtra(Intent.EXTRA_TITLE, "mon-evolution-profils.json");
                startActivityForResult(i, SAVE);
            });
        }
        @JavascriptInterface public void linkExistingBackup() {
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
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                startActivityForResult(i, LOAD);
            });
        }
        @JavascriptInterface public void exportMealsPdf(String reportJson) {
            if (reportJson == null || reportJson.length() > 15_000_000) {
                js("exportFailed()");
                return;
            }
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
                String token=pendingPhotoToken;
                io.execute(() -> {
                    try{
                        String photo=compressedPhoto(uri);
                        js("photoPicked("+JSONObject.quote(token)+","+JSONObject.quote(photo)+")");
                    }catch(Exception e){js("showMessage('Photo illisible ou trop volumineuse')");}
                });
            } else if (request == PDF) {
                String report=pendingPdfJson;
                io.execute(() -> {
                    try{createMealsPdf(uri,report);js("pdfCompleted()");}
                    catch(Exception e){js("exportFailed()");}
                });
            } else if (request == PROGRESS_PDF) {
                String report=pendingProgressJson;
                io.execute(() -> {
                    try{createProgressPdf(uri,report);js("exportCompleted()");}
                    catch(Exception e){js("exportFailed()");}
                });
            } else if (request == EXPORT_CSV || request == EXPORT_PROFILE) {
                String content=pendingExport;
                io.execute(() -> {
                    try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                        if(out==null)throw new Exception("Export not writable");
                        out.write(content.getBytes(StandardCharsets.UTF_8));
                        js("exportCompleted()");
                    }catch(Exception e){js("exportFailed()");}
                });
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
            } else if (request == SHARE_CREATE) {
                String id = pendingShareId, json = pendingShareJson;
                if (id == null || json == null) throw new Exception("Aucun profil à partager");
                boolean retained = persistUri(uri, true);
                String payload = makeSharedDocument(id, new JSONObject(json).getJSONObject("profile"));
                writeShared(uri, payload);
                if (retained) getPreferences(MODE_PRIVATE).edit()
                    .remove("share_link_" + id)
                    .putString("share_uri_" + id, uri.toString()).apply();
                web.evaluateJavascript("shareCreated(" + retained + ")", null);
            } else if (request == SHARE_RELINK) {
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
                    .remove("share_link_"+pendingShareId)
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
                persistUri(uri, false);
                getPreferences(MODE_PRIVATE).edit()
                    .remove("received_public_url")
                    .putString("received_share_uri", uri.toString()).apply();
                loadShared(uri);
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
            if (request == SHARE_CREATE || request == SHARE_RELINK) {
                web.evaluateJavascript("sharedUpdateFailed()", null);
            } else if (request == BACKUP_RELINK) {
                web.evaluateJavascript("backupRelinkFailed()", null);
            } else if (request == SHARE_OPEN) {
                web.evaluateJavascript("sharedReadFailed()", null);
            } else {
                web.evaluateJavascript("showMessage('Opération impossible : vérifie le fichier ou Google Drive')", null);
            }
        } finally {
            pendingShareId = null;
            pendingShareName = null;
            pendingShareJson = null;
            pendingJson = null;
            pendingPdfJson = null;
            pendingPhotoToken = null;
            pendingExport = null;
            pendingProgressJson = null;
        }
    }
    private boolean validDriveShareLink(String url) {
        try {
            Uri uri=Uri.parse(url);
            if(!"https".equalsIgnoreCase(uri.getScheme())
                || !"drive.google.com".equalsIgnoreCase(uri.getHost())) return false;
            String path=uri.getPath();
            if(path==null)return false;
            if(path.matches("/file/d/[A-Za-z0-9_-]{10,200}(/view)?/?"))return true;
            String id=uri.getQueryParameter("id");
            return "/open".equals(path) && id!=null && id.matches("[A-Za-z0-9_-]{10,200}");
        }catch(Exception e){return false;}
    }

    // Read an existing SAF document with a strict size cap, before linking.
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
    private boolean persistUri(Uri uri, boolean writable) {
        try {
            int flags=Intent.FLAG_GRANT_READ_URI_PERMISSION |
                (writable ? Intent.FLAG_GRANT_WRITE_URI_PERMISSION : 0);
            getContentResolver().takePersistableUriPermission(uri, flags);
            return true;
        } catch (SecurityException e) {
            if (writable) {
                try {
                    getContentResolver().takePersistableUriPermission(
                        uri, Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    return true;
                } catch (SecurityException ignored) { }
            }
            return false;
        }
    }

    private void writeShared(Uri uri, String json) throws Exception {
        try (OutputStream out=getContentResolver().openOutputStream(uri, "wt")) {
            if(out==null) throw new Exception("Fichier Drive inaccessible en écriture");
            out.write(json.getBytes(StandardCharsets.UTF_8));
        }
    }

    private String makeSharedDocument(String id, JSONObject input) throws Exception {
        JSONObject profile=new JSONObject();
        String name=input.getString("name");
        if(name.isEmpty() || name.length()>100) throw new Exception("Nom invalide");
        profile.put("name",name);
        profile.put("height",input.getDouble("height"));
        profile.put("goal",input.getDouble("goal"));
        JSONArray entries=input.getJSONArray("entries");
        if(entries.length()==0 || entries.length()>20000) throw new Exception("Pesées manquantes");
        profile.put("entries",entries);
        // Whitelist: no photo de profil, no other profiles or backup private metadata.
        JSONObject filteredMeals=new JSONObject();
        JSONObject meals=input.optJSONObject("meals");
        boolean includePhotos=getPreferences(MODE_PRIVATE).getBoolean("share_photos_"+id,false);
        if (meals!=null) {
            java.util.Iterator<String> days=meals.keys();
            while(days.hasNext()) {
                String date=days.next();
                if(!date.matches("\\d{4}-\\d{2}-\\d{2}"))continue;
                JSONObject meal=meals.optJSONObject(date);
                if(meal==null)continue;
                JSONObject cleaned=new JSONObject();
                String[] keys={"morning","morningSnack","lunch","afternoonSnack","dinner","eveningSnack"};
                for(String key:keys) {
                    String text=meal.optString(key,"");
                    if(!text.isEmpty())cleaned.put(key,text.substring(0,Math.min(3000,text.length())));
                    if(includePhotos) {
                        String image=meal.optString(key+"Photo","");
                        if(image.startsWith("data:image/jpeg;base64,") && image.length()<250000)
                            cleaned.put(key+"Photo",image);
                    }
                }
                if(cleaned.length()>0)filteredMeals.put(date,cleaned);
            }
        }
        profile.put("meals",filteredMeals);
        java.text.SimpleDateFormat df=new java.text.SimpleDateFormat(
            "yyyy-MM-dd'T'HH:mm:ss'Z'",java.util.Locale.US);
        df.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
        JSONObject document=new JSONObject();
        document.put("format","mon-evolution-lecture-seule");
        document.put("version",1);
        document.put("exportedAt",df.format(new java.util.Date()));
        document.put("profile",profile);
        String result=document.toString();
        if(result.length()>40_000_000)throw new Exception("Profil trop volumineux");
        return result;
    }

    // Independent of private backup: update only documents explicitly linked by the user.
    private void updateSharedFiles(String backup) {
        if(backup==null || backup.length()>50_000_000)return;
        io.execute(() -> {
            try {
                JSONObject root=new JSONObject(backup);
                JSONArray profiles=root.getJSONObject("data").getJSONArray("profiles");
                for(int index=0; index<profiles.length(); index++) {
                    JSONObject p=profiles.getJSONObject(index);
                    String id=p.optString("id","");
                    if(!id.matches("[a-zA-Z0-9_-]{1,75}"))continue;
                    String value=getPreferences(MODE_PRIVATE).getString("share_uri_"+id,null);
                    if(value==null)continue;
                    try {
                        String document=makeSharedDocument(id,p);
                        writeShared(Uri.parse(value),document);
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));
                    } catch(Exception e) {
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdateFailed()",null));
                    }
                }
            } catch(Exception ignored) { }
        });
    }

    private void loadShared(Uri uri) {
        io.execute(() -> {
            try(InputStream in=getContentResolver().openInputStream(uri)) {
                if(in==null)throw new Exception("Fichier partagé inaccessible");
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                byte[] buffer=new byte[8192];
                int n;
                while((n=in.read(buffer))!=-1) {
                    out.write(buffer,0,n);
                    if(out.size()>40_000_000)throw new Exception("Fichier trop volumineux");
                }
                // Decode and validate in the read-only JS view.
                String encoded=android.util.Base64.encodeToString(
                    out.toByteArray(),android.util.Base64.NO_WRAP);
                runOnUiThread(() -> web.evaluateJavascript("sharedLoaded('"+encoded+"')",null));
            } catch(Exception e) {
                runOnUiThread(() -> web.evaluateJavascript("sharedReadFailed()",null));
            }
        });
    }


    // JS callbacks are dispatched only on the Android UI thread.
    private void js(String source) {
        runOnUiThread(() -> {
            if(web!=null)web.evaluateJavascript(source,null);
        });
    }
    private String driveFileId(String url) {
        if(url==null || url.length()>1500 || !validDriveShareLink(url))return null;
        try{
            Uri u=Uri.parse(url);
            String path=u.getPath();
            String id=path!=null && path.startsWith("/file/d/")?
                path.substring("/file/d/".length()).split("/")[0]:
                u.getQueryParameter("id");
            return id!=null && id.matches("[A-Za-z0-9_-]{10,200}")?id:null;
        }catch(Exception e){return null;}
    }
    private byte[] fetchPublicProfile(String id) throws Exception {
        java.net.URL url=new java.net.URL("https://drive.google.com/uc?export=download&id="+id);
        for(int n=0;n<5;n++){
            java.net.HttpURLConnection c=(java.net.HttpURLConnection)url.openConnection();
            c.setConnectTimeout(9000);
            c.setReadTimeout(14000);
            c.setInstanceFollowRedirects(false);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("User-Agent","MonEvolutionIMC/1.6.0");
            int status=c.getResponseCode();
            if(status>=300 && status<400){
                String loc=c.getHeaderField("Location");
                c.disconnect();
                if(loc==null)throw new Exception("Missing redirect");
                java.net.URL next=new java.net.URL(url,loc);
                String host=next.getHost().toLowerCase(java.util.Locale.ROOT);
                if(!"https".equals(next.getProtocol())
                    || !(host.equals("drive.google.com")
                         || host.endsWith(".googleusercontent.com")))
                    throw new Exception("Unsafe redirect");
                url=next;
                continue;
            }
            if(status!=200){c.disconnect();throw new Exception("Drive returned "+status);}
            String type=c.getContentType();
            if(type!=null && type.toLowerCase(java.util.Locale.ROOT).contains("text/html")){
                c.disconnect();
                throw new Exception("Drive returned login/preview HTML, not public JSON");
            }
            try(InputStream in=c.getInputStream()){
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                byte[] bytes=new byte[8192];int count;
                while((count=in.read(bytes))!=-1){
                    out.write(bytes,0,count);
                    if(out.size()>15_000_000)throw new Exception("Profile too large");
                }
                return out.toByteArray();
            }finally{c.disconnect();}
        }
        throw new Exception("Too many Drive redirects");
    }
    private String httpRead(String address,int limit) throws Exception {
        java.net.HttpURLConnection c=(java.net.HttpURLConnection)new java.net.URL(address).openConnection();
        c.setConnectTimeout(9000);c.setReadTimeout(12000);
        c.setRequestProperty("Accept","application/vnd.github+json");
        c.setRequestProperty("User-Agent","MonEvolutionIMC/1.6.0");
        try {
            if(c.getResponseCode()!=200)throw new Exception("Update check unavailable");
            try(InputStream in=c.getInputStream()){
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                byte[] buf=new byte[4096];int n;
                while((n=in.read(buf))!=-1){
                    out.write(buf,0,n);
                    if(out.size()>limit)throw new Exception("Response too large");
                }
                return out.toString("UTF-8");
            }
        }finally{c.disconnect();}
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

    private void createProgressPdf(Uri uri,String reportJson) throws Exception {
        JSONObject report=new JSONObject(reportJson);
        JSONArray weights=report.getJSONArray("weights");
        if(weights.length()==0 || weights.length()>12000)throw new Exception("Invalid number of weights");
        String name=report.optString("name","Profil");
        if(name.length()>100)name=name.substring(0,100);
        double goal=report.getDouble("goal");
        double height=report.optDouble("height",170);
        double first=weights.getJSONObject(0).getDouble("weight");
        double last=weights.getJSONObject(weights.length()-1).getDouble("weight");
        PdfDocument pdf=new PdfDocument();
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(Color.rgb(24,44,63));
        p.setTextSize(12f);
        try {
            int number=1;
            PdfDocument.Page page=pdf.startPage(
                new PdfDocument.PageInfo.Builder(595,842,number).create());
            Canvas canvas=page.getCanvas();
            canvas.drawColor(Color.WHITE);
            p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
            p.setTextSize(20f);
            canvas.drawText("Mon Évolution IMC - Bilan global",38f,56f,p);
            p.setTypeface(Typeface.DEFAULT);p.setTextSize(12f);
            canvas.drawText("Profil : "+name,38f,85f,p);
            canvas.drawText("Départ : "+String.format(java.util.Locale.FRANCE,"%.1f kg",first)
                +"  Actuel : "+String.format(java.util.Locale.FRANCE,"%.1f kg",last),
                38f,110f,p);
            canvas.drawText("Évolution : "+String.format(java.util.Locale.FRANCE,"%+.1f kg",last-first)
                +"  Objectif : "+String.format(java.util.Locale.FRANCE,"%.1f kg",goal),38f,132f,p);
            if(height>0)canvas.drawText("IMC actuel : "+String.format(java.util.Locale.FRANCE,
                "%.1f",last/Math.pow(height/100d,2)),38f,152f,p);
            drawWeightChart(canvas,weights,goal,178f);
            p.setColor(Color.rgb(37,69,89));
            p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));p.setTextSize(14f);
            canvas.drawText("Historique des pesées",38f,378f,p);
            p.setTypeface(Typeface.DEFAULT);p.setTextSize(11f);
            int y=407;
            for(int i=0;i<weights.length();i++){
                if(y>778){
                    pdf.finishPage(page);
                    page=pdf.startPage(new PdfDocument.PageInfo.Builder(595,842,++number).create());
                    canvas=page.getCanvas();canvas.drawColor(Color.WHITE);
                    p.setTextSize(13f);p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
                    canvas.drawText("Bilan global - "+name+" (suite)",38f,45f,p);
                    p.setTypeface(Typeface.DEFAULT);p.setTextSize(11f);
                    y=75;
                }
                JSONObject w=weights.getJSONObject(i);
                String row=w.optString("date","")+"  "
                    +String.format(java.util.Locale.FRANCE,"%.1f kg",w.getDouble("weight"));
                String note=w.optString("note","");
                if(!note.isEmpty())row+="  "+note.substring(0,Math.min(note.length(),75));
                canvas.drawText(row,38f,(float)y,p);
                y+=17;
            }
            pdf.finishPage(page);
            try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                if(out==null)throw new Exception("PDF destination unavailable");
                pdf.writeTo(out);
            }
        }finally{pdf.close();}
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
