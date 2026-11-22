/* Mon Evolution IMC v1.6.121 — Guided child share file permissions.
 * Adds an action for the EXACT selected Android SAF document, not the Drive home page.
 * "Editor" cannot be granted by this app; the owner confirms this manually in Drive.
 * The optional editing wizard remains disabled until a child share was actually linked.
 */
(() => {
  'use strict';
  const api=window.AndroidBackup;
  const owner=document.getElementById('child-collab-owner');
  const wizard=document.getElementById('child-owner-required-steps');
  const enabled=document.getElementById('child-collab-enable');
  if(!api||!owner||!wizard||!enabled)return;
  const current=()=>typeof profile==='function'?profile():null;
  const check=document.getElementById('child-verify-invitation');
  const checkbox=check;
  const verify=wizard.querySelector('button.primary');
  const rows=document.createElement('div');
  rows.id='child-share-file-guide';
  rows.style.cssText='border:1px solid #396b82;border-radius:12px;padding:13px;margin:12px 0;background:#0c2538';
  const headline=document.createElement('h4');
  headline.textContent='Le fichier à partager — étape par étape';
  headline.style.margin='0 0 8px';
  const info=document.createElement('p');
  info.className='notice';
  info.id='child-share-selected-file';
  info.style.cssText='margin:0 0 8px;overflow-wrap:anywhere';
  const create=document.createElement('button');
  create.type='button';create.className='secondary';
  create.id='child-share-file-create';
  create.style.cssText='width:100%;margin:6px 0';
  const relink=document.createElement('button');
  relink.type='button';relink.className='secondary';
  relink.id='child-share-file-relink';
  relink.style.cssText='width:100%;margin:6px 0';
  relink.textContent='↗ J’ai déjà un fichier : le relier';
  const open=document.createElement('button');
  open.type='button';open.className='primary';
  open.id='child-share-file-open';
  open.style.cssText='width:100%;margin:6px 0';
  open.textContent='📂 Ouvrir CE fichier dans Google Drive';
  const detail=document.createElement('p');
  detail.className='notice';
  detail.id='child-share-file-howto';
  detail.style.margin='10px 0 0';
  const feedback=document.createElement('p');
  feedback.className='notice';feedback.id='child-share-file-feedback';
  feedback.setAttribute('role','status');
  rows.append(headline,info,create,relink,open,detail,feedback);
  const checks=wizard.querySelector('div:not(#child-share-file-guide)');
  wizard.insertBefore(rows,checks||wizard.children[1]||null);
  // Put the attestation AFTER the document button, never show a green "invited"
  // check when no document exists. Do not alter read-only sharing.
  const editableHint=owner.querySelector('p.notice');
  if(editableHint)editableHint.textContent='Tu n’as pas besoin de chercher le fichier manuellement : utilise les boutons ci-dessous pour ouvrir son emplacement et donner au deuxième parent le rôle Éditeur.';

  let lastProfile='',lastLink='';
  // Mirror the actual permission status in the verification checklist.
  // An unchecked checkbox by assignment alone does not refresh that checklist.
  function clearConfirmation(){
    if(checkbox?.checked){
      checkbox.checked=false;
      checkbox.dispatchEvent(new Event('change',{bubbles:true}));
    }
  }
  let cachedInfo=null,cachedKey='',cachedAt=0;
  function getInfo(id){
    const key=id+'|'+(api.sharedStatus?.(id)||'0');
    if(cachedKey===key&&Date.now()-cachedAt<15000&&cachedInfo)return cachedInfo;
    try{
      const result=JSON.parse(api.childShareDocumentInfo?.(id)||'{}');
      cachedInfo=result;cachedKey=key;cachedAt=Date.now();
      return result;
    }catch(_){return {}}
  }
  const active=()=>enabled.checked && !wizard.hidden;
  function redraw(){
    const p=current();
    if(!p||!active()){rows.hidden=true;return}
    rows.hidden=false;
    if(p.id!==lastProfile){
      lastProfile=p.id;
      lastLink='';
      clearConfirmation();
    }
    const file=getInfo(p.id);
    const linked=file.linked===true && api.sharedStatus?.(p.id)==='1';
    const password=!!api.hasSharePassword?.(p.id);
    const fileName=typeof file.name==='string'&&file.name.length?file.name:
      'mon-evolution-partage-'+p.id+'.json';
    const revision=(linked?'linked':'missing')+'|'+(password?'password':'none')+'|'+fileName;
    if(lastLink!==revision){
      lastLink=revision;
      clearConfirmation();
    }
    info.textContent=linked
      ?'✓ Fichier de ce profil : « '+fileName+' »'+(file.provider?' · '+file.provider:'')
      :'✕ Aucun fichier relié pour « '+p.name+' ». Il faut le créer une seule fois avant d’autoriser quelqu’un à le modifier.';
    create.textContent=linked?'✓ 1. Fichier déjà relié':'＋ 1. Créer le fichier de '+p.name;
    create.disabled=linked;
    relink.hidden=linked;
    open.disabled=!linked;
    open.textContent=linked?'📂 2. Ouvrir CE fichier dans Google Drive':'📂 2. Ouvrir le fichier (après création)';
    detail.textContent=linked
      ?'Après ouverture dans Drive : appuie sur ⋮ → Gérer l’accès ou Partager → ajoute l’adresse Google du deuxième parent → choisis Éditeur → Enregistrer. Dans « Accès général », garde « Limité ». Reviens ici pour cocher la confirmation puis vérifier.'
      :'Étape 1 : crée le fichier dans Google Drive (ou relie le fichier existant). Reviens sur cet écran après l’enregistrement ; le bouton d’ouverture deviendra disponible.';
    if(checkbox){
      checkbox.disabled=!(linked&&password);
      if(checkbox.disabled)clearConfirmation();
      const label=checkbox.closest('label');
      if(label)label.style.opacity=checkbox.disabled?'.50':'1';
    }
    if(verify)verify.disabled=!(linked&&password&&checkbox?.checked);
    const ownerStatus=document.getElementById('child-collab-status');
    if(ownerStatus)ownerStatus.textContent=
      'Autorisation de modification en attente : crée ou relie le fichier, configure Éditeur dans Drive puis valide les contrôles ci-dessous.';
    if(!linked)feedback.textContent='Configuration non terminée : aucun accès Éditeur ne peut être accordé avant la création du fichier.';
    else if(!password)feedback.textContent='Le fichier est relié, mais son mot de passe de partage doit être rétabli avant les contrôles.';
    else if(!checkbox?.checked)feedback.textContent='Ensuite, confirme que le deuxième parent est bien Éditeur dans Google Drive.';
    else feedback.textContent='✓ Vérifie maintenant les autorisations du fichier.';
  }
  create.addEventListener('click',()=>{
    const p=current();if(!p||!active())return;
    const advanced=document.getElementById('outgoing-advanced');
    const outer=document.getElementById('outgoing-share-wrapper');
    if(outer)outer.open=true;
    if(advanced)advanced.open=true;
    const button=document.getElementById('create-share');
    if(!button)return;
    feedback.textContent='Choisis Google Drive dans le sélecteur Android et enregistre le fichier du profil.';
    button.click();
  });
  relink.addEventListener('click',()=>{
    const outer=document.getElementById('outgoing-share-wrapper');
    const advanced=document.getElementById('outgoing-advanced');
    if(outer)outer.open=true;
    if(advanced)advanced.open=true;
    document.getElementById('share-relink')?.click();
    feedback.textContent='Sélectionne le fichier déjà existant dans Google Drive ; aucun doublon ne sera créé.';
  });
  open.addEventListener('click',()=>{
    const p=current();if(!p||!active())return;
    if(api.sharedStatus?.(p.id)!=='1')return redraw();
    feedback.textContent='Ouverture du fichier relié. Dans Drive : ⋮ → Partager/Gérer l’accès → Éditeur.';
    if(api.openChildShareDocument)api.openChildShareDocument(p.id);
    else feedback.textContent='Mise à jour Android nécessaire pour ouvrir le fichier exact.';
  });
  window.childShareFileOpenResult=(id,code)=>{
    if(!current()||current().id!==id)return;
    if(code==='opened'){
      feedback.textContent='Le fichier lié a été ouvert. Dans Google Drive, utilise ⋮ → Partager/Gérer l’accès → compte du deuxième parent → Éditeur. Si un lecteur JSON s’ouvre, recherche le nom affiché dans Drive.';
    }else if(code==='need_link'){
      feedback.textContent='Le lien direct Drive manque. Ouvre le fichier lié et enregistre son lien dans les paramètres avancés, puis réessaie.';
    }else{
      feedback.textContent='Impossible d’ouvrir ce fichier automatiquement. Ouvre Google Drive et recherche exactement le nom indiqué ci-dessus.';
    }
  };
  checkbox?.addEventListener('change',()=>queueMicrotask(redraw));
  enabled.addEventListener('change',()=>queueMicrotask(redraw));
  // On Android SAF return and on asynchronous share creation, update the file
  // state even if no profile view changed. Observe only the share-state text.
  const shareState=document.getElementById('share-state');
  if(shareState){
    const observer=new MutationObserver(()=>queueMicrotask(redraw));
    observer.observe(shareState,{childList:true,characterData:true,subtree:true});
  }
  window.addEventListener('pageshow',()=>{cachedAt=0;redraw()});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){cachedAt=0;redraw()}});
  const oldRender=window.render;
  if(typeof oldRender==='function')window.render=function(...args){
    const r=oldRender.apply(this,args);redraw();return r;
  };
  redraw();
})();
