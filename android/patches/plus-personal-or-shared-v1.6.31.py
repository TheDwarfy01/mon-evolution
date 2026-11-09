#!/usr/bin/env python3
"""v1.6.31: add either local profile or shared profile via portrait-strip plus."""
from pathlib import Path
root=Path("android/source-1.6.31/app")
h=root/"src/main/assets/index.html";g=root/"build.gradle";m=root/"src/main/AndroidManifest.xml";j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} matches of {a[:90]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 46","versionCode 47")
R(g,"versionName '1.6.30'","versionName '1.6.31'")
R(m,'android:versionCode="46" android:versionName="1.6.30"','android:versionCode="47" android:versionName="1.6.31"')
R(j,"MonEvolutionIMC/1.6.30","MonEvolutionIMC/1.6.31")
R(h,'Version installée : <strong>1.6.30</strong>','Version installée : <strong>1.6.31</strong>')
R(h,'const installed="1.6.30";','const installed="1.6.31";')
R(h,"const latest=String(version||''),installed='1.6.30';","const latest=String(version||''),installed='1.6.31';")
# Keep existing invitation route and original profile creation action.
R(h,"button.setAttribute('aria-label','Ajouter un profil partagé');",
    "  button.setAttribute('aria-label','Ajouter un profil personnel ou partagé');")
R(h,"  button.onclick=()=>oldAdd.click();",
"""  const chooser=document.createElement('dialog');
  chooser.id='add-profile-chooser';
  chooser.style.cssText='border-radius:18px;background:#122e43;color:#f1f8ff;border:1px solid #476d81;padding:22px;max-width:min(92vw,400px);width:90%';
  const title=document.createElement('h3');title.textContent='Ajouter un profil';
  const personal=document.createElement('button');personal.type='button';personal.className='primary';
  personal.textContent='＋ Créer un profil personnel';
  personal.onclick=()=>{chooser.close();$('new-profile')?.click()};
  const friend=document.createElement('button');friend.type='button';friend.className='secondary';
  friend.style.cssText='display:block;width:100%;margin-top:12px';
  friend.textContent='♧ Ajouter un profil partagé';
  friend.onclick=()=>{chooser.close();oldAdd.click()};
  const cancel=document.createElement('button');cancel.type='button';cancel.className='secondary';
  cancel.style.cssText='display:block;width:100%;margin-top:12px';
  cancel.textContent='Annuler';cancel.onclick=()=>chooser.close();
  chooser.append(title,personal,friend,cancel);document.body.append(chooser);
  button.onclick=()=>chooser.showModal();""")
print("v1.6.31: + profile chooser supports personal and shared")
