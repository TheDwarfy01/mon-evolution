/* v1.6.119 — Contrôles obligatoires UNIQUEMENT si le partage enfant modifiable est activé.
 * Les profils personnels / reçus en lecture seule ne sont jamais bloqués.
 * SAF verifies actual granted access; Google account invitations are explicitly
 * confirmed by the owner and tested on recipient device, not guessed from a URL.
 */
(() => {
  'use strict';
  const api=window.AndroidBackup;
  const owner=document.getElementById('child-collab-owner');
  const ownerFlag=document.getElementById('child-collab-enable');
  const receivedEditor=document.getElementById('child-collab-editor');
  const receiverSave=document.getElementById('child-edit-save');
  if(!api||!owner||!ownerFlag||!receivedEditor||!receiverSave)return;

  const current=()=>typeof profile==='function'?profile():null;
  const minor=p=>{
    if(!/^\d{4}-\d{2}-\d{2}$/.test(p?.birthDate||''))return false;
    const dob=new Date(p.birthDate+'T12:00:00'),now=new Date();
    if(!Number.isFinite(dob.getTime())||dob>now)return false;
    let age=now.getFullYear()-dob.getFullYear();
    if(now.getMonth()<dob.getMonth()||
       (now.getMonth()===dob.getMonth()&&now.getDate()<dob.getDate()))age--;
    return age>=0&&age<18;
  };
  const drawChecks=(parent,items)=>{
    parent.replaceChildren();
    for(const [yes,description] of items){
      const line=document.createElement('div');
      line.style.cssText='display:flex;align-items:flex-start;gap:8px;margin:8px 0;font-size:12px';
      const symbol=document.createElement('span');
      symbol.textContent=yes===true?'✓':yes===false?'✕':'◌';
      symbol.style.cssText='font-size:16px;font-weight:800;color:'+(yes===true?'#7de7c4':yes===false?'#ffb3a9':'#f5c87b');
      const text=document.createElement('span');text.textContent=description;
      line.append(symbol,text);parent.append(line);
    }
  };
  const ownerPane=document.createElement('section');
  ownerPane.id='child-owner-required-steps';
  ownerPane.hidden=true;
  ownerPane.style.cssText='border:1px solid #528d9d;border-radius:12px;background:#102e45;padding:12px;margin-top:12px';
  const ownerTitle=document.createElement('h4');ownerTitle.textContent='🔐 Contrôles obligatoires du partage parental';
  ownerTitle.style.cssText='margin:0 0 7px';
  const ownerText=document.createElement('p');ownerText.className='notice';
  ownerText.textContent='Ce contrôle apparaît uniquement lorsque tu actives les modifications du profil enfant.';
  const ownerChecks=document.createElement('div');
  const parentAttest=document.createElement('label');parentAttest.className='checkline';
  parentAttest.innerHTML='<input type="checkbox" id="child-verify-invitation"> J’ai autorisé le deuxième parent comme Éditeur sur ce fichier Drive privé, avec « Accès général : Limité ».';
  const verifyOwner=document.createElement('button');
  verifyOwner.type='button';verifyOwner.className='primary';
  verifyOwner.textContent='Vérifier et activer le partage modifiable';
  const ownerStatus=document.createElement('p');ownerStatus.className='notice';
  ownerStatus.setAttribute('role','status');
  ownerPane.append(ownerTitle,ownerText,ownerChecks,parentAttest,verifyOwner,ownerStatus);
  owner.append(ownerPane);
  let ownerRequest='',ownerBusy=false,publishingOwner='';
  function showOwner(){
    const p=current();
    const active=!!p&&minor(p)&&!!api.childEditEnabled?.(p.id);
    const verified=active&&!!api.childSetupVerified?.(p.id)&&publishingOwner!==p.id;
    ownerPane.hidden=!active||verified;
    if(!ownerPane.hidden){
      const title=owner.querySelector('h4');
      if(title)title.textContent='👨‍👩‍👧 Partage parental — configuration à terminer';
      ownerStatus.textContent='Le mode de modification n’est pas encore actif. Termine les contrôles ci-dessous.';
      drawChecks(ownerChecks,[
        [true,'Profil enfant valide'],
        [api.sharedStatus?.(p.id)==='1','Fichier de partage privé relié sur Drive'],
        [!!api.hasSharePassword?.(p.id),'Mot de passe de partage présent'],
        [null,'Accès en lecture et écriture du fichier Drive — à vérifier'],
        [parentAttest.querySelector('input').checked,'Invitation Éditeur privée confirmée par le propriétaire']
      ]);
    }
  }
  ownerFlag.addEventListener('change',()=>{
    parentAttest.querySelector('input').checked=false;
    // This listener runs after the existing option handler; enabling alone
    // does not publish editable=true until native confirms every prerequisite.
    requestAnimationFrame(showOwner);
  });
  parentAttest.querySelector('input').addEventListener('change',showOwner);
  verifyOwner.onclick=()=>{
    const p=current();
    if(!minor(p)||!api.childEditEnabled?.(p.id))return;
    if(!parentAttest.querySelector('input').checked){
      ownerStatus.textContent='Confirme d’abord les droits Éditeur et l’accès général Limité dans Google Drive.';
      showOwner();return;
    }
    if(!api.verifyOwnedChildShare){
      ownerStatus.textContent='Cette version de l’application ne prend pas en charge le contrôle des droits Drive.';
      return;
    }
    if(ownerBusy)return;
    ownerBusy=true;ownerRequest=p.id;
    verifyOwner.disabled=true;
    ownerStatus.textContent='Vérification du fichier Drive, du mot de passe et des droits d’écriture…';
    api.verifyOwnedChildShare(p.id);
  };
  window.childOwnerVerificationResult=(id,result)=>{
    if(ownerRequest!==id)return;
    ownerBusy=false;verifyOwner.disabled=false;
    let checks;try{checks=JSON.parse(result)}catch(_){checks={}}
    const p=current();if(!p||p.id!==id||!minor(p))return;
    const ready=!!(checks.child&&checks.linked&&checks.password&&checks.read&&checks.write&&checks.sameProfile&&checks.revisionMatches);
    drawChecks(ownerChecks,[
      [checks.child,'Profil enfant valide'],
      [checks.linked,'Fichier privé de ce profil relié'],
      [checks.password,'Mot de passe et déchiffrement vérifiés'],
      [checks.read,'Fichier Drive accessible en lecture'],
      [checks.write,'Autorisation d’écriture présente pour ce téléphone'],
      [checks.sameProfile,'Le document correspond exactement à cet enfant'],
      [checks.revisionMatches,'Document à jour, sans modification distante à écraser'],
      [parentAttest.querySelector('input').checked,'Invitation Éditeur et accès général Limité confirmés']
    ]);
    if(!ready||!parentAttest.querySelector('input').checked){
      ownerStatus.textContent='Configuration incomplète : corrige les étapes signalées. Le partage modifiable reste désactivé.';
      return;
    }
    if(!api.completeOwnedChildSetup?.(id)){
      ownerStatus.textContent='Impossible de finaliser cette configuration. Le partage modifiable reste désactivé.';
      return;
    }
    // The share is still encrypted and uses the same Drive document and password.
    publishingOwner=id;
    api.autoSave?.(backupPayload());
    ownerStatus.textContent='Contrôles validés. Publication de l’autorisation sur Drive en cours…';
    ownerPane.hidden=false;
    verifyOwner.disabled=true;
  };
  window.childOwnerSetupPublished=function(id){
    if(current()?.id!==id)return;
    publishingOwner='';
    ownerPane.hidden=true;
    verifyOwner.disabled=false;
    const title=owner.querySelector('h4');
    if(title)title.textContent='👨‍👩‍👧 Partage parental activé';
    const summary=document.getElementById('child-collab-status');
    if(summary)summary.textContent='✓ Autorisation de modification publiée sur Drive. Le deuxième parent doit encore valider ses droits sur son téléphone.';
  };
  window.childOwnerSetupPublishFailed=function(id){
    if(current()?.id!==id)return;
    publishingOwner='';
    ownerPane.hidden=false;
    verifyOwner.disabled=false;
    ownerStatus.textContent='Échec de publication sur Drive : corrige les droits puis relance le contrôle.';
  };
  // Keep the setup visible when the child profile changes or app becomes visible,
  // but never demand these checks for normal read-only use.
  const previousRender=window.render;
  if(typeof previousRender==='function')window.render=function(...args){
    const result=previousRender.apply(this,args);showOwner();return result;
  };
  window.addEventListener('pageshow',showOwner);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)showOwner()});
  showOwner();

  const receiverPane=document.createElement('section');
  receiverPane.id='child-receiver-required-steps';
  receiverPane.hidden=true;
  receiverPane.style.cssText='border:1px solid #528d9d;border-radius:12px;background:#102e45;padding:12px;margin-top:10px';
  receiverPane.innerHTML='<h4 style="margin:0 0 8px">🔐 Vérification obligatoire du deuxième parent</h4>'+
    '<p class="notice">Nécessaire seulement pour modifier un profil enfant reçu. La lecture seule reste accessible sans ces contrôles.</p>'+
    '<div id="child-receiver-checks"></div>'+
    '<button type="button" class="secondary" id="child-receiver-select" style="width:100%;margin:8px 0">Choisir le fichier Drive privé autorisé</button>'+
    '<button type="button" class="primary" id="child-receiver-verify">Vérifier mes accès</button>'+
    '<p class="notice" id="child-receiver-status" role="status"></p>';
  receivedEditor.insertBefore(receiverPane,receivedEditor.firstChild.nextSibling);
  const receiverChecks=receiverPane.querySelector('#child-receiver-checks');
  const receiverStatus=receiverPane.querySelector('#child-receiver-status');
  const receiverVerify=receiverPane.querySelector('#child-receiver-verify');
  const receiverSelect=receiverPane.querySelector('#child-receiver-select');
  const currentReceived=()=>typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:')
       ?unifiedCurrent.slice(9):'';
  let receivedKey='',receiverReady=false,receiverRequest='';
  receiverSelect.onclick=()=>document.getElementById('shared-open')?.click();
  function checkReceived(){
    if(!receivedKey||receivedKey!==currentReceived()){
      receiverReady=false;receiverSave.disabled=true;
      receiverPane.hidden=!receivedKey;
      return;
    }
    if(!api.verifyReceivedChildShare){
      receiverReady=false;receiverSave.disabled=true;
      receiverPane.hidden=false;
      receiverStatus.textContent='Version Android incompatible : la modification reste bloquée.';
      return;
    }
    receiverReady=false;
    receiverSave.disabled=true;
    receiverRequest=receivedKey;
    receiverPane.hidden=false;
    receiverVerify.disabled=true;
    receiverStatus.textContent='Contrôle du compte Drive et du fichier privé…';
    api.verifyReceivedChildShare(receivedKey);
  }
  receiverVerify.onclick=checkReceived;
  window.childReceiverVerificationResult=(key,result)=>{
    if(receiverRequest!==key)return;
    receiverVerify.disabled=false;
    let checks;try{checks=JSON.parse(result)}catch(_){checks={}}
    receiverReady=!!(checks.private&&checks.child&&checks.editable&&checks.read&&checks.write&&checks.password);
    drawChecks(receiverChecks,[
      [checks.private,'Fichier privé Google Drive sélectionné'],
      [checks.child,'Profil de moins de 18 ans'],
      [checks.editable,'Modification explicitement autorisée par le propriétaire'],
      [checks.password,'Mot de passe du partage valide'],
      [checks.read,'Accès Drive en lecture'],
      [checks.write,'Autorisation Android d’écriture du document (rôle Éditeur requis)']
    ]);
    receiverPane.hidden=receiverReady;
    receiverSave.disabled=!receiverReady;
    receiverStatus.textContent=receiverReady
      ?'✓ Accès contrôlé. Une écriture réelle sera confirmée lors du premier enregistrement.'
      :'Configuration incomplète. Demande le rôle Éditeur dans Drive puis sélectionne le fichier privé avec le compte autorisé.';
  };
  const previousReceived=window.sharedLoaded;
  if(typeof previousReceived==='function')window.sharedLoaded=function(base64,key){
    const result=previousReceived.apply(this,arguments);
    let eligible=false;
    try{
      const text=new TextDecoder().decode(Uint8Array.from(atob(base64),c=>c.charCodeAt(0)));
      const doc=JSON.parse(text);
      eligible=doc?.collaboration?.editable===true&&minor(doc.profile)
        &&typeof getReceivedList==='function'
        &&getReceivedList().some(item=>item.key===key&&item.kind==='private');
    }catch(_){}
    receivedKey=eligible?key:'';
    receiverReady=false;
    receiverSave.disabled=!!eligible;
    receiverPane.hidden=!eligible;
    if(eligible)checkReceived();
    return result;
  };
  // Do not allow a stale verification to enable edits after switching profile.
  receiverSave.addEventListener('click',event=>{
    if(!receiverReady||!receivedKey||receivedKey!==currentReceived()){
      event.preventDefault();event.stopImmediatePropagation();
      receiverStatus.textContent='Contrôles obligatoires non validés : la modification reste bloquée.';
      receiverPane.hidden=false;
    }
  },true);
})();
