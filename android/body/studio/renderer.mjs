/* MakeHuman Studio v2 for Mon Évolution IMC.
 * Original implementation with Three.js (MIT); source GLBs are CC0 assets.
 * Large rigged character + actual textures, separate hair and clothing meshes.
 * The old v1 procedural painter is deliberately not loaded.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { profileCategory, allowedOutfitsFor } from './profile-rules.mjs';
import { FACE_CHOICES,faceMorphsFor } from './face-presets.mjs';
import { latestMeasurements, visualRatios, deformPosition } from './measurement-morph.mjs';
import { createStudioMarkers } from './measurement-markers.mjs';
import { estimatedThighIntensity,softenInnerThigh } from './thigh-fill.mjs';
import { readVisualOverrides,recordVisualOverrides,resolveVisualMeasurements } from './visual-overrides.mjs';
import { isStudioEnabled, setStudioEnabled } from './visibility-preference.mjs';
import { hideMaskFor, coveredTriangle, behindOpaqueGarment } from './clothing-coverage.mjs';
import { maskIndexedTriangles, touchesExposedArm, touchesSleeveOpening } from './skin-triangle-mask.mjs';
import {applyUniformBodySkin} from './skin-material.mjs';
import { estimateVisualMeasurements, readVisualMode, writeVisualMode } from './visual-defaults.mjs';
import {annySnapshot} from './anny-profile.mjs';
import {ANNY_ANCHORS,annyWeights,visualIndex,annyFile,isAnnyFile} from './anny-inline.mjs';
import {REGIONS} from './measurement-morph.mjs';
import {initialView,boundedView,pinchView,gestureDirection,needsRecenter} from './studio-zoom.mjs';

(()=>{
'use strict';
const section=document.getElementById('body-measurements');
const stage=document.getElementById('bm-model');
const root=document.getElementById('bm-main');
const bridge=window.AndroidBackup;
if(!section||!stage||!root||!bridge||typeof bridge.makeHumanStudioState!=='function')return;
const HAIRS={
 short02:'Court naturel',short04:'Court soigné',bob02:'Carré',
 long01:'Long',ponytail01:'Queue-de-cheval',braid01:'Tresse',afro01:'Bouclé'
};
const CLOTHES={
 // A single stable outfit avoids abrupt leg-color boundaries and garment swaps.
 classic:{label:'T-shirt et jean',files:['clothing_tshirt.glb','clothing_jeans.glb','clothing_shoes.glb']}
};
// Only licensed fitted garment meshes are exposed in the profile-specific choices.
const css=document.createElement('style');
css.id='makehuman-studio-style';
css.textContent=[
 '#body-measurements #bm-model.bm-makehuman-active{position:relative!important;isolation:isolate!important;background:radial-gradient(ellipse at 55% 35%,#28536b,#0f263b 78%)!important;}',
 '#body-measurements #bm-model canvas.bm-makehuman-canvas{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;display:block!important;z-index:2!important;touch-action:pan-y;border-radius:12px;}',
 '#body-measurements .bm-mh-panel{display:flex!important;align-items:center;justify-content:center;gap:9px;flex-wrap:wrap;margin:10px 0 14px!important;padding:11px;border:1px solid #2d6279;border-radius:13px;background:#12354c;}',
 '#body-measurements .bm-mh-panel button{cursor:pointer;border:1px solid #6fcfb9;border-radius:11px;padding:10px 14px;background:#185f68;color:#effffb;min-height:43px;font-weight:650;}',
 '#body-measurements .bm-mh-panel span{font-size:11px;color:#b9d7df;text-align:center;line-height:1.35;width:100%;}',
 '#body-measurements .bm-studio-controls{display:flex;gap:9px;flex-wrap:wrap;justify-content:space-between;margin:10px 0 5px;}',
 '#body-measurements .bm-studio-controls label{flex:1 1 120px;font-size:12px;color:#c7e9ef;}',
 '#body-measurements .bm-studio-controls select{background:#103448;color:#e8f9ff;border:1px solid #457e8d;border-radius:8px;min-height:40px;margin-top:4px;padding:7px;width:100%;}',
 '#body-measurements .bm-shape-controls{display:flex;gap:6px;align-items:stretch;flex-wrap:wrap;margin:5px 0 8px}',
 '#body-measurements .bm-shape-controls button{flex:1 1 90px;min-width:0;cursor:pointer;border:1px solid #47788b;border-radius:9px;background:#153b52;color:#e8fbff;padding:8px 6px;min-height:41px;font-size:11px}',
 '#body-measurements .bm-shape-controls button[aria-pressed="true"]{background:#1b706e;border-color:#8feeda;color:#fff;font-weight:800}',
 '#body-measurements .bm-zoom-tools{position:absolute;left:8px;top:8px;z-index:11;display:flex;gap:4px;align-items:center;background:#0b2c40df;border:1px solid #47788b;padding:3px;border-radius:9px;touch-action:manipulation}',
 '#body-measurements .bm-zoom-tools[hidden]{display:none!important}',
 '#body-measurements .bm-zoom-tools button{border:1px solid #47788b;background:#153b52;color:#effffb;border-radius:6px;min-height:33px;min-width:33px;font-size:15px;padding:4px 7px;touch-action:manipulation}',
 '#body-measurements .bm-zoom-tools button:disabled{opacity:.4}',
 '#body-measurements .bm-shape-warning{width:100%;font-size:11px;color:#bdd8df;line-height:1.4;margin:2px 0 0}',
 '#body-measurements #bm-main.bm-table-only .bm-studio-controls,#body-measurements #bm-main.bm-table-only .bm-shape-controls{display:none!important;}'
].join('\n');
document.head.append(css);
const panel=document.createElement('div');panel.className='bm-mh-panel';
const btn=document.createElement('button');btn.type='button';btn.textContent='Installer le modèle 3D Studio';
const note=document.createElement('span');note.setAttribute('role','status');
note.textContent='Module distinct de l’APK · textures, vêtements, cheveux et animation';
panel.append(btn,note);stage.before(panel);
const controls=document.createElement('div');controls.className='bm-studio-controls';
function selectOption(label,options){
 const field=document.createElement('label');
 field.textContent=label;
 const select=document.createElement('select');
 for(const [key,text] of options){
  const el=document.createElement('option');el.value=key;el.textContent=text;select.append(el);
 }
 field.append(select);controls.append(field);return select;
}
const hairSel=selectOption('Coiffure',Object.entries(HAIRS));
// Use only facial shape keys confirmed to exist in the actual exported GLB.
const faceSel=selectOption('Visage',FACE_CHOICES.map(o=>[o.id,o.label]));
const clothSel=selectOption('Tenue',Object.entries(CLOTHES).map(([id,o])=>[id,o.label]));
// Only one authorized outfit remains, so hide the unnecessary choice.
clothSel.parentElement.hidden=true;
panel.insertAdjacentElement('afterend',controls);
// Display modes only change the artistic 3D body; not the records or growth data.
const shapeControls=document.createElement('div');shapeControls.className='bm-shape-controls';
const modeButtons=new Map();
for(const [mode,label] of [['measured','Mes mesures'],['neutral','↺ Réinitialiser'],['estimated','≈ Selon mon poids']]){
 const button=document.createElement('button');button.type='button';button.textContent=label;
 button.setAttribute('aria-pressed','false');button.title=label;
 button.addEventListener('click',()=>setVisualMode(mode));
 modeButtons.set(mode,button);shapeControls.append(button);
}
const shapeWarning=document.createElement('p');shapeWarning.className='bm-shape-warning';
shapeWarning.textContent='Le rendu est indicatif. Rien ne sera effacé ni ajouté à ton historique.';
shapeControls.append(shapeWarning);controls.insertAdjacentElement('afterend',shapeControls);

const gauges=document.createElement('div');gauges.className='bm-anny-gauges';gauges.hidden=true;
const gaugeCss=document.createElement('style');
gaugeCss.textContent='#body-measurements .bm-anny-gauges{padding:10px;border:1px solid #315f77;border-radius:12px;background:#102e41;margin:8px 0;color:#d9f8f2;display:grid;gap:7px}#body-measurements .bm-anny-gauges[hidden]{display:none!important}#body-measurements .bm-anny-gauges label{font-size:12px}#body-measurements .bm-anny-gauges input[type=range]{width:100%;accent-color:#75e8d0;min-height:28px}#body-measurements .bm-anny-gauges select{width:100%;padding:8px;border-radius:8px;color:#e8f9ff;background:#153b52;border:1px solid #47788b}#body-measurements .bm-anny-gauges p{font-size:11px;margin:0;color:#b9d7df}#body-measurements #bm-model.bm-anny-active>.bm-man,#body-measurements #bm-model.bm-anny-active>.bm-point,#body-measurements #bm-model.bm-anny-active>.bm-measure-lines,#body-measurements #bm-model.bm-anny-active>.bm-photo-canvas,#body-measurements #bm-model.bm-anny-active>.bm-photo-fallback{display:none!important}';
document.head.append(gaugeCss);
const gaugeTitle=document.createElement('strong');gaugeTitle.textContent='Ajustement de la silhouette';
const massLabel=document.createElement('label'),massRange=document.createElement('input');
const regionLabel=document.createElement('label'),regionRange=document.createElement('input');
const regionSelect=document.createElement('select');regionSelect.setAttribute('aria-label','Zone à ajuster');
for(const item of REGIONS){const opt=document.createElement('option');opt.value=item.key;opt.textContent=item.label;regionSelect.append(opt);}
regionSelect.value='belly';
for(const [range,label] of [[massRange,massLabel],[regionRange,regionLabel]]){
 range.type='range';range.min='-100';range.max='100';range.step='1';range.id=range===massRange?'anny-mass':'anny-region';label.htmlFor=range.id;
}
const gaugeHelp=document.createElement('p');gaugeHelp.textContent='Jauges visuelles uniquement : aucune mesure ni pesée enregistrée n’est modifiée. « Selon mon poids » recale les jauges.';
gauges.append(gaugeTitle,massLabel,massRange,regionSelect,regionLabel,regionRange,gaugeHelp);
shapeControls.after(gauges);
const fallback=document.createElement('button');fallback.type='button';fallback.textContent='Ouvrir en rendu natif';fallback.hidden=true;fallback.style.display='none';
fallback.onclick=()=>{const p=profileInfo();if(!isAnny(p))return;const snap=annyVisual(p);if(snap)bridge.openAnnyProfile(JSON.stringify(snap));};panel.append(fallback);
function annyVisual(p){
 const snap=annySnapshot(p,visualMode(p),displayedMeasurements(p));if(!snap)return null;
 const sig=JSON.stringify([p.sex,p.height,p.weight,p.lastDate,p.measurements,p.measurementDate,visualMode(p)]);
 let d=visualDrafts.get(String(p.id));if(d?.sig!==sig){d={sig,local:{}};visualDrafts.set(String(p.id),d);}
 if(Number.isFinite(d.mass))snap.mass=d.mass;
 for(const region of snap.regions)if(Number.isFinite(d.local[region.key]))region.local=d.local[region.key];
 return snap;
}
function updateGauges(p,snap){
 if(!snap)return;
 const selected=snap.regions.find(x=>x.key===regionSelect.value)||snap.regions[5];
 massRange.value=String(Math.round(snap.mass*100));
 massLabel.textContent='Corpulence · '+p.weight.toLocaleString('fr-FR')+' kg · IMC '+(p.weight/(p.height/100)**2).toLocaleString('fr-FR',{maximumFractionDigits:1})+' · indice visuel '+visualIndex(snap.mass);
 regionRange.value=String(Math.round(selected.local*100));
 regionLabel.textContent=selected.label+' · '+Math.round(100+50*selected.local)+' % (visuel)';
}
function setGauge(kind,value){
 const p=profileInfo();if(!active||!isAnny(p)||!annyVisual(p))return;
 const d=visualDrafts.get(String(p.id));
 if(kind==='mass')d.mass=value;else d.local[regionSelect.value]=value;
 configure();renderOnce();
}
massRange.oninput=()=>setGauge('mass',Number(massRange.value)/100);
regionRange.oninput=()=>setGauge('region',Number(regionRange.value)/100);
regionSelect.onchange=()=>{const p=profileInfo();if(isAnny(p))updateGauges(p,annyVisual(p));};
function selectAnnyGauge(key){if(!gauges.hidden){regionSelect.value=key;regionSelect.onchange();}}
function setAnnyLayout(enabled){
 controls.style.setProperty('display',enabled?'none':'','important');
 if(!enabled)controls.style.removeProperty('display');
 if(enabled&&shapeControls.previousElementSibling!==stage)stage.after(shapeControls);
 if(!enabled&&shapeControls.previousElementSibling!==controls)controls.after(shapeControls);
 if(gauges.previousElementSibling!==shapeControls)shapeControls.after(gauges);
 gauges.hidden=!enabled||!active;
}

const canvas=document.createElement('canvas');canvas.className='bm-makehuman-canvas';
canvas.setAttribute('aria-label','Mannequin 3D MakeHuman habillé');canvas.setAttribute('role','img');
stage.append(canvas);
const zoomTools=document.createElement('div');zoomTools.className='bm-zoom-tools';zoomTools.hidden=true;zoomTools.setAttribute('aria-label','Zoom du mannequin');
const zoomReset=document.createElement('button');
zoomReset.type='button';zoomReset.textContent='⤢ Recentrer';zoomReset.title='Rétablir le cadrage initial du mannequin';
zoomReset.setAttribute('aria-label',zoomReset.title);zoomTools.append(zoomReset);
stage.append(zoomTools);
const parser=new GLTFLoader();
let renderer=null,scene=null,camera=null,mixer=null,figure=null,body=null,lighting=null;
let active=false,busy=false,disposed=false,autoShowAfterInstall=false,currentKey='',oldStatus='',firstRun=true;
let lastY=0,yaw=0,raf=0,profileId='',lastProfileCheck=0;
let cameraView=initialView();const pointers=new Map();let touchGesture=null;
let studioBounds=null,studioMarkers=null,markerProfile=null,studioBones=[];
let bodyKind='',annyMesh=null,annyCurrent=null;
const visualDrafts=new Map();
const basePositions=new WeakMap();
const loaded=new Map(),pending=new Map(),clothing=new Map(),hairObjects=new Map();
const autoTriedProfiles=new Set();
function isAnny(p){return !!(p&&!p.child&&typeof bridge.annyAssetBytes==='function');}
function visibilityStore(){try{return window.localStorage;}catch{return null;}}
function visibilityEnabled(id){return isStudioEnabled(String(id||''),visibilityStore());}
function rememberVisibility(id,enabled){return setStudioEnabled(String(id||''),enabled,visibilityStore());}
function visualMode(p){return readVisualMode(p?.id,visibilityStore());}
function displayedMeasurements(p){
 return resolveVisualMeasurements(p,visualMode(p),readVisualOverrides(p.id,visibilityStore()));
}
function syncVisualMode(p){
 const mode=visualMode(p);
 for(const [value,button] of modeButtons)button.setAttribute('aria-pressed',String(value===mode));
 shapeWarning.textContent=mode==='neutral'?
  'Silhouette neutre : historique conservé, aucune mensuration supprimée.':
  mode==='estimated'?
  (p.child?'Enfant : forme illustrative uniquement, sans référence médicale ni norme de croissance.':
    'Silhouette indicative ajustée au poids et à la taille ; une mesure enregistrée remplace l’estimation correspondante.'):
  (isAnny(p)?'Corpulence indicative selon ton poids ; les tours enregistrés ajustent chaque zone.':'Silhouette fondée sur les tours réellement enregistrés dans ton historique.');
}
function setVisualMode(mode){
 const p=profileInfo();if(!p)return;
 if(!writeVisualMode(p.id,mode,visibilityStore())){
  note.textContent='Préférence indisponible : stockage local inaccessible.';return;
 }
 visualDrafts.delete(String(p.id));
 syncVisualMode(p);
 currentKey='';refreshScene(true);
}
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function ensureMounted(){
 if(!stage.contains(canvas))stage.append(canvas);
 if(!stage.contains(zoomTools))stage.append(zoomTools);
 if(!panel.isConnected)stage.before(panel);
 if(!controls.isConnected)panel.after(controls);
 if(!shapeControls.isConnected){if(isAnny(profileInfo()))stage.after(shapeControls);else controls.after(shapeControls);}
 if(!gauges.isConnected)shapeControls.after(gauges);
}
new MutationObserver(ensureMounted).observe(stage,{childList:true});
function profileInfo(){
 if(typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'))return null;
 const p=typeof profile==='function'?profile():null;
 if(!p)return null;
 const weights=(p.entries||[]).filter(e=>Number.isFinite(+e.weight)&&+e.weight>0)
  .slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
 if(!weights.length||!(+p.height>40))return null;
 // The profile itself is authoritative. The old appearance selector may
 // contain a stale sex and must NEVER override the person it represents.
 const kind=profileCategory(p);
 if(!kind)return null;
 const weight=+weights.at(-1).weight,initial=+weights[0].weight;
 const {age,child}=kind,app=p.bodyAppearance||{};
 const records=(p.bodyMeasurements||[]).filter(r=>r&&r.date).slice()
  .sort((a,b)=>a.date.localeCompare(b.date));
 const last=records.at(-1)||{};
 const measurements=latestMeasurements(p);
 return {id:p.id||'',sex:kind.sex,kind:kind.kind,
   age,child,height:+p.height,weight,initial,
   skin:app.skin||'#D99E78',hair:app.hair||'#4A2D22',eyes:app.eyes||'#593826',
   waist:measurements.waist??null,hips:measurements.hips??null,
   measurements,records,measurementDate:records.at(-1)?.date||'',
   lastDate:weights.at(-1).date};
}
function allowedOutfits(p){
 return allowedOutfitsFor(p.kind);
}
function choices(p){
 let options={};
 try{options=JSON.parse(localStorage.getItem('mh-studio-v2-'+p.id)||'{}')||{}}catch{}
 const allowed=allowedOutfits(p);
 return {hair:HAIRS[options.hair]?options.hair:(p.sex==='female'?'bob02':'short02'),
  face:FACE_CHOICES.some(o=>o.id===options.face)?options.face:'soft',
  clothes:allowed.includes(options.clothes)?options.clothes:(allowed[0]||'classic')};
}
function syncOutfitControl(p){
 const allowed=allowedOutfits(p);
 const previous=clothSel.value;
 const current=[...clothSel.options].map(o=>o.value);
 if(current.join('|')===allowed.join('|'))return;
 clothSel.replaceChildren();
 for(const id of allowed){
  const opt=document.createElement('option');
  opt.value=id;opt.textContent=CLOTHES[id].label;clothSel.append(opt);
 }
 clothSel.value=allowed.includes(previous)?previous:allowed[0];
}
function saveChoice(){
 const p=profileInfo();if(!p)return;
 try{localStorage.setItem('mh-studio-v2-'+p.id,
  JSON.stringify({hair:hairSel.value,face:faceSel.value,clothes:clothSel.value}));}catch{}
 refreshScene(true);
}
async function readGlb(name){
 const anny=isAnnyFile(name);
 if(!anny&&!/^(?:base_body_anim|hair_(?:short02|short04|bob02|long01|ponytail01|braid01|afro01)|clothing_(?:tshirt|jeans|shoes))\.glb$/.test(name)){
  throw Error('Fichier 3D non autorisé : '+String(name));
 }
 const size=anny?bridge.annyAssetBytes(name):bridge.makeHumanStudioBytes(name);
 if(!(size>10000&&size<14000000))throw Error('Ressource absente : '+name);
 const bytes=new Uint8Array(size);
 for(let start=0;start<size;start+=49152){
  const part=anny?bridge.annyAssetReadChunk(name,start):bridge.makeHumanStudioReadChunk(name,start);
  if(!part)throw Error('Lecture impossible : '+name);
  const raw=atob(part);
  if(raw.length>size-start)throw Error('Lecture 3D invalide');
  for(let i=0;i<raw.length;i++)bytes[start+i]=raw.charCodeAt(i);
  if((start%(49152*8))===0)await new Promise(done=>setTimeout(done,0));
 }
 if(bytes[0]!==103||bytes[1]!==108||bytes[2]!==84||bytes[3]!==70)
  throw Error('Format 3D incorrect');
 return parser.parseAsync(bytes.buffer,'');
}
function asset(name){
 if(loaded.has(name))return Promise.resolve(loaded.get(name));
 if(pending.has(name))return pending.get(name);
 const task=readGlb(name).then(g=>{loaded.set(name,g);pending.delete(name);return g;})
  .catch(e=>{pending.delete(name);throw e;});
 pending.set(name,task);return task;
}
function init(){
 if(renderer)return;
 renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;
 renderer.toneMappingExposure=1.22;
 renderer.setClearColor(0x10283b,0);
 scene=new THREE.Scene();
 figure=new THREE.Group();figure.rotation.y=0;scene.add(figure);
 scene.add(new THREE.HemisphereLight(0xeaf6ff,0x435063,2.3));
 const key=new THREE.DirectionalLight(0xfff4e7,3.1);key.position.set(2.5,4.5,5.1);scene.add(key);
 const fill=new THREE.DirectionalLight(0xa0defc,1.25);fill.position.set(-3.5,2,-2);scene.add(fill);
 const ground=new THREE.Mesh(new THREE.CircleGeometry(.55,64),
   new THREE.MeshBasicMaterial({color:0x15384a,transparent:true,opacity:.45,depthWrite:false}));
 ground.rotation.x=-Math.PI/2;ground.position.y=-.018;scene.add(ground);
 camera=new THREE.OrthographicCamera(-.78,.78,1.12,-1.12,.01,40);
 camera.position.set(0,1.05,4.5);camera.lookAt(0,.9,0);
 window.addEventListener('resize',renderOnce);
 studioMarkers=createStudioMarkers({
  stage,figure,camera,getBounds:getBodyBounds,
  getProfile:()=>markerProfile,getBones:()=>studioBones,isActive:()=>active,
  getSurfaceAnchor:annyAnchor,onSelectRegion:selectAnnyGauge
 });
}
function registerMaterials(group,type,p){
 group.traverse(o=>{
  if(!o.isMesh)return;
  o.frustumCulled=false;
  if(!o.userData.studioPrepared){
   o.userData.studioPrepared=true;
   const mats=Array.isArray(o.material)?o.material:[o.material];
   o.userData.studioMats=mats.map(m=>m?m.clone():null);
   o.material=Array.isArray(o.material)?o.userData.studioMats:o.userData.studioMats[0];
  }
  const items=o.userData.studioMats||[];
  for(const mat of items){
   if(!mat)continue;
   const label=(o.name+' '+mat.name).toLowerCase();
   if(type==='hair'){
    if(mat.color)mat.color.set(p.hair);
    mat.side=THREE.DoubleSide;
    mat.needsUpdate=true;
   }else if(type==='clothing'){
    // Opaque garments must not vanish when a fold faces away from the camera.
    mat.side=THREE.DoubleSide;
    mat.transparent=false;
    mat.depthWrite=true;
    mat.needsUpdate=true;
   }else if(type==='body'){
    if(/iris/.test(label)){if(mat.color)mat.color.set(p.eyes);}
    else if(applyUniformBodySkin(mat,o.name,p.skin)){
      // The original baked skin albedo map is tinted unevenly across
      // the face, arms and legs. Remove only that diffuse map.
      // Lighting, roughness, normals and all other materials remain.
    }
   }
  }
 });
}
function findMorphInfluences(p){
 // Names are present in the CC0 exported GLBs and are never fabricated.
 // Weight is indicative only, not an anatomical/medical reconstruction.
 const bmi=p.weight/Math.pow(p.height/100,2),m={};
 m.gender_female=p.sex==='female'?1:0;
 m.gender_male=p.sex==='male'?1:0;
 m.age_child=p.child?clamp((18-p.age)/17,0,1):0;
 m.age_old=!p.child?clamp((p.age-58)/40,0,1):0;
 if(p.child){
  const change=Math.log(Math.max(.15,p.weight/Math.max(.1,p.initial)));
  m.weight_max=clamp(change*.13,0,.23);
  m.weight_min=clamp(-change*.13,0,.23);
 }else{
  const waistAdjust=p.waist&&p.hips?clamp((p.waist/p.hips-.82)*.15,-.05,.07):0;
  m.weight_max=clamp((bmi-24)/17+waistAdjust,0,1);
  m.weight_min=clamp((19-bmi)/8-waistAdjust,0,1);
 }
 m.muscle_min=0;m.muscle_max=0;
 m.height_short=clamp((165-p.height)/47,0,.6);
 m.height_tall=clamp((p.height-177)/58,0,.45);
 return m;
}
function applyMorph(group,influences){
 if(!group)return;
 group.traverse(o=>{
  if(!o.isMesh||!o.morphTargetDictionary||!o.morphTargetInfluences)return;
  const dict=o.morphTargetDictionary;
  for(const [name,idx] of Object.entries(dict)){
   const key=name.startsWith('corr_')?name.slice(5).split('__'):null;
   let value=key&&key.length===2? (influences[key[0]]||0)*(influences[key[1]]||0):
      (influences[name]||0);
   o.morphTargetInfluences[idx]=clamp(value,0,1);
  }
 });
}
function bonesOf(group){
 const map=new Map();
 group.traverse(o=>{if(o.isBone)map.set(o.name,o);});
 return map;
}
// All equipped SkinnedMeshes are bound to the body's SAME skeleton.
// No independent garment skeleton is animated or manually guessed.
function masterSkin(){
 let best=null;
 body?.traverse(o=>{
  if(o.isSkinnedMesh&&(!best||(o.geometry?.getAttribute('position')?.count||0)>
    (best.geometry?.getAttribute('position')?.count||0)))best=o;
 });
 return best;
}
// Body zones exported with the CC0 meshes; exclude triangles hidden beneath
// the worn opaque garment instead of relying on fragile skin-colored patches.
const baseSkinIndices=new WeakMap();
function concealCoveredSkin(files){
 if(!body)return;
 const mask=hideMaskFor(files);
 const {minY,height}=getBodyBounds();
 body.traverse(mesh=>{
  if(!mesh.isSkinnedMesh||!mesh.geometry)return;
  if(!baseSkinIndices.has(mesh)){
   mesh.geometry=mesh.geometry.clone();
   const index=mesh.geometry.getIndex();
   if(!index)return;
   baseSkinIndices.set(mesh,new index.array.constructor(index.array));
  }
  const initial=baseSkinIndices.get(mesh);
  if(!initial)return;
  if(!mask){
   mesh.geometry.setIndex(new THREE.BufferAttribute(new initial.constructor(initial),1));
   return;
  }
  const geo=mesh.geometry;
  const attr=geo.getAttribute('_cczone')||geo.getAttribute('_CCZONE');
  const pos=geo.getAttribute('position');
  if(!pos)return;
  const jointIds=geo.getAttribute('skinIndex');
  const jointWeights=geo.getAttribute('skinWeight');
  const jointNames=mesh.skeleton?.bones?.map(b=>b.name)||[];
  // Preserve GLB material draw-group offsets by retaining index length.
  const masked=maskIndexedTriangles(initial,(a,b,c)=>{
   if(touchesExposedArm([a,b,c],jointIds,jointWeights,jointNames))return false;
   if(touchesSleeveOpening([a,b,c],pos,minY,height,files))return false;
   const yn=((pos.getY(a)+pos.getY(b)+pos.getY(c))/3-minY)/height;
   const xn=(Math.abs(pos.getX(a))+Math.abs(pos.getX(b))+Math.abs(pos.getX(c)))/(3*height);
   // If rig labels are missing, keep upper outer limbs rather than cut elbows.
   if(yn>.47&&yn<.79&&xn>.17)return false;
   const hiddenByZone=attr&&coveredTriangle([attr.getX(a),attr.getX(b),attr.getX(c)],mask);
   const hiddenByFabric=behindOpaqueGarment(yn,xn,files);
   return !!(hiddenByZone||hiddenByFabric);
  });
  // Degenerate triangles hide covered skin without shifting material groups.
  geo.setIndex(new THREE.BufferAttribute(masked,1));
 });
}


function getBodyBounds(){
 if(studioBounds)return studioBounds;
 const skin=masterSkin();
 const pos=skin?.geometry?.getAttribute('position');
 if(!pos)throw Error('Maillage 3D principal non trouvé');
 let min=Infinity,max=-Infinity;
 for(let i=0;i<pos.count;i++){
  const y=pos.getY(i);
  if(Number.isFinite(y)){min=Math.min(min,y);max=Math.max(max,y);}
 }
 if(!Number.isFinite(min)||max-min<.1)throw Error('Dimensions 3D incompatibles');
 studioBounds={minY:min,height:max-min};
 return studioBounds;
}
function deformMesh(mesh,ratios,thighIntensity=0,estimated=false){
 if(!mesh.isSkinnedMesh||!mesh.geometry?.getAttribute('position'))return;
 if(!basePositions.has(mesh)){
  mesh.geometry=mesh.geometry.clone();
  const position=mesh.geometry.getAttribute('position');
  basePositions.set(mesh,new Float32Array(position.array));
 }
 const position=mesh.geometry.getAttribute('position');
 const base=basePositions.get(mesh);
 const {minY,height}=getBodyBounds();
 if(!position||position.array.length!==base.length)return;
 const data=position.array;
 const has=Object.keys(ratios).length>0;
 for(let i=0;i<base.length;i+=3){
  const value=has?deformPosition(base[i],base[i+1],base[i+2],minY,height,ratios,estimated):
   [base[i],base[i+1],base[i+2]];
  const shaped=thighIntensity>0?softenInnerThigh(...value,minY,height,thighIntensity):value;
  data[i]=shaped[0];data[i+1]=shaped[1];data[i+2]=shaped[2];
 }
 position.needsUpdate=true;
 mesh.geometry.computeBoundingSphere();
 mesh.geometry.computeBoundingBox();
 // Recompute normals from the ORIGINAL triangle topology. The visible
 // indices contain deliberately collapsed garment-covered triangles; using
 // those for normals creates black wedges and faceted shading around upper
 // arms, sleeve openings and armpits after a measurement update.
 const fullIndices=baseSkinIndices.get(mesh);
 const maskedIndex=mesh.geometry.getIndex();
 if(fullIndices&&maskedIndex&&fullIndices.length===maskedIndex.count){
  mesh.geometry.setIndex(new THREE.BufferAttribute(fullIndices,1));
  try{mesh.geometry.computeVertexNormals();}
  finally{mesh.geometry.setIndex(maskedIndex);}
 }else{
  mesh.geometry.computeVertexNormals();
 }
}
function refreshBodyMeasurements(p){
 if(!body)return;
 const display=displayedMeasurements(p);
 const measures=display.values;
 const weightEstimated=visualMode(p)==='estimated'&&!p.child;
 const ratios=visualRatios(measures,p.height,p.weight,p.child,weightEstimated);
 const intensity=weightEstimated&&display.estimatedKeys.includes('thigh')?
  estimatedThighIntensity(p.height,p.weight,p.child):0;
 const skin=masterSkin();studioBones=skin?.skeleton?.bones||[];
 markerProfile={...p,visualMeasurements:measures,estimatedKeys:display.estimatedKeys,measurementMode:visualMode(p)};
 body.traverse(m=>{if(m.isSkinnedMesh && m===skin)deformMesh(m,ratios,intensity,weightEstimated);});
 for(const [,group] of clothing)group.traverse(m=>{if(m.isSkinnedMesh)deformMesh(m,ratios,intensity,weightEstimated);});
}

function renderOnce(){
 if(!active||!renderer||!section.isConnected||section.hidden)return;
 const w=Math.max(5,canvas.clientWidth),h=Math.max(5,canvas.clientHeight);
 if(canvas.width!==Math.floor(w*renderer.getPixelRatio())||
    canvas.height!==Math.floor(h*renderer.getPixelRatio()))
     renderer.setSize(w,h,false);
 const ratio=w/h;cameraView=boundedView(cameraView.zoom,cameraView.x,cameraView.y,ratio);
 const colorMode=stage.classList.contains('bm-color-mode');
 // Shift the figure left at normal zoom so the color panel does not cover it.
 const half=1.2/cameraView.zoom*(colorMode&&cameraView.zoom<=1.001?1.15:1);
 const shift=colorMode&&cameraView.zoom<=1.001?half*ratio*.40:0;
 camera.left=cameraView.x+shift-half*ratio;camera.right=cameraView.x+shift+half*ratio;
 camera.top=cameraView.y+half;camera.bottom=cameraView.y-half;camera.updateProjectionMatrix();
 figure.rotation.y=yaw;
 renderer.render(scene,camera);
 studioMarkers?.update();
}
function frame(t){
 if(!active)return;
 try{
  if(mixer&&lastY){mixer.update(Math.min(.05,(t-lastY)/1000));}
  lastY=t;
  if(t-lastProfileCheck>800){lastProfileCheck=t;refreshScene(false);}
  renderOnce();
  if(active)raf=requestAnimationFrame(frame);
 }catch(err){
  stopPreview();
  if(isAnny(profileInfo())){fallback.hidden=false;fallback.style.display='';}
  note.textContent='Erreur 3D : le tableau est conservé ('+String(err.message||err)+').';
 }
}

function annyAnchor(region,turn){
 if(!annyMesh||!annyCurrent)return null;
 const ids=ANNY_ANCHORS[annyCurrent.sex]?.[region.key];if(!ids)return null;
 const index=ids[Math.cos(turn)<0?1:0];
 const v=new THREE.Vector3();annyMesh.getVertexPosition(index,v);
 return annyMesh.localToWorld(v);
}
function attachAnny(gltf,p){
 const key='anny-'+p.sex;
 if(bodyKind!==key){
  if(body)figure.remove(body);
  if(mixer)mixer.stopAllAction();mixer=null;
  body=gltf.scene;figure.add(body);bodyKind=key;
  for(const g of [...clothing.values(),...hairObjects.values()])g.visible=false;
  body.position.set(0,0,0);body.scale.setScalar(1);body.updateMatrixWorld(true);
  let position=null;body.traverse(m=>{if(!position&&m.isMesh)position=m.geometry.attributes.position;});
  if(!position)throw Error('Géométrie Anny absente');
  const bounds=new THREE.Box3().setFromBufferAttribute(position);
  const size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());
  if(!(size.y>.1))throw Error('Dimensions Anny incompatibles');
  const scale=1.75/size.y;
  body.scale.setScalar(scale);body.position.set(-center.x*scale,-bounds.min.y*scale,-center.z*scale);
  annyMesh=null;
  body.traverse(m=>{if(m.isMesh){
   if(m.geometry.attributes.position.count!==13718||m.morphTargetInfluences?.length!==20)throw Error('Topologie Anny incompatible');
   if(!annyMesh)annyMesh=m;
   m.frustumCulled=false;
  }});
  if(!annyMesh)throw Error('Maillage Anny absent');
 }
 studioBounds={minY:0,height:1.75};studioBones=[];
}
function configureAnny(p){
 const snap=annyVisual(p);if(!snap||!body)return;
 annyCurrent=snap;profileId=p.id;syncVisualMode(p);
 const weights=annyWeights(snap);
 const palette={skin:snap.skin,hair:snap.hair,iris:snap.eyes};
 body.traverse(m=>{
  if(!m.isMesh)return;
  for(let i=0;i<weights.length;i++)m.morphTargetInfluences[i]=weights[i];
  for(const mat of (Array.isArray(m.material)?m.material:[m.material])){
   const color=palette[String(mat?.name||'').toLowerCase()];if(color&&mat.color)mat.color.set(color);
  }
 });
 const display=displayedMeasurements(p);
 markerProfile={...p,visualMeasurements:display.values,estimatedKeys:display.estimatedKeys,measurementMode:visualMode(p),anny:true};
 camera.position.set(0,1.05,4.5);camera.lookAt(0,.875,0);
 updateGauges(p,snap);body.updateMatrixWorld(true);
}

function configure(){
 const p=profileInfo();if(!p||!body)return;
 if(isAnny(p)){configureAnny(p);return;}
 syncOutfitControl(p);
 syncVisualMode(p);
 const opts=choices(p);
 if(profileId!==p.id){profileId=p.id;hairSel.value=opts.hair;faceSel.value=opts.face;clothSel.value=opts.clothes;}
 if(!allowedOutfits(p).includes(clothSel.value))clothSel.value=opts.clothes;
 const inf={...findMorphInfluences(p),...faceMorphsFor(p.kind,faceSel.value)};
 applyMorph(body,inf);
 registerMaterials(body,'body',p);
 for(const group of clothing.values())applyMorph(group,inf);
 for(const group of hairObjects.values()){applyMorph(group,inf);registerMaterials(group,'hair',p);}
 // Skin and clothing remain separate materials. The same pose controls both.
 const relevant=CLOTHES[clothSel.value]?.files||CLOTHES.classic.files;
 concealCoveredSkin(relevant);
 refreshBodyMeasurements(p);
 for(const [name,group] of clothing)group.visible=relevant.includes(name);
 for(const [name,group] of hairObjects)group.visible=name==='hair_'+hairSel.value+'.glb';
 const bb=new THREE.Box3().setFromObject(body);
 const size=bb.getSize(new THREE.Vector3());
 // The age morph changes body height; camera tracks the current figure.
 if(Number.isFinite(size.y)&&size.y>.15){
  const target=(bb.min.y+bb.max.y)*.5;
  camera.position.y=target+Math.max(1.0,size.y*.2);
  camera.lookAt(0,target,0);
 }
}
async function addAsset(name,mode,p){
 const g=await asset(name);
 const parent=figure;
 const main=masterSkin();
 if(!main?.skeleton||!main.bindMatrix)throw Error('Rig MakeHuman indisponible');
 const meshes=[];
 // Reuse the GLB body rig for clothes and hair, exactly as for their morphs.
 // This prevents animations shifting garments away from the moving body.
 g.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});
 if(!meshes.length)throw Error('Vêtement incompatible : '+name);
 const masterByName=new Map(main.skeleton.bones.map((bone,i)=>[bone.name,i]));
 for(const mesh of meshes){
  if(!mesh.skeleton)throw Error('Ossature absente : '+name);
  const translation=mesh.skeleton.bones.map(b=>masterByName.get(b.name));
  if(translation.some(i=>i===undefined))throw Error('Ossature incompatible : '+name);
  if(translation.some((n,i)=>n!==i)){
   // Each garment uses the body rig, but the GLB exporter may reorder bones.
   // Remap all four joint indices per vertex before sharing that skeleton.
   mesh.geometry=mesh.geometry.clone();
   const attribute=mesh.geometry.getAttribute('skinIndex');
   if(!attribute)throw Error('Indices d’ossature manquants : '+name);
   const raw=attribute.array;
   for(let i=0;i<raw.length;i++)raw[i]=translation[raw[i]];
   attribute.needsUpdate=true;
  }
 }
 const group=new THREE.Group();
 parent.add(group);
 for(const mesh of meshes){
  mesh.removeFromParent();
  mesh.position.copy(main.position);
  mesh.quaternion.copy(main.quaternion);
  mesh.scale.copy(main.scale);
  mesh.bind(main.skeleton,main.bindMatrix);
  mesh.frustumCulled=false;
  group.add(mesh);
 }
 registerMaterials(group,mode,p);
 group.visible=false;
 if(mode==='hair')hairObjects.set(name,group);
 else clothing.set(name,group);
 return group;
}
async function ensureAccessories(p){
 const wants=CLOTHES[clothSel.value]?.files||CLOTHES.classic.files;
 const targetHair='hair_'+hairSel.value+'.glb';
 const missing=[...wants,targetHair].filter(name=>!clothing.has(name)&&!hairObjects.has(name));
 // Render the body as soon as it has loaded, but never publish an
 // unfinished undressed 3D figure: we activate only after all garments load.
 for(const name of missing)await addAsset(name,name.startsWith('hair_')?'hair':'clothing',p);
}
async function startPreview(){
 if(busy||active)return;
 busy=true;btn.disabled=true;
 note.textContent='Préparation du modèle, des textures et des vêtements…';
 try{
  const p=profileInfo();
  if(!p)throw Error('Complète le sexe, la naissance, la taille et le poids du profil. Seul le tableau est affiché.');
  init();
  const adult=isAnny(p);
  const model=adult?annyFile(p.sex):'base_body_anim.glb';
  if(!model)throw Error('Profil sans modèle 3D autorisé');
  const gltf=await asset(model);
  const now=profileInfo();if(!now||now.id!==p.id||now.sex!==p.sex||now.child!==p.child)throw Error('Profil changé pendant le chargement');
  if(adult){attachAnny(gltf,p);}else{
  if(bodyKind!=='studio'){
   if(body)figure.remove(body);if(mixer)mixer.stopAllAction();
   body=null;annyMesh=null;annyCurrent=null;studioBounds=null;bodyKind='studio';
  }
  if(!body){
   body=gltf.scene;figure.add(body);
   mixer=new THREE.AnimationMixer(body);
   const idle=gltf.animations.find(a=>/idle/i.test(a.name))||gltf.animations[0];
   if(idle)mixer.clipAction(idle).setLoop(THREE.LoopRepeat).play();
  }
  syncOutfitControl(p);
  const opts=choices(p);hairSel.value=opts.hair;faceSel.value=opts.face;clothSel.value=opts.clothes;
  profileId=p.id;
  autoTriedProfiles.add(String(p.id));
  await ensureAccessories(p);
  }
  configure();
  stage.classList.add('bm-makehuman-active');
  active=true;cameraView=initialView();syncZoom();profileId=p.id;autoTriedProfiles.add(String(p.id));currentKey='';btn.textContent='Masquer le mannequin 3D';
  stage.classList.toggle('bm-anny-active',adult);setAnnyLayout(adult);fallback.hidden=true;fallback.style.display='none';
  rememberVisibility(p.id,true);
  note.textContent=(adult?'Anny intégré hors ligne':'3D Studio')+' • rendu indicatif • pivoter avec le doigt';
  refreshScene(true);
  raf=requestAnimationFrame(frame);
 }catch(e){
  console.error('MakeHuman Studio:',e);
  active=false;zoomTools.hidden=true;pointers.clear();touchGesture=null;stage.classList.remove('bm-makehuman-active','bm-anny-active');gauges.hidden=true;
  if(isAnny(profileInfo())){fallback.hidden=false;fallback.style.display='';}
  btn.textContent='Réessayer le modèle 3D';
  note.textContent='Visualisation indisponible : '+String(e.message||e);
 }finally{busy=false;btn.disabled=false;}
}
function stopPreview(manual=false){
 if(manual){
  const current=profileInfo();
  if(current)rememberVisibility(current.id,false);
 }
 active=false;zoomTools.hidden=true;pointers.clear();touchGesture=null;if(raf)cancelAnimationFrame(raf);raf=0;lastY=0;
 studioMarkers?.update();
 stage.classList.remove('bm-makehuman-active','bm-anny-active');gauges.hidden=true;
 btn.textContent='Afficher le mannequin 3D';
 note.textContent='Masqué. Le module reste installé pour les prochaines ouvertures.';
}
function refreshScene(force){
 if(!active)return;
 const p=profileInfo();
 if(!p){stopPreview();note.textContent='Profil incomplet ou sexe non précisé : tableau uniquement.';return;}
 if(profileId!==p.id && !visibilityEnabled(p.id)){
  autoTriedProfiles.delete(String(profileId));
  stopPreview();
  note.textContent='Mannequin désactivé pour ce profil. Active-le pour le conserver aux prochains démarrages.';
  return;
 }
 const desired=isAnny(p)?'anny-'+p.sex:'studio';
 if(desired!==bodyKind){stopPreview(false);autoTriedProfiles.delete(String(p.id));if(visibilityEnabled(p.id))startPreview();return;}
 const k=[p.id,p.sex,p.age.toFixed(2),p.height,p.weight,p.initial,
  JSON.stringify(p.measurements),p.measurementDate,visualMode(p),p.skin,p.hair,p.eyes,p.lastDate,
  hairSel.value,faceSel.value,clothSel.value].join('|');
 if(force||k!==currentKey){
  currentKey=k;
  configure();
  if(isAnny(p))return;
  const wantHair='hair_'+hairSel.value+'.glb';
  const clothes=CLOTHES[clothSel.value]?.files||[];
  if([...clothes,wantHair].some(n=>!(clothing.has(n)||hairObjects.has(n)))){
   ensureAccessories(p).then(()=>{if(active){configure();renderOnce();}}).catch(e=>{
    note.textContent='Tenue indisponible : '+String(e.message||e);});
  }
 }
}
function updateStatus(){
 if(busy)return;
 const adult=profileInfo();
 if(isAnny(adult)){
  if(active&&bodyKind!=='anny-'+adult.sex){stopPreview(false);autoTriedProfiles.delete(String(adult.id));}
  const changed=oldStatus!=='anny';oldStatus='anny';btn.disabled=false;
  btn.textContent=active?'Masquer le mannequin 3D':'Afficher le mannequin 3D';
  setAnnyLayout(true);
  if(changed)note.textContent='Anny intégré à l’application · sans téléchargement supplémentaire';
  syncVisualMode(adult);
  if(!active&&!section.hidden&&visibilityEnabled(adult.id)&&!autoTriedProfiles.has(String(adult.id))){
   autoTriedProfiles.add(String(adult.id));startPreview();
  }
  return;
 }
 if(oldStatus==='anny'){
  if(active&&bodyKind.startsWith('anny-'))stopPreview(false);
  oldStatus='';setAnnyLayout(false);fallback.hidden=true;fallback.style.display='none';
 }
 const status=bridge.makeHumanStudioState();
 const changed=status!==oldStatus;
 oldStatus=status;
 if(status==='ready'){
  btn.disabled=false;
  btn.textContent=active?'Masquer le mannequin 3D':'Afficher le mannequin 3D';
  if(changed&&!active)note.textContent='Module Studio installé • activation mémorisée par profil';
  if(autoShowAfterInstall){
   autoShowAfterInstall=false;
   startPreview();
   return;
  }
  const current=profileInfo();
  if(!active&&!section.hidden&&current&&visibilityEnabled(current.id)&&
     !autoTriedProfiles.has(String(current.id))){
   autoTriedProfiles.add(String(current.id));
   startPreview();
  }
 }else if(status==='downloading'){
  btn.disabled=true;note.textContent='Installation du Studio 3D complet en cours…';
 }else if(changed){
  btn.disabled=false;btn.textContent='Installer le modèle 3D Studio';
  note.textContent=status.startsWith('error')?'Erreur de téléchargement. Réessaie.':
   'Module optionnel distinct de l’APK • installation unique';
 }
}
btn.addEventListener('click',()=>{
 const p=profileInfo();
 if(isAnny(p)){if(active)stopPreview(true);else startPreview();return;}
 const status=bridge.makeHumanStudioState();
 if(active){stopPreview(true);return;}
 if(status==='ready'){startPreview();return;}
 if(status==='downloading')return;
 autoShowAfterInstall=true;btn.disabled=true;
 note.textContent='Téléchargement sécurisé des modèles 3D Studio…';
 bridge.makeHumanStudioInstall();
});
hairSel.addEventListener('change',saveChoice);
faceSel.addEventListener('change',saveChoice);
clothSel.addEventListener('change',saveChoice);
canvas.addEventListener('webglcontextlost',e=>{
 e.preventDefault();
 stopPreview();
 if(isAnny(profileInfo())){fallback.hidden=false;fallback.style.display='';}
 note.textContent='Rendu graphique interrompu. Le tableau des mensurations reste accessible.';
});
function syncZoom(){
 zoomTools.hidden=!active||!needsRecenter(cameraView);
}
function stepZoom(factor){
 if(!active)return;
 cameraView=boundedView(cameraView.zoom*factor,cameraView.x,cameraView.y,canvas.clientWidth/Math.max(1,canvas.clientHeight));
 syncZoom();renderOnce();
}
zoomReset.onclick=()=>{cameraView=initialView();syncZoom();renderOnce();};
function localPoint(e){const r=canvas.getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top};}
// Native vertical scrolling remains enabled (pan-y). Touch events consume only
// horizontal rotation and two-finger gestures; pointer events handle mouse/pen.
const touchPoints=e=>Array.from(e.targetTouches).slice(0,2).map(t=>({...localPoint(t),id:t.identifier}));
canvas.addEventListener('touchstart',e=>{
 if(!active)return;
 const pts=touchPoints(e);
 if(pts.length===2){
  if(e.cancelable)e.preventDefault();
  touchGesture={mode:'pinch',points:pts};
 }else if(pts.length===1&&!touchGesture){
  touchGesture={mode:'pending',start:pts[0],points:pts};
 }
},{passive:false});
canvas.addEventListener('touchmove',e=>{
 if(!active||!touchGesture)return;
 const pts=touchPoints(e),g=touchGesture;
 if(pts.length===2){
  if(!e.cancelable){touchGesture=null;return;}
  e.preventDefault();
  if(g.mode==='pinch'&&g.points.length===2){
   const ordered=g.points.map(p=>pts.find(n=>n.id===p.id));
   if(ordered.every(Boolean)){
    cameraView=pinchView(cameraView,g.points,ordered,canvas.clientWidth,canvas.clientHeight);
    syncZoom();renderOnce();
   }
  }
  touchGesture={mode:'pinch',points:pts};return;
 }
 if(pts.length!==1||g.mode==='pinch'||g.mode==='scroll'||g.mode==='after-pinch')return;
 const p=pts[0];
 if(g.mode==='pending'){
  g.mode=gestureDirection(p.x-g.start.x,p.y-g.start.y);
  if(g.mode==='pending')return;
 }
 if(g.mode==='rotate'&&e.cancelable){
  e.preventDefault();
  yaw+=(p.x-g.points[0].x)*.008;renderOnce();
 }
 g.points=pts;
},{passive:false});
canvas.addEventListener('touchend',e=>{
 const pts=touchPoints(e);
 touchGesture=pts.length?{mode:'after-pinch',points:pts}:null;
},{passive:true});
canvas.addEventListener('touchcancel',()=>{touchGesture=null;},{passive:true});
canvas.addEventListener('pointerdown',e=>{
 if(!active||e.pointerType==='touch'||e.button!==0)return;
 pointers.set(e.pointerId,{start:localPoint(e),last:localPoint(e),mode:'pending'});
 canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove',e=>{
 if(!active||!pointers.has(e.pointerId))return;
 const p=localPoint(e),g=pointers.get(e.pointerId);
 if(g.mode==='pending')g.mode=gestureDirection(p.x-g.start.x,p.y-g.start.y);
 if(g.mode==='rotate'){yaw+=(p.x-g.last.x)*.008;renderOnce();}
 if(g.mode!=='pending')g.last=p;
});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>pointers.delete(e.pointerId));
canvas.addEventListener('wheel',e=>{if(!active||!e.ctrlKey)return;e.preventDefault();stepZoom(Math.exp(-e.deltaY*.002));},{passive:false});
window.addEventListener('mon-evolution-appearance-changed',()=>refreshScene(true));
window.addEventListener('mon-evolution-color-mode-changed',()=>{studioMarkers?.close();renderOnce();});
window.addEventListener('mon-evolution-measurements-changed',event=>{
 const detail=event?.detail||{};
 const p=profileInfo();
 if(p&&String(p.id)===String(detail.profileId))visualDrafts.delete(String(p.id));
 if(p&&String(p.id)===String(detail.profileId)&&visualMode(p)==='estimated'&&
    Array.isArray(detail.changedKeys)&&detail.changedKeys.length)
  recordVisualOverrides(p.id,detail.date,detail.changedKeys,visibilityStore());
 refreshScene(true);
});
window.annyFocusMeasurement=(id,key)=>{
 const p=profileInfo();if(!p||String(p.id)!==id||!['neck','chest','arm','forearm','waist','belly','hips','thigh','calf'].includes(key))return;
 const input=document.getElementById('bm-'+key);if(input&&!input.disabled){input.scrollIntoView({block:'center'});input.focus();}
};
window.addEventListener('mon-evolution-studio-ready',updateStatus);
setInterval(()=>{if(section.hidden)return;updateStatus();},1400);
updateStatus();
// Reopen only when the selected profile explicitly enabled this model before.
})();