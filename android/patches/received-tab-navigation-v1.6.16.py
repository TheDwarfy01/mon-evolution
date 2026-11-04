#!/usr/bin/env python3
"""v1.6.16: unified received profiles across read-only tabs (no personal data overwritten)."""
from pathlib import Path
root=Path("android/source-1.6.16/app")
h=root/"src/main/assets/index.html"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1:raise AssertionError((str(path),n,old[:110]))
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 31","versionCode 32")
R(g,"versionName '1.6.15'","versionName '1.6.16'")
R(m,'android:versionCode="31" android:versionName="1.6.15"','android:versionCode="32" android:versionName="1.6.16"')
R(j,"MonEvolutionIMC/1.6.15","MonEvolutionIMC/1.6.16")
R(h,'Version installée : <strong>1.6.15</strong>','Version installée : <strong>1.6.16</strong>')
R(h,'const installed="1.6.15";','const installed="1.6.16";')
# Use one function to enter a received profile, no side-effect to personal data.
# Display read-only snapshots sourced from sharedLoaded's validated profile.
code=r"""
<script>
(function(){
 const tabs=['home','chart','history','meals','profiles'];
 const index={home:0,chart:1,history:2,meals:3,profiles:0};
 let receivedTab='home';
 function clearFriendPanels(){
  for(const tab of tabs){
   const node=$(tab);
   node.classList.remove('friend-view-active');
   node.querySelectorAll(':scope > .friend-view').forEach(v=>v.remove());
  }
 }
 function displayFriendTab(tab){
  if(!unifiedCurrent.startsWith('received:'))return false;
  if(tab==='shared'){
   clearFriendPanels();
   showUnifiedTab('shared');
   return true;
  }
  if(!tabs.includes(tab))return false;
  receivedTab=tab;
  clearFriendPanels();
  const area=$(tab);
  area.classList.add('friend-view-active');
  const section=document.createElement('section');
  section.className='friend-view';
  const selected=getReceivedList().find(p=>'received:'+p.key===unifiedCurrent);
  const heading=document.createElement('h2');
  heading.textContent=(selected?selected.name:'Profil partagé')+' · '+(
   {home:'Résumé',chart:'Courbe',history:'Poids',meals:'Repas',profiles:'Profil'}[tab]);
  section.append(heading);
  const readOnly=document.createElement('p');
  readOnly.className='notice';
  readOnly.textContent='Consultation en lecture seule — aucune modification du profil personnel';
  section.append(readOnly);
  const cards=Array.from($('shared-content').children);
  // Validation and rendering of the received document occurs in sharedLoaded.
  const source=cards[index[tab]];
  if(source){
   const copy=source.cloneNode(true);
   section.append(copy);
   copy.querySelectorAll('img').forEach(img=>{
    img.style.cursor='zoom-in';
    img.onclick=()=>window.showMealPhoto?.(img.src);
   });
  } else {
   const notice=document.createElement('p');
   notice.textContent='Chargement des données du profil partagé…';
   section.append(notice);
  }
  area.append(section);
  showUnifiedTab(tab);
  // showUnifiedTab may render editable personal meal fields in the background;
  // the CSS below keeps them hidden throughout friend mode.
  return true;
 }
 const sheet=document.createElement('style');
 sheet.textContent='.friend-view-active > :not(.friend-view){display:none!important}.friend-view-active > .friend-view{display:block}.friend-view .card{margin-top:12px}';
 document.head.append(sheet);
 // Original listeners unconditionally reset received selection to local:...
 // Intercept user tab navigation before those listeners can change selection.
 for(const nav of document.querySelectorAll('.nav [data-tab]')){
  nav.addEventListener('click',e=>{
   if(!unifiedCurrent.startsWith('received:'))return;
   e.preventDefault();e.stopImmediatePropagation();
   displayFriendTab(nav.dataset.tab);
  },true);
 }
 const originalSelect=selectUnified;
 selectUnified=function(value,refresh=true){
  if(value && value.startsWith('local:')){
   clearFriendPanels();
   return originalSelect(value,refresh);
  }
  if(value && value.startsWith('received:')){
   const selected=getReceivedList().some(item=>'received:'+item.key===value);
   if(!selected)return;
   const changed=unifiedCurrent!==value;
   unifiedCurrent=value;
   localStorage.setItem(unifiedStorageKey,value);
   updateUnifiedPicker(value);
   if(changed)$('shared-content').replaceChildren();
   displayFriendTab('home');
   updateFirstLaunch();
   if(refresh)window.AndroidBackup?.selectReceivedProfile?.(value.slice(9));
   return;
  }
  return originalSelect(value,refresh);
 };
 // The native callback fires after sharedLoaded has validated and rendered
 // the friend's data. Keep the friend selected and switch back to its summary.
 const beforeLoaded=window.onReceivedProfileLoaded;
 window.onReceivedProfileLoaded=function(key,name){
  if(typeof beforeLoaded==='function')beforeLoaded(key,name);
  if(!key||!getReceivedList().some(p=>p.key===key))return;
  unifiedCurrent='received:'+key;
  localStorage.setItem(unifiedStorageKey,unifiedCurrent);
  updateUnifiedPicker(unifiedCurrent);
  displayFriendTab(receivedTab);
 };
 // Make the friend row activate the full profile including the top picker.
 const list=$('received-list-choices');
 if(list){
  list.addEventListener('click',e=>{
   const button=e.target.closest('button[data-friend-key]');
   if(!button)return;
   e.preventDefault();e.stopPropagation();
   selectUnified('received:'+button.dataset.friendKey);
  },true);
 }
 // In case Android reloads a WebView while a friend's profile is selected.
 if(unifiedCurrent.startsWith('received:')){
  selectUnified(unifiedCurrent);
 }
})();
</script>
"""
R(h,'</body></html>',code+'</body></html>')
# Force list buttons to provide a stable key and invoke unified switching.
R(h,"button.textContent='Consulter le profil complet';\n   button.onclick=()=>selectUnified('received:'+friend.key);",
    "button.textContent='Consulter le profil complet';\n   button.dataset.friendKey=friend.key;\n   button.onclick=()=>selectUnified('received:'+friend.key);")
print("v1.6.16: selected friend shown in picker and read-only home/chart/history/meals")
