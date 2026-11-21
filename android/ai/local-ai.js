/* Mon Evolution IMC: optional on-device Gemma nutrition estimates.
   Never modify the existing meal/photo records or their strict validator. */
(() => {
  'use strict';
  if (!window.AndroidBackup || typeof AndroidBackup.aiStatus !== 'function') return;
  const toggleKey = 'imc-local-meal-ai-enabled-v1';
  let lastStatus = '';
  let currentRequest = '';
  let installedOnce = false;
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
      description: String(obj.description || '').slice(0, 600),
      kcal: asNumber(obj.kcal),
      protein: asNumber(obj.protein),
      carbs: asNumber(obj.carbs),
      fat: asNumber(obj.fat),
      source: 'Gemma 4 E2B (estimation)'
    };
    if ([r.kcal,r.protein,r.carbs,r.fat].some(x => x === null))
      throw Error('Les estimations numériques sont absentes.');
    return r;
  }
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
    const heading = document.createElement('div');
    heading.style.cssText = 'display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap';
    const title = document.createElement('strong'); title.textContent = '✦ IA alimentaire locale · Gemma';
    const label = document.createElement('label'); label.style.cssText='display:flex;gap:6px;align-items:center;font-size:.86rem';
    const toggle = document.createElement('input'); toggle.type='checkbox'; toggle.checked=enabled();
    toggle.onchange = () => { localStorage.setItem(toggleKey, toggle.checked?'yes':'no'); renderMeals(); };
    label.append(toggle, document.createTextNode('Activer'));
    heading.append(title,label);header.append(heading);
    const state = status();lastStatus=state.state;
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
      actions.append(button('⬇ Installer Gemma (~2,59 Go)',() => {
        if(!confirm("Télécharger 2,59 Go en Wi-Fi ? Le modèle sera conservé lors des mises à jour IMC."))return;
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
    const photo = saved[key+'Photo'];
    if (!photo || !enabled()) return;
    const box = document.createElement('div');
    box.className='ai-meal-result';
    box.style.cssText='margin:10px 0 16px;padding:12px;border:1px solid #4c7181;border-radius:12px;';
    const title=document.createElement('strong');title.textContent='✦ Estimation nutritionnelle';
    box.append(title);
    const s=status();
    const analyze=button(value?'↻ Réanalyser la photo':'✦ Analyser la photo',()=>{
      if (status().state!=='ready') {alert("Installez d'abord le modèle IA et attendez sa vérification.");return;}
      const token=p.id+'|'+date+'|'+key;
      currentRequest=token;
      const description=$ai('meal-'+key)?.value||saved[key]||'';
      AndroidBackup.aiAnalyze(token,photo,description);
      analyze.disabled=true;analyze.textContent='Analyse locale en cours…';
    });
    if (s.state!=='ready') analyze.disabled=true;
    box.append(analyze);
    if(value) {
      const desc=document.createElement('p');desc.textContent=value.description||'Aliments reconnus';
      desc.style.cssText='font-size:.87rem;margin:10px 0';box.append(desc);
      const fields=document.createElement('div');
      fields.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px;';
      for(const [prop,label,unit] of [['kcal','Calories','kcal'],['protein','Protéines','g'],
          ['carbs','Glucides','g'],['fat','Lipides','g']]) {
        const cell=document.createElement('label');cell.style.cssText='display:flex;flex-direction:column;gap:3px;font-size:.78rem';
        cell.append(document.createTextNode(label+' ('+unit+')'));
        const input=document.createElement('input');input.type='number';input.min='0';input.max='10000';
        input.step='0.1';input.value=String(value[prop]??'');
        input.style.cssText='width:100%;box-sizing:border-box';
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
    notice.textContent='Chiffres approximatifs à corriger selon les quantités réelles.';
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
      if(!p||!mealTypes.some(a=>a[0]===key)||!p.meals?.[date]?.[key+'Photo'])return;
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
