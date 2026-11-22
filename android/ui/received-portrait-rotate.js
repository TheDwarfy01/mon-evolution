/* Shared portrait orientation — local display only, never writes owner's Drive. */
(() => {
 'use strict';
 if(!window.AndroidBackup?.rotateReceivedAvatar ||
    !window.AndroidBackup?.receivedAvatar)return;
 const profiles=document.getElementById('profiles');
 const shared=document.getElementById('shared');
 if(!profiles||!shared)return;
 const style=document.createElement('style');
 style.textContent=[
  '.friend-portrait-tools{padding:14px;border:1px solid #44748a;border-radius:16px;background:#132e42;margin:12px 0 18px}',
  '.friend-portrait-tools h3{margin:0 0 4px;font-size:16px}',
  '.friend-portrait-tools p{font-size:12px;color:#adcbd9;margin:7px 0 12px;line-height:1.5}',
  '.friend-portrait-preview{display:block;width:116px;height:116px;object-fit:contain;border-radius:50%;border:2px solid #80e9d5;background:#102637;margin:8px auto 12px}',
  '.friend-portrait-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}',
  '.friend-portrait-actions button{display:inline-flex;gap:5px;align-items:center;min-height:43px;padding:8px 10px;border-radius:11px;background:#294d63;color:#e9fbfb;border:1px solid #4b768a;font-size:12px}',
  '.friend-portrait-actions button:active{background:#376c77}',
 ].join('\n');
 document.head.append(style);
 let activeKey='',root=null;
 function selected(){
  if(typeof unifiedCurrent!=='string'||!unifiedCurrent.startsWith('received:'))return '';
  const key=unifiedCurrent.slice(9);
  return /^[a-f0-9-]{36}$/.test(key)?key:'';
 }
 function button(label,action,key){
  const b=document.createElement('button');b.type='button';b.textContent=label;
  b.onclick=()=>{
   if(!window.AndroidBackup.rotateReceivedAvatar(key,action)){
    message('Rotation indisponible pour cette photo partagée.');return;
   }
   const next=window.AndroidBackup.receivedAvatar(key)||'';
   const img=root?.querySelector('img.friend-portrait-preview');
   if(img && next)img.src=next;
   if(typeof updateUnifiedPicker==='function')updateUnifiedPicker(unifiedCurrent);
   message('Orientation enregistrée sur ce téléphone ✓');
  };
  return b;
 }
 function mount(){
  const key=selected();
  const friend=profiles.querySelector(':scope > .friend-view');
  const showingFriend=!profiles.hidden&&!!friend;
  const showingShared=!shared.hidden;
  const target=showingFriend?friend:showingShared?shared:null;
  if(!key || !target){if(root){root.remove();root=null;}return;}
  const avatar=window.AndroidBackup.receivedAvatar(key)||'';
  if(root && root.parentNode===target && activeKey===key){
   const img=root.querySelector('.friend-portrait-preview');
   if(img && avatar && img.src!==avatar)img.src=avatar;
   return;
  }
  if(root){root.remove();root=null;}
  activeKey=key;
  root=document.createElement('div');root.className='friend-portrait-tools';
  const heading=document.createElement('h3');heading.textContent='↻ Orientation de la photo partagée';
  root.append(heading);
  const hint=document.createElement('p');
  hint.textContent='Rotation visible uniquement sur ton téléphone. La photo originale et le fichier Drive du propriétaire restent inchangés.';
  root.append(hint);
  if(avatar){
   const img=document.createElement('img');img.className='friend-portrait-preview';
   img.src=avatar;img.alt='Portrait du profil partagé';root.append(img);
   const actions=document.createElement('div');actions.className='friend-portrait-actions';
   actions.append(button('⟲ Gauche','left',key),button('⟳ Droite','right',key),
                  button('⇋ Miroir','mirror',key),button('↺ Réinitialiser','reset',key));
   root.append(actions);
  }else{
   const p=document.createElement('p');p.textContent='Aucune photo reçue : demande au propriétaire d’activer le partage de son portrait.';
   root.append(p);
  }
  // In friend mode the first heading/notice is left intact.
  const anchor=target.querySelector('.friend-view > .notice')||target.querySelector(':scope > .notice');
  if(anchor && anchor.parentNode===target)anchor.insertAdjacentElement('afterend',root);
  else target.prepend(root);
 }
 // Friend-view panels are created/replaced by the existing read-only navigation.
 const watch=new MutationObserver(mount);
 watch.observe(profiles,{childList:true});
 watch.observe(shared,{childList:true});
 document.addEventListener('click',event=>{
  if(event.target?.closest?.('.friend-portrait-tools'))return;
  queueMicrotask(mount);
 },false);
 const prior=window.onReceivedProfileLoaded;
 window.onReceivedProfileLoaded=function(){
  const r=typeof prior==='function'?prior.apply(this,arguments):undefined;
  queueMicrotask(mount);
  return r;
 };
 mount();
})();