/* Mon Evolution IMC: optional on-device Gemma nutrition estimates.
   Never modify the existing meal/photo records or their strict validator. */
(() => {
  'use strict';
  if (!window.AndroidBackup || typeof AndroidBackup.aiStatus !== 'function') return;
  const toggleKey = 'imc-local-meal-ai-enabled-v1';
  let lastStatus = '';
  let currentRequest = '';
  let aiSettingsExpanded = false;
  const $ai = id => document.getElementById(id);
  const enabled = () => localStorage.getItem(toggleKey) === 'yes';
  const currentProfile = () => profile();
  function status() {
    try { return JSON.parse(AndroidBackup.aiStatus()); }
    catch (_) { return {state:'error',detail:"Etat IA indisponible."}; }
  }
  const asNumber = value => {
    const n = Number(value);
    return Number.isFinite(n) && n >= 0 && n <= 10000 ? Math.round(n * 10) / 10 : null;
  };
  function validResult(raw) {
    const obj = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!obj || typeof obj !== 'object' || obj.error) throw Error(obj?.error || 'Réponse non exploitable');
    const r = {
      description: String(obj.description || '').trim().slice(0, 240),
      kcal: asNumber(obj.kcal),
      protein: asNumber(obj.protein),
      carbs: asNumber(obj.carbs),
      fat: asNumber(obj.fat),
      source: 'Gemma 4 E4B (estimation)'
    };
    if ([r.kcal,r.protein,r.carbs,r.fat].some(x => x === null))
      throw Error('Les estimations numériques sont absentes.');
    return r;
  }
  // Existing analyses are not changed; only their on-screen description is shortened.
  const shortDescription = value => {
    const raw=String(value||'').replace(/\s+/g,' ').trim();
    if(!raw)return 'Aliments et portions estimés';
    const sentence=raw.split(/(?<=[.!?])\s+/)[0];
    const summary=(sentence.length>=15&&sentence.length<=115)?sentence:raw;
    if(summary.length<=115)return summary;
    const cut=summary.slice(0,112);
    return cut.slice(0,Math.max(65,cut.lastIndexOf(' '))).trimEnd()+'…';
  };
  const button = (label, handler) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary'; b.textContent = label;
    b.style.cssText = 'font-size:.86rem;padding:9px 12px;max-width:100%;white-space:normal;';
    b.onclick = handler; return b;
  };
  function buildHeader() {
    const list = $ai('meal-inputs');
    if (!list) return;
    let header = $ai('local-meal-ai-panel');
    if (!header) {
      header = document.createElement('div');
      header.id = 'local-meal-ai-panel';
      header.style.cssText = 'border:1px solid #396676;border-radius:14px;padding:13px;margin:12px 0;background:rgba(75,153,164,.07)';
      list.parentElement.insertBefore(header, list);
    }
    header.replaceChildren();
    const state = status(); lastStatus = state.state;
    const compact = enabled() && !aiSettingsExpanded &&
      (state.state === 'ready' || state.state === 'analyzing');
    if (compact) {
      // Keep a discreet, accessible way to reopen the configuration.
      header.style.cssText = 'border:1px solid #396676;border-radius:12px;padding:7px 10px;margin:8px 0;background:rgba(75,153,164,.07)';
      const row=document.createElement('div');
      row.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:30px';
      const label=document.createElement('span');
      label.style.cssText='font-size:.82rem;opacity:.9';
      label.textContent = state.state==='analyzing'
        ? '✦ IA · analyse en cours…' : '✦ IA active · Gemma E4B';
      row.append(label);
      const settings=button('⚙',()=>{
        aiSettingsExpanded=true;
        buildHeader();
      });
      settings.setAttribute('aria-label','Afficher les paramètres IA');
      settings.title='Paramètres IA';
      settings.style.cssText='padding:4px 10px;min-width:38px;font-size:1rem;';
      row.append(settings);
      header.append(row);
      return;
    }
    header.style.cssText = 'border:1px solid #396676;border-radius:14px;padding:13px;margin:12px 0;background:rgba(75,153,164,.07)';
    const heading = document.createElement('div');
    heading.style.cssText = 'display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap';
    const title = document.createElement('strong'); title.textContent = '✦ IA alimentaire locale · Gemma E4B';
    const label = document.createElement('label'); label.style.cssText='display:flex;gap:6px;align-items:center;font-size:.86rem';
    const toggle = document.createElement('input'); toggle.type='checkbox'; toggle.checked=enabled();
    toggle.onchange = () => {
      localStorage.setItem(toggleKey, toggle.checked?'yes':'no');
      aiSettingsExpanded=false;
      renderMeals();
    };
    label.append(toggle, document.createTextNode('Activer'));
    heading.append(title,label);
    if (enabled() && (state.state==='ready'||state.state==='analyzing')) {
      const collapse=button('▴ Masquer',()=>{aiSettingsExpanded=false;buildHeader();});
      collapse.style.cssText='font-size:.78rem;padding:6px 8px';
      heading.append(collapse);
    }
    header.append(heading);
    const p = document.createElement('p');
    p.style.cssText='margin:9px 0;font-size:.88rem;opacity:.9';
    const labels = {ready:'Prête • 100 % hors ligne',analyzing:'Analyse en cours…',
      checking:'Vérification du téléchargement…',downloading:'Téléchargement en cours…',
      not_installed:'Modèle non installé',incompatible:'Téléphone incompatible',
      error:'Erreur de modèle',removing:'Suppression du modèle…'};
    p.textContent=(labels[state.state] || state.state) + (state.percent>=0?' · '+state.percent+' %':'') +
      (state.detail?' — '+state.detail:'');
    header.append(p);
    if (!enabled()) {
      const hint=document.createElement('p');
      hint.style.cssText='font-size:.82rem;margin:4px 0';
      hint.textContent='Facultatif : désactivé. Vos pesées et photos restent inchangées.';
      header.append(hint);
      return;
    }
    const actions=document.createElement('div');actions.style.cssText='display:flex;gap:8px;flex-wrap:wrap';
    if (state.state==='not_installed' || state.state==='error') {
      actions.append(button('⬇ Installer Gemma E4B (~3,66 Go)',() => {
        if(!confirm("Télécharger 3,66 Go en Wi-Fi ? Le modèle sera conservé lors des mises à jour IMC."))return;
        const res=JSON.parse(AndroidBackup.aiDownload());
        if(res.state==='error')alert(res.detail);
        buildHeader();
      }));
    }
    if (['ready','error','downloading','checking','not_installed'].includes(state.state)) {
      actions.append(button('🗑 Supprimer seulement le modèle IA',() => {
        if (!confirm("Supprimer le modèle IA ? Les profils, repas, photos et pesées seront conservés.")) return;
        const res=JSON.parse(AndroidBackup.aiRemove());
        if(res.state==='error')alert(res.detail);
        buildHeader();
      }));
    }
    header.append(actions);
    const note = document.createElement('p');
    note.style.cssText='font-size:.8rem;opacity:.8;margin:8px 0 0';
    note.textContent="Estimations indicatives. Huile, sauces et portions cachées ne peuvent pas être mesurées précisément à partir d'une photo.";
    header.append(note);
  }
  function drawResults(wrapper, saved, p, date, key) {
    const value = p.aiMeals?.[date]?.[key];
    const photo = saved[key+'Photo'] || '';
    const originalText = String(saved[key]||'').trim();
    if ((!photo && !originalText) || !enabled()) return;
    const box = document.createElement('div');
    box.className='ai-meal-result';
    box.style.cssText='margin:10px 0 16px;padding:12px;border:1px solid #4c7181;border-radius:12px;';
    const heading=document.createElement('div');
    heading.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap';
    const title=document.createElement('strong');title.textContent='✦ Estimation nutritionnelle';
    title.style.cssText='font-size:.9rem';
    heading.append(title);
    const s=status();
    const analyze=button(value?'↻ Réanalyser':(photo?'✦ Analyser la photo':'✦ Analyser le texte'),()=>{
      if (status().state!=='ready') {alert("Installez d'abord le modèle IA et attendez sa vérification.");return;}
      // Persist any unsaved text before asynchronous inference, without replacing the photo.
      const typed=String($ai('meal-'+key)?.value||'').trim();
      if(typed !== originalText) saveMealInputs(false);
      const persisted=mealRecord(p,date);
      const description=String(persisted[key]||'').trim();
      const photoData=persisted[key+'Photo'] || '';
      if(!photoData && !description){alert('Renseignez une description ou une photo du repas.');return;}
      const token=p.id+'|'+date+'|'+key;
      currentRequest=token;
      analyze.disabled=true;analyze.textContent='Analyse en cours…';
      AndroidBackup.aiAnalyze(token,photoData,description);
    });
    analyze.style.cssText+='font-size:.78rem;padding:7px 10px;';
    if(s.state!=='ready')analyze.disabled=true;
    heading.append(analyze);
    box.append(heading);
    if(value) {
      const desc=document.createElement('p');desc.textContent=shortDescription(value.description);
      desc.style.cssText='font-size:.84rem;line-height:1.4;margin:9px 0 5px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;';
      box.append(desc);
      const fields=document.createElement('div');
      fields.style.cssText='display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:9px;width:100%;';
      for(const [prop,label] of [['kcal','kcal'],['protein','Prot. (g)'],
          ['carbs','Gluc. (g)'],['fat','Lip. (g)']]) {
        const cell=document.createElement('label');
        cell.style.cssText='display:flex;flex-direction:column;gap:4px;font-size:clamp(.63rem,2.6vw,.75rem);min-width:0;';
        cell.append(document.createTextNode(label));
        const input=document.createElement('input');input.type='number';input.min='0';input.max='10000';
        input.step='0.1';input.value=String(value[prop]??'');
        input.style.cssText='width:100%;min-width:0;box-sizing:border-box;padding:8px 2px;text-align:center;font-size:clamp(.8rem,3.6vw,1rem);';
        input.onchange=()=>{
          const num=asNumber(input.value);
          if(num===null){alert('Valeur nutritionnelle invalide.');input.value=String(value[prop]??'');return;}
          value[prop]=num;save();refreshTotal();
        };
        cell.append(input);fields.append(cell);
      }
      box.append(fields);
      const deleteEstimate=button('Supprimer cette estimation',()=>{
        if(!confirm("Effacer uniquement le calcul IA de ce repas ?")) return;
        delete p.aiMeals[date][key];save();renderMeals();
      });
      deleteEstimate.style.marginTop='8px';box.append(deleteEstimate);
    }
    const notice=document.createElement('p');notice.style.cssText='font-size:.74rem;opacity:.7;margin:6px 0 0';
    notice.textContent=photo?'Estimation visuelle à corriger si nécessaire.':'Estimation à partir du texte, à corriger selon les quantités.';
    box.append(notice);
    wrapper.append(box);
  }
  function refreshTotal(){
    const p=currentProfile(), day = p.aiMeals?.[mealDate] || {};
    const entries=Object.values(day).filter(v => v && typeof v==='object' && Number.isFinite(Number(v.kcal)));
    const el=$ai('local-meal-ai-total');if(!el)return;
    if(!entries.length){el.textContent='Pas encore de repas analysé ce jour.';return;}
    const total=key=>Math.round(entries.reduce((sum,v)=>sum+(Number(v[key])||0),0));
    el.textContent='Total estimé du jour : '+total('kcal')+' kcal · P '+total('protein')+' g · G '+total('carbs')+' g · L '+total('fat')+' g';
  }
  function decorate() {
    const inputs=$ai('meal-inputs');if(!inputs)return;
    buildHeader();
    if (!enabled())return;
    let total=$ai('local-meal-ai-total');
    if(!total) {
      total=document.createElement('p');total.id='local-meal-ai-total';
      total.style.cssText='font-weight:600;margin:8px 0;padding:10px;border-radius:10px;background:rgba(75,153,164,.1)';
      inputs.parentElement.insertBefore(total,inputs);
    }
    refreshTotal();
    const p=currentProfile(),date=mealDate,saved=mealRecord(p,date);
    for(const [key] of mealTypes){
      const input=$ai('meal-'+key);
      if(!input)return;
      const container=input.closest('.meal-field');
      if(container)drawResults(container,saved,p,date,key);
    }
  }
  const oldRenderMeals=renderMeals;
  renderMeals=function(){oldRenderMeals();decorate();};
  window.localAiMealResult=function(token,resultJson){
    try{
      if(!token || token!==currentRequest) return;
      const [id,date,key]=token.split('|');
      const p=data.profiles.find(q=>q.id===id);
      const meal=p?.meals?.[date];
      if(!p||!mealTypes.some(a=>a[0]===key)||(!meal?.[key+'Photo']&&!String(meal?.[key]||'').trim()))return;
      const obj=validResult(resultJson);
      p.aiMeals ||= {};p.aiMeals[date] ||= {};
      p.aiMeals[date][key]=obj;
      save();
      if(profile().id===id && mealDate===date)renderMeals();
      message('Estimation du repas enregistrée ✓');
    }catch(error){alert('IA alimentaire : '+(error.message||error));renderMeals();}
    finally{currentRequest='';}
  };
  // Restoring the UI after selecting another date/profile leaves all prior meal data intact.
  const timer=window.setInterval(()=>{
    const el=$ai('local-meal-ai-panel');
    if(!el || !enabled())return;
    const s=status();
    if(s.state!==lastStatus || s.state==='downloading') {
      const previous=lastStatus;
      buildHeader();
      if(s.state==='ready' && previous!=='ready')renderMeals();
    }
  },3500);
  renderMeals();
})();
