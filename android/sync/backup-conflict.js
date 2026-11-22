/* Mon Évolution IMC: explicit, guarded reconciliation of a changed backup file.
   No silent overwrite; keep remote-only data and local-only data. */
(() => {
  'use strict';
  if (!window.AndroidBackup?.readBackupForMerge || !window.AndroidBackup?.resolveBackupMerge) return;
  const card = document.getElementById('drive-state');
  if (!card || typeof data === 'undefined') return;
  const panel = document.createElement('div');
  panel.id='backup-conflict-panel';
  panel.style.cssText='display:none;margin:12px 0;padding:14px;border:1px solid #deaf67;border-radius:12px;background:#283646;color:#f3f6f9;line-height:1.5;';
  card.insertAdjacentElement('afterend',panel);
  let pending=null, notified=false, resolving=false;
  const isObj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const copy = x => JSON.parse(JSON.stringify(x));
  const same = (a,b) => JSON.stringify(a)===JSON.stringify(b);
  // Use a genuine per-record edit timestamp when both versions have one.
  // A weighing's calendar date is NOT an edit timestamp.
  const editedAt = x => {
    if(!isObj(x))return null;
    const value=x.updatedAt||x.modifiedAt||x.lastModifiedAt;
    if(typeof value!=='string' || !/^\d{4}-\d{2}-\d{2}T/.test(value))return null;
    const ms=Date.parse(value);
    return Number.isFinite(ms) ? ms : null;
  };
  const btn = (text, click) => {
    const b=document.createElement('button');b.className='secondary';b.type='button';
    b.textContent=text;b.style.cssText='padding:11px 13px;min-height:44px;white-space:normal;flex:1 1 190px';
    b.onclick=click;return b;
  };
  function show(state, detail='') {
    panel.replaceChildren();
    panel.style.display='block';
    const heading=document.createElement('strong');
    heading.textContent=state==='pending'?'↻ Lecture de la sauvegarde Drive…':
      state==='review'?'⇄ Fusion sécurisée des sauvegardes':
      state==='saving'?'↻ Enregistrement de la fusion…':
      state==='error'?'⚠ Fusion suspendue':'⚠ Sauvegarde Drive modifiée';
    panel.append(heading);
    const p=document.createElement('p');
    p.style.cssText='margin:8px 0 10px;font-size:.9rem;';
    p.textContent=detail || 'Le fichier Drive a été modifié depuis la dernière sauvegarde de ce téléphone. Les données locales sont conservées. La sauvegarde automatique est suspendue pour éviter un écrasement.';
    panel.append(p);
    if(state==='saving'||state==='pending')return;
    const actions=document.createElement('div');actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
    if(state==='review' && pending) {
      const summary=document.createElement('div');
      summary.style.cssText='font-size:.86rem;flex-basis:100%;margin:0 0 6px;';
      const count=pending.stats;
      summary.textContent='Données à réunir : '+count.profiles+' profil(s), '+count.entries+' pesée(s) supplémentaires, '+count.meals+' donnée(s) de repas, '+count.ai+' estimation(s) IA. '+count.conflicts+' valeur(s) différente(s) présentes des deux côtés.';
      actions.append(summary);
      const explain=document.createElement('p');explain.style.cssText='font-size:.82rem;margin:0 0 7px;flex-basis:100%;';
      explain.textContent='Si une date de modification fiable existe des deux côtés, la plus récente est retenue. Sinon, choisis une priorité pour les différences. Les données uniques sont réunies sans propager automatiquement les suppressions.';
      actions.append(explain);
      actions.append(btn('Privilégier ce téléphone',()=>commit('local')));
      actions.append(btn('Privilégier Drive',()=>commit('remote')));
      actions.append(btn('Annuler',()=>{pending=null;show('conflict')}));
    } else {
      actions.append(btn('Comparer et fusionner',()=>{
        if(resolving)return;
        pending=null;show('pending');
        AndroidBackup.readBackupForMerge();
      }));
    }
    panel.append(actions);
  }
  function reconcile(local, remote, preference, stats) {
    const prefer = (a,b) => copy(preference==='local'?a:b);
    function merge(a,b,path, lastEdited=null) {
      if(a===undefined)return copy(b);
      if(b===undefined)return copy(a);
      if(same(a,b))return copy(a);
      if(Array.isArray(a)&&Array.isArray(b) && (path.endsWith('.entries') || path.endsWith('.bodyMeasurements'))) {
        const out=copy(a);
        const seen=new Map(out.map((item,i)=>[String(item.id),i]));
        for(const item of b){
          const id=String(item.id);
          if(!seen.has(id)){seen.set(id,out.length);out.push(copy(item));stats.entries++}
          else out[seen.get(id)]=merge(out[seen.get(id)],item,path+'.entry');
        }
        return out;
      }
      if(isObj(a)&&isObj(b)) {
        const ta=editedAt(a),tb=editedAt(b);
        const newest=ta!==null&&tb!==null&&ta!==tb?(ta>tb?'local':'remote'):lastEdited;
        const out={};
        for(const key of new Set([...Object.keys(a),...Object.keys(b)])){
          if(a[key]===undefined) {
            out[key]=copy(b[key]);
            if(path.endsWith('.meals'))stats.meals++;
            if(path.endsWith('.aiMeals'))stats.ai++;
          }else if(b[key]===undefined)out[key]=copy(a[key]);
          else out[key]=merge(a[key],b[key],path+'.'+key,newest);
        }
        return out;
      }
      stats.conflicts++;
      if(lastEdited==='local')return copy(a);
      if(lastEdited==='remote')return copy(b);
      return prefer(a,b);
    }
    const profiles=copy(local.profiles);
    const lookup=new Map(profiles.map((p,i)=>[p.id,i]));
    for(const p of remote.profiles){
      if(!lookup.has(p.id)) {
        lookup.set(p.id,profiles.length);profiles.push(copy(p));stats.profiles++;
      }else {
        const i=lookup.get(p.id);
        if(profiles[i].name !== p.name) {
          // An accidentally reused ID must not combine two different people.
          const clone=copy(p);
          let n=1;
          let fresh='import_'+String(p.id).replace(/[^a-zA-Z0-9_-]/g,'')+'_'+n;
          while(lookup.has(fresh)){n++;fresh='import_'+String(p.id).replace(/[^a-zA-Z0-9_-]/g,'')+'_'+n}
          clone.id=fresh;
          lookup.set(fresh,profiles.length);profiles.push(clone);stats.profiles++;
        } else profiles[i]=merge(profiles[i],p,'profile');
      }
    }
    return {...copy(local),profiles,active:local.active};
  }
  function evaluate(remote) {
    const stats={profiles:0,entries:0,meals:0,ai:0,conflicts:0};
    reconcile(data,remote,'local',stats);
    return stats;
  }
  window.backupConflict=()=>{
    // A banner replaces repeated modal alerts on each local change.
    if(!resolving && !pending)show('conflict');
    if(!notified){
      notified=true;
      message('⚠ Sauvegarde Drive suspendue : comparer et fusionner dans Profils.');
    }
  };
  window.backupMergeLoaded=(encoded,remoteHash)=>{
    try {
      const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
      const doc=JSON.parse(new TextDecoder().decode(bytes));
      if(!window.MonEvolutionQuality?.isBackupDocument(doc))throw Error('Sauvegarde Drive incompatible');
      validate(doc.data);
      if(typeof remoteHash!=='string'||!remoteHash.trim())throw Error('Empreinte Drive manquante');
      const stats=evaluate(doc.data);
      pending={remote:doc.data,hash:remoteHash,stats};
      show('review');
    }catch(e){pending=null;show('error','Lecture ou validation impossible : '+(e.message||e));}
  };
  window.backupMergeReadFailed=(reason)=>{
    pending=null;show('error','Impossible de lire le fichier Drive. Aucune donnée locale n’a été modifiée. '+String(reason||''));
  };
  function commit(preference) {
    if(!pending || resolving)return;
    try{
      const plan=pending;
      const currentStats={profiles:0,entries:0,meals:0,ai:0,conflicts:0};
      const merged=reconcile(data,plan.remote,preference,currentStats);
      if(merged.profiles.length>50)throw Error('Plus de 50 profils après fusion');
      validate(merged);
      const description='Fusionner la sauvegarde Drive avec les données de ce téléphone ?\n\n'+
        'Éléments supplémentaires : '+currentStats.profiles+' profils, '+currentStats.entries+' pesées, '+currentStats.meals+' entrées de repas.\n'+
        'Différences sur les mêmes champs : '+currentStats.conflicts+
        '. Priorité : '+(preference==='local'?'ce téléphone':'Drive')+'.\n\n'+
        'Une fusion sera enregistrée localement d’abord. Drive ne sera modifié que si son fichier n’a pas changé entre-temps.';
      if(!confirm(description))return;
      // Keep a copy of the ORIGINAL local version for a possible recovery.
      const beforeMerge=JSON.stringify({format:'mon-evolution',version:1,
        exportedAt:new Date().toISOString(),data});
      // Protect the merged result locally first, even if the remote write fails.
      data=merged;
      save(false);
      render();
      resolving=true;
      show('saving','Fusion locale conservée. Copies de sécurité et vérification finale avant écriture Drive.');
      AndroidBackup.resolveBackupMerge(backupPayload(),plan.hash,beforeMerge);
      pending=null;
    }catch(e){
      resolving=false;show('error','Fusion non effectuée : '+(e.message||e));
    }
  }
  window.backupMergeSaved=()=>{
    resolving=false;pending=null;notified=false;
    panel.style.display='none';
    refreshDriveState();
    if(typeof renderBackupVerification==='function')renderBackupVerification();
    message('✓ Fusion Drive enregistrée. Données des deux appareils conservées.');
  };
  window.backupMergeSaveFailed=(reason)=>{
    resolving=false;pending=null;
    show('error','La fusion locale est conservée, mais Drive n’a pas été remplacé. '+String(reason||'Vérifie puis recommence la comparaison.'));
  };
})();