#!/usr/bin/env python3
"""v1.6.21 - Collapse advanced profile and Drive actions into two menus."""
from pathlib import Path
root=Path("android/source-1.6.21/app")
html=root/"src/main/assets/index.html"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 count=s.count(old)
 if count!=1:raise AssertionError(f"{path}: expected 1 occurrence, found {count}: {old[:110]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
R(gradle,"versionCode 36","versionCode 37")
R(gradle,"versionName '1.6.20'","versionName '1.6.21'")
R(manifest,'android:versionCode="36" android:versionName="1.6.20"','android:versionCode="37" android:versionName="1.6.21"')
R(java,'MonEvolutionIMC/1.6.20','MonEvolutionIMC/1.6.21')
R(html,'Version installée : <strong>1.6.20</strong>','Version installée : <strong>1.6.21</strong>')
R(html,'const installed="1.6.20";','const installed="1.6.21";')
script=r"""
<style>
.profile-tools-toggle{display:flex;justify-content:space-between;align-items:center;text-align:left;width:100%;font-weight:650;padding:14px 16px}
.profile-tools-toggle .chevron{transition:transform .16s ease}
.profile-tools-toggle[aria-expanded="true"] .chevron{transform:rotate(180deg)}
.profile-tools-body{margin-top:12px;display:grid;gap:10px}
.profile-tools-body button{width:100%!important;margin:0!important}
.profile-tools-body[hidden]{display:none!important}
.profile-tools-danger{border-top:1px solid #466276;padding-top:12px;margin-top:4px}
.profile-tools-status{font-size:12px;color:#a4c8d7;line-height:1.45;margin:6px 0}
</style>
<script>
(function(){
 const profiles=$('profiles');
 if(!profiles)return;
 function makeMenu(title,description){
  const shell=document.createElement('div');
  const toggle=document.createElement('button');
  toggle.type='button';toggle.className='secondary profile-tools-toggle';
  toggle.setAttribute('aria-expanded','false');
  const text=document.createElement('span');text.textContent=title;
  const chevron=document.createElement('span');chevron.className='chevron';chevron.textContent='⌄';
  chevron.setAttribute('aria-hidden','true');
  toggle.append(text,chevron);
  const body=document.createElement('div');
  body.className='profile-tools-body';body.hidden=true;
  const id='profile-tools-'+title.toLowerCase().replace(/[^a-z]/g,'-');
  body.id=id;toggle.setAttribute('aria-controls',id);
  if(description) {
   const info=document.createElement('p');info.className='profile-tools-status';
   info.textContent=description;body.append(info);
  }
  toggle.onclick=()=>{
   const open=body.hidden;
   body.hidden=!open;toggle.setAttribute('aria-expanded',String(open));
  };
  shell.append(toggle,body);
  return {shell,body};
 }
 const exportButton=$('export-weights');
 const profileCard=exportButton?.closest('.card');
 if(!profileCard)return;
 const profileMenu=makeMenu('Gestion du profil','Exporter tes données ou supprimer un profil. Les suppressions demandent une confirmation.');
 for(const id of ['export-weights','export-profile']){
  const element=$(id);if(element)profileMenu.body.append(element);
 }
 const danger=document.createElement('div');danger.className='profile-tools-body profile-tools-danger';
 for(const id of ['delete-profile','delete-drive-profile']){
  const element=$(id);if(element)danger.append(element);
 }
 profileMenu.body.append(danger);profileCard.append(profileMenu.shell);
 const driveState=$('drive-state');
 const driveCard=driveState?.closest('.card');
 if(!driveCard)return;
 const driveMenu=makeMenu('Options Google Drive','Gérer la sauvegarde, restaurer ou déconnecter le fichier relié.');
 for(const id of ['backup','backup-relink','restore','disconnect']){
  const element=$(id);if(element)driveMenu.body.append(element);
 }
 // Keep the live backup status visible without opening the menu.
 driveCard.append(driveMenu.shell);
 // Hide verbose guidance in the collapsed section but preserve it for review.
 for(const p of [...driveCard.querySelectorAll(':scope > p.notice')]){
  if(p!==driveState)driveMenu.body.append(p);
 }
})();
</script>
"""
R(html,'</body></html>',script+'</body></html>')
print("v1.6.21: profile management and Google Drive operations collapsed")
