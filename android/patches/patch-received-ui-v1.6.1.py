#!/usr/bin/env python3
"""UI portion: always-visible switcher across own and received profiles."""
from pathlib import Path

source=Path("android/source-1.6.0/app/src/main/assets/index.html")
dest=Path("android/source-1.6.1/app/src/main/assets/index.html")
dest.parent.mkdir(parents=True,exist_ok=True)
s=source.read_text(encoding="utf-8")

def rep(old,new):
    global s
    n=s.count(old)
    assert n==1,f"Expected one occurrence ({n}) of {old[:90]!r}"
    s=s.replace(old,new)

rep("Version installée : <strong>1.6.0</strong>", "Version installée : <strong>1.6.1</strong>")
rep("Version installée : 1.6.0. Vérifie sur GitHub", "Version installée : 1.6.1. Vérifie sur GitHub")
rep('const installed="1.6.0";','const installed="1.6.1";')

rep('<h1>Mon Évolution ✦</h1><nav class="nav">',
'''<h1>Mon Évolution ✦</h1>
<div class="profile-global" style="margin-top:16px">
  <label for="unified-profile-picker" style="font-size:13px;color:#cfe7f6">Profil affiché</label>
  <select id="unified-profile-picker" aria-label="Choisir un profil personnel ou partagé" style="margin-top:5px"></select>
  <button id="unified-add-received" type="button" style="font-size:12px;color:#93e6d6;background:transparent;border:0;padding:10px 0 0">＋ Ajouter un profil partagé</button>
</div><nav class="nav">''')
rep('id="setup-restore" type="button">☁ Restaurer une sauvegarde Google Drive</button>',
'''id="setup-restore" type="button">☁ Restaurer une sauvegarde Google Drive</button>
<button class="secondary" id="setup-received" type="button">♧ Consulter un profil partagé</button>''')
rep("sharedNav.textContent='♧ Proche';","sharedNav.textContent='♧ Partagés';")
rep('''  <button class="secondary" style="width:100%;margin-top:10px" id="shared-open">Ou choisir un fichier Drive privé</button></div>''',
'''  <button class="secondary" style="width:100%;margin-top:10px" id="shared-open">Ou choisir un fichier Drive privé</button>
  <button class="secondary" style="width:100%;margin-top:12px" id="forget-received">Retirer ce profil partagé de ma liste</button>
  <p class="notice">Cette action retire uniquement le raccourci de ton application, jamais le fichier Drive appartenant à ton proche.</p></div>''')
rep('function sharedLoaded(base64){','function sharedLoaded(base64,receivedKey){')
rep("   message('Profil partagé actualisé ✓');",
    "   window.onReceivedProfileLoaded?.(receivedKey,p.name);\n   message('Profil partagé actualisé ✓');")
rep('''function updateFirstLaunch(){const empty=!data||!Array.isArray(data.profiles)||data.profiles.length===0;document.body.classList.toggle('needs-setup',empty);}''',
'''function updateFirstLaunch(){
 const empty=!data||!Array.isArray(data.profiles)||data.profiles.length===0;
 let received=false;
 try{received=JSON.parse(window.AndroidBackup?.listReceivedProfiles?.()||"[]").length>0;}catch(e){}
 document.body.classList.toggle('needs-setup',empty&&!received);
}''')
rep("$('setup-restore').addEventListener('click',()=>{if(window.AndroidBackup?.load)AndroidBackup.load();else message('Restauration disponible sur Android')});",
'''$('setup-restore').addEventListener('click',()=>{if(window.AndroidBackup?.load)AndroidBackup.load();else message('Restauration disponible sur Android')});
$('setup-received').addEventListener('click',()=>{
 document.body.classList.remove('needs-setup');
 sharedNav.click();
 $('shared-public-url').focus();
});''')

