#!/usr/bin/env python3
"""1.6.8 UI regression repair: saved received profiles are visible in Shared tab."""
from pathlib import Path
p=Path("android/source-1.6.8/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
needle="</script>\n</body></html>"
assert s.count(needle)==1
add="""</script>
<script>
// Always show saved received profiles, even when a personal profile is active.
// Source documents remain on Google Drive; this list stores only name/key/kind.
(function(){
 const section=$('shared');
 const card=document.createElement('div');
 card.className='card';
 card.id='received-list-card';
 const heading=document.createElement('h3');
 heading.textContent='Profils partagés déjà reçus';
 const status=document.createElement('p');
 status.className='notice';
 status.id='received-list-status';
 const choices=document.createElement('div');
 choices.id='received-list-choices';
 card.append(heading,status,choices);
 section.insertBefore(card,section.querySelector('.card'));
 function updateReceivedChoices(){
  const saved=getReceivedList();
  choices.replaceChildren();
  if(!saved.length){
   status.textContent='Aucun profil partagé enregistré sur ce téléphone. Ouvre une invitation ou importe un fichier Drive.';
   return;
  }
  status.textContent=saved.length===1?'1 profil partagé enregistré':'Profils partagés enregistrés : '+saved.length;
  for(const item of saved){
   const button=document.createElement('button');
   button.type='button';button.className='secondary';
   button.style.cssText='width:100%;margin-top:10px';
   button.textContent='👤 '+item.name+' · Consulter en lecture seule';
   button.onclick=()=>selectUnified('received:'+item.key);
   choices.append(button);
  }
 }
 const oldClick=sharedNav.onclick;
 sharedNav.onclick=()=>{
  if(typeof oldClick==='function')oldClick();
  updateReceivedChoices();
  const saved=getReceivedList();
  const preferred=window.AndroidBackup?.receivedSelected?.()||'';
  const selected=saved.find(item=>item.key===preferred)||saved[0];
  if(selected && !unifiedCurrent.startsWith('received:')){
   // Show last received summary rather than a blank Shared tab.
   selectUnified('received:'+selected.key);
  }
 };
 const loaded=window.onReceivedProfileLoaded;
 window.onReceivedProfileLoaded=function(key,name){
  if(typeof loaded==='function')loaded(key,name);
  updateReceivedChoices();
 };
 updateReceivedChoices();
})();
</script>
</body></html>"""
s=s.replace(needle,add)
assert "Profils partagés déjà reçus" in s
p.write_text(s,encoding="utf-8")
print("Saved received profiles are now listed and last summary reopens on tab.")
