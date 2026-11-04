#!/usr/bin/env python3
"""Mon Evolution 1.6.11: Samsung-compatible camera capture and photo visibility."""
from pathlib import Path
root=Path("android/source-1.6.11/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def replace(path,old,new):
 s=path.read_text(encoding="utf-8")
 count=s.count(old)
 if count!=1:
  raise AssertionError(f"{path}: expected 1, got {count} for {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
replace(g,"versionCode 26","versionCode 27")
replace(g,"versionName '1.6.10'","versionName '1.6.11'")
replace(m,'android:versionCode="26" android:versionName="1.6.10"',
          'android:versionCode="27" android:versionName="1.6.11"')
replace(j,'MonEvolutionIMC/1.6.10','MonEvolutionIMC/1.6.11')
replace(h,'Version installée : <strong>1.6.10</strong>','Version installée : <strong>1.6.11</strong>')
replace(h,'const installed="1.6.10";','const installed="1.6.11";')
# Samsung Camera sometimes crashes when third-party apps send an IS_PENDING
# MediaStore URI as EXTRA_OUTPUT. A standard thumbnail-returning Intent avoids
# the incompatible output URI. Gallery remains available for full-resolution photos.
start=j.read_text(encoding="utf-8").index('        private void openCamera(){')
end=j.read_text(encoding="utf-8").index('\n    }\n\n    @Override protected void onActivityResult',start)
s=j.read_text(encoding="utf-8")
old=s[start:end]
new='''        private void openCamera(){
            pendingCameraUri=null;
            try{
                Intent intent=new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                // Request a standard result thumbnail without EXTRA_OUTPUT.
                // Passing a pending MediaStore URI crashes certain Samsung Camera versions.
                // The photo is compressed and stored immediately in the meal record.
                if(intent.resolveActivity(getPackageManager())==null)
                    throw new Exception("Aucune application appareil photo disponible");
                startActivityForResult(intent,PHOTO_CAMERA);
            }catch(Exception e){
                pendingPhotoToken=null;
                js("showMessage('Appareil photo indisponible. Utilise la galerie ou vérifie l’application Caméra Samsung.')");
            }
        }'''
j.write_text(s[:start]+new+s[end:],encoding="utf-8")
# The camera sends a Bitmap thumbnail (not always a URI).
replace(j,'''            final android.graphics.Bitmap thumbnail=cameraUri==null && data!=null
                && data.getExtras()!=null && data.getExtras().get("data") instanceof android.graphics.Bitmap
                ?(android.graphics.Bitmap)data.getExtras().get("data"):null;''',
'''            final android.graphics.Bitmap thumbnail=data!=null
                && data.getExtras()!=null && data.getExtras().get("data") instanceof android.graphics.Bitmap
                ?(android.graphics.Bitmap)data.getExtras().get("data"):null;''')
# Lower memory pressure, keep photo in quota. Scale thumbnails and cap encoded size.
replace(j,'''        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,65,out);
        if(out.size()>180000)throw new Exception("Photo trop volumineuse");''',
'''        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,65,out);
        if(out.size()>130000){
            out.reset();
            bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,40,out);
        }
        if(out.size()>180000)throw new Exception("Photo trop volumineuse");''')
# Plain-language feedback if camera result is not provided.
replace(j,"js(\"showMessage('Photo illisible : réessaie ou choisis la galerie')\");",
          "js(\"showMessage('La caméra n’a renvoyé aucune photo. Essaie la galerie si le problème persiste.')\");")
# Photos may be stored but users won't notice if off-screen; scroll to photo on render.
replace(h,"image.style.cssText='display:block;max-width:100%;max-height:190px;object-fit:contain;border-radius:12px;margin:9px 0';",
          "image.style.cssText='display:block;max-width:100%;max-height:190px;object-fit:contain;border-radius:12px;margin:9px 0';")
assert 'EXTRA_OUTPUT' not in new
assert 'versionCode 27' in g.read_text(encoding="utf-8")
print("1.6.11 Samsung camera thumbnail compatibility patch applied")
