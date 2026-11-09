#!/usr/bin/env python3
"""v1.6.26: six inline camera icons in meal headers, preserving existing handlers."""
from pathlib import Path
root=Path("android/source-1.6.26/app")
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} occurrences for {a[:100]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 41","versionCode 42")
R(g,"versionName '1.6.25'","versionName '1.6.26'")
R(m,'android:versionCode="41" android:versionName="1.6.25"','android:versionCode="42" android:versionName="1.6.26"')
R(j,"MonEvolutionIMC/1.6.25","MonEvolutionIMC/1.6.26")
R(h,'Version installée : <strong>1.6.25</strong>','Version installée : <strong>1.6.26</strong>')
R(h,'const installed="1.6.25";','const installed="1.6.26";')
script=r"""
<style>
.meal-field{margin:10px 0!important}
.meal-header-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px;min-height:38px}
.meal-header-row>label{font-weight:650;flex:1;margin:0}
.meal-photo-actions{display:flex;align-items:center;gap:6px;flex-shrink:0}
.meal-header-row .meal-camera-icon{width:40px;height:36px;padding:6px!important;margin:0!important;border-radius:10px;font-size:19px;line-height:1;display:flex;align-items:center;justify-content:center}
.meal-camera-icon.has-photo{border-color:#78e3ca;color:#9cf1d9}
.meal-header-row .meal-photo-remove{width:34px;height:36px;padding:5px!important;margin:0!important;border-radius:10px;font-size:18px;line-height:1}
.meal-field textarea{margin-top:0!important;min-height:60px}
</style>
<script>
(function(){
 const original=renderMeals;
 renderMeals=function(){
  original();
  for(const wrapper of document.querySelectorAll('#meal-inputs > .meal-field')){
   const label=wrapper.querySelector(':scope > label');
   const buttons=[...wrapper.children].filter(e=>e.tagName==='BUTTON');
   if(!label||!buttons.length)continue;
   const header=document.createElement('div');header.className='meal-header-row';
   const actions=document.createElement('div');actions.className='meal-photo-actions';
   const photo=buttons[0];
   const hasPhoto=!!wrapper.querySelector(':scope > img');
   photo.textContent='📷';
   photo.classList.add('meal-camera-icon');
   if(hasPhoto)photo.classList.add('has-photo');
   photo.setAttribute('aria-label',hasPhoto?'Remplacer la photo du '+label.textContent:'Ajouter une photo du '+label.textContent);
   photo.title=hasPhoto?'Remplacer la photo':'Prendre une photo ou choisir dans la galerie';
   actions.append(photo);
   const remove=buttons[1];
   if(remove){
    remove.textContent='✕';
    remove.classList.add('meal-photo-remove');
    remove.setAttribute('aria-label','Retirer la photo du '+label.textContent);
    remove.title='Retirer la photo';
    actions.append(remove);
   }
   header.append(label,actions);
   wrapper.prepend(header);
  }
 };
 renderMeals();
})();
</script>
"""
R(h,'</body></html>',script+'</body></html>')
print("v1.6.26: all six meal photo controls moved next to meal headings")
