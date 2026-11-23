/* MakeHuman Studio v2 for Mon Évolution IMC.
 * Original implementation with Three.js (MIT); source GLBs are CC0 assets.
 * Large rigged character + actual textures, separate hair and clothing meshes.
 * The old v1 procedural painter is deliberately not loaded.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { profileCategory, allowedOutfitsFor } from './profile-rules.mjs';
import { latestMeasurements, visualRatios, deformPosition } from './measurement-morph.mjs';
import { createStudioMarkers } from './measurement-markers.mjs';
import { estimatedThighIntensity,softenInnerThigh } from './thigh-fill.mjs';
import { readVisualOverrides,recordVisualOverrides,resolveVisualMeasurements } from './visual-overrides.mjs';
import { isStudioEnabled, setStudioEnabled } from './visibility-preference.mjs';
import { hideMaskFor, coveredTriangle, behindOpaqueGarment } from './clothing-coverage.mjs';
import { maskIndexedTriangles, touchesExposedArm } from './skin-triangle-mask.mjs';
import { estimateVisualMeasurements, readVisualMode, writeVisualMode } from './visual-defaults.mjs';

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
 classic:{label:'T-shirt et jean',files:['clothing_tshirt.glb','clothing_jeans.glb','clothing_shoes.glb']},
 shirt:{label:'Chemise et jean',files:['clothing_shirt.glb','clothing_jeans.glb','clothing_shoes.glb']},
 casual:{label:'Sweat et jean',files:['clothing_hoodie.glb','clothing_jeans.glb','clothing_shoes.glb']},
 summer:{label:'T-shirt et short',files:['clothing_tshirt.glb','clothing_shorts.glb','clothing_shoes.glb']},
 skirt:{label:'T-shirt et jupe',files:['clothing_tshirt.glb','clothing_skirt.glb','clothing_shoes.glb']}
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
const clothSel=selectOption('Tenue',Object.entries(CLOTHES).map(([id,o])=>[id,o.label]));
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
const canvas=document.createElement('canvas');canvas.className='bm-makehuman-canvas';
canvas.setAttribute('aria-label','Mannequin 3D MakeHuman habillé');canvas.setAttribute('role','img');
stage.append(canvas);
const parser=new GLTFLoader();
let renderer=null,scene=null,camera=null,mixer=null,figure=null,body=null,lighting=null;
let active=false,busy=false,disposed=false,autoShowAfterInstall=false,currentKey='',oldStatus='',firstRun=true;
let lastY=0,yaw=0,pointer=null,raf=0,profileId='',lastProfileCheck=0;
let studioBounds=null,studioMarkers=null,markerProfile=null,studioBones=[];
const basePositions=new WeakMap();
const loaded=new Map(),pending=new Map(),clothing=new Map(),hairObjects=new Map();
const autoTriedProfiles=new Set();
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
    'Estimation esthétique d’après le poids. Une mesure enregistrée remplace son estimation pour la silhouette.'):
  'Silhouette fondée sur les tours réellement enregistrés dans ton historique.';
}
function setVisualMode(mode){
 const p=profileInfo();if(!p)return;
 if(!writeVisualMode(p.id,mode,visibilityStore())){
  note.textContent='Préférence indisponible : stockage local inaccessible.';return;
 }
 syncVisualMode(p);
 currentKey='';refreshScene(true);
}
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function ensureMounted(){
 if(!stage.contains(canvas))stage.append(canvas);
 if(!panel.isConnected)stage.before(panel);
 if(!controls.isConnected)panel.after(controls);
 if(!shapeControls.isConnected)controls.after(shapeControls);
}
new MutationObserver(ensureMounted).observe(stage,{childList:true});
function profileInfo(){
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
  JSON.stringify({hair:hairSel.value,clothes:clothSel.value}));}catch{}
 refreshScene(true);
}
async function readGlb(name){
 if(!/^(?:base_body_anim|hair_(?:short02|short04|bob02|long01|ponytail01|braid01|afro01)|clothing_(?:tshirt|shirt|hoodie|jeans|shorts|skirt|shoes))\.glb$/.test(name)){
  throw Error('Fichier 3D non autorisé');
 }
 const size=bridge.makeHumanStudioBytes(name);
 if(!(size>10000&&size<14000000))throw Error('Ressource absente : '+name);
 const bytes=new Uint8Array(size);
 for(let start=0;start<size;start+=49152){
  const part=bridge.makeHumanStudioReadChunk(name,start);
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
  getProfile:()=>markerProfile,getBones:()=>studioBones,isActive:()=>active
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
    else if(/skin|body|character|surface/.test(label)){
      if(mat.color)mat.color.set(p.skin);
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
function deformMesh(mesh,ratios,thighIntensity=0){
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
  const value=has?deformPosition(base[i],base[i+1],base[i+2],minY,height,ratios):
   [base[i],base[i+1],base[i+2]];
  const shaped=thighIntensity>0?softenInnerThigh(...value,minY,height,thighIntensity):value;
  data[i]=shaped[0];data[i+1]=shaped[1];data[i+2]=shaped[2];
 }
 position.needsUpdate=true;
 mesh.geometry.computeBoundingSphere();
 mesh.geometry.computeBoundingBox();
 // Relight surfaces after a local circumference change.
 mesh.geometry.computeVertexNormals();
}
function refreshBodyMeasurements(p){
 if(!body)return;
 const display=displayedMeasurements(p);
 const measures=display.values;
 const ratios=visualRatios(measures,p.height,p.weight,p.child);
 const intensity=visualMode(p)==='estimated'&&display.estimatedKeys.includes('thigh')?
  estimatedThighIntensity(p.height,p.weight,p.child):0;
 const skin=masterSkin();studioBones=skin?.skeleton?.bones||[];
 markerProfile={...p,visualMeasurements:measures,estimatedKeys:display.estimatedKeys,measurementMode:visualMode(p)};
 body.traverse(m=>{if(m.isSkinnedMesh && m===skin)deformMesh(m,ratios,intensity);});
 for(const [,group] of clothing)group.traverse(m=>{if(m.isSkinnedMesh)deformMesh(m,ratios,intensity);});
}

function renderOnce(){
 if(!active||!renderer||!section.isConnected||section.hidden)return;
 const w=Math.max(5,canvas.clientWidth),h=Math.max(5,canvas.clientHeight);
 if(canvas.width!==Math.floor(w*renderer.getPixelRatio())||
    canvas.height!==Math.floor(h*renderer.getPixelRatio()))
     renderer.setSize(w,h,false);
 const ratio=w/h,half=1.2;
 camera.left=-half*ratio;camera.right=half*ratio;
 camera.top=half;camera.bottom=-half;camera.updateProjectionMatrix();
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
  note.textContent='Erreur 3D : le tableau est conservé ('+String(err.message||err)+').';
 }
}
function configure(){
 const p=profileInfo();if(!p||!body)return;
 syncOutfitControl(p);
 syncVisualMode(p);
 const opts=choices(p);
 if(profileId!==p.id){profileId=p.id;hairSel.value=opts.hair;clothSel.value=opts.clothes;}
 if(!allowedOutfits(p).includes(clothSel.value))clothSel.value=opts.clothes;
 const inf=findMorphInfluences(p);
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
  const gltf=await asset('base_body_anim.glb');
  if(!body){
   body=gltf.scene;figure.add(body);
   mixer=new THREE.AnimationMixer(body);
   const idle=gltf.animations.find(a=>/idle/i.test(a.name))||gltf.animations[0];
   if(idle)mixer.clipAction(idle).setLoop(THREE.LoopRepeat).play();
  }
  syncOutfitControl(p);
  const opts=choices(p);hairSel.value=opts.hair;clothSel.value=opts.clothes;
  profileId=p.id;
  autoTriedProfiles.add(String(p.id));
  await ensureAccessories(p);
  configure();
  stage.classList.add('bm-makehuman-active');
  active=true;currentKey='';btn.textContent='Masquer le mannequin 3D';
  rememberVisibility(p.id,true);
  note.textContent='3D Studio • rendu indicatif, sans valeur médicale • pivoter avec le doigt';
  refreshScene(true);
  raf=requestAnimationFrame(frame);
 }catch(e){
  console.error('MakeHuman Studio:',e);
  active=false;stage.classList.remove('bm-makehuman-active');
  btn.textContent='Réessayer le modèle 3D';
  note.textContent='Visualisation indisponible : '+String(e.message||e);
 }finally{busy=false;btn.disabled=false;}
}
function stopPreview(manual=false){
 if(manual){
  const current=profileInfo();
  if(current)rememberVisibility(current.id,false);
 }
 active=false;if(raf)cancelAnimationFrame(raf);raf=0;lastY=0;
 studioMarkers?.update();
 stage.classList.remove('bm-makehuman-active');
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
 const k=[p.id,p.sex,p.age.toFixed(2),p.height,p.weight,p.initial,
  JSON.stringify(p.measurements),p.measurementDate,visualMode(p),p.skin,p.hair,p.eyes,p.lastDate,
  hairSel.value,clothSel.value].join('|');
 if(force||k!==currentKey){
  currentKey=k;
  configure();
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
 const status=bridge.makeHumanStudioState();
 if(active){stopPreview(true);return;}
 if(status==='ready'){startPreview();return;}
 if(status==='downloading')return;
 autoShowAfterInstall=true;btn.disabled=true;
 note.textContent='Téléchargement sécurisé des modèles 3D Studio…';
 bridge.makeHumanStudioInstall();
});
hairSel.addEventListener('change',saveChoice);
clothSel.addEventListener('change',saveChoice);
canvas.addEventListener('webglcontextlost',e=>{
 e.preventDefault();
 stopPreview();
 note.textContent='Rendu graphique interrompu. Le tableau des mensurations reste accessible.';
});
canvas.addEventListener('pointerdown',e=>{
 if(!active)return;
 pointer={x:e.clientX,angle:yaw};canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove',e=>{
 if(pointer){yaw=pointer.angle+(e.clientX-pointer.x)*.008;renderOnce();}
});
canvas.addEventListener('pointerup',()=>{pointer=null;});
canvas.addEventListener('pointercancel',()=>{pointer=null;});
window.addEventListener('mon-evolution-appearance-changed',()=>refreshScene(true));
window.addEventListener('mon-evolution-measurements-changed',event=>{
 const detail=event?.detail||{};
 const p=profileInfo();
 if(p&&String(p.id)===String(detail.profileId)&&visualMode(p)==='estimated'&&
    Array.isArray(detail.changedKeys)&&detail.changedKeys.length)
  recordVisualOverrides(p.id,detail.date,detail.changedKeys,visibilityStore());
 refreshScene(true);
});
window.addEventListener('mon-evolution-studio-ready',updateStatus);
setInterval(()=>{if(section.hidden)return;updateStatus();},1400);
updateStatus();
// Reopen only when the selected profile explicitly enabled this model before.
})();