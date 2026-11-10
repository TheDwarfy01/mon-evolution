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
    private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44, SHARE_CREATE = 45, SHARE_OPEN = 46, SHARE_RELINK = 47, BACKUP_RELINK = 48, EXPORT_CSV = 49, EXPORT_PROFILE = 50, PROGRESS_PDF = 51, PHOTO_CAMERA = 52;
    private WebView web;
    private String pendingJson;
    private String pendingPdfJson;
    private String pendingPhotoToken;
    private Uri pendingCameraUri;
    private String pendingCameraFilename;
    private String pendingShareId;
    private String pendingShareName;
    private String pendingShareJson;
    private volatile String pendingReceivedPassword="";
    private String pendingExport;
    private String pendingProgressJson;
    private String pendingInvitationId;
    private String pendingInvitationResourceKey;
    private boolean appPageReady=false;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    // Invalidate outdated background selections whenever a new invitation is loaded.
    private final java.util.concurrent.atomic.AtomicLong receivedLoadEpoch =
        new java.util.concurrent.atomic.AtomicLong();
    private final java.util.concurrent.atomic.AtomicBoolean friendsRefreshRunning =
        new java.util.concurrent.atomic.AtomicBoolean(false);
    private static final String PREFS = "drive_backup";
    private static final String BACKUP_URI = "backup_uri";
    private static final String BACKUP_HASH = "backup_hash";
    private static final String BACKUP_TIME = "backup_time";
    private static final String BACKUP_VERIFIED_AT = "backup_verified_at";
    private static final String BACKUP_VERIFY_STATE = "backup_verify_state";
    private static final String BACKUP_VERIFY_INFO = "backup_verify_info";

    @Override protected void onSaveInstanceState(android.os.Bundle state){
        super.onSaveInstanceState(state);
        if(pendingCameraUri!=null)state.putString("camera_uri",pendingCameraUri.toString());
        if(pendingPhotoToken!=null)state.putString("photo_token",pendingPhotoToken);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if(state!=null){
            String camera=state.getString("camera_uri");
            if(camera!=null)pendingCameraUri=Uri.parse(camera);
            pendingPhotoToken=state.getString("photo_token");
        }
        pendingInvitationId=extractInvitationFileId(getIntent());
        pendingInvitationResourceKey=extractInvitationResourceKey(getIntent());
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
            @Override public void onPageFinished(WebView view,String url) {
                super.onPageFinished(view,url);
                if(url!=null && url.startsWith("file:///android_asset/index.html")) {
                    appPageReady=true;
                    deliverInvitation();
                }
            }
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


    // All externally supplied deep links are parsed and validated by Android
    // before any data reaches the JavaScript UI. No automatic addition.
    private String extractInvitationFileId(Intent intent) {
        if(intent==null || !Intent.ACTION_VIEW.equals(intent.getAction()))return null;
        Uri uri=intent.getData();
        if(uri==null || !"monevolution".equalsIgnoreCase(uri.getScheme())
            || !"share".equalsIgnoreCase(uri.getHost()))return null;
        String id=uri.getQueryParameter("file");
        return id!=null && id.matches("[A-Za-z0-9_-]{10,200}")?id:null;
    }

    private String extractInvitationResourceKey(Intent intent) {
        try {
            if(intent==null)return null;
            Uri uri=intent.getData();
            if(uri==null)return null;
            String value=uri.getQueryParameter("resourcekey");
            return value!=null && value.matches("[A-Za-z0-9_-]{3,200}")?value:null;
        }catch(Exception ignored){return null;}
    }

    private void deliverInvitation() {
        if(!appPageReady || pendingInvitationId==null)return;
        String fileId=pendingInvitationId;
        String resourceKey=pendingInvitationResourceKey;
        pendingInvitationId=null;
        pendingInvitationResourceKey=null;
        web.evaluateJavascript("window.receiveShareInvitation("+JSONObject.quote(fileId)
            +","+JSONObject.quote(resourceKey==null?"":resourceKey)+")",null);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        String fileId=extractInvitationFileId(intent);
        if(fileId!=null){
            pendingInvitationId=fileId;
            pendingInvitationResourceKey=extractInvitationResourceKey(intent);
            if(appPageReady)deliverInvitation();
        }
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
        @JavascriptInterface public boolean saveSharePassword(String id,String pass) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return false;
            try{if(!validNewSharePassword(pass))return false;saveSecret("share_pass_"+id,pass);return true;}catch(Exception e){return false;}
        }
        // Generate using Android SecureRandom, never Math.random().
        @JavascriptInterface public String generateSharePassword(){
            final String upper="ABCDEFGHJKLMNPQRSTUVWXYZ";
            final String lower="abcdefghjkmnpqrstuvwxyz";
            final String digits="23456789";
            final String symbols="!@#$%&*-_";
            final String alphabet=upper+lower+digits+symbols;
            java.security.SecureRandom random=new java.security.SecureRandom();
            char[] password=new char[16];
            password[0]=upper.charAt(random.nextInt(upper.length()));
            password[1]=symbols.charAt(random.nextInt(symbols.length()));
            for(int i=2;i<password.length;i++)password[i]=alphabet.charAt(random.nextInt(alphabet.length()));
            for(int i=password.length-1;i>0;i--){
                int k=random.nextInt(i+1);
                char tmp=password[i];password[i]=password[k];password[k]=tmp;
            }
            return new String(password);
        }
        @JavascriptInterface public void copySharePassword(String password) {
            if(!validNewSharePassword(password))return;
            runOnUiThread(()->{
                android.content.ClipboardManager clipboard=
                    (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                if(clipboard==null)return;
                android.content.ClipData clip=android.content.ClipData.newPlainText("Mot de passe du profil partagé",password);
                clipboard.setPrimaryClip(clip);
                web.evaluateJavascript("showMessage('Mot de passe copié ✓')",null);
            });
        }
        @JavascriptInterface public void sendSharePassword(String password) {
            if(!validNewSharePassword(password))return;
            runOnUiThread(()->{
                try{
                    Intent send=new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_SUBJECT,"Mot de passe Mon Évolution IMC");
                    send.putExtra(Intent.EXTRA_TEXT,"Voici le mot de passe de mon profil partagé Mon Évolution IMC (à conserver confidentiel) : "+password);
                    startActivity(Intent.createChooser(send,"Envoyer le mot de passe séparément"));
                }catch(Exception e){web.evaluateJavascript("showMessage('Impossible d’ouvrir le partage Android')",null);}
            });
        }
        // Never expose an existing password to JavaScript. Read it from encrypted
        // app storage and perform clipboard / Android share operations natively.
        @JavascriptInterface public void copyCurrentSharePassword(String id){
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            try{
                if(!getPreferences(MODE_PRIVATE).contains("share_uri_"+id))throw new Exception();
                String password=readSecret("share_pass_"+id);
                if(password==null || password.length()<6)throw new Exception();
                final String secret=password;
                runOnUiThread(()->{
                    try{
                        android.content.ClipboardManager clipboard=
                            (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                        if(clipboard==null)throw new Exception();
                        android.content.ClipData clip=android.content.ClipData.newPlainText(
                            "Mot de passe du profil partagé",secret);
                        // Android 13+ hides the copied value from clipboard previews.
                        if(android.os.Build.VERSION.SDK_INT>=33){
                            android.os.PersistableBundle extras=new android.os.PersistableBundle();
                            extras.putBoolean(android.content.ClipDescription.EXTRA_IS_SENSITIVE,true);
                            clip.getDescription().setExtras(extras);
                        }
                        clipboard.setPrimaryClip(clip);
                        web.evaluateJavascript("showMessage('Mot de passe actuel copié ✓')",null);
                    }catch(Exception e){web.evaluateJavascript("showMessage('Copie impossible')",null);}
                });
            }catch(Exception e){js("shareCurrentPasswordUnavailable()");}
        }
        @JavascriptInterface public void sendCurrentSharePassword(String id){
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            try{
                if(!getPreferences(MODE_PRIVATE).contains("share_uri_"+id))throw new Exception();
                String password=readSecret("share_pass_"+id);
                if(password==null || password.length()<6)throw new Exception();
                final String secret=password;
                runOnUiThread(()->{
                    try{
                        Intent send=new Intent(Intent.ACTION_SEND);
                        send.setType("text/plain");
                        send.putExtra(Intent.EXTRA_SUBJECT,"Mot de passe Mon Évolution IMC");
                        send.putExtra(Intent.EXTRA_TEXT,
                            "Voici le mot de passe actuel de mon profil partagé Mon Évolution IMC (à conserver confidentiel) : "+secret);
                        startActivity(Intent.createChooser(send,"Envoyer le mot de passe actuel"));
                    }catch(Exception e){web.evaluateJavascript("showMessage('Envoi impossible')",null);}
                });
            }catch(Exception e){js("shareCurrentPasswordUnavailable()");}
        }
        @JavascriptInterface public boolean hasSharePassword(String id){
            return id!=null && getPreferences(MODE_PRIVATE).contains("share_pass_"+id);
        }
        @JavascriptInterface public void loadSharedPublicPassword(String url,String pass){
            pendingReceivedPassword=pass==null?"":pass;
            loadSharedPublic(url);
        }
        @JavascriptInterface public void openSharedPassword(String pass){
            pendingReceivedPassword=pass==null?"":pass;
            openShared();
        }
        // Rotates the encryption of the *existing* linked document in place.
        // Always verify that its current contents can be decrypted by the saved
        // password. The selected SAF Uri and its invitations are not changed.
        @JavascriptInterface public void rotateSharePassword(String id,String nextPassword) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}")
                || !validNewSharePassword(nextPassword)){
                js("sharePasswordChangeFailed('Mot de passe invalide : 6 caractères minimum, une majuscule et un caractère spécial.')");
                return;
            }
            final String uriValue=getPreferences(MODE_PRIVATE).getString("share_uri_"+id,null);
            if(uriValue==null){
                js("sharePasswordChangeFailed('Aucun fichier partagé relié à ce profil.')");
                return;
            }
            io.execute(()->{
                try{
                    String oldPassword=readSecret("share_pass_"+id);
                    if(oldPassword==null)throw new Exception("Ancien mot de passe introuvable.");
                    if(oldPassword.equals(nextPassword))throw new Exception("Le nouveau mot de passe doit être différent.");
                    Uri uri=Uri.parse(uriValue);
                    String previous=readSafJson(uri,40_000_000);
                    JSONObject content=decodeShared(previous,oldPassword);
                    if(!"mon-evolution-lecture-seule".equals(content.optString("format")))
                        throw new Exception("Contenu du partage invalide.");
                    // Encrypt exactly the current remote document: no stale local profile.
                    String encrypted=encryptShared(content.toString(),nextPassword);
                    // Recheck before overwriting in case the document changed elsewhere.
                    if(!previous.equals(readSafJson(uri,40_000_000)))
                        throw new Exception("Le fichier a été modifié. Actualise et réessaie.");
                    try {
                        writeShared(uri,encrypted);
                        // A successful write call alone is not proof that the cloud
                        // provider kept the complete replacement document.
                        if(!encrypted.equals(readSafJson(uri,40_000_000)))
                            throw new Exception("Le stockage n’a pas confirmé le nouveau fichier.");
                        saveSecret("share_pass_"+id,nextPassword);
                    }catch(Exception changeError){
                        // Restore the previous remote contents whenever the new
                        // password cannot be saved or its upload cannot be checked.
                        try{
                            writeShared(uri,previous);
                            if(!previous.equals(readSafJson(uri,40_000_000)))
                                throw new Exception("Restauration non confirmée");
                        }catch(Exception rollbackError){
                            throw new Exception("ATTENTION : état du partage incertain. Désactive la synchronisation et vérifie le fichier avant toute modification.");
                        }
                        throw new Exception("Changement annulé, ancien mot de passe conservé : "+changeError.getMessage());
                    }
                    js("sharePasswordChanged()");
                }catch(Exception e){
                    js("sharePasswordChangeFailed("+JSONObject.quote(
                        e.getMessage()==null?"Échec de modification du mot de passe.":e.getMessage())+")");
                }
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
        @JavascriptInterface public boolean shareAvatarEnabled(String id) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return false;
            return getPreferences(MODE_PRIVATE).getBoolean("share_avatar_" + id, true);
        }
        @JavascriptInterface public void setShareAvatar(String id, boolean enabled) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return;
            getPreferences(MODE_PRIVATE).edit().putBoolean("share_avatar_" + id, enabled).apply();
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
        @JavascriptInterface public String getInvitationLink(String profileId) {
            String drive=getShareLink(profileId);
            String id=driveFileId(drive);
            if(id==null)return "";
            // The public landing page contains no personal data. The file ID
            // itself grants no read permission unless the Drive owner permits it.
            String key=driveResourceKey(drive);
            return "https://thedwarfy01.github.io/mon-evolution/share.html?file="+id
                +(key==null?"":"&resourcekey="+Uri.encode(key));
        }
        @JavascriptInterface public void copyShareLink(String id) {
            final String url=getInvitationLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Colle d’abord le lien obtenu dans Google Drive')",null);
                    return;
                }
                android.content.ClipboardManager clipboard=
                    (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Lien du profil partagé",url));
                web.evaluateJavascript("showMessage('Lien d’invitation copié ✓')",null);
            });
        }
        @JavascriptInterface public void sendShareLink(String id) {
            final String url=getInvitationLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Enregistre d’abord le lien Google Drive')",null);
                    return;
                }
                try {
                    Intent send=new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_SUBJECT,"Invitation à mon profil Mon Évolution IMC");
                    send.putExtra(Intent.EXTRA_TEXT,"Je t’invite à consulter mon profil Mon Évolution IMC en lecture seule. Ouvre ce lien sur ton téléphone, puis choisis « Ouvrir dans Mon Évolution » :\n"+url);
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
    @JavascriptInterface public String receivedSyncInfo(String key){
        if(!isReceivedSaved(key))return "{}";
        return getPreferences(MODE_PRIVATE).getString("received_sync_"+key,"{}");
    }
    @JavascriptInterface public void updateReceivedPassword(String key,String password){
        if(!isReceivedSaved(key)||password==null||password.length()<6||password.length()>512){
            js("receivedPasswordUpdateFailed("+JSONObject.quote(key==null?"":key)+
                ",'invalid')");return;
        }
        final String freshPassword=password;
        io.execute(()->{
            try{
                JSONArray list=new JSONArray(getPreferences(MODE_PRIVATE)
                    .getString("received_profiles","[]"));
                JSONObject item=null;
                for(int i=0;i<list.length();i++){
                    JSONObject value=list.getJSONObject(i);
                    if(key.equals(value.optString("key"))){item=value;break;}
                }
                if(item==null)return; // Removed in the meantime; do not resurrect.
                String kind=item.getString("kind"),source=item.getString("source");
                String raw;
                if("public".equals(kind)){
                    String fileId=driveFileId(source);
                    if(fileId==null)throw new Exception("notfound");
                    raw=new String(fetchPublicProfile(fileId,driveResourceKey(source)),
                        StandardCharsets.UTF_8);
                }else if("private".equals(kind))
                    raw=readSafJson(Uri.parse(source),40_000_000);
                else throw new Exception("format");
                // Decrypt and validate *before* storing or replacing the previous password.
                JSONObject doc=decodeShared(raw,freshPassword);
                if(!isReceivedSaved(key))return;
                saveSecret("receive_pass_"+key,freshPassword);
                synchronized(MainActivity.this){
                    JSONArray latest=new JSONArray(getPreferences(MODE_PRIVATE)
                        .getString("received_profiles","[]"));
                    for(int i=0;i<latest.length();i++){
                        JSONObject entry=latest.getJSONObject(i);
                        if(key.equals(entry.optString("key"))){
                            fillFriendOverview(entry,doc);
                            getPreferences(MODE_PRIVATE).edit()
                                .putString("received_profiles",latest.toString()).apply();
                            break;
                        }
                    }
                }
                recordReceivedSync(key,"ok");
                js("receivedPasswordUpdateSucceeded("+JSONObject.quote(key)+")");
            }catch(Exception e){
                String code=receivedErrorCode(e);
                if(isReceivedSaved(key)){
                    recordReceivedSync(key,code);
                    js("receivedPasswordUpdateFailed("+JSONObject.quote(key)+","+
                        JSONObject.quote(code)+")");
                }
            }
        });
    }

    // Only a validated read updates the cached friend summary. Never switch tabs.
    private JSONObject readFriendDocument(JSONObject item,String key) throws Exception{
        String kind=item.getString("kind"),source=item.getString("source"),raw;
        if("public".equals(kind)){
            String file=driveFileId(source);
            if(file==null)throw new Exception("notfound");
            raw=new String(fetchPublicProfile(file,driveResourceKey(source)),StandardCharsets.UTF_8);
        }else if("private".equals(kind))raw=readSafJson(Uri.parse(source),40_000_000);
        else throw new Exception("invalid_json");
        return decodeShared(raw,readSecret("receive_pass_"+key));
    }
    private void updateFriendSummary(String key,JSONObject doc) throws Exception{
        synchronized(MainActivity.this){
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            JSONArray latest=new JSONArray(prefs.getString("received_profiles","[]"));
            for(int i=0;i<latest.length();i++){
                JSONObject item=latest.getJSONObject(i);
                if(key.equals(item.optString("key"))){
                    fillFriendOverview(item,doc);
                    prefs.edit().putString("received_profiles",latest.toString()).apply();
                    return;
                }
            }
            throw new Exception("Profil retiré");
        }
    }
    @JavascriptInterface public void refreshFriendOverview(String key){
        if(!isReceivedSaved(key))return;
        recordReceivedSync(key,"pending");
        io.execute(()->{
            if(!isReceivedSaved(key))return;
            try{
                JSONArray list=new JSONArray(getPreferences(MODE_PRIVATE)
                    .getString("received_profiles","[]"));
                JSONObject item=null;
                for(int i=0;i<list.length();i++){
                    JSONObject candidate=list.getJSONObject(i);
                    if(key.equals(candidate.optString("key"))){item=candidate;break;}
                }
                if(item==null)return;
                JSONObject doc=readFriendDocument(item,key);
                if(!isReceivedSaved(key))return;
                updateFriendSummary(key,doc);
                recordReceivedSync(key,"ok");
                js("friendsOverviewUpdated()");
            }catch(Exception e){
                if(isReceivedSaved(key))recordReceivedSync(key,receivedErrorCode(e));
            }
        });
    }
    @JavascriptInterface public void refreshFriendsOverview() {
        if(!friendsRefreshRunning.compareAndSet(false,true))return;
        io.execute(()->{
            int succeeded=0,failed=0;
            try{
                JSONArray saved=new JSONArray(getPreferences(MODE_PRIVATE)
                    .getString("received_profiles","[]"));
                int count=Math.min(saved.length(),30);
                for(int i=0;i<count;i++){
                    JSONObject item;
                    try{item=saved.getJSONObject(i);}catch(Exception e){failed++;continue;}
                    String key=item.optString("key","");
                    if(!isReceivedSaved(key))continue;
                    recordReceivedSync(key,"pending");
                    try{
                        JSONObject doc=readFriendDocument(item,key);
                        if(!isReceivedSaved(key))continue;
                        updateFriendSummary(key,doc);
                        succeeded++;
                        recordReceivedSync(key,"ok");
                        js("friendsOverviewUpdated()");
                    }catch(Exception e){
                        failed++;
                        if(isReceivedSaved(key))recordReceivedSync(key,receivedErrorCode(e));
                    }
                }
            }catch(Exception e){failed++;}
            finally{
                friendsRefreshRunning.set(false);
                js("friendsOverviewUpdated()");
                js("friendsOverviewSyncFinished("+succeeded+","+failed+")");
            }
        });
    }

        @JavascriptInterface public String receivedAvatar(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return "";
            return getPreferences(MODE_PRIVATE).getString("friend_avatar_"+key,"");
        }
        @JavascriptInterface public String listReceivedProfiles() {
            return getPreferences(MODE_PRIVATE).getString("received_profiles","[]");
        }
        @JavascriptInterface public String receivedSelected() {
            return getPreferences(MODE_PRIVATE).getString("received_selected","");
        }
        @JavascriptInterface public boolean forgetReceivedProfile(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return false;
            synchronized(MainActivity.this) {
                try {
                    android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                    JSONArray old=new JSONArray(prefs.getString("received_profiles","[]"));
                    JSONArray remaining=new JSONArray();
                    boolean removed=false;
                    for(int i=0;i<old.length();i++){
                        JSONObject item=old.getJSONObject(i);
                        if(key.equals(item.optString("key")))removed=true;
                        else remaining.put(item);
                    }
                    if(!removed)return false;
                    android.content.SharedPreferences.Editor edit=prefs.edit()
                        .putString("received_profiles",remaining.toString());
                    if(key.equals(prefs.getString("received_selected","")))
                        edit.remove("received_selected");
                    edit.remove("receive_pass_"+key);
                    edit.remove("friend_avatar_"+key);
                    edit.remove("received_sync_"+key);
                    edit.apply();
                    // Never delete the source document or revoke the owner's sharing.
                    return true;
                } catch(Exception ignored){return false;}
            }
        }
        @JavascriptInterface public void loadComparisonProfile(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return;
            io.execute(() -> {
                try {
                    JSONArray saved=new JSONArray(getPreferences(MODE_PRIVATE)
                        .getString("received_profiles","[]"));
                    JSONObject item=null;
                    for(int i=0;i<saved.length();i++){
                        JSONObject candidate=saved.getJSONObject(i);
                        if(key.equals(candidate.optString("key"))){item=candidate;break;}
                    }
                    if(item==null)throw new Exception("Profil non enregistré");
                    String kind=item.getString("kind"),source=item.getString("source");
                    String raw;
                    if("public".equals(kind)){
                        String file=driveFileId(source);
                        if(file==null)throw new Exception("Lien invalide");
                        raw=new String(fetchPublicProfile(file,driveResourceKey(source)),
                            StandardCharsets.UTF_8);
                    }else if("private".equals(kind)){
                        raw=readSafJson(Uri.parse(source),40_000_000);
                    }else throw new Exception("Type non autorisé");
                    JSONObject doc=decodeShared(raw,readSecret("receive_pass_"+key));
                    validateReceived(doc);
                    JSONObject received=doc.getJSONObject("profile");
                    // Comparison is restricted to read-only weight measures.
                    JSONObject output=new JSONObject();
                    output.put("name",received.getString("name"));
                    output.put("height",received.getDouble("height"));
                    output.put("goal",received.getDouble("goal"));
                    output.put("entries",received.getJSONArray("entries"));
                    String b64=android.util.Base64.encodeToString(
                        output.toString().getBytes(StandardCharsets.UTF_8),
                        android.util.Base64.NO_WRAP);
                    js("comparisonProfileLoaded("+JSONObject.quote(key)+","+
                       JSONObject.quote(b64)+")");
                }catch(Exception e){
                    js("comparisonProfileFailed("+JSONObject.quote(key)+")");
                }
            });
        }
        @JavascriptInterface public void selectReceivedProfile(String key) {
            if(!isReceivedSaved(key)){
                // A previously deleted key can still be queued by an old refresh.
                return;
            }
            final long request=receivedLoadEpoch.incrementAndGet();
            io.execute(() -> {
                if(request!=receivedLoadEpoch.get()||!isReceivedSaved(key))return;
                try {
                    JSONArray saved=new JSONArray(getPreferences(MODE_PRIVATE)
                        .getString("received_profiles","[]"));
                    JSONObject item=null;
                    for(int i=0;i<saved.length();i++){
                        JSONObject current=saved.getJSONObject(i);
                        if(key.equals(current.optString("key"))){item=current;break;}
                    }
                    if(item==null)return;
                    String kind=item.getString("kind");
                    String source=item.getString("source");
                    byte[] body;
                    if("public".equals(kind)){
                        String fileId=driveFileId(source);
                        if(fileId==null)throw new Exception("notfound");
                        body=fetchPublicProfile(fileId,driveResourceKey(source));
                    }else if("private".equals(kind)){
                        String raw=readSafJson(Uri.parse(source),40_000_000);
                        body=raw.getBytes(StandardCharsets.UTF_8);
                    }else throw new Exception("format");
                    JSONObject doc=decodeShared(new String(body,StandardCharsets.UTF_8),
                        readSecret("receive_pass_"+key));
                    if(request!=receivedLoadEpoch.get()||!isReceivedSaved(key))return;
                    // No new keys and no change to the user's visible tab.
                    registerReceived(kind,source,doc);
                    getPreferences(MODE_PRIVATE).edit().putString("received_selected",key).apply();
                    recordReceivedSync(key,"ok");
                    String base64=android.util.Base64.encodeToString(
                        doc.toString().getBytes(StandardCharsets.UTF_8),
                        android.util.Base64.NO_WRAP);
                    js("sharedLoaded("+JSONObject.quote(base64)+","+JSONObject.quote(key)+")");
                }catch(Exception e){
                    if(request==receivedLoadEpoch.get()&&isReceivedSaved(key)){
                        String code=receivedErrorCode(e);
                        recordReceivedSync(key,code);
                        js("sharedReadFailed("+JSONObject.quote(code)+","+
                            JSONObject.quote(key)+")");
                    }
                }
            });
        }
        @JavascriptInterface public void loadSharedPublic(String url) {
            final long request=receivedLoadEpoch.incrementAndGet();
            final String pass=pendingReceivedPassword;
            pendingReceivedPassword="";
            String id=driveFileId(url);
            if(id==null){js("sharedPublicFailed('invalid_link')");return;}
            io.execute(() -> {
                if(request!=receivedLoadEpoch.get())return;
                try {
                    byte[] body=fetchPublicProfile(id,driveResourceKey(url));
                    JSONObject doc=decodeShared(new String(body,StandardCharsets.UTF_8),pass);
                    String resourceKey=driveResourceKey(url);
                    String source="https://drive.google.com/file/d/"+id+"/view"
                        +(resourceKey==null?"":"?resourcekey="+Uri.encode(resourceKey));
                    if(request!=receivedLoadEpoch.get())return;
                    String key=registerReceived("public",source,doc);
                    if(pass!=null && pass.length()>=6 && pass.length()<=512)saveSecret("receive_pass_"+key,pass);
                    byte[] clear=doc.toString().getBytes(StandardCharsets.UTF_8);
                    String b64=android.util.Base64.encodeToString(clear,android.util.Base64.NO_WRAP);
                    getPreferences(MODE_PRIVATE).edit()
                        .remove("received_public_url").remove("received_share_uri")
                        .putString("received_selected",key).apply();
                    recordReceivedSync(key,"ok");
                    js("sharedLoaded("+JSONObject.quote(b64)+","+JSONObject.quote(key)+")");
                }catch(Exception e){
                    // Do not show an error from an invitation the user has replaced.
                    if(request==receivedLoadEpoch.get()){
                        String code=receivedErrorCode(e);
                        js("sharedPublicFailed("+JSONObject.quote(code)+")");
                    }
                }
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
                // Google Drive does not always report .json as application/json.
                // Accept the chosen document and validate its JSON contents.
                intent.setType("*/*");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, SHARE_OPEN);
            });
        }
        @JavascriptInterface public void refreshShared() {
            String key=getPreferences(MODE_PRIVATE).getString("received_selected",null);
            if(key!=null){selectReceivedProfile(key);return;}
            String publicUrl=getPreferences(MODE_PRIVATE).getString("received_public_url",null);
            if(publicUrl!=null){loadSharedPublic(publicUrl);return;}
            String value=getPreferences(MODE_PRIVATE).getString("received_share_uri",null);
            if(value!=null)loadShared(Uri.parse(value));
        }
        @JavascriptInterface public String personalReminderSettings(String id) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return "{}";
            SharedPreferences p=getSharedPreferences("reminders",MODE_PRIVATE);
            JSONObject result=new JSONObject();
            try {
                for(String type:new String[]{"meals","photos","breakfast","lunch","dinner","weight","injection","water0","water1","water2","water3","water4","water5","water6","water7","water8","water9","water10","water11","water12","water13","water14","water15","water16","water17","water18","water19","water20","water21","water22","water23"}){
                    String prefix="v2_"+id+"|"+type;
                    JSONObject item=new JSONObject();
                    item.put("enabled",p.getBoolean(prefix+"_enabled",false));
                    item.put("hour",p.getInt(prefix+"_hour",type.equals("weight")?9:20));
                    item.put("minute",p.getInt(prefix+"_minute",0));
                    item.put("weekday",p.getInt(prefix+"_weekday",java.util.Calendar.MONDAY));
                    result.put(type,item);
                }
            }catch(Exception ignored){}
            return result.toString();
        }
        @JavascriptInterface public void setPersonalReminder(String id,String name,String type,boolean enabled,int hour,int minute,int weekday){
            runOnUiThread(() -> {
                ReminderReceiver.configurePersonal(MainActivity.this,id,name,type,enabled,hour,minute,weekday);
                if(enabled&&android.os.Build.VERSION.SDK_INT>=33
                  &&checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
                    requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},72);
            });
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
        // Android Storage Access Framework : l’utilisateur choisit librement un fournisseur
        // installé (Drive, Dropbox, OneDrive, stockage local ou NAS exposé par Android).
        @JavascriptInterface public String backupProviderLabel() {
            String stored=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            if(stored==null)return "";
            try {
                Uri uri=Uri.parse(stored);
                android.content.pm.PackageManager pm=getPackageManager();
                android.content.pm.ProviderInfo info=pm.resolveContentProvider(uri.getAuthority(),0);
                if(info!=null){
                    CharSequence label=info.loadLabel(pm);
                    if(label!=null && label.length()>0)return label.toString();
                }
                String authority=uri.getAuthority();
                if(authority==null)return "Stockage Android";
                if(authority.contains("drive"))return "Google Drive";
                if(authority.contains("dropbox"))return "Dropbox";
                if(authority.contains("onedrive")||authority.contains("skydrive"))return "OneDrive";
                if(authority.contains("documents"))return "Stockage Android";
                return "Fournisseur de fichiers";
            }catch(Exception ignored){return "Stockage Android";}
        }
        @JavascriptInterface public String backupStatus() {
            SharedPreferences prefs = getPreferences(MODE_PRIVATE);
            return (prefs.contains(BACKUP_URI) ? "1" : "0") + "|" + prefs.getLong(BACKUP_TIME, 0);
        }
        @JavascriptInterface public String backupVerificationStatus() {
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            JSONObject result=new JSONObject();
            try{
                result.put("state",prefs.getString(BACKUP_VERIFY_STATE,"unknown"));
                result.put("verifiedAt",prefs.getLong(BACKUP_VERIFIED_AT,0));
                result.put("info",prefs.getString(BACKUP_VERIFY_INFO,""));
            }catch(Exception ignored){}
            return result.toString();
        }
        // Verify readability and backup structure without writing or restoring data.
        @JavascriptInterface public void verifyLinkedBackup(){
            final String reference=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            if(reference==null){
                js("backupVerificationResult('unlinked','Aucune sauvegarde reliée.')");
                return;
            }
            js("backupVerificationResult('pending','Vérification du fichier en lecture seule…')");
            io.execute(()->{
                String state="ok",description="Sauvegarde valide et lisible.";
                try{
                    String raw=readSafJson(Uri.parse(reference),40_000_000);
                    JSONObject wrapper=new JSONObject(raw);
                    if(!"mon-evolution".equals(wrapper.optString("format"))
                        ||wrapper.optInt("version")!=1)throw new Exception("format");
                    JSONArray profiles=wrapper.getJSONObject("data").getJSONArray("profiles");
                    if(profiles.length()<1||profiles.length()>50)throw new Exception("format");
                    int records=0;
                    for(int i=0;i<profiles.length();i++){
                        JSONObject profile=profiles.getJSONObject(i);
                        if(profile.optString("id","").trim().isEmpty()
                            ||profile.optString("name","").trim().isEmpty()
                            ||profile.getDouble("height")<45||profile.getDouble("height")>250
                            ||profile.getDouble("goal")<1||profile.getDouble("goal")>400)
                            throw new Exception("format");
                        JSONArray entries=profile.getJSONArray("entries");
                        if(entries.length()<1||entries.length()>20000)throw new Exception("format");
                        for(int k=0;k<entries.length();k++){
                            JSONObject entry=entries.getJSONObject(k);
                            double weight=entry.getDouble("weight");
                            if(!Double.isFinite(weight)||weight<1||weight>400
                                ||!entry.getString("date").matches("\\d{4}-\\d{2}-\\d{2}"))
                                throw new Exception("format");
                            records++;
                        }
                    }
                    description=profiles.length()+" profil(s) · "+records+" pesée(s) vérifiées.";
                    String expected=getPreferences(MODE_PRIVATE).getString(BACKUP_HASH,null);
                    if(expected!=null&&!expected.equals(stringHash(raw))){
                        state="conflict";
                        description="Fichier valide, mais modifié depuis la dernière sauvegarde connue. Vérifier avant de remplacer.";
                    }
                }catch(Exception e){
                    state="error";
                    description="Impossible de lire ou valider le fichier. Les données locales restent inchangées.";
                }
                // Discard the result if the user disconnected or relinked mid-check.
                if(!reference.equals(getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null)))return;
                getPreferences(MODE_PRIVATE).edit()
                    .putString(BACKUP_VERIFY_STATE,state)
                    .putString(BACKUP_VERIFY_INFO,description)
                    .putLong(BACKUP_VERIFIED_AT,System.currentTimeMillis()).apply();
                js("backupVerificationResult("+JSONObject.quote(state)+","+JSONObject.quote(description)+")");
            });
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
            if(token==null || token.length()>150)return;
            runOnUiThread(() -> {
                pendingPhotoToken=token;
                new android.app.AlertDialog.Builder(MainActivity.this)
                    .setTitle("Ajouter une photo")
                    .setItems(new String[]{"📷 Prendre une photo","🖼️ Choisir dans la galerie"},
                        (dialog,which)->{
                            if(which==0)openCamera();
                            else openPhotoGallery();
                        })
                    .show();
            });
        }
        private void openPhotoGallery(){
            pendingCameraUri=null;
            Intent intent=new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("image/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            try{startActivityForResult(intent,PHOTO);}
            catch(Exception e){js("showMessage('Galerie indisponible')");}
        }
        private void openCamera(){
            pendingCameraUri=null;
            pendingCameraFilename=null;
            try {
                String filename="capture-"+java.util.UUID.randomUUID()+".jpg";
                Uri uri=CameraPhotoProvider.uriFor(filename);
                pendingCameraUri=uri;
                pendingCameraFilename=filename;
                Intent intent=new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                intent.putExtra(android.provider.MediaStore.EXTRA_OUTPUT,uri);
                intent.setClipData(android.content.ClipData.newUri(
                    getContentResolver(),"Photo de repas",uri));
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                // ClipData grants access to the cache-backed content URI on Samsung.
                startActivityForResult(intent,PHOTO_CAMERA);
            }catch(Exception e){
                if(pendingCameraUri!=null){
                    try{getContentResolver().delete(pendingCameraUri,null,null);}
                    catch(Exception ignored){}
                }
                pendingCameraUri=null;pendingCameraFilename=null;
                pendingPhotoToken=null;
                js("showMessage('La caméra ne peut pas être ouverte. Utilise la galerie.')");
            }
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if(request==PHOTO_CAMERA){
            final Uri cameraUri=pendingCameraUri;
            pendingCameraUri=null;
            pendingCameraFilename=null;
            if(result!=RESULT_OK){
                if(cameraUri!=null)try{getContentResolver().delete(cameraUri,null,null);}
                    catch(Exception ignored){}
                pendingPhotoToken=null;
                return;
            }
            final String token=pendingPhotoToken;
            pendingPhotoToken=null;
            final android.graphics.Bitmap thumbnail=data!=null
                && data.getExtras()!=null && data.getExtras().get("data") instanceof android.graphics.Bitmap
                ?(android.graphics.Bitmap)data.getExtras().get("data"):null;
            io.execute(() -> {
                try{
                    String photo;
                    try{
                        if(cameraUri==null)throw new Exception("Capture sans destination");
                        photo=compressedPhoto(cameraUri);
                    }catch(Exception ex){
                        // Some camera apps return only a thumbnail: handle gracefully.
                        photo=compressedThumbnail(thumbnail);
                    }
                    js("photoPicked("+JSONObject.quote(token)+","+JSONObject.quote(photo)+")");
                }catch(Exception e){js("showMessage('La caméra n’a renvoyé aucune photo. Essaie la galerie si le problème persiste.')");}
                finally{
                    if(cameraUri!=null)try{getContentResolver().delete(cameraUri,null,null);}
                        catch(Exception ignored){}
                    if(thumbnail!=null && !thumbnail.isRecycled())thumbnail.recycle();
                }
            });
            return;
        }
        if(result!=RESULT_OK || data==null || data.getData()==null)return;
        Uri uri=data.getData();
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
                JSONObject existing=decodeShared(document.toString(),
                    readSecret("share_pass_"+pendingShareId)).getJSONObject("profile");
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
                if(!persistUri(uri,false))
                    throw new Exception("Le fournisseur ne permet pas de conserver l’accès");
                getPreferences(MODE_PRIVATE).edit()
                    .remove("received_public_url").remove("received_share_uri").apply();
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
        // Birth date and growth-reference sex are shared only with this
        // explicitly selected profile, never with other private profiles.
        String birth=input.optString("birthDate","");
        String sex=input.optString("sex","");
        if(birth.matches("\\d{4}-\\d{2}-\\d{2}") && ("male".equals(sex)||"female".equals(sex))){
            profile.put("birthDate",birth);
            profile.put("sex",sex);
        }
        JSONArray entries=input.getJSONArray("entries");
        if(entries.length()==0 || entries.length()>20000) throw new Exception("Pesées manquantes");
        profile.put("entries",entries);
        // Include only this profile's chosen portrait, never any other profile.
        String avatar=input.optString("avatar","");
        if(getPreferences(MODE_PRIVATE).getBoolean("share_avatar_"+id,true)
            && avatar.startsWith("data:image/jpeg;base64,") && avatar.length()<250000)
            profile.put("avatar",avatar);
        // Whitelist: no other profiles or backup private metadata.
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
        return encryptShared(result,readSecret("share_pass_"+id));
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
                    if(!getPreferences(MODE_PRIVATE).contains("share_pass_"+id)){
                        js("sharedSyncNeedsPassword()");
                        continue;
                    }
                    try {
                        String document=makeSharedDocument(id,p);
                        writeShared(Uri.parse(value),document);
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));
                    } catch(Exception e) {
                        // A broken Drive permission must not interrupt meal editing.
                        js("sharedSyncFailed()");
                    }
                }
            } catch(Exception ignored) { }
        });
    }

    private boolean isReceivedSaved(String key){
        if(key==null || !key.matches("[a-f0-9-]{36}"))return false;
        try{
            JSONArray list=new JSONArray(getPreferences(MODE_PRIVATE)
                .getString("received_profiles","[]"));
            for(int i=0;i<list.length();i++)
                if(key.equals(list.getJSONObject(i).optString("key")))return true;
        }catch(Exception ignored){}
        return false;
    }
    private String receivedErrorCode(Exception failure){
        for(Throwable cur=failure;cur!=null;cur=cur.getCause()){
            if(cur instanceof javax.crypto.AEADBadTagException)return "password";
        }
        String msg=failure==null?"":String.valueOf(failure.getMessage());
        if(msg.contains("Mot de passe")||msg.contains("password")||msg.contains("Invalid secret"))
            return "password";
        if("forbidden".equals(msg))return "access";
        if("notfound".equals(msg))return "missing";
        if("network".equals(msg))return "network";
        if("html".equals(msg))return "preview";
        if("invalid_json".equals(msg)||msg.contains("Format")||msg.contains("invalide"))
            return "format";
        return "error";
    }
    private void recordReceivedSync(String key,String code) {
        if(!isReceivedSaved(key))return;
        try {
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            JSONObject saved=new JSONObject(prefs.getString("received_sync_"+key,"{}"));
            long now=System.currentTimeMillis();
            saved.put("state",code);
            saved.put("attemptAt",now);
            if("ok".equals(code))saved.put("successAt",now);
            prefs.edit().putString("received_sync_"+key,saved.toString()).apply();
            js("friendSyncUpdated("+JSONObject.quote(key)+","+JSONObject.quote(code)+")");
        }catch(Exception ignored){}
    }
    private void loadShared(Uri uri) {
        final long request=receivedLoadEpoch.incrementAndGet();
        final String pass=pendingReceivedPassword;
        pendingReceivedPassword="";
        io.execute(() -> {
            if(request!=receivedLoadEpoch.get())return;
            try {
                String raw=readSafJson(uri,40_000_000);
                JSONObject doc=decodeShared(raw,pass);
                if(request!=receivedLoadEpoch.get())return;
                String key=registerReceived("private",uri.toString(),doc);
                if(pass!=null && pass.length()>=6 && pass.length()<=512)saveSecret("receive_pass_"+key,pass);
                raw=doc.toString();
                getPreferences(MODE_PRIVATE).edit().putString("received_selected",key).apply();
                String encoded=android.util.Base64.encodeToString(
                    raw.getBytes(StandardCharsets.UTF_8),android.util.Base64.NO_WRAP);
                recordReceivedSync(key,"ok");
                js("sharedLoaded("+JSONObject.quote(encoded)+","+JSONObject.quote(key)+")");
            }catch(Exception e){
                if(request==receivedLoadEpoch.get())
                    js("sharedReadFailed("+JSONObject.quote(receivedErrorCode(e))+",null)");
            }
        });
    }


    // JS callbacks are dispatched only on the Android UI thread.
    private void js(String source) {
        runOnUiThread(() -> {
            if(web!=null)web.evaluateJavascript(source,null);
        });
    }

    private javax.crypto.SecretKey secretKey() throws Exception {
        java.security.KeyStore store=java.security.KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        java.security.Key k=store.getKey("mon_evolution_secrets",null);
        if(k!=null)return (javax.crypto.SecretKey)k;
        javax.crypto.KeyGenerator gen=javax.crypto.KeyGenerator.getInstance("AES","AndroidKeyStore");
        gen.init(new android.security.keystore.KeyGenParameterSpec.Builder("mon_evolution_secrets",
            android.security.keystore.KeyProperties.PURPOSE_ENCRYPT |
            android.security.keystore.KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes("GCM").setEncryptionPaddings("NoPadding").setKeySize(256).build());
        return gen.generateKey();
    }
    private boolean validTenCode(String input) {
        if(input==null || input.length()!=10)return false;
        int digits=0,uppercase=0,symbols=0;
        for(char c:input.toCharArray()){
            if(c>='0' && c<='9')digits++;
            else if(c>='A' && c<='Z')uppercase++;
            else if("!@#$%&*?._-".indexOf(c)>=0)symbols++;
            else if(c>='a' && c<='z'){}
            else return false;
        }
        return digits>=4 && uppercase>=1 && symbols>=1;
    }
    // New outgoing share passwords: six characters, one uppercase and one symbol.
    // Existing stored passwords remain compatible.
    private boolean validNewSharePassword(String input) {
        if(input==null || input.length()<6 || input.length()>512)return false;
        boolean uppercase=false,special=false;
        for(int i=0;i<input.length();i++){
            char c=input.charAt(i);
            if(c>='A' && c<='Z')uppercase=true;
            if(!Character.isLetterOrDigit(c))special=true;
        }
        return uppercase && special;
    }
    private void saveSecret(String name,String value) throws Exception {
        if(value==null || value.length()<6 || value.length()>512)
            throw new Exception("Invalid secret");
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.ENCRYPT_MODE,secretKey());
        JSONObject o=new JSONObject();
        o.put("iv",android.util.Base64.encodeToString(c.getIV(),2));
        o.put("data",android.util.Base64.encodeToString(c.doFinal(value.getBytes(StandardCharsets.UTF_8)),2));
        getPreferences(MODE_PRIVATE).edit().putString(name,o.toString()).apply();
    }
    private String readSecret(String name) throws Exception {
        String raw=getPreferences(MODE_PRIVATE).getString(name,null);
        if(raw==null)return null;
        JSONObject o=new JSONObject(raw);
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.DECRYPT_MODE,secretKey(),
            new javax.crypto.spec.GCMParameterSpec(128,android.util.Base64.decode(o.getString("iv"),0)));
        return new String(c.doFinal(android.util.Base64.decode(o.getString("data"),0)),StandardCharsets.UTF_8);
    }
    private javax.crypto.SecretKey deriveKey(String password,byte[] salt) throws Exception {
        if(password==null || password.length()<6 || password.length()>512)
            throw new Exception("Mot de passe de partage : 6 caractères minimum");
        javax.crypto.spec.PBEKeySpec spec=new javax.crypto.spec.PBEKeySpec(password.toCharArray(),salt,210000,256);
        byte[] raw=javax.crypto.SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
        spec.clearPassword();
        javax.crypto.SecretKey key=new javax.crypto.spec.SecretKeySpec(raw,"AES");
        java.util.Arrays.fill(raw,(byte)0);
        return key;
    }
    private String encryptShared(String plain,String password) throws Exception {
        byte[] salt=new byte[16],nonce=new byte[12];
        java.security.SecureRandom random=new java.security.SecureRandom();
        random.nextBytes(salt);random.nextBytes(nonce);
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.ENCRYPT_MODE,deriveKey(password,salt),
            new javax.crypto.spec.GCMParameterSpec(128,nonce));
        c.updateAAD("mon-evolution-chiffre-v1".getBytes(StandardCharsets.UTF_8));
        JSONObject result=new JSONObject();
        result.put("format","mon-evolution-chiffre");
        result.put("version",1);result.put("iterations",210000);
        result.put("alg","AES-256-GCM");
        result.put("salt",android.util.Base64.encodeToString(salt,2));
        result.put("nonce",android.util.Base64.encodeToString(nonce,2));
        result.put("data",android.util.Base64.encodeToString(c.doFinal(plain.getBytes(StandardCharsets.UTF_8)),2));
        return result.toString();
    }
    private JSONObject decodeShared(String raw,String password) throws Exception {
        JSONObject o=new JSONObject(raw);
        if("mon-evolution-lecture-seule".equals(o.optString("format"))){
            validateReceived(o);return o;
        }
        if(!"mon-evolution-chiffre".equals(o.optString("format"))
            ||o.optInt("version")!=1 ||o.optInt("iterations")!=210000
            ||!"AES-256-GCM".equals(o.optString("alg")))
            throw new Exception("Format non reconnu");
        byte[] salt=android.util.Base64.decode(o.getString("salt"),0);
        byte[] nonce=android.util.Base64.decode(o.getString("nonce"),0);
        byte[] ciphertext=android.util.Base64.decode(o.getString("data"),0);
        if(salt.length!=16 || nonce.length!=12 || ciphertext.length>40000000)
            throw new Exception("Enveloppe invalide");
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.DECRYPT_MODE,deriveKey(password,salt),
            new javax.crypto.spec.GCMParameterSpec(128,nonce));
        c.updateAAD("mon-evolution-chiffre-v1".getBytes(StandardCharsets.UTF_8));
        JSONObject doc=new JSONObject(new String(c.doFinal(ciphertext),StandardCharsets.UTF_8));
        validateReceived(doc);
        return doc;
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
    private String driveResourceKey(String link) {
        if(link==null)return null;
        try{
            Uri uri=Uri.parse(link);
            if(!"https".equalsIgnoreCase(uri.getScheme()) ||
               !"drive.google.com".equalsIgnoreCase(uri.getHost()))return null;
            String value=uri.getQueryParameter("resourcekey");
            return value!=null && value.matches("[A-Za-z0-9_-]{3,200}")?value:null;
        }catch(Exception ignored){return null;}
    }

    private boolean googleDriveDownloadHost(java.net.URL target) {
        if(!"https".equalsIgnoreCase(target.getProtocol()))return false;
        String host=target.getHost().toLowerCase(java.util.Locale.ROOT);
        return host.equals("drive.google.com")
            || host.equals("drive.usercontent.google.com")
            || host.equals("docs.google.com")
            || host.endsWith(".googleusercontent.com");
    }

    // Google Drive may return an HTML preview instead of the public JSON file.
    // These Google-hosted download forms are compatibility fallbacks, not a
    // replacement for an authenticated Google Drive API integration.
    private byte[] fetchPublicProfile(String id,String key) throws Exception {
        if(id==null || !id.matches("[A-Za-z0-9_-]{10,200}"))
            throw new Exception("notfound");
        if(key!=null && !key.matches("[A-Za-z0-9_-]{3,200}"))
            throw new Exception("forbidden");
        String suffix=key==null?"":"&resourcekey="+Uri.encode(key);
        String[] endpoints={
            "https://drive.usercontent.google.com/download?id="+id+"&export=download&confirm=t"+suffix,
            "https://drive.usercontent.google.com/download?id="+id+suffix,
            "https://drive.google.com/uc?export=download&id="+id+"&confirm=t"+suffix,
            "https://drive.google.com/uc?export=download&id="+id+suffix
        };
        String error="network";
        for(String endpoint:endpoints){
            try{
                byte[] body=downloadDriveCandidate(new java.net.URL(endpoint),id,key);
                String text=new String(body,StandardCharsets.UTF_8).trim();
                if(text.startsWith("\uFEFF"))text=text.substring(1).trim();
                if(!text.startsWith("{"))throw new Exception("html");
                JSONObject json;
                try{
                    json=new JSONObject(text);
                    if(json.optInt("version")!=1)throw new Exception("invalid_json");
                    if("mon-evolution-lecture-seule".equals(json.optString("format")))
                        json.getJSONObject("profile").getJSONArray("entries");
                    else if("mon-evolution-chiffre".equals(json.optString("format")))
                        json.getString("data");
                    else throw new Exception("invalid_json");
                }catch(Exception ignored){throw new Exception("invalid_json");}
                return text.getBytes(StandardCharsets.UTF_8);
            }catch(Exception e){
                String code=e.getMessage();
                if("too_large".equals(code) || "invalid_json".equals(code))throw e;
                if("html".equals(code))error="html";
                else if("forbidden".equals(code)&&!"html".equals(error))error="forbidden";
                else if("notfound".equals(code)&&"network".equals(error))error="notfound";
            }
        }
        throw new Exception(error);
    }

    private byte[] downloadDriveCandidate(java.net.URL start,String fileId,String key)
        throws Exception {
        java.net.URL target=start;
        for(int hop=0;hop<7;hop++){
            if(!googleDriveDownloadHost(target))throw new Exception("forbidden");
            java.net.HttpURLConnection connection=
                (java.net.HttpURLConnection)target.openConnection();
            try{
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(15000);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept","application/json,application/octet-stream,*/*");
                connection.setRequestProperty("User-Agent","Mozilla/5.0 (Linux; Android 14) MonEvolutionIMC/1.6.31");
                if(key!=null)connection.setRequestProperty("X-Goog-Drive-Resource-Keys",
                    fileId+"/"+key);
                int status=connection.getResponseCode();
                if(status>=300&&status<400){
                    String location=connection.getHeaderField("Location");
                    if(location==null)throw new Exception("network");
                    target=new java.net.URL(target,location);
                    continue;
                }
                if(status==401||status==403)throw new Exception("forbidden");
                if(status==404||status==410)throw new Exception("notfound");
                if(status!=200)throw new Exception("network");
                try(InputStream in=connection.getInputStream()){
                    if(in==null)throw new Exception("network");
                    java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                    byte[] buffer=new byte[8192];
                    int read;
                    while((read=in.read(buffer))!=-1){
                        out.write(buffer,0,read);
                        if(out.size()>15_000_000)throw new Exception("too_large");
                    }
                    byte[] result=out.toByteArray();
                    String first=new String(result,0,Math.min(160,result.length),
                        StandardCharsets.UTF_8).trim().toLowerCase(java.util.Locale.ROOT);
                    if(first.startsWith("<!doctype")||first.startsWith("<html")
                        ||first.startsWith("<head")||first.startsWith("<body"))
                        throw new Exception("html");
                    return result;
                }
            }finally{connection.disconnect();}
        }
        throw new Exception("network");
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
    // The indexed list is local metadata. Never merge received profiles into the
    // editable backup data and never delete a remote document when forgetting one.
    private void validateReceived(JSONObject doc) throws Exception {
        if(!"mon-evolution-lecture-seule".equals(doc.optString("format"))
            || doc.optInt("version")!=1)throw new Exception("Format de partage invalide");
        JSONObject p=doc.getJSONObject("profile");
        String name=p.getString("name");
        if(name.trim().isEmpty() || name.length()>100)throw new Exception("Nom invalide");
        double height=p.getDouble("height"),goal=p.getDouble("goal");
        if(!Double.isFinite(height) || height<45 || height>250 ||
            !Double.isFinite(goal) || goal<1 || goal>400)
            throw new Exception("Données du profil invalides");
        String avatar=p.optString("avatar","");
        if(!avatar.isEmpty() &&
            (!avatar.startsWith("data:image/jpeg;base64,") || avatar.length()>=250000))
            throw new Exception("Photo de profil invalide");
        JSONArray entries=p.getJSONArray("entries");
        if(entries.length()<1 || entries.length()>20000)
            throw new Exception("Historique invalide");
        for(int i=0;i<entries.length();i++){
            JSONObject e=entries.getJSONObject(i);
            double w=e.getDouble("weight");
            if(!Double.isFinite(w)||w<1||w>400||
                !e.getString("date").matches("\\d{4}-\\d{2}-\\d{2}"))
                throw new Exception("Pesée invalide");
        }
    }

    private void fillFriendOverview(JSONObject entry,JSONObject document) throws Exception {
        JSONObject profile=document.getJSONObject("profile");
        String key=entry.optString("key","");
        if(key.matches("[a-f0-9-]{36}")){
            String portrait=profile.optString("avatar","");
            if(portrait.startsWith("data:image/jpeg;base64,") && portrait.length()<250000)
                getPreferences(MODE_PRIVATE).edit().putString("friend_avatar_"+key,portrait).apply();
            else
                getPreferences(MODE_PRIVATE).edit().remove("friend_avatar_"+key).apply();
        }
        JSONArray weights=profile.getJSONArray("entries");
        JSONObject first=null,last=null;
        for(int i=0;i<weights.length();i++){
            JSONObject current=weights.getJSONObject(i);
            if(first==null || current.getString("date").compareTo(first.getString("date"))<0)first=current;
            if(last==null || current.getString("date").compareTo(last.getString("date"))>0)last=current;
        }
        if(first==null || last==null)throw new Exception("Missing weights");
        entry.put("previewStart",first.getDouble("weight"));
        entry.put("previewCurrent",last.getDouble("weight"));
        entry.put("previewGoal",profile.getDouble("goal"));
        entry.put("previewDate",last.getString("date"));
        entry.put("previewCount",weights.length());
    }


    private synchronized String registerReceived(String kind,String source,JSONObject doc)
        throws Exception {
        validateReceived(doc);
        if(!"public".equals(kind)&&!"private".equals(kind))
            throw new Exception("Source de partage inconnue");
        if(source==null || source.length()>2500)
            throw new Exception("Lien Drive invalide");
        android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
        JSONArray list;
        try{list=new JSONArray(prefs.getString("received_profiles","[]"));}
        catch(Exception ignored){list=new JSONArray();}
        String name=doc.getJSONObject("profile").getString("name");
        for(int i=0;i<list.length();i++){
            JSONObject entry=list.getJSONObject(i);
            if(kind.equals(entry.optString("kind")) &&
                source.equals(entry.optString("source"))){
                entry.put("name",name);
                fillFriendOverview(entry,doc);
                prefs.edit().putString("received_profiles",list.toString()).apply();
                return entry.getString("key");
            }
        }
        if(list.length()>=100)throw new Exception("Trop de profils partagés");
        String key=java.util.UUID.randomUUID().toString();
        JSONObject item=new JSONObject();
        item.put("key",key);
        item.put("name",name);
        item.put("kind",kind);
        item.put("source",source);
        fillFriendOverview(item,doc);
        list.put(item);
        prefs.edit().putString("received_profiles",list.toString()).apply();
        return key;
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
    private String compressedThumbnail(android.graphics.Bitmap bitmap) throws Exception {
        if(bitmap==null)throw new Exception("Aucune image reçue");
        java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,65,out);
        if(out.size()>130000){
            out.reset();
            bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,40,out);
        }
        if(out.size()>180000)throw new Exception("Photo trop volumineuse");
        return "data:image/jpeg;base64,"+
            android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP);
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
        float scale = Math.min(1f, 1000f / longest);
        Bitmap small=Bitmap.createScaledBitmap(decoded,
            Math.max(1,Math.round(decoded.getWidth()*scale)),
            Math.max(1,Math.round(decoded.getHeight()*scale)),true);
        java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream();
        for(int quality:new int[]{86,78,70,62,54,46}){
            output.reset();
            small.compress(Bitmap.CompressFormat.JPEG,quality,output);
            if(output.size()<=170_000)break;
        }
        if(output.size()>170_000){
            Bitmap reduced=Bitmap.createScaledBitmap(small,
                Math.max(1,Math.round(small.getWidth()*.75f)),
                Math.max(1,Math.round(small.getHeight()*.75f)),true);
            output.reset();reduced.compress(Bitmap.CompressFormat.JPEG,60,output);
            reduced.recycle();
        }
        if (small!=decoded)small.recycle();
        decoded.recycle();
        if(output.size()>180_000)throw new Exception("Photo trop volumineuse");
        return "data:image/jpeg;base64,"+android.util.Base64.encodeToString(
            output.toByteArray(),android.util.Base64.NO_WRAP);
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
