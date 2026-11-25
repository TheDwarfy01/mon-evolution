/* Mon Évolution IMC — mensurations adultes, mannequin vectoriel personnalisable.
   Fonctionne intégralement hors ligne, enregistre dans les profils existants. */
(function(){
 'use strict';
 const section=document.getElementById('body-measurements');
 if(!section || typeof profile!=='function')return;
 const nav=document.querySelector('.nav [data-tab="body-measurements"]');
 const METRICS=[
  {key:'chest',label:'Poitrine',short:'Poitrine',min:20,max:260,color:'#6de9da'},
  {key:'arm',label:'Bras (tour)',short:'Bras',min:10,max:110,color:'#92c7fa'},
  {key:'waist',label:'Taille (tour)',short:'Taille',min:20,max:260,color:'#2ee1ff'},
  {key:'belly',label:'Ventre (tour)',short:'Ventre',min:20,max:300,color:'#f1a4f9'},
  {key:'hips',label:'Hanches / fessier',short:'Hanches',min:20,max:300,color:'#f6ca63'},
  {key:'thigh',label:'Cuisse',short:'Cuisse',min:15,max:200,color:'#97e9c1'},
  {key:'calf',label:'Mollet',short:'Mollet',min:10,max:130,color:'#e3b6fd'},
  {key:'neck',label:'Cou',short:'Cou',min:10,max:110,color:'#a0d6e8'},
  {key:'forearm',label:'Avant-bras',short:'Avant-bras',min:10,max:110,color:'#b1eabe'}
 ];
 const metricByKey=Object.fromEntries(METRICS.map(m=>[m.key,m]));
 const SKINS=[['Porcelaine','#F7DCC8'],['Clair','#E7B99A'],['Doré','#D99E78'],['Olive','#B77C59'],['Métissé','#996243'],['Brun','#774B35'],['Foncé','#533322'],['Ébène','#34221D']];
 const HAIRS=[['Noir','#201916'],['Brun','#4A2D22'],['Châtain','#7C5238'],['Auburn','#A64D2B'],['Roux','#C96E39'],['Blond','#CDA66A'],['Blond clair','#F0D8A2'],['Gris','#9FA7B0'],['Blanc','#EAE5DA']];
 const EYES=[['Marron','#593826'],['Noisette','#9A7844'],['Vert','#4B8B62'],['Bleu','#4B91C4'],['Gris','#8A9DA5'],['Ambre','#BE873D']];
 const DEFAULT={model:'male',skin:SKINS[2][1],hair:HAIRS[1][1],eyes:EYES[0][1]};
 // COLOR_SLIDER_HELPERS_BEGIN
 const validColor=v=>typeof v==='string'&&/^#[0-9a-f]{6}$/i.test(v);
 const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
 const maxColorStep=colors=>(colors.length-1)*100;
 function gradientColor(colors,position){
  const n=Math.max(0,Math.min(maxColorStep(colors),Number(position)||0))/100;
  const i=Math.min(colors.length-2,Math.floor(n)),t=n-i;
  const a=rgb(colors[i][1]),b=rgb(colors[i+1][1]);
  return '#'+a.map((v,k)=>Math.round(v+(b[k]-v)*t).toString(16).padStart(2,'0')).join('').toUpperCase();
 }
 function gradientPosition(colors,color){
  const exact=colors.findIndex(x=>x[1].toUpperCase()===String(color).toUpperCase());
  if(exact>=0)return exact*100;
  if(!validColor(color))return 0;
  const c=rgb(color);let best=Infinity,position=0;
  for(let i=0;i<colors.length-1;i++){
   const a=rgb(colors[i][1]),b=rgb(colors[i+1][1]),d=b.map((v,k)=>v-a[k]);
   const t=Math.max(0,Math.min(1,d.reduce((s,v,k)=>s+v*(c[k]-a[k]),0)/(d.reduce((s,v)=>s+v*v,0)||1)));
   const error=a.reduce((s,v,k)=>s+(v+t*d[k]-c[k])**2,0);
   if(error<best){best=error;position=Math.round(100*(i+t));}
  }
  return position;
 }
 // COLOR_SLIDER_HELPERS_END
 const APPEARANCE='bodyAppearance', RECORDS='bodyMeasurements';
 let selectedMetric='waist',editingDate=dateNow(),chartSet=new Set(['waist','belly','hips']);
 let draftDirty=false;
 const dirtyMetricKeys=new Set();
 const get=id=>document.getElementById(id);
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const format=n=>Number(n).toLocaleString('fr-FR',{minimumFractionDigits:1,maximumFractionDigits:1});
 const records=p=>(Array.isArray(p?.[RECORDS])?p[RECORDS]:[]).slice().sort((a,b)=>a.date.localeCompare(b.date));
 const lastKnown=(p,key)=>{
  const r=records(p).filter(x=>typeof x[key]==='number').at(-1);
  return r?{value:r[key],date:r.date}:null;
 };
 const validBirth=raw=>typeof raw==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(raw) && Number.isFinite(new Date(raw+'T12:00:00').getTime()) && raw<=dateNow();
 const adult=p=>{ // Kept as a compatibility name; accepts adults AND children
  if(!validBirth(p?.birthDate))return null;
  const now=new Date(dateNow()+'T12:00:00');
  const born=new Date(p.birthDate+'T12:00:00');
  let age=now.getFullYear()-born.getFullYear();
  if(now.getMonth()<born.getMonth()||(now.getMonth()===born.getMonth()&&now.getDate()<born.getDate()))age--;
  return age>=0; // measurements are allowed at every age, without weight-loss goals
 };
 const local=()=>!(typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'));
 // An optional profile extension. Existing backups remain fully compatible.
 const priorValidate=validate;
 validate=function(v){
  priorValidate(v);
  for(const p of v.profiles){
   const list=p.bodyMeasurements;
   if(list===undefined)continue;
   if(!Array.isArray(list)||list.length>3000)throw Error('Mensurations invalides');
   const ids=new Set();
   for(const r of list){
    if(!r||typeof r!=='object'||Array.isArray(r)||
       typeof r.date!=='string'||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(r.date)||
       typeof r.id!=='string'||r.id!=='m-'+r.date||ids.has(r.id))
       throw Error('Mensuration datée invalide');
    ids.add(r.id);
    for(const m of METRICS){
     if(r[m.key]===undefined)continue;
     if(typeof r[m.key]!=='number'||!Number.isFinite(r[m.key])||
        r[m.key]<m.min||r[m.key]>m.max)throw Error('Valeur de mensuration invalide');
    }
    if(r.photo!==undefined &&
      (typeof r.photo!=='string'||!r.photo.startsWith('data:image/jpeg;base64,')||r.photo.length>=250000))
      throw Error('Photo de mensuration invalide');
    if(r.updatedAt!==undefined && (typeof r.updatedAt!=='string'||r.updatedAt.length>80))
      throw Error('Date de modification invalide');
   }
  }
 };
 const appearance=p=>{
  const preferred=p?.sex==='female'?'female':'male';
  const a=p?.[APPEARANCE]||{};
  return {model:['male','female'].includes(a.model)?a.model:preferred,
   skin:validColor(a.skin)?a.skin:DEFAULT.skin,
   hair:validColor(a.hair)?a.hair:DEFAULT.hair,
   eyes:validColor(a.eyes)?a.eyes:DEFAULT.eyes};
 };
 const safeUpdate=(p,key,value)=>{
  p[APPEARANCE]={...appearance(p),[key]:value};
  save();renderMannequin();paintColors();
  // Explicitly repaint the full-resolution photo after the legacy SVG
  // resets the stage; do not rely only on asynchronous MutationObserver.
  window.dispatchEvent(new Event('mon-evolution-appearance-changed'));
 };
 const style=document.createElement('style');
 style.textContent=[
  '.nav{display:flex!important;flex-wrap:nowrap;overflow-x:auto;gap:2px;scrollbar-width:thin;scrollbar-color:#43748b transparent;-webkit-overflow-scrolling:touch}',
  '.nav button{flex:0 0 auto!important;min-width:78px;padding:12px 8px!important;white-space:nowrap;font-size:11px!important}',
  '.nav button[hidden]{display:none!important}',
  '#body-measurements .bm-title{display:flex;gap:9px;align-items:center;color:#f0fcff}',
  '#body-measurements .bm-title span{color:#75f1d8}',
  '.bm-layout{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:13px;margin-top:16px}',
  '#body-measurements .bm-layout[hidden]{display:none!important}',
  '.bm-card{border:1px solid #315e74;background:linear-gradient(145deg,#122f45,#10283c);border-radius:18px;padding:16px;min-width:0}',
  '.bm-card h3{margin:0 0 8px;font-size:17px}',
  '.bm-hint{font-size:12px;color:#a9cad8;line-height:1.5}',
  '.bm-controls{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}',
  '.bm-button{border:1px solid #4d7388;color:#eefaff;background:#23475e;border-radius:12px;padding:9px 13px;min-height:39px;cursor:pointer}',
  '.bm-button[aria-pressed="true"]{border-color:#75f2d3;background:#68eaca;color:#073536;font-weight:800}',
  '.bm-stage{height:595px;max-width:430px;position:relative;margin:0 auto;overflow:hidden;border-radius:15px;background:radial-gradient(ellipse at 50% 35%,#21455a88,transparent 63%)}',
  '.bm-man{height:100%;width:100%;display:block}',
  '.bm-point{position:absolute;display:flex;align-items:center;gap:4px;min-width:87px;max-width:40%;padding:6px 7px;border:1px solid #459bad;border-radius:11px;background:#092638ec;color:#e9fbff;cursor:pointer;box-shadow:0 3px 12px #02101b55;font-size:11px;text-align:left;z-index:1}',
  '.bm-point strong{display:block;font-size:12px}',
  '.bm-point small{display:block;font-size:11px;color:#83eedb}',
  '.bm-point[data-active="true"]{border:2px solid #89ffdf;background:#225b60}',
  '.bm-point[data-side="left"]{left:1%}.bm-point[data-side="right"]{right:1%}',
  '.bm-palette{display:grid;grid-template-columns:1fr;gap:9px;border-top:1px solid #34566b;padding-top:13px}',
  '.bm-palette h4{font-size:12px;margin:0 0 4px;color:#d5edf1;font-weight:650}',
  '.bm-color-slider-row{display:grid;grid-template-columns:minmax(0,1fr) 31px;gap:10px;align-items:center}',
  '.bm-color-range{appearance:none;-webkit-appearance:none;width:100%;height:32px;margin:3px 0;background:transparent;cursor:pointer;touch-action:pan-y}',
  '.bm-color-range::-webkit-slider-runnable-track{height:17px;border-radius:12px;background:var(--bm-gradient);border:1px solid #91aab5}',
  '.bm-color-range::-webkit-slider-thumb{-webkit-appearance:none;width:27px;height:27px;margin-top:-6px;border-radius:50%;background:var(--bm-current);border:3px solid white;box-shadow:0 1px 5px #061725}',
  '.bm-color-range::-moz-range-track{height:17px;border-radius:12px;background:var(--bm-gradient)}',
  '.bm-color-range::-moz-range-thumb{width:24px;height:24px;border-radius:50%;background:var(--bm-current);border:3px solid white}',
  '.bm-color-preview{width:30px;height:30px;border-radius:50%;border:2px solid #a3b7c2;box-sizing:border-box}',
  '.bm-color-value{color:#bdd8df;font-size:11px;display:block;margin-top:2px}',
  '.bm-swatches{display:flex;gap:7px;flex-wrap:wrap}',
  '.bm-swatch{width:29px;height:29px;border-radius:50%;border:2px solid #7891a0;cursor:pointer;box-shadow:0 1px 4px #061725}',
  '.bm-swatch[aria-pressed="true"]{outline:2px solid #71f2d6;outline-offset:2px}',
  '.bm-form-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}',
  '.bm-form-grid label{font-size:12px;color:#c9e2eb;display:block;min-width:0}',
  '.bm-form-grid input,.bm-date,#bm-chart-select{width:100%;border:1px solid #466a7d;border-radius:11px;color:#f6fdff;background:#0b2535;padding:11px 8px;font-size:15px;min-width:0}',
  '.bm-form-grid input:focus{outline:2px solid #72e8d1;outline-offset:1px}',
  '.bm-form-grid input.bm-focused{border:2px solid #75edcc}',
  '.bm-save{display:block;width:100%;margin-top:14px;border:none;border-radius:13px;padding:13px;background:#78ead2;color:#062c2c;font-weight:800;font-size:15px;min-height:45px}',
  '.bm-status{display:block;min-height:1.2em;margin-top:9px;font-size:12px;color:#e3ba83}',
  '.bm-history{max-height:260px;overflow-y:auto}',
  '.bm-history-row{padding:9px 0;border-bottom:1px solid #35556d;display:flex;align-items:center;gap:9px;justify-content:space-between;font-size:12px}',
  '.bm-history-row button{padding:7px 9px;font-size:12px;min-height:34px}',
  '.bm-progress{width:100%;display:block;aspect-ratio:500/265;min-height:170px}',
  '.bm-key{display:flex;gap:9px;flex-wrap:wrap;padding:4px 0 10px}',
  '.bm-key label{font-size:12px;display:flex;gap:5px;align-items:center;cursor:pointer}',
  '.bm-key input{accent-color:#75e9d2}',
  '.bm-last{font-size:13px;color:#c2dce9;margin-top:6px;min-height:30px}',
  '.bm-photo{max-width:100%;max-height:240px;object-fit:contain;border-radius:10px;display:block;margin:10px auto}',
  '.bm-photo-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}',
  '.bm-locked{margin-top:15px;border:1px solid #41667b;border-radius:14px;padding:22px;background:#123248}',
  '@media(max-width:790px){.bm-layout{grid-template-columns:1fr}.bm-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.bm-stage{height:565px}.bm-card{padding:13px}}',
  '@media(max-width:360px){.bm-stage{height:525px}.bm-point{min-width:80px;font-size:10px;padding:5px}.bm-point strong{font-size:11px}}'
 ].join('\n');
 document.head.append(style);
 const colorRgb=s=>parseInt(s.slice(1),16);
 const tint=(hex,scale)=>{
  const n=colorRgb(hex);let components=[(n>>16)&255,(n>>8)&255,n&255];
  components=components.map(c=>Math.max(0,Math.min(255,Math.round(scale>0?c+(255-c)*scale:c*(1+scale)))));
  return '#'+components.map(v=>v.toString(16).padStart(2,'0')).join('');
 };
 const svg=(model,skin,hair,eyes)=>{
  const hi=tint(skin,.17),shadow=tint(skin,-.24),hairHi=tint(hair,.22);
  const female=model==='female';
  const legs=female?
   '<path d="M121 348 Q144 359 155 363 L155 444 L147 535 Q146 563 144 581 L118 581 Q115 564 117 539 L117 440 Q112 405 117 365 Z"/><path d="M166 364 Q179 351 198 348 L202 418 L199 488 L204 581 L177 581 Q170 540 170 501 L164 431 Z"/>':
   '<path d="M125 347 Q144 358 155 363 L153 444 L144 575 L117 575 Q117 562 118 538 L118 429 L116 371 Z"/><path d="M166 363 Q185 352 198 348 L204 435 L203 530 L204 575 L178 575 Q170 525 170 465 Z"/>';
  const torso=female?
   '<path d="M129 152 Q145 146 151 145 L169 145 Q188 148 195 155 Q189 197 187 227 Q182 255 195 295 Q204 324 204 353 L116 353 Q118 318 127 293 Q140 256 133 230 Q130 185 129 152Z"/>':
   '<path d="M118 153 Q144 145 151 146 L170 146 Q191 146 202 154 Q197 187 197 226 Q196 257 194 286 L200 353 L120 353 Q125 303 124 281 Q124 249 123 226 Z"/>';
  const arms=female?
   '<path d="M129 153 Q116 152 108 171 L96 218 L82 281 L67 339 Q65 356 77 360 Q89 353 91 341 L108 290 L125 246 L137 184Z"/><path d="M194 154 Q208 153 217 173 L227 227 L240 279 L253 338 Q259 354 245 362 Q234 358 230 342 L209 287 L193 242 L184 184Z"/>':
   '<path d="M119 153 Q102 145 91 169 L78 215 L67 273 L52 335 Q48 353 61 360 Q75 356 77 340 L96 290 L115 245 L135 178Z"/><path d="M200 153 Q221 147 230 171 L241 218 L255 277 L270 336 Q273 352 258 360 Q246 355 244 341 L223 287 L204 241 L184 178Z"/>';
  const hairShape=female?
   '<ellipse cx="160" cy="45" rx="22" ry="18" fill="'+hair+'"/><path d="M125 74 Q118 40 147 45 Q173 34 190 55 Q199 79 189 124 L178 132 L176 99 Q169 90 165 70 Q153 89 127 94 L131 122 Q113 111 125 74Z" fill="'+hair+'"/><path d="M125 74 Q133 50 158 56 Q180 56 189 83" fill="none" stroke="'+hairHi+'" stroke-width="3" opacity=".5"/>':
   '<path d="M129 79 Q118 43 153 43 Q192 39 194 73 L189 95 L181 66 Q165 71 154 63 Q145 77 130 80Z" fill="'+hair+'"/><path d="M133 63 Q151 49 169 53 Q184 52 190 69" fill="none" stroke="'+hairHi+'" stroke-width="4" opacity=".5"/>';
  const suit=female?
   '<path d="M132 204 Q152 210 161 204 Q180 211 189 205 L194 244 Q167 251 126 243Z" fill="#172938" stroke="#7092a3" stroke-width="1.5"/><path d="M130 203 L138 179 L143 179 L140 208 M186 207 L181 179 L176 179 L182 207" fill="none" stroke="#172938" stroke-width="6"/><path d="M120 345 Q163 351 200 345 L204 402 L172 405 L164 378 L156 378 L147 405 L115 402Z" fill="#1c3446" stroke="#74889a" stroke-width="1.6"/>':
   '<path d="M119 337 Q159 344 199 337 L200 402 L171 404 L165 372 L155 372 L147 405 L118 401Z" fill="#1c3446" stroke="#74889a" stroke-width="1.6"/><path d="M160 341 L160 375" stroke="#4b6677" stroke-width="1.5"/>';
  const defs='<defs><linearGradient id="bm-skin" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="'+shadow+'"/><stop offset=".29" stop-color="'+skin+'"/><stop offset=".62" stop-color="'+hi+'"/><stop offset="1" stop-color="'+shadow+'"/></linearGradient><linearGradient id="bm-light" x1="0" y1="0" x2="0" y2="1"><stop stop-color="'+hi+'"/><stop offset="1" stop-color="'+skin+'"/></linearGradient></defs>';
  return '<svg class="bm-man" viewBox="0 0 320 620" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Mannequin '+(female?'féminin':'masculin')+' personnalisable avec repères de mensurations" xmlns="http://www.w3.org/2000/svg">'+defs+
   '<ellipse cx="160" cy="607" rx="70" ry="7" fill="#001322" opacity=".35"/>'+
   '<g stroke="'+shadow+'" stroke-width="1.1" stroke-linejoin="round" fill="url(#bm-skin)">'+legs+arms+torso+
   '<path d="M150 124 L150 155 Q160 165 170 154 L170 124Z"/>'+
   '<ellipse cx="160" cy="94" rx="37" ry="48" fill="url(#bm-light)"/>'+
   '<path d="M117 565 L146 565 L147 584 Q143 596 117 596 Q105 591 117 565Z"/><path d="M178 565 L204 565 L213 594 Q191 599 178 591Z"/></g>'+
   hairShape+
   '<path d="M140 92 Q145 87 151 91 M169 91 Q175 87 181 91" fill="none" stroke="'+tint(hair,-.3)+'" stroke-width="2.4" stroke-linecap="round"/>'+
   '<ellipse cx="147" cy="94" rx="3.5" ry="2.8" fill="#f7f0e8"/><ellipse cx="175" cy="94" rx="3.5" ry="2.8" fill="#f7f0e8"/>'+
   '<circle cx="147" cy="94" r="2" fill="'+eyes+'"/><circle cx="175" cy="94" r="2" fill="'+eyes+'"/>'+
   '<circle cx="147" cy="94" r=".9" fill="#11171a"/><circle cx="175" cy="94" r=".9" fill="#11171a"/>'+
   '<path d="M161 98 L158 108 L163 110" fill="none" stroke="'+shadow+'" stroke-width="1.2"/>'+
   '<path d="M150 117 Q161 121 171 116" stroke="'+tint(skin,-.42)+'" fill="none" stroke-width="1.6" stroke-linecap="round"/>'+
   (!female?'<path d="M132 210 Q150 218 159 208 Q171 218 188 209 M159 216 L159 308 M136 281 Q158 291 183 281" stroke="'+shadow+'" stroke-width="1.8" fill="none" opacity=".35"/>':'')+
   suit+
   '<g fill="none" stroke="#62f6de" stroke-width="1.5" stroke-dasharray="5 4" opacity=".9">'+
   '<path d="M117 224 Q160 231 201 224"/><path d="M120 292 Q160 298 198 292"/>'+
   '<path d="M119 318 Q159 331 200 318"/><path d="M118 351 Q159 357 200 351"/>'+
   '<path d="M113 452 Q130 458 146 452"/><path d="M177 499 Q190 505 205 499"/>'+
   '</g>'+
   '<g fill="#65edd5" stroke="#a9fff1" stroke-width="1.5">'+
   '<circle cx="160" cy="224" r="5"/><circle cx="219" cy="239" r="5"/>'+
   '<circle cx="160" cy="292" r="5"/><circle cx="162" cy="318" r="5"/>'+
   '<circle cx="160" cy="352" r="5"/><circle cx="128" cy="451" r="5"/>'+
   '<circle cx="195" cy="500" r="5"/><circle cx="160" cy="146" r="4"/>'+
   '</g></svg>';
 };
 section.innerHTML='<div class="bm-title"><span>📏</span><h2 style="margin:0">Mensurations</h2></div>'+
  '<p class="muted">Suivi des mensurations corporelles pour adultes et enfants. Toutes les valeurs sont en centimètres.</p>'+
  '<div id="bm-lock" class="bm-locked" hidden></div>'+
  '<div id="bm-main" class="bm-layout">'+
   '<div class="bm-card"><h3>📏 Ma silhouette</h3><p class="bm-hint">Appuie sur une zone du mannequin pour saisir ou consulter sa mesure.</p>'+
    '<div class="bm-controls" id="bm-models"></div>'+
    '<div id="bm-model" class="bm-stage"></div>'+
    '<div id="bm-colors" class="bm-palette"></div>'+
    '<div class="bm-last" id="bm-latest"></div>'+
   '</div>'+
   '<div style="display:grid;gap:13px;align-content:start">'+
    '<div class="bm-card"><h3>▣ Enregistrer les mensurations</h3>'+
      '<label class="bm-hint" for="bm-date">Date de mesure</label>'+
      '<input id="bm-date" class="bm-date" type="date" style="margin:6px 0 12px"/>'+
      '<div id="bm-fields" class="bm-form-grid"></div>'+
      '<button id="bm-save" class="bm-save" type="button">✓ Enregistrer les mensurations</button>'+
      '<small id="bm-status" class="bm-status" role="status"></small>'+
      '<div class="bm-photo-actions"><button type="button" class="bm-button" id="bm-pick-photo">📷 Photo de progression</button><button type="button" class="bm-button" id="bm-remove-photo" hidden>Supprimer la photo</button></div>'+
      '<div id="bm-photo-box"></div>'+
    '</div>'+
    '<div class="bm-card"><h3>☷ Historique des mensurations</h3><div class="bm-history" id="bm-history"></div></div>'+
    '<div class="bm-card"><h3>↗ Évolution des mensurations</h3><p class="bm-hint">Sélectionne les courbes à comparer.</p><div id="bm-legend" class="bm-key"></div><svg id="bm-graph" class="bm-progress" viewBox="0 0 500 265" role="img" aria-label="Graphique des mensurations"></svg><p class="bm-hint">Mesures renseignées uniquement — pas d’interpolation médicale.</p></div>'+
   '</div>'+
  '</div>';
 const coords={
  chest:{side:'left',y:'27%',label:'Poitrine'},arm:{side:'right',y:'33%',label:'Bras'},
  waist:{side:'left',y:'41%',label:'Taille'},belly:{side:'right',y:'49%',label:'Ventre'},
  hips:{side:'left',y:'55%',label:'Hanches'},thigh:{side:'left',y:'69%',label:'Cuisse'},
  calf:{side:'right',y:'80%',label:'Mollet'},neck:{side:'right',y:'22%',label:'Cou'},
  forearm:{side:'right',y:'62%',label:'Avant-bras'}
 };
 function renderMannequin() {
  const p=profile(),a=appearance(p),stage=get('bm-model');
  // Preserve the independently downloaded MakeHuman viewer on every repaint.
  // Discarding the WebGL canvas here silently reverted the UI to old photos
  // whenever a profile, measure or appearance changed.
  const makeHumanCanvas=stage.querySelector(':scope > canvas.bm-makehuman-canvas');
  const palette=stage.querySelector(':scope > #bm-colors');
  const colorToggle=stage.querySelector(':scope > .bm-colors-toggle');
  stage.innerHTML=svg(a.model,a.skin,a.hair,a.eyes);
  if(makeHumanCanvas)stage.append(makeHumanCanvas);
  if(palette)stage.append(palette);
  if(colorToggle)stage.append(colorToggle);
  const modelButtons=get('bm-models');
  modelButtons.replaceChildren();
  for(const [key,name] of [['male','♂ Homme'],['female','♀ Femme']]){
   const b=document.createElement('button');b.className='bm-button';
   b.type='button';b.textContent=name;
   b.setAttribute('aria-pressed',String(a.model===key));
   b.onclick=()=>safeUpdate(p,'model',key);
   modelButtons.append(b);
  }
  for(const m of METRICS){
   const c=coords[m.key],last=lastKnown(p,m.key);
   const b=document.createElement('button');b.className='bm-point';b.type='button';
   b.style.top=c.y;b.dataset.side=c.side;b.dataset.active=String(selectedMetric===m.key);
   b.setAttribute('aria-label','Saisir '+m.label+', '+(last?format(last.value)+' centimètres':'aucune mesure'));
   const name=document.createElement('span');
   const strong=document.createElement('strong');strong.textContent=c.label;
   const small=document.createElement('small');small.textContent=last?format(last.value)+' cm':'— cm';
   name.append(strong,small);b.append(name);
   b.onclick=()=>{
    selectedMetric=m.key;
    const input=get('bm-'+m.key);
    if(input){input.focus();input.scrollIntoView({behavior:'smooth',block:'center'})}
    [...stage.querySelectorAll('.bm-point')].forEach(e=>e.dataset.active=String(e===b));
   };
   stage.append(b);
  }
  const latest=records(p).at(-1);
  get('bm-latest').textContent=latest?'Dernière saisie : '+day(latest.date):'Aucune mensuration enregistrée.';
 }
 function paintColors(){
  const p=profile(),a=appearance(p);
  const box=get('bm-colors');box.replaceChildren();
  for(const [property,label,colors] of [['skin','Carnation',SKINS],['hair','Couleur des cheveux',HAIRS],['eyes','Couleur des yeux',[EYES[0],EYES[5],EYES[1],EYES[2],EYES[3],EYES[4]]]]){
   const group=document.createElement('div');
   const h=document.createElement('label');h.textContent=label;h.htmlFor='bm-color-'+property;
   h.style.cssText='font-size:12px;font-weight:650;color:#d5edf1';group.append(h);
   const row=document.createElement('div');row.className='bm-color-slider-row';
   const range=document.createElement('input');range.type='range';range.className='bm-color-range';range.id=h.htmlFor;
   range.min='0';range.max=String(maxColorStep(colors));range.step='1';
   range.value=String(gradientPosition(colors,a[property]));range.disabled=!local();
   range.style.setProperty('--bm-gradient','linear-gradient(to right,'+colors.map(c=>c[1]).join(',')+')');
   const swatch=document.createElement('span');swatch.className='bm-color-preview';swatch.setAttribute('aria-hidden','true');
   const value=document.createElement('span');value.className='bm-color-value';
   function display(color){
    const name=colors.find(c=>c[1].toUpperCase()===color.toUpperCase())?.[0]||'Nuance personnalisée';
    range.style.setProperty('--bm-current',color);swatch.style.backgroundColor=color;
    value.textContent=name;range.setAttribute('aria-valuetext',name+' '+color);
   }
   display(a[property]);let dirty=false;
   function commit(){if(!dirty)return;dirty=false;save();}
   range.addEventListener('input',()=>{
    const current=profile();if(!local()||!current||String(current.id)!==String(p.id))return;
    const color=gradientColor(colors,range.value);
    current[APPEARANCE]={...appearance(current),[property]:color};dirty=true;display(color);
    // Live preview without rebuilding the WebGL stage or the active slider.
    if(!get('bm-model').classList.contains('bm-makehuman-active')){
     const picture=get('bm-model').querySelector(':scope > svg.bm-man'),app=appearance(current);
     if(picture)picture.outerHTML=svg(app.model,app.skin,app.hair,app.eyes);
    }
    window.dispatchEvent(new Event('mon-evolution-appearance-changed'));
   });
   for(const event of ['change','blur','pointercancel'])range.addEventListener(event,commit);
   row.append(range,swatch);group.append(row,value);box.append(group);
  }
 }
 function ensureRecord(p,date){
  p[RECORDS] ||= [];
  let r=p[RECORDS].find(x=>x.date===date);
  if(!r){r={id:'m-'+date,date,updatedAt:new Date().toISOString()};p[RECORDS].push(r)}
  return r;
 }
 function dateChosen(){
  const d=get('bm-date').value;
  editingDate=d||dateNow();
  const p=profile(),r=records(p).find(v=>v.date===editingDate);
  for(const m of METRICS){get('bm-'+m.key).value=typeof r?.[m.key]==='number'?String(r[m.key]):''}
  const img=get('bm-photo-box');img.replaceChildren();
  get('bm-remove-photo').hidden=!r?.photo;
  if(typeof r?.photo==='string'&&/^data:image\/jpeg;base64,/.test(r.photo)){
   const picture=document.createElement('img');picture.src=r.photo;picture.className='bm-photo';picture.alt='Photo de progression '+day(editingDate);
   img.append(picture);
  }
  draftDirty=false;dirtyMetricKeys.clear();
  get('bm-status').textContent=r?'Mesures du '+day(editingDate)+' chargées.':'Nouvelle saisie.';
 }
 function drawFields(){
  const fields=get('bm-fields');fields.replaceChildren();
  for(const m of METRICS){
   const lab=document.createElement('label');lab.htmlFor='bm-'+m.key;lab.textContent=m.label;
   const input=document.createElement('input');input.id='bm-'+m.key;input.type='number';
   input.inputMode='decimal';input.min=String(m.min);input.max=String(m.max);input.step='0.1';input.placeholder='— cm';
   input.oninput=()=>{draftDirty=true;dirtyMetricKeys.add(m.key);get('bm-status').textContent='● Modifications non enregistrées';};
   input.onfocus=()=>{
    selectedMetric=m.key;
    [...get('bm-model').querySelectorAll('.bm-point')].forEach(b=>b.dataset.active=String(b.getAttribute('aria-label')?.startsWith('Saisir '+m.label+',')));
   };
   lab.append(input);fields.append(lab);
  }
 }
 function saveMeasurements(){
  if(adult(profile())!==true||!local())return;
  const date=get('bm-date').value;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||date>dateNow()||!validBirth(date)) {
   get('bm-status').textContent='Choisis une date valide, non future.';return;
  }
  const values={};let any=false;
  for(const m of METRICS){
   const input=get('bm-'+m.key);
   const t=input.value.trim().replace(',','.');
   if(!t)continue;
   const val=Number(t);
   if(!Number.isFinite(val)||val<m.min||val>m.max){
    input.focus();get('bm-status').textContent=m.label+' : valeur attendue entre '+m.min+' et '+m.max+' cm.';return;
   }
   values[m.key]=Math.round(val*10)/10;any=true;
  }
  const p=profile(),existing=records(p).find(x=>x.date===date);
  if(!any&&!existing?.photo){
   get('bm-status').textContent='Renseigne au moins une mensuration ou ajoute une photo.';return;
  }
  const changedKeys=[...dirtyMetricKeys].filter(key=>Object.prototype.hasOwnProperty.call(values,key));
  const rec=ensureRecord(p,date);
  for(const m of METRICS){if(m.key in values)rec[m.key]=values[m.key];else delete rec[m.key]}
  rec.updatedAt=new Date().toISOString();
  save();
  renderData();
  window.dispatchEvent(new CustomEvent('mon-evolution-measurements-changed',{
   detail:{profileId:p.id,date,changedKeys}
  }));
  get('bm-status').textContent='✓ Mensurations du '+day(date)+' enregistrées.';
 }
 function renderHistory(){
  const parent=get('bm-history');parent.replaceChildren();
  const p=profile();const rows=records(p).slice().reverse();
  if(!rows.length){parent.textContent='Aucune mesure. Ajoute une première date pour commencer ton suivi.';parent.classList.add('bm-hint');return;}
  for(const r of rows){
   const row=document.createElement('div');row.className='bm-history-row';
   const detail=document.createElement('div');
   const title=document.createElement('strong');title.textContent=day(r.date);
   const desc=document.createElement('div');desc.className='bm-hint';
   const parts=METRICS.filter(m=>typeof r[m.key]==='number').map(m=>m.short+' '+format(r[m.key]));
   desc.textContent=parts.slice(0,4).join(' · ')+(parts.length>4?' · +'+(parts.length-4):'')+(r.photo?' · 📷':'');
   detail.append(title,desc);
   const buttons=document.createElement('div');buttons.style.cssText='display:flex;gap:5px';
   const edit=document.createElement('button');edit.className='bm-button';edit.type='button';edit.title='Modifier';
   edit.setAttribute('aria-label','Modifier les mensurations du '+day(r.date));edit.textContent='✎';
   edit.onclick=()=>{
    if(draftDirty&&!confirm('Des modifications ne sont pas enregistrées. Ouvrir une autre date ?'))return;
    get('bm-date').value=r.date;dateChosen();get('bm-date').scrollIntoView({behavior:'smooth',block:'center'});
   };
   const del=document.createElement('button');del.className='bm-button';del.type='button';del.title='Supprimer';
   del.setAttribute('aria-label','Supprimer les mensurations du '+day(r.date));del.textContent='🗑';
   del.onclick=()=>{
    if(!confirm('Supprimer les mensurations et la photo du '+day(r.date)+' sur ce profil ?'))return;
    p[RECORDS]=p[RECORDS].filter(x=>x.id!==r.id);
    save();renderData();dateChosen();
    window.dispatchEvent(new CustomEvent('mon-evolution-measurements-changed',{
     detail:{profileId:p.id,date:r.date,deleted:true}
    }));
   };
   buttons.append(edit,del);row.append(detail,buttons);parent.append(row);
  }
 }
 function renderGraph(){
  const key=get('bm-legend');key.replaceChildren();
  for(const m of METRICS){
   const label=document.createElement('label');
   const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=chartSet.has(m.key);
   checkbox.onchange=()=>{if(checkbox.checked)chartSet.add(m.key);else chartSet.delete(m.key);renderGraph()};
   const dot=document.createElement('span');dot.style.cssText='width:8px;height:8px;border-radius:50%;background:'+m.color;
   label.append(checkbox,dot,document.createTextNode(m.short));key.append(label);
  }
  const graph=get('bm-graph');graph.replaceChildren();
  const NS='http://www.w3.org/2000/svg';
  const el=(tag,attrs,text)=>{
   const item=document.createElementNS(NS,tag);
   for(const [k,v] of Object.entries(attrs||{}))item.setAttribute(k,String(v));
   if(text!==undefined)item.textContent=text;
   graph.append(item);return item;
  };
  const values=records(profile()).filter(x=>METRICS.some(m=>chartSet.has(m.key)&&Number.isFinite(x[m.key])));
  if(!values.length){el('text',{x:250,y:130,fill:'#c2dce8','text-anchor':'middle','font-size':15},'Choisis des mesures pour voir leur évolution.');return;}
  const times=values.map(r=>new Date(r.date+'T12:00:00').getTime());
  const minTime=Math.min(...times),maxTime=Math.max(...times);
  const all=values.flatMap(r=>METRICS.filter(m=>chartSet.has(m.key)&&Number.isFinite(r[m.key])).map(m=>r[m.key]));
  let bottom=Math.max(0,Math.floor((Math.min(...all)-8)/5)*5),top=Math.ceil((Math.max(...all)+8)/5)*5;
  if(top-bottom<20){top=bottom+20}
  const X=t=>55+(maxTime===minTime?195:(t-minTime)/(maxTime-minTime)*415);
  const Y=v=>226-(v-bottom)/(top-bottom)*198;
  for(let i=0;i<=4;i++){
   const v=bottom+i*(top-bottom)/4,y=Y(v);
   el('line',{x1:53,y1:y,x2:478,y2:y,stroke:'#45647b','stroke-width':1,'stroke-opacity':.55});
   el('text',{x:47,y:y+4,fill:'#b8d4e0','font-size':12,'text-anchor':'end'},format(v));
  }
  const marks=[values[0],values[Math.floor((values.length-1)/2)],values[values.length-1]];
  for(const r of [...new Set(marks)]){
   const x=X(new Date(r.date+'T12:00:00').getTime());
   el('text',{x,y:251,fill:'#c4dde6','font-size':11,'text-anchor':'middle'},new Date(r.date+'T12:00:00').toLocaleDateString('fr-FR',{day:'2-digit',month:'short'}));
  }
  for(const m of METRICS.filter(k=>chartSet.has(k.key))){
   const pts=values.filter(r=>Number.isFinite(r[m.key])).map(r=>({x:X(new Date(r.date+'T12:00:00').getTime()),y:Y(r[m.key]),value:r[m.key],date:r.date}));
   if(!pts.length)continue;
   if(pts.length>1)el('polyline',{points:pts.map(p=>p.x+','+p.y).join(' '),fill:'none',stroke:m.color,'stroke-width':2.8,'stroke-linecap':'round','stroke-linejoin':'round'});
   for(const pt of pts){
    const circ=el('circle',{cx:pt.x,cy:pt.y,r:4.3,fill:m.color,stroke:'#17394a','stroke-width':1.5});
    const title=document.createElementNS(NS,'title');title.textContent=m.label+' · '+day(pt.date)+' : '+format(pt.value)+' cm';circ.append(title);
   }
  }
 }
 function renderData(){
  renderMannequin();paintColors();renderHistory();renderGraph();dateChosen();
 }
 // Shared profiles may optionally contain measurements with the owner's consent.
 // Never display the active PERSONAL profile's measurements for a received profile.
 const receivedMeasurements=new Map();
 const receivedBirths=new Map();
 const priorSharedLoaded=window.sharedLoaded;
 window.sharedLoaded=function(encoded,key){
   try{
     const raw=new TextDecoder().decode(Uint8Array.from(atob(encoded),x=>x.charCodeAt(0)));
     const doc=JSON.parse(raw);
     if(doc.format==='mon-evolution-lecture-seule'&&doc.version===1&&
        doc.profile && Array.isArray(doc.profile.bodyMeasurements)){
       const list=doc.profile.bodyMeasurements.filter(r=>r && typeof r==='object' &&
         /^\d{4}-\d{2}-\d{2}$/.test(r.date||'') &&
         METRICS.some(m=>Number.isFinite(r[m.key])&&r[m.key]>=m.min&&r[m.key]<=m.max));
       receivedMeasurements.set(key,list.slice(-3000));
       if(typeof doc.profile.birthDate==='string')receivedBirths.set(key,doc.profile.birthDate);
     }else{
       receivedMeasurements.delete(key);
       if(typeof doc.profile?.birthDate==='string')receivedBirths.set(key,doc.profile.birthDate);
     }
   }catch(e){receivedMeasurements.delete(key);receivedBirths.delete(key)}
   const result=typeof priorSharedLoaded==='function'?priorSharedLoaded.apply(this,arguments):undefined;
   if(!section.hidden && !local())queueMicrotask(refreshAccess);
   return result;
 };
 function showReadOnly(){
   const parent=get('bm-lock');parent.replaceChildren();
   const key=(typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'))?
     unifiedCurrent.slice(9):'';
   const friend=typeof getReceivedList==='function'?getReceivedList().find(f=>f.key===key):null;
   const heading=document.createElement('h3');heading.textContent='Mensurations de '+(friend?.name||'ce profil partagé');
   parent.append(heading);
   const readOnly=document.createElement('p');
   readOnly.className='bm-hint';
   readOnly.textContent='Consultation en lecture seule. Aucune modification du profil personnel ou du fichier Drive.';
   parent.append(readOnly);
   const list=receivedMeasurements.get(key)||[];
   if(!list.length){
     const note=document.createElement('p');
     note.textContent='Aucune mensuration partagée pour le moment. Les mesures du propriétaire ne sont pas visibles sans son autorisation.';
     parent.append(note);
     return;
   }
   for(const r of list.slice().sort((a,b)=>b.date.localeCompare(a.date)).slice(0,45)){
     const line=document.createElement('div');line.className='bm-history-row';
     const date=document.createElement('strong');date.textContent=day(r.date);
     const details=document.createElement('span');
     details.textContent=METRICS.filter(m=>Number.isFinite(r[m.key]))
       .map(m=>m.short+' : '+format(r[m.key])+' cm').join(' · ');
     line.append(date,details);parent.append(line);
   }
 }
 function refreshAccess(){
   const readonly=!local();
   const key=readonly&&typeof unifiedCurrent==='string'?unifiedCurrent.slice(9):'';
   const eligible=readonly?(receivedBirths.has(key)?adult({birthDate:receivedBirths.get(key)}):null):adult(profile());
   const allowed=eligible===true&&!readonly;
   // Never disappear simply because a SHARED profile is selected.
   // A verified local child is excluded; unspecified age shows an explanation.
   nav.hidden=eligible===false;
   get('bm-main').hidden=!allowed;get('bm-lock').hidden=allowed;
   if(!allowed){
     if(readonly)showReadOnly();
     else get('bm-lock').textContent=eligible===false?
       'Renseigne une date de naissance valide pour accéder aux mensurations.':
       'Pour activer les mensurations, renseigne la date de naissance dans Profils.';
     if(!section.hidden && eligible===false){
       section.hidden=true;
       const home=document.querySelector('.nav [data-tab="home"]');
       if(home)home.click();
     }
     return;
   }
   if(!get('bm-date').value) get('bm-date').value=editingDate;
   renderData();
 }
 drawFields();
 get('bm-date').value=editingDate;
 get('bm-date').max=dateNow();
 get('bm-date').addEventListener('change',()=>{
  if(draftDirty&&!confirm('Modifications non enregistrées. Changer de date ?')){
   get('bm-date').value=editingDate;return;
  }
  dateChosen();
 });
 get('bm-save').onclick=saveMeasurements;
 get('bm-pick-photo').onclick=()=>{
  if(adult(profile())!==true)return;
  if(draftDirty){
   if(!confirm('Enregistrer les mensurations saisies avant de choisir la photo ?'))return;
   saveMeasurements();
   if(draftDirty)return;
  }
  const d=get('bm-date').value;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(d)||d>dateNow()){get('bm-status').textContent='Choisis une date valide.';return;}
  if(!window.AndroidBackup?.pickPhoto){get('bm-status').textContent='Photo disponible dans l’application Android.';return}
  AndroidBackup.pickPhoto('bodyphoto|'+profile().id+'|'+d);
 };
 get('bm-remove-photo').onclick=()=>{
  const p=profile(),r=records(p).find(x=>x.date===get('bm-date').value);
  if(!r?.photo||!confirm('Supprimer uniquement cette photo de progression ?'))return;
  delete r.photo;r.updatedAt=new Date().toISOString();
  if(!METRICS.some(m=>typeof r[m.key]==='number'))p[RECORDS]=p[RECORDS].filter(x=>x.id!==r.id);
  save();renderData();get('bm-status').textContent='Photo supprimée.';
 };
 const previousPhotoPicked=photoPicked;
 photoPicked=function(token,photo){
  if(typeof token==='string'&&token.startsWith('bodyphoto|')){
   const parts=token.split('|');const id=parts[1],date=parts[2];
   const p=data.profiles.find(v=>v.id===id);
   if(!p||adult(p)!==true || !/^\d{4}-\d{2}-\d{2}$/.test(date)||date>dateNow() ||
      !/^data:image\/jpeg;base64,/.test(photo)||photo.length>=250000){
    message('Photo de mensuration non reconnue');return;
   }
   const r=ensureRecord(p,date);r.photo=photo;r.updatedAt=new Date().toISOString();
   save();if(profile().id===id)renderData();message('Photo de mensuration enregistrée ✓');
   return;
  }
  return previousPhotoPicked(token,photo);
 };
 const oldRender=render;
 render=function(){const result=oldRender.apply(this,arguments);refreshAccess();return result;};
 const oldShowUnified=typeof showUnifiedTab==='function'?showUnifiedTab:null;
 if(oldShowUnified){
  showUnifiedTab=function(tab){
   const result=oldShowUnified.apply(this,arguments);
   section.hidden=tab!=='body-measurements';return result;
  };
 }
 // Hide sensitive local body measurements when switching to a shared profile.
 const oldSelectUnified=typeof selectUnified==='function'?selectUnified:null;
 if(oldSelectUnified){
  selectUnified=function(){
   const result=oldSelectUnified.apply(this,arguments);
   if(!local())section.hidden=true;
   refreshAccess();
   return result;
  };
 }
 window.showSharedBodyMeasurements=function(){
   if(local())return;
   if(typeof showUnifiedTab==='function')showUnifiedTab('body-measurements');
   else{
     document.querySelectorAll('main>section').forEach(s=>s.hidden=s!==section);
     document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('on',b===nav));
   }
   section.hidden=false;refreshAccess();
 };
 nav.addEventListener('click',e=>{
  if(!local()){e.preventDefault();window.showSharedBodyMeasurements();return;}
  if(adult(profile())!==true){e.preventDefault();refreshAccess();return;}
  if(typeof showUnifiedTab==='function')showUnifiedTab('body-measurements');
  else{
   document.querySelectorAll('main>section').forEach(s=>s.hidden=s!==section);
   document.querySelectorAll('.nav [data-tab]').forEach(b=>b.classList.toggle('on',b===nav));
  }
  section.hidden=false;refreshAccess();
 });
 // Prevent accidental loss when leaving the page or switching a profile.
 document.addEventListener('click',e=>{
  if(section.hidden||!draftDirty)return;
  const clicked=e.target?.closest?.('.nav [data-tab],#visual-profile-picker .profile-portrait-choice');
  if(!clicked||clicked===nav)return;
  if(!confirm('Des mensurations sont modifiées sans être enregistrées. Quitter cette saisie ?')){
   e.preventDefault();e.stopImmediatePropagation();
  }else draftDirty=false;
 },true);
 document.addEventListener('change',e=>{
  if(section.hidden||!draftDirty)return;
  const el=e.target;
  if(el?.id!=='unified-profile-picker'&&el?.id!=='profile-picker')return;
  if(!confirm('Des mensurations sont modifiées sans être enregistrées. Changer de profil ?')){
   e.preventDefault();e.stopImmediatePropagation();
   if(el.id==='unified-profile-picker')el.value=unifiedCurrent;
   else el.value=data.active;
  }else draftDirty=false;
 },true);
 document.addEventListener('click',e=>{
  const button=e.target?.closest?.('[data-tab]');
  if(button&&button!==nav){section.hidden=true;}
 },true);
 refreshAccess();
})();