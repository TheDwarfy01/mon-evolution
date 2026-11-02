#!/usr/bin/env python3
"""v1.6.6: import the invitation on Android app opening, without a second tap."""
from pathlib import Path
root=Path("android/source-1.6.6/app")
html=root/"src/main/assets/index.html"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"

def replace(path, old, new):
    source=path.read_text(encoding="utf-8")
    count=source.count(old)
    if count!=1: raise AssertionError(f"{path}: expected 1 anchor, got {count}: {old[:90]!r}")
    path.write_text(source.replace(old,new),encoding="utf-8")

replace(gradle,"versionCode 21","versionCode 22")
replace(gradle,"versionName '1.6.5'","versionName '1.6.6'")
replace(manifest,'android:versionCode="21" android:versionName="1.6.5"','android:versionCode="22" android:versionName="1.6.6"')
replace(java,'MonEvolutionIMC/1.6.5','MonEvolutionIMC/1.6.6')
replace(html,'Version installée : <strong>1.6.5</strong>','Version installée : <strong>1.6.6</strong>')
replace(html,'const installed="1.6.5";','const installed="1.6.6";')
replace(html,'// The user must explicitly choose whether to add this profile.','// Opening the shared link is the explicit action: immediately try the read-only import.')
replace(html,"'Aucune donnée de ton téléphone ne sera remplacée. Confirme avant de l’ajouter.</p>'+","'Aucune donnée de ton téléphone ne sera remplacée. Importation automatique en cours.</p>'+")
replace(html," let pendingResourceKey='';\n window.receiveShareInvitation=function(fileId,resourceKey){",
""" let pendingResourceKey='';
 let invitationLoading=false;
 window.receiveShareInvitation=function(fileId,resourceKey){""")
replace(html,
"""   $('shared-state').textContent='Invitation reçue : confirme pour ajouter ce profil.';
   panel.scrollIntoView({block:'start'});
 };
 $('invite-accept').onclick=()=>{
   if(!pendingId)return;
   $('shared-state').textContent='Lecture du lien… Si le fichier est privé, utilise le bouton « Accès privé : choisir le fichier Google Drive ».';
   const source='https://drive.google.com/file/d/'+pendingId+'/view'
     +(pendingResourceKey?'?resourcekey='+encodeURIComponent(pendingResourceKey):'');
   window.AndroidBackup?.loadSharedPublic?.(source);
  };""",
"""   $('shared-state').textContent='Invitation reçue. Importation automatique du profil en lecture seule…';
   panel.scrollIntoView({block:'start'});
   // The user already chose to open the invitation link. Do not require a second tap.
   $('invite-accept').click();
 };
 $('invite-accept').onclick=()=>{
   if(!pendingId || invitationLoading)return;
   if(!window.AndroidBackup?.loadSharedPublic){
     $('shared-state').textContent='Importation indisponible : mets à jour l’application.';
     return;
    }
   invitationLoading=true;
   $('invite-accept').disabled=true;
   $('shared-state').textContent='Chargement du profil partagé depuis Google Drive…';
   const source='https://drive.google.com/file/d/'+pendingId+'/view'
     +(pendingResourceKey?'?resourcekey='+encodeURIComponent(pendingResourceKey):'');
   window.AndroidBackup.loadSharedPublic(source);
  };""")
replace(html,
""" $('invite-cancel').onclick=()=>{
   pendingId='';""",
""" $('invite-cancel').onclick=()=>{
   invitationLoading=false;
   $('invite-accept').disabled=false;
   pendingId='';""")
replace(html,
""" window.onReceivedProfileLoaded=function(key,name){
   pendingId='';""",
""" window.onReceivedProfileLoaded=function(key,name){
   invitationLoading=false;
   $('invite-accept').disabled=false;
   pendingId='';""")
# When Drive rejects direct retrieval, keep the invitation visible for manual private-file import.
replace(html,
"""function sharedPublicFailed(reason){
 const errors={""",
"""function sharedPublicFailed(reason){
 const accept=$('invite-accept');
 if(accept){accept.disabled=false;}
 if(typeof window.resetInvitationLoading==='function')window.resetInvitationLoading();
 const errors={""")
replace(html," let invitationLoading=false;\n window.receiveShareInvitation",
""" let invitationLoading=false;
 window.resetInvitationLoading=()=>{invitationLoading=false;};
 window.receiveShareInvitation""")
assert 'window.AndroidBackup.loadSharedPublic(source)' in html.read_text(encoding="utf-8")
assert 'versionCode 22' in gradle.read_text(encoding="utf-8")
print("1.6.6: invitation auto-import, safe fallback, version updated")
