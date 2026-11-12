#!/usr/bin/env python3
"""v1.6.57: prevent concurrent photo replacement and ensure deletion is always accessible."""
from pathlib import Path
root=Path("android/source-1.6.58/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def replace_one(path,old,new):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1: raise AssertionError(f"{path}: {n} matches: {old[:110]!r}")
    path.write_text(s.replace(old,new),encoding="utf-8")
# The previous callback was not guarded against two photo selection flows overlapping.
replace_one(j,"    private String pendingPhotoToken;","    private String pendingPhotoToken;\n    private boolean photoPickerBusy=false;")
replace_one(j,'''        @JavascriptInterface public void pickPhoto(String token) {
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
        }''','''        @JavascriptInterface public void pickPhoto(String token) {
            if(token==null || token.length()>150)return;
            runOnUiThread(() -> {
                if(photoPickerBusy){
                    js("showMessage('Une photo est déjà en cours de sélection')");
                    return;
                }
                photoPickerBusy=true;
                pendingPhotoToken=token;
                new android.app.AlertDialog.Builder(MainActivity.this)
                    .setTitle("Choisir ou remplacer une photo")
                    .setItems(new String[]{"📷 Prendre une photo","🖼️ Choisir dans la galerie"},
                        (dialog,which)->{
                            if(which==0)openCamera();
                            else openPhotoGallery();
                        })
                    .setOnCancelListener(dialog->{
                        photoPickerBusy=false;
                        pendingPhotoToken=null;
                    })
                    .show();
            });
        }''')
replace_one(j,'''            catch(Exception e){js("showMessage('Galerie indisponible')");}''',
'''            catch(Exception e){
                pendingPhotoToken=null;photoPickerBusy=false;
                js("showMessage('Galerie indisponible')");
            }''')
replace_one(j,'''                pendingPhotoToken=null;
                js("showMessage('La caméra ne peut pas être ouverte. Utilise la galerie.')");''',
'''                pendingPhotoToken=null;photoPickerBusy=false;
                js("showMessage('La caméra ne peut pas être ouverte. Utilise la galerie.')");''')
replace_one(j,'''                pendingPhotoToken=null;
                return;
            }
            final String token=pendingPhotoToken;''',
'''                pendingPhotoToken=null;photoPickerBusy=false;
                return;
            }
            final String token=pendingPhotoToken;''')
replace_one(j,'''                    if(thumbnail!=null && !thumbnail.isRecycled())thumbnail.recycle();
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
            } else if (request == PDF) {''',
'''                    if(thumbnail!=null && !thumbnail.isRecycled())thumbnail.recycle();
                    runOnUiThread(()->photoPickerBusy=false);
                }
            });
            return;
        }
        if(result!=RESULT_OK || data==null || data.getData()==null){
            if(request==PHOTO){pendingPhotoToken=null;photoPickerBusy=false;}
            return;
        }
        Uri uri=data.getData();
        try {
            if (request == PHOTO) {
                String token=pendingPhotoToken;
                pendingPhotoToken=null;
                io.execute(() -> {
                    try{
                        String photo=compressedPhoto(uri);
                        js("photoPicked("+JSONObject.quote(token)+","+JSONObject.quote(photo)+")");
                    }catch(Exception e){js("showMessage('Photo illisible ou trop volumineuse')");}
                    finally{runOnUiThread(()->photoPickerBusy=false);}
                });
            } else if (request == PDF) {''')
# An independent "remove" control below each photo survives all rerenders.
# It also ensures removal does not depend on the old little X staying visible.
ui=r"""
<style>
.meal-photo-recovery{display:flex;justify-content:flex-end;margin:-4px 0 12px}
.meal-photo-recovery button{width:auto!important;min-height:39px;padding:8px 14px!important;border-radius:10px;font-size:13px}
</style>
<script>
(function(){
 const before=renderMeals;
 renderMeals=function(){
  const result=before();
  for(const [key,label] of mealTypes){
   const field=$('meal-'+key);
   const wrapper=field?.closest('.meal-field');
   if(!wrapper)continue;
   const image=wrapper.querySelector('img');
   const photoButton=wrapper.querySelector('.meal-camera-icon');
   const originalRemove=wrapper.querySelector('.meal-photo-remove');
   if(photoButton){
    // Ask before replacing. Cancelling keeps the original photo untouched.
    // A new wrapper is built at each render so this listener is never duplicated.
    photoButton.addEventListener('click',event=>{
     const p=profile();
     if(p?.meals?.[mealDate]?.[key+'Photo']&&
        !confirm('Remplacer la photo du '+label+' ? La photo précédente sera remplacée.')){
        event.stopImmediatePropagation();
        event.preventDefault();
     }
    },true);
   }
   if(!image)continue;
   const recovery=document.createElement('div');
   recovery.className='meal-photo-recovery';
   const remove=document.createElement('button');remove.type='button';remove.className='secondary';
   remove.textContent='🗑 Supprimer cette photo';
   remove.setAttribute('aria-label','Supprimer la photo du '+label);
   remove.onclick=()=>{
    const p=profile();
    if(!p?.meals?.[mealDate]?.[key+'Photo'])return;
    if(!confirm('Supprimer la photo du '+label+' ?'))return;
    delete p.meals[mealDate][key+'Photo'];
    save();
    renderMeals();
    message('Photo supprimée ✓');
   };
   recovery.append(remove);
   image.insertAdjacentElement('afterend',recovery);
   // Keep the compact X as well; both buttons target the same saved photo.
   if(originalRemove){
    originalRemove.title='Supprimer la photo du '+label;
    originalRemove.setAttribute('aria-label','Supprimer la photo du '+label);
   }
  }
  return result;
 };
 renderMeals();
})();
</script>
"""
replace_one(h,"</body></html>",ui+"\n</body></html>")
print("v1.6.57: photo picker concurrent requests guarded, cancel-safe, independent delete controls")
