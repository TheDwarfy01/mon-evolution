/* Mon Évolution IMC — collaboration familiale sur un seul profil enfant.
   Le droit d'écriture est contrôlé par Google Drive et vérifié par Android.
   Les profils adultes et les partages publics restent en lecture seule. */
(() => {
  'use strict';
  const native=window.AndroidBackup;
  if(!native||!document.getElementById('profiles')||!document.getElementById('shared'))return;
  const minor=p=>{
    if(!p||!/^\d{4}-\d{2}-\d{2}$/.test(p.birthDate||''))return false;
    const d=new Date(p.birthDate+'T12:00:00'),now=new Date();
    if(!Number.isFinite(d.getTime())||d>now)return false;
    let a=now.getFullYear()-d.getFullYear();
    if(now.getMonth()<d.getMonth()||(now.getMonth()===d.getMonth()&&now.getDate()<d.getDate()))a--;
    return a>=0&&a<18;
  };
  const note=(txt)=>{if(typeof message==='function')message(txt);};
  const current=()=>typeof profile==='function'?profile():null;
  const wrapper=document.createElement('div');
  wrapper.id='child-collab-owner';
  wrapper.style.cssText='border:1px solid #345b74;border-radius:12px;padding:12px;margin:14px 0;background:#0c293d';
  wrapper.innerHTML='<h4 style="margin:0 0 8px">👨‍👩‍👧 Partage parental du profil enfant</h4>'+
   '<label class="checkline"><input type="checkbox" id="child-collab-enable"> Autoriser les modifications par un autre parent</label>'+
   '<p class="notice">Dans Google Drive, invite uniquement cette personne avec le rôle Éditeur et conserve l’accès général sur Limité. Un simple lien ou le mot de passe ne donne pas le droit de modifier.</p>'+
   '<button type="button" class="secondary" id="child-collab-sync" style="width:100%">↻ Récupérer les modifications de l’autre parent</button>'+
   '<p class="notice" id="child-collab-status" aria-live="polite"></p>';
  const share=document.getElementById('create-share');
  if(share)share.parentNode.insertBefore(wrapper,share);
  const status=wrapper.querySelector('#child-collab-status');
  const enabled=wrapper.querySelector('#child-collab-enable');
  const sync=wrapper.querySelector('#child-collab-sync');
  function redraw(){
    const p=current();if(!p)return;
    wrapper.hidden=!minor(p);
    if(wrapper.hidden)return;
    enabled.checked=!!native.childEditEnabled?.(p.id);
    sync.disabled=native.sharedStatus?.(p.id)!=='1';
    status.textContent=enabled.checked
      ?'Modification autorisée pour ce profil enfant. Les droits Éditeur du fichier restent gérés dans Drive.'
      :'Consultation uniquement. Aucune autorisation de modification activée.';
  }
  enabled.addEventListener('change',()=>{
    const p=current();
    if(!minor(p)){enabled.checked=false;return}
    if(enabled.checked&&!confirm('Autoriser les destinataires ayant accès Éditeur au fichier Drive ET au mot de passe à modifier les pesées, la taille et les repas de cet enfant ?')){
      enabled.checked=false;return;
    }
    native.setChildEditEnabled?.(p.id,enabled.checked);
    if(native.sharedStatus?.(p.id)==='1')native.autoSave?.(backupPayload());
    redraw();
  });
  sync.onclick=()=>{
    const p=current();
    if(!minor(p)||native.sharedStatus?.(p.id)!=='1')return;
    status.textContent='Lecture du profil enfant partagé depuis Drive…';
    native.syncOwnedChild?.(p.id);
  };
  const oldRender=window.render;
  if(typeof oldRender==='function'){
    window.render=function(...args){const out=oldRender.apply(this,args);redraw();return out};
  }
  redraw();

  let receivedKey='',receivedDocument=null;
  const reader=document.createElement('div');
  reader.className='card';reader.id='child-collab-editor';reader.hidden=true;
  reader.innerHTML='<h3>✎ Modifier le suivi de cet enfant</h3>'+
   '<p class="notice">Partage privé autorisé : les modifications seront enregistrées dans le fichier Drive du propriétaire. Les autres profils restent inaccessibles.</p>'+
   '<label class="field">Date de la mesure<input type="date" id="child-edit-date"></label>'+
   '<label class="field">Poids (kg, facultatif)<input type="number" id="child-edit-weight" min="1" max="400" step=".1"></label>'+
   '<label class="field">Taille mesurée (cm, facultatif)<input type="number" id="child-edit-height" min="45" max="250" step=".1"></label>'+
   '<label class="field">Repas à modifier<select id="child-edit-meal"><option value="">Ne pas modifier les repas</option>'+
   '<option value="morning">Petit-déjeuner</option><option value="morningSnack">Collation du matin</option>'+
   '<option value="lunch">Déjeuner</option><option value="afternoonSnack">Goûter</option>'+
   '<option value="dinner">Dîner</option><option value="eveningSnack">Collation du soir</option></select></label>'+
   '<label class="field" id="child-edit-meal-row" hidden>Description du repas<textarea id="child-edit-meal-text" maxlength="3000" rows="3" style="width:100%;padding:10px;border-radius:10px;background:#092436;color:white"></textarea></label>'+
   '<button type="button" class="primary" id="child-edit-save">Enregistrer dans le partage</button>'+
   '<p class="notice" id="child-edit-status" aria-live="polite"></p>';
  document.getElementById('shared-content')?.insertAdjacentElement('afterend',reader);
  const el=id=>document.getElementById(id);
  const date=el('child-edit-date'),weight=el('child-edit-weight'),height=el('child-edit-height');
  const meal=el('child-edit-meal'),mealRow=el('child-edit-meal-row'),mealText=el('child-edit-meal-text');
  const editorStatus=el('child-edit-status');
  const encodedToObject=raw=>JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(raw),c=>c.charCodeAt(0))));
  const rowForDate=(doc,d)=>(doc?.profile?.entries||[]).filter(e=>e.date===d).sort((a,b)=>Number(a.id||0)-Number(b.id||0)).at(-1)||null;
  function changeDate(){
    if(!receivedDocument)return;
    const e=rowForDate(receivedDocument,date.value);
    weight.value=e?.weight??'';
    height.value=e?.heightCm??'';
    mealChanged();
  }
  function mealChanged(){
    mealRow.hidden=!meal.value;
    mealText.value=meal.value ? String(receivedDocument?.profile?.meals?.[date.value]?.[meal.value]||''):'';
  }
  date.onchange=changeDate;meal.onchange=mealChanged;
  const oldShared=window.sharedLoaded;
  if(typeof oldShared==='function')window.sharedLoaded=function(base64,key){
    const out=oldShared.apply(this,arguments);
    try{
      const doc=encodedToObject(base64);
      const allowed=doc?.collaboration?.editable===true&&minor(doc.profile)
         &&(window.getReceivedList?.().find(x=>x.key===key)?.kind==='private');
      receivedKey=allowed?key:'';
      receivedDocument=allowed?doc:null;
      reader.hidden=!allowed;
      if(allowed){
        date.value=(new Date()).toISOString().slice(0,10);
        date.max=date.value;
        meal.value='';
        editorStatus.textContent='Écriture réservée aux personnes autorisées sur le fichier privé Drive.';
        changeDate();
      }
    }catch(e){reader.hidden=true;receivedDocument=null;receivedKey=''}
    return out;
  };
  el('child-edit-save').onclick=()=>{
    if(!receivedKey||!receivedDocument)return;
    const d=date.value;
    if(!/^\d{4}-\d{2}-\d{2}$/.test(d)||d>new Date().toISOString().slice(0,10))return alert('Date invalide.');
    const edit={date:d};
    const currentRow=rowForDate(receivedDocument,d);
    if(weight.value.trim()){
      const v=Number(weight.value);if(!Number.isFinite(v)||v<1||v>400)return alert('Poids invalide');
      edit.weight=v;edit.expectedRow=currentRow?JSON.stringify(currentRow):'';
    }
    if(height.value.trim()){
      const v=Number(height.value);if(!Number.isFinite(v)||v<45||v>250)return alert('Taille invalide');
      edit.heightCm=v;edit.expectedRow=currentRow?JSON.stringify(currentRow):'';
    }
    if(meal.value){
      edit.mealKey=meal.value;
      edit.mealText=mealText.value.trim().slice(0,3000);
      edit.expectedMeal=String(receivedDocument.profile.meals?.[d]?.[meal.value]||'');
    }
    if(!('weight' in edit)&&!('heightCm' in edit)&&!edit.mealKey)return alert('Renseigne une mesure ou un repas.');
    editorStatus.textContent='Vérification des droits et enregistrement Drive…';
    el('child-edit-save').disabled=true;
    native.updateReceivedChild?.(receivedKey,JSON.stringify(edit));
  };
  window.childEditResult=function(key,result,base64){
    el('child-edit-save').disabled=false;
    if(result!=='ok'){
      editorStatus.textContent={
        conflict:'La même mesure a été modifiée ailleurs. Actualise le profil avant de recommencer.',
        access:'Accès Éditeur Drive nécessaire : le document est en lecture seule.',
        denied:'Le propriétaire n’autorise pas la modification de ce profil.',
        error:'Enregistrement impossible : aucune donnée distante n’a été volontairement remplacée.'
      }[result]||'Échec de synchronisation.';
      if(result==='conflict')native.selectReceivedProfile?.(key);
      return;
    }
    editorStatus.textContent='✓ Modifications enregistrées et partagées.';
    if(base64)window.sharedLoaded?.(base64,key);
    note('Profil enfant mis à jour sur Drive ✓');
  };
  window.childOwnerNeedsSync=function(id){
    if(current()?.id===id&&minor(current())){
      status.textContent='⚠ L’autre parent a modifié ce profil. Utilise « Récupérer les modifications » avant de publier de nouvelles données.';
    }
  };
  window.childOwnerSyncResult=function(id,result,base64){
    if(current()?.id!==id)return;
    if(result==='uptodate'){status.textContent='✓ Le profil enfant est à jour.';return;}
    if(result!=='update'||!base64){status.textContent='Impossible de lire le partage Drive. Vérifie les droits ou le mot de passe.';return;}
    try{
      const doc=encodedToObject(base64),remote=doc.profile;
      const p=data.profiles.find(v=>v.id===id);
      if(!p||!minor(p)||!minor(remote))throw Error('profil');
      const clone=x=>JSON.parse(JSON.stringify(x));
      const merged=clone(p),byId=new Map(merged.entries.map(e=>[String(e.id),e]));
      let conflicts=0,added=0;
      for(const e of remote.entries){
        const key=String(e.id),old=byId.get(key);
        if(!old){merged.entries.push(clone(e));added++}
        else if(JSON.stringify(old)!==JSON.stringify(e)){conflicts++;Object.assign(old,clone(e))}
      }
      merged.meals||={};
      for(const [d,fields] of Object.entries(remote.meals||{})){
        merged.meals[d]||={};
        for(const [k,v] of Object.entries(fields)){
          if(k in merged.meals[d]&&JSON.stringify(merged.meals[d][k])!==JSON.stringify(v))conflicts++;
          merged.meals[d][k]=clone(v);
        }
      }
      if(merged.height!==remote.height){conflicts++;merged.height=remote.height}
      const description='Récupérer '+added+' nouvelle(s) pesée(s) et '+conflicts+
         ' valeur(s) différente(s) depuis Drive ? Les valeurs en conflit de Drive seront prioritaires.';
      if(!confirm(description)){status.textContent='Importation annulée : les données locales sont conservées.';return}
      const revision=Number(doc.collaboration?.revision);
      if(!native.ackOwnedChild?.(id,revision)){status.textContent='Synchronisation interrompue : actualise le document.';return}
      Object.assign(p,merged);
      save();
      render();
      status.textContent='✓ Changements importés et données synchronisées.';
    }catch(e){status.textContent='Impossible de fusionner ce profil sans risque : aucune donnée locale remplacée.'}
  };
})();
