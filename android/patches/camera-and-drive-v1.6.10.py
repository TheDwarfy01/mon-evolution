#!/usr/bin/env python3
"""v1.6.10: camera/gallery choice and non-disruptive Drive sharing failures."""
from pathlib import Path
root=Path("android/source-1.6.10/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(p,a,b):
    s=p.read_text(encoding="utf-8")
    n=s.count(a)
    assert n==1,(str(p),n,a[:130])
    p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 25","versionCode 26")
R(g,"versionName '1.6.9'","versionName '1.6.10'")
R(m,'android:versionCode="25" android:versionName="1.6.9"','android:versionCode="26" android:versionName="1.6.10"')
R(h,'Version installée : <strong>1.6.9</strong>','Version installée : <strong>1.6.10</strong>')
R(h,'const installed="1.6.9";','const installed="1.6.10";')
R(j,"MonEvolutionIMC/1.6.9","MonEvolutionIMC/1.6.10")
R(j,'EXPORT_PROFILE = 50, PROGRESS_PDF = 51;', 'EXPORT_PROFILE = 50, PROGRESS_PDF = 51, PHOTO_CAMERA = 52;')
R(j,'    private String pendingPhotoToken;',
'''    private String pendingPhotoToken;
    private Uri pendingCameraUri;''')
# Native two-way choice, full-resolution output on Android 10+, thumbnail fallback on older Android.
R(j,'''        @JavascriptInterface public void pickPhoto(String token) {
            if (token == null || token.length() > 150) return;
            runOnUiThread(() -> {
                pendingPhotoToken = token;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.setType("image/*");
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(intent, PHOTO);
            });
        }''',
'''        @JavascriptInterface public void pickPhoto(String token) {
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
            try{
                Intent intent=new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                if(android.os.Build.VERSION.SDK_INT>=29){
                    android.content.ContentValues values=new android.content.ContentValues();
                    values.put(android.provider.MediaStore.Images.Media.DISPLAY_NAME,
                        "mon-evolution-temp-"+System.currentTimeMillis()+".jpg");
                    values.put(android.provider.MediaStore.Images.Media.MIME_TYPE,"image/jpeg");
                    values.put(android.provider.MediaStore.Images.Media.IS_PENDING,1);
                    Uri uri=getContentResolver().insert(
                        android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI,values);
                    if(uri==null)throw new Exception("Destination photo indisponible");
                    pendingCameraUri=uri;
                    intent.putExtra(android.provider.MediaStore.EXTRA_OUTPUT,uri);
                    intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                        | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    intent.setClipData(android.content.ClipData.newUri(
                        getContentResolver(),"Photo de repas",uri));
                }
                startActivityForResult(intent,PHOTO_CAMERA);
            }catch(Exception e){
                if(pendingCameraUri!=null){
                    try{getContentResolver().delete(pendingCameraUri,null,null);}
                    catch(Exception ignored){}
                    pendingCameraUri=null;
                }
                js("showMessage('Appareil photo indisponible')");
            }
        }''')
R(j,'''        if (result != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try {
            if (request == PHOTO) {''',
'''        if(request==PHOTO_CAMERA){
            final Uri cameraUri=pendingCameraUri;
            pendingCameraUri=null;
            if(result!=RESULT_OK){
                if(cameraUri!=null)try{getContentResolver().delete(cameraUri,null,null);}
                    catch(Exception ignored){}
                pendingPhotoToken=null;
                return;
            }
            final String token=pendingPhotoToken;
            pendingPhotoToken=null;
            final android.graphics.Bitmap thumbnail=cameraUri==null && data!=null
                && data.getExtras()!=null && data.getExtras().get("data") instanceof android.graphics.Bitmap
                ?(android.graphics.Bitmap)data.getExtras().get("data"):null;
            io.execute(() -> {
                try{
                    String photo=cameraUri!=null
                        ?compressedPhoto(cameraUri):compressedThumbnail(thumbnail);
                    js("photoPicked("+JSONObject.quote(token)+","+JSONObject.quote(photo)+")");
                }catch(Exception e){js("showMessage('Photo illisible : réessaie ou choisis la galerie')");}
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
            if (request == PHOTO) {''')
R(j,'''    private String compressedPhoto(Uri uri) throws Exception {''',
'''    private String compressedThumbnail(android.graphics.Bitmap bitmap) throws Exception {
        if(bitmap==null)throw new Exception("Aucune image reçue");
        java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,65,out);
        if(out.size()>180000)throw new Exception("Photo trop volumineuse");
        return "data:image/jpeg;base64,"+
            android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP);
    }
    private String compressedPhoto(Uri uri) throws Exception {''')
# Avoid user-facing alert spam when personal entries update and share permission is unavailable.
# In particular, existing unencrypted linked files may be missing the new encryption code.
R(j,'''                    if(value==null)continue;
                    try {
                        String document=makeSharedDocument(id,p);''',
'''                    if(value==null)continue;
                    if(!getPreferences(MODE_PRIVATE).contains("share_pass_"+id)){
                        js("sharedSyncNeedsPassword()");
                        continue;
                    }
                    try {
                        String document=makeSharedDocument(id,p);''')
R(j,'''                    } catch(Exception e) {
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdateFailed()",null));
                    }
                }
            } catch(Exception ignored) { }
        });
    }

    private void loadShared(Uri uri) {''',
'''                    } catch(Exception e) {
                        // A broken Drive permission must not interrupt meal editing.
                        js("sharedSyncFailed()");
                    }
                }
            } catch(Exception ignored) { }
        });
    }

    private void loadShared(Uri uri) {''')
R(h,'''function sharedUpdateFailed(){alert('Impossible de créer, relier ou modifier le fichier partagé. Vérifie les droits Google Drive. N’en crée pas un nouveau avant d’avoir essayé « Relier un fichier partagé existant ».');}''',
'''function sharedUpdateFailed(){
 $('share-state').textContent='Mise à jour du partage impossible. Vérifie le mot de passe de partage et les droits Google Drive ; utilise « Relier un fichier partagé existant » si nécessaire.';
 alert('Impossible de modifier le fichier partagé. Le profil personnel reste enregistré. Vérifie le mot de passe ou les droits Drive, sans créer de fichier en double.');
}
function sharedSyncNeedsPassword(){
 const note=$('share-state');
 if(note)note.textContent='Ton profil est bien enregistré. Le fichier partagé existant n’a pas encore de code de chiffrement : ouvre Profils → Mettre à jour le partage Drive pour définir le code à 10 caractères.';
}
function sharedSyncFailed(){
 const note=$('share-state');
 if(note)note.textContent='Ton profil personnel est enregistré, mais le fichier partagé n’a pas pu être synchronisé. Vérifie les autorisations de modification Google Drive dans Profils.';
}''')
R(h,"'📷 Remplacer la photo':'📷 Ajouter une photo'",
    "'📷 Remplacer la photo':'📷 Ajouter une photo'")
# The native Android choice now opens camera or gallery. Explain via button label.
R(h,"photoButton.textContent=saved[key+'Photo']?'📷 Remplacer la photo':'📷 Ajouter une photo';",
    "photoButton.textContent=saved[key+'Photo']?'📷 Remplacer la photo':'📷 Photo : appareil ou galerie';")
assert 'PHOTO_CAMERA = 52' in j.read_text(encoding="utf-8")
assert 'sharedSyncNeedsPassword()' in j.read_text(encoding="utf-8")
print("v1.6.10 camera/Drive update fixes installed")
