#!/usr/bin/env python3
"""v1.6.15: secure camera content URI for full-resolution Samsung captures."""
from pathlib import Path
root=Path("android/source-1.6.15/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
provider=root/"src/main/java/fr/monevolution/app/CameraPhotoProvider.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1: raise AssertionError((str(p),n,a[:120]))
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 30","versionCode 31")
R(g,"versionName '1.6.14'","versionName '1.6.15'")
R(m,'android:versionCode="30" android:versionName="1.6.14"','android:versionCode="31" android:versionName="1.6.15"')
R(j,"MonEvolutionIMC/1.6.14","MonEvolutionIMC/1.6.15")
R(h,'Version installée : <strong>1.6.14</strong>','Version installée : <strong>1.6.15</strong>')
R(h,'const installed="1.6.14";','const installed="1.6.15";')
R(m,'    <activity android:name=".MainActivity"',
'''    <!-- Private cache file exposed only to camera apps explicitly granted a URI. -->
    <provider android:name=".CameraPhotoProvider"
              android:authorities="fr.monevolution.app.camera"
              android:exported="false"
              android:grantUriPermissions="true"/>
    <activity android:name=".MainActivity"''')
provider.write_text(r"""package fr.monevolution.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.File;
import java.io.FileNotFoundException;

/** Camera output backed by the app's private cache, granted for this one capture. */
public final class CameraPhotoProvider extends ContentProvider {
    public static final String AUTHORITY="fr.monevolution.app.camera";
    public static Uri uriFor(String filename) {
        return new Uri.Builder().scheme("content").authority(AUTHORITY)
            .appendPath(filename).build();
    }
    private File target(Uri uri) throws FileNotFoundException {
        if(uri==null || !AUTHORITY.equals(uri.getAuthority()))
            throw new FileNotFoundException("Wrong authority");
        String filename=uri.getLastPathSegment();
        if(filename==null || !filename.matches("capture-[a-f0-9-]{36}\\.jpg"))
            throw new FileNotFoundException("Invalid camera file");
        File folder=new File(getContext().getCacheDir(),"meal-camera");
        if(!folder.exists()&&!folder.mkdirs())throw new FileNotFoundException("Cache unavailable");
        return new File(folder,filename);
    }
    @Override public boolean onCreate(){return true;}
    @Override public String getType(Uri uri){return "image/jpeg";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,
                                 String[] selectionArgs,String sortOrder){
        try{
            File f=target(uri);
            String[] fields=projection==null
               ?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;
            MatrixCursor rows=new MatrixCursor(fields);
            Object[] row=new Object[fields.length];
            for(int n=0;n<fields.length;n++){
                if(OpenableColumns.DISPLAY_NAME.equals(fields[n]))row[n]=f.getName();
                else if(OpenableColumns.SIZE.equals(fields[n]))row[n]=f.length();
            }
            rows.addRow(row);return rows;
        }catch(FileNotFoundException ex){return null;}
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        File f=target(uri);
        // Callers cannot access any path outside the specifically named camera captures.
        int flags;
        if("r".equals(mode))flags=ParcelFileDescriptor.MODE_READ_ONLY;
        else if("w".equals(mode)||"wt".equals(mode))flags=ParcelFileDescriptor.MODE_WRITE_ONLY|ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE;
        else if("rw".equals(mode))flags=ParcelFileDescriptor.MODE_READ_WRITE|ParcelFileDescriptor.MODE_CREATE;
        else throw new FileNotFoundException("Unsupported mode");
        return ParcelFileDescriptor.open(f,flags);
    }
    @Override public int delete(Uri uri,String selection,String[] args) {
        try{return target(uri).delete()?1:0;}catch(Exception e){return 0;}
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args) {
        throw new UnsupportedOperationException();
    }
}
""",encoding="utf-8")
# Ensure onActivityResult can resolve output even if Activity is recreated by camera.
R(j,'    private Uri pendingCameraUri;','''    private Uri pendingCameraUri;
    private String pendingCameraFilename;''')
R(j,'        super.onActivityResult(request, result, data);',
'''        super.onActivityResult(request, result, data);''')
# Save outstanding path in Android state instead of relying on a field that may be lost.
R(j,'    @Override public void onCreate(Bundle state) {',
'''    @Override protected void onSaveInstanceState(android.os.Bundle state){
        super.onSaveInstanceState(state);
        if(pendingCameraUri!=null)state.putString("camera_uri",pendingCameraUri.toString());
        if(pendingPhotoToken!=null)state.putString("photo_token",pendingPhotoToken);
    }
    @Override public void onCreate(Bundle state) {''')
R(j,'        super.onCreate(state);',
'''        super.onCreate(state);
        if(state!=null){
            String camera=state.getString("camera_uri");
            if(camera!=null)pendingCameraUri=Uri.parse(camera);
            pendingPhotoToken=state.getString("photo_token");
        }''')
# Provide a new file for the camera to write, with standard content permissions.
start=j.read_text(encoding="utf-8").index('        private void openCamera(){')
end=j.read_text(encoding="utf-8").index('\n    }\n\n    @Override protected void onActivityResult',start)
s=j.read_text(encoding="utf-8")
original=s[start:end]
replacement='''        private void openCamera(){
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
        }'''
j.write_text(s[:start]+replacement+s[end:],encoding="utf-8")
# Handle both high-quality camera output and fallback thumbnails.
R(j,'''            pendingCameraUri=null;
            if(result!=RESULT_OK){''',
'''            pendingCameraUri=null;
            pendingCameraFilename=null;
            if(result!=RESULT_OK){''')
R(j,'''                    String photo=cameraUri!=null
                        ?compressedPhoto(cameraUri):compressedThumbnail(thumbnail);''',
'''                    String photo;
                    try{
                        if(cameraUri==null)throw new Exception("Capture sans destination");
                        photo=compressedPhoto(cameraUri);
                    }catch(Exception ex){
                        // Some camera apps return only a thumbnail: handle gracefully.
                        photo=compressedThumbnail(thumbnail);
                    }''')
R(j,'''                    if(cameraUri!=null)try{getContentResolver().delete(cameraUri,null,null);}
                        catch(Exception ignored){}''',
'''                    if(cameraUri!=null)try{getContentResolver().delete(cameraUri,null,null);}
                        catch(Exception ignored){}''')
# Better image: 1000px, and aim below 170KiB JPEG to remain within the existing
# sharing threshold (<250,000 base64 characters). Do not change photo format/API.
old='''        int longest = Math.max(decoded.getWidth(), decoded.getHeight());
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
        return "data:image/jpeg;base64," + android.util.Base64.encodeToString(output.toByteArray(), android.util.Base64.NO_WRAP);'''
new='''        int longest = Math.max(decoded.getWidth(), decoded.getHeight());
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
            output.toByteArray(),android.util.Base64.NO_WRAP);'''
R(j,old,new)
# The existing photo preview remains unchanged; clearly tell user quality
# improves for future photos only.
assert 'height:210px' in h.read_text(encoding="utf-8")
assert 'android.permission.CAMERA' not in m.read_text(encoding="utf-8")
print("v1.6.15 ready: full-res camera private content URI and better compression")
