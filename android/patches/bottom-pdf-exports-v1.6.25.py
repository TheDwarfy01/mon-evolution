#!/usr/bin/env python3
"""v1.6.25: place PDF download actions at bottom in compact expandable sections."""
from pathlib import Path
root=Path("android/source-1.6.25/app")
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: expected 1 found {n}: {a[:90]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 40","versionCode 41")
R(g,"versionName '1.6.24'","versionName '1.6.25'")
R(m,'android:versionCode="40" android:versionName="1.6.24"','android:versionCode="41" android:versionName="1.6.25"')
R(j,"MonEvolutionIMC/1.6.24","MonEvolutionIMC/1.6.25")
R(h,'Version installée : <strong>1.6.24</strong>','Version installée : <strong>1.6.25</strong>')
R(h,'const installed="1.6.24";','const installed="1.6.25";')
script=r"""
<style>
.export-details{border:1px solid #355b70;border-radius:14px;background:#102b3c;margin-top:14px;overflow:hidden}
.export-details>summary{cursor:pointer;padding:14px 16px;font-size:13px;font-weight:700;color:#def4f7;list-style:none;display:flex;justify-content:space-between;align-items:center}
.export-details>summary::-webkit-details-marker{display:none}
.export-details>summary:after{content:'⌄';font-size:19px}
.export-details[open]>summary:after{content:'⌃'}
.export-details .export-content{padding:0 15px 15px}
.export-details .export-content button{width:100%}
</style>
<script>
(function(){
 function bottomExport(sectionId,buttonId,title,description){
  const section=$(sectionId),button=$(buttonId);
  if(!section||!button)return;
  const details=document.createElement('details');details.className='export-details';
  const summary=document.createElement('summary');summary.textContent=title;
  const content=document.createElement('div');content.className='export-content';
  const hint=document.createElement('p');hint.className='notice';hint.textContent=description;
  content.append(hint,button);details.append(summary,content);
  section.append(details);
 }
 // Move the existing buttons, preserving their original event handlers and PDFs.
 bottomExport('home','export-progress-pdf','↓ Télécharger mon bilan complet',
  'Bilan PDF de ton profil : évolution du poids, objectif et historique des pesées.');
 bottomExport('meals','export-meals-pdf','↓ Télécharger le compte rendu mensuel',
  'Compte rendu PDF des repas du mois affiché dans le calendrier.');
 // Remove the now-empty card at the end of the meal journal.
 const meals=$('meals');
 const empty=[...meals.querySelectorAll(':scope > .card')].find(c=>
  c.querySelector('h3')?.textContent==='Compte rendu mensuel' &&
  !c.querySelector('button'));
 if(empty)empty.remove();
})();
</script>
"""
R(h,'</body></html>',script+'</body></html>')
print("v1.6.25: both PDF exports placed at the bottom in collapsible menus")