# Append after first-launch initialization, so all functions and elements exist.
appender=r'''<script>
// Unified list: personal profiles are editable; received profiles remain read-only.
const unifiedPicker=$('unified-profile-picker');
const unifiedStorageKey='mon-evolution-unified-selection-v1';
let unifiedCurrent='';
function getReceivedList(){
 try{
  const list=JSON.parse(window.AndroidBackup?.listReceivedProfiles?.()||'[]');
  return Array.isArray(list)?list.filter(item=>
   item && typeof item.key==='string' && /^[a-f0-9-]{36}$/.test(item.key) &&
   typeof item.name==='string' && item.name.length<=100 &&
   ['private','public'].includes(item.kind)
  ).slice(0,100):[];
 }catch(e){return [];}
}
function showUnifiedTab(tab){
 const nav=document.querySelector('[data-tab="'+tab+'"]');
 document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('on',b===nav));
 ['home','chart','history','meals','profiles','shared'].forEach(t=>$(t).hidden=t!==tab);
 if(tab==='meals' && data.profiles.length)renderMeals();
}
function updateUnifiedPicker(prefer){
 const received=getReceivedList();
 const before=prefer||unifiedCurrent||localStorage.getItem(unifiedStorageKey)||('local:'+data.active);
 unifiedPicker.replaceChildren();
 const own=data.profiles||[];
 if(own.length){
  const group=document.createElement('optgroup');group.label='Mes profils personnels';
  for(const p of own){
   const item=document.createElement('option');
   item.value='local:'+p.id;
   item.textContent=p.name+' · Personnel';
   group.append(item);
  }
  unifiedPicker.append(group);
 }
 if(received.length){
  const group=document.createElement('optgroup');group.label='Profils reçus (lecture seule)';
  received.forEach((r,i)=>{
   const item=document.createElement('option');
   item.value='received:'+r.key;
   item.textContent=r.name+' · Partagé '+(r.kind==='private'?'(privé)':'(lien)');
   group.append(item);
  });
  unifiedPicker.append(group);
 }
 const options=[...unifiedPicker.options].map(o=>o.value);
 const fallback=own.length?'local:'+data.active:(received.length?'received:'+received[0].key:'');
 const next=options.includes(before)?before:fallback;
 if(next){
  unifiedPicker.value=next;
  unifiedCurrent=next;
 }else unifiedCurrent='';
 unifiedPicker.disabled=!next;
 $('forget-received').style.display=unifiedCurrent.startsWith('received:')?'block':'none';
 return next;
}
function selectUnified(value,refresh=true){
 if(!value)return;
 if(value.startsWith('local:')){
  const id=value.slice(6);
  if(!data.profiles.some(p=>p.id===id))return;
  unifiedCurrent=value;
  localStorage.setItem(unifiedStorageKey,value);
  if(data.active!==id){data.active=id;save();render();}
  updateUnifiedPicker(value);
  showUnifiedTab('home');
  updateFirstLaunch();
 }else if(value.startsWith('received:')){
  const key=value.slice(9);
  if(!getReceivedList().some(p=>p.key===key))return;
  unifiedCurrent=value;
  localStorage.setItem(unifiedStorageKey,value);
  updateUnifiedPicker(value);
  showUnifiedTab('shared');
  $('shared-state').textContent='Chargement du profil partagé en lecture seule…';
  updateFirstLaunch();
  if(refresh)window.AndroidBackup?.selectReceivedProfile?.(key);
 }
}
unifiedPicker.addEventListener('change',()=>selectUnified(unifiedPicker.value));
$('unified-add-received').addEventListener('click',()=>{
 document.body.classList.remove('needs-setup');
 sharedNav.click();
 $('shared-public-url').focus();
});
$('forget-received').onclick=()=>{
 const chosen=unifiedCurrent.startsWith('received:')?unifiedCurrent.slice(9):
   (window.AndroidBackup?.receivedSelected?.()||'');
 if(!chosen)return alert('Sélectionne un profil partagé pour le retirer de ta liste.');
 const item=getReceivedList().find(p=>p.key===chosen);
 if(!item)return;
 if(!confirm('Retirer « '+item.name+' » de cette application ? Aucun fichier du propriétaire ne sera supprimé.'))return;
 if(!window.AndroidBackup?.forgetReceivedProfile?.(chosen))
  return alert('Impossible de retirer ce profil de la liste.');
 $('shared-content').replaceChildren();
 unifiedCurrent='';
 localStorage.removeItem(unifiedStorageKey);
 const fallback=updateUnifiedPicker();
 if(fallback)selectUnified(fallback);
 else updateFirstLaunch();
 message('Profil partagé retiré de ta liste ✓');
};
window.onReceivedProfileLoaded=(key,name)=>{
 if(!key || !getReceivedList().some(p=>p.key===key))return;
 unifiedCurrent='received:'+key;
 localStorage.setItem(unifiedStorageKey,unifiedCurrent);
 updateUnifiedPicker(unifiedCurrent);
 showUnifiedTab('shared');
 updateFirstLaunch();
};
const originalRenderForSwitcher=render;
render=function(){
 originalRenderForSwitcher();
 if(data.profiles.length && !unifiedCurrent.startsWith('received:')){
  unifiedCurrent='local:'+data.active;
 }
 updateUnifiedPicker();
};
$('profile-picker').addEventListener('change',()=>{
 unifiedCurrent='local:'+data.active;
 localStorage.setItem(unifiedStorageKey,unifiedCurrent);
 updateUnifiedPicker(unifiedCurrent);
});
document.querySelectorAll('[data-tab]:not([data-tab="shared"])').forEach(b=>
 b.addEventListener('click',()=>{
  if(data.profiles.length){
   unifiedCurrent='local:'+data.active;
   localStorage.setItem(unifiedStorageKey,unifiedCurrent);
   updateUnifiedPicker(unifiedCurrent);
  }
 })
);
const initialUnified=updateUnifiedPicker();
if(initialUnified.startsWith('received:'))selectUnified(initialUnified);
</script>
'''
assert s.endswith("</body></html>")
s=s.replace("</body></html>",appender+"</body></html>")
# Existing button opens received management. It should not override a selected
# personal profile unless a received document was actually loaded successfully.
rep("window.AndroidBackup?.refreshShared?.();\n};\ndocument.querySelectorAll('[data-tab]:not([data-tab=\"shared\"])']",'''if(window.AndroidBackup?.receivedSelected?.())window.AndroidBackup.refreshShared();
};
document.querySelectorAll('[data-tab]:not([data-tab="shared"])']''')
# Same identifier may appear in multiple scripts but use only one.
assert "id=\"unified-profile-picker\"" in s
assert "forgetReceivedProfile" in s
assert "function sharedLoaded(base64,receivedKey)" in s
assert "listReceivedProfiles" in s and "selectReceivedProfile" in s
assert "id=\"setup-received\"" in s
dest.write_text(s,encoding="utf-8")
print("Unified UI added: all personal and private/public received profiles in one picker.")
