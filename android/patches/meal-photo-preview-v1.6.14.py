#!/usr/bin/env python3
"""Mon Evolution 1.6.14: landscape-sized previews and clear meal save action."""
from pathlib import Path
root=Path("android/source-1.6.14/app")
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(str(path),s.count(old),old[:100])
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 29","versionCode 30")
R(g,"versionName '1.6.13'","versionName '1.6.14'")
R(m,'android:versionCode="29" android:versionName="1.6.13"','android:versionCode="30" android:versionName="1.6.14"')
R(j,"MonEvolutionIMC/1.6.13","MonEvolutionIMC/1.6.14")
R(h,'Version installée : <strong>1.6.13</strong>','Version installée : <strong>1.6.14</strong>')
R(h,'const installed="1.6.13";','const installed="1.6.14";')
R(h,"image.style.cssText='display:block;width:auto;max-width:min(100%,320px);height:auto;max-height:320px;object-fit:contain;border-radius:12px;margin:12px 0';",
"""image.style.cssText='display:block;width:100%;height:210px;max-width:100%;object-fit:cover;object-position:center;border-radius:12px;margin:12px 0;cursor:zoom-in';
       image.title='Appuyer pour voir la photo entière';
       image.onclick=()=>window.showMealPhoto?.(image.src);""")
R(h,"img.style.cssText='display:block;width:auto;max-width:min(100%,320px);height:auto;max-height:320px;border-radius:9px;object-fit:contain;margin:10px 0';",
"""img.style.cssText='display:block;width:100%;height:210px;max-width:100%;object-fit:cover;object-position:center;border-radius:9px;margin:10px 0;cursor:zoom-in';img.title='Appuyer pour voir la photo entière';img.onclick=()=>window.showMealPhoto?.(img.src);""")
# Set up the larger uncropped preview as an on-demand overlay, so the main meal list stays compact.
R(h,'<script>\n// Incoming Android intent:',
"""<script>
(function(){
 const dialog=document.createElement('dialog');
 dialog.id='meal-photo-zoom';
 dialog.style.cssText='background:#0b1d2b;border:0;border-radius:14px;padding:12px;max-width:96vw;max-height:94vh';
 dialog.innerHTML='<button type="button" id="meal-photo-zoom-close" style="display:block;margin:0 0 10px auto;padding:10px">Fermer ✕</button><img id="meal-photo-zoom-image" alt="Photo complète du repas" style="display:block;max-width:90vw;max-height:82vh;width:auto;height:auto;object-fit:contain;margin:auto">';
 document.body.append(dialog);
 $('meal-photo-zoom-close').onclick=()=>dialog.close();
 window.showMealPhoto=(src)=>{
  if(typeof src!=='string'||!src.startsWith('data:image/jpeg;base64,'))return;
  $('meal-photo-zoom-image').src=src;
  dialog.showModal();
 };
 dialog.addEventListener('close',()=>{$('meal-photo-zoom-image').removeAttribute('src')});
})();
</script>
<script>
// Incoming Android intent:""")
R(h,"$('save-meals').onclick=()=>saveMealInputs();",
"""$('save-meals').textContent='Enregistrer les descriptions des repas';
 $('save-meals').title='Enregistre les aliments, boissons et quantités saisis. Les photos sont enregistrées dès leur ajout.';
 const info=document.createElement('p');
 info.className='notice';
 info.textContent='Les photos sont enregistrées automatiquement dès leur ajout. Ce bouton enregistre tes descriptions de repas.';
 $('save-meals').insertAdjacentElement('afterend',info);
 $('save-meals').onclick=()=>saveMealInputs();""")
print("v1.6.14 horizontal photo preview, tap-to-zoom and clear meal text save.")
