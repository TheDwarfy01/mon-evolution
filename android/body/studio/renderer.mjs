/* MakeHuman Studio v2 for Mon Évolution IMC.
 * Original implementation with Three.js (MIT); source GLBs are CC0 assets.
 * Large rigged character + actual textures, separate hair and clothing meshes.
 * The old v1 procedural painter is deliberately not loaded.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

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
 '#body-measurements #bm-main.bm-table-only .bm-studio-controls{display:none!important;}'
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
const canvas=document.createElement('canvas');canvas.className='bm-makehuman-canvas';
canvas.setAttribute('aria-label','Mannequin 3D MakeHuman habillé');canvas.setAttribute('role','img');
stage.append(canvas);
const parser=new GLTFLoader();
let renderer=null,scene=null,camera=null,mixer=null,figure=null,body=null,lighting=null;
let active=false,busy=false,disposed=false,autoShowAfterInstall=false,currentKey='',oldStatus='',firstRun=true;
let lastY=0,yaw=0,pointer=null,raf=0,profileId='',lastProfileCheck=0;
const loaded=new Map(),pending=new Map(),clothing=new Map(),hairObjects=new Map();
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function ensureMounted(){
 if(!stage.contains(canvas))stage.append(canvas);
 if(!panel.isConnected)stage.before(panel);
 if(!controls.isConnected)panel.after(controls);
}
new MutationObserver(ensureMounted).observe(stage,{childList:true});
function profileInfo(){
 const p=typeof profile==='function'?profile():null;
 if(!p)return null;
 const weights=(p.entries||[]).filter(e=>Number.isFinite(+e.weight)&&+e.weight>0)
  .slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
 if(!weights.length||!(+p.height>40))return null;
 const weight=+weights.at(-1).weight,initial=+weights[0].weight;
 let age=35;
 if(typeof p.birthDate==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(p.birthDate)){
  const diff=Date.now()-new Date(p.birthDate+'T12:00:00').getTime();
  if(Number.isFinite(diff))age=clamp(diff/31556952000,0,105);
 }
 const child=age<18,app=p.bodyAppearance||{};
 const records=(p.bodyMeasurements||[]).filter(r=>r&&r.date).slice()
  .sort((a,b)=>a.date.localeCompare(b.date));
 const last=records.at(-1)||{};
 return {id:p.id||'',sex:app.model==='female'?'female':app.model==='male'?'male':
   p.sex==='female'?'female':'male',age,child,height:+p.height,weight,initial,
   skin:app.skin||'#D99E78',hair:app.hair||'#4A2D22',eyes:app.eyes||'#593826',
   waist:+last.waist||null,hips:+last.hips||null,
   lastDate:weights.at(-1).date};
}
function choices(p){
 let options={};
 try{options=JSON.parse(localStorage.getItem('mh-studio-v2-'+p.id)||'{}')||{}}catch{}
 return {hair:HAIRS[options.hair]?options.hair:(p.sex==='female'?'bob02':'short02'),
  clothes:CLOTHES[options.clothes]?options.clothes:'classic'};
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
function synchronizeBones(){
 if(!body)return;
 const baseline=bonesOf(body);
 for(const group of [...clothing.values(),...hairObjects.values()]){
  if(!group.visible)continue;
  group.traverse(o=>{
   if(!o.isBone)return;
   const master=baseline.get(o.name);
   if(master){
    o.quaternion.copy(master.quaternion);
    o.scale.copy(master.scale);
   }
  });
 }
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
}
function frame(t){
 if(!active)return;
 if(mixer&&lastY){mixer.update(Math.min(.05,(t-lastY)/1000));synchronizeBones();}
 lastY=t;
 if(t-lastProfileCheck>800){lastProfileCheck=t;refreshScene(false);}
 renderOnce();
 raf=requestAnimationFrame(frame);
}
function configure(){
 const p=profileInfo();if(!p||!body)return;
 const opts=choices(p);
 if(profileId!==p.id){profileId=p.id;hairSel.value=opts.hair;clothSel.value=opts.clothes;}
 const inf=findMorphInfluences(p);
 applyMorph(body,inf);
 registerMaterials(body,'body',p);
 for(const group of clothing.values())applyMorph(group,inf);
 for(const group of hairObjects.values()){applyMorph(group,inf);registerMaterials(group,'hair',p);}
 // Skin and clothing remain separate materials. The same pose controls both.
 const relevant=CLOTHES[clothSel.value]?.files||CLOTHES.classic.files;
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
 const cloned=cloneSkinned(g.scene);
 // Keep a separate copy of the independently authored rig for each clothing.
 figure.add(cloned);
 registerMaterials(cloned,mode,p);
 if(mode==='hair')hairObjects.set(name,cloned);
 else clothing.set(name,cloned);
 return cloned;
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
  if(!p)throw Error('Renseigne taille et poids dans le profil.');
  init();
  const gltf=await asset('base_body_anim.glb');
  if(!body){
   body=gltf.scene;figure.add(body);
   mixer=new THREE.AnimationMixer(body);
   const idle=gltf.animations.find(a=>/idle/i.test(a.name))||gltf.animations[0];
   if(idle)mixer.clipAction(idle).setLoop(THREE.LoopRepeat).play();
  }
  const opts=choices(p);hairSel.value=opts.hair;clothSel.value=opts.clothes;
  profileId=p.id;
  await ensureAccessories(p);
  configure();
  stage.classList.add('bm-makehuman-active');
  active=true;currentKey='';btn.textContent='Masquer le mannequin 3D';
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
function stopPreview(){
 active=false;if(raf)cancelAnimationFrame(raf);raf=0;lastY=0;
 stage.classList.remove('bm-makehuman-active');
 btn.textContent='Afficher le mannequin 3D';
 note.textContent='Masqué. Le module reste installé pour les prochaines ouvertures.';
}
function refreshScene(force){
 if(!active)return;
 const p=profileInfo();if(!p)return;
 const k=[p.id,p.sex,p.age.toFixed(2),p.height,p.weight,p.initial,
  p.waist,p.hips,p.skin,p.hair,p.eyes,p.lastDate,
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
 const s=bridge.makeHumanStudioState();
 if(s===oldStatus&&!autoShowAfterInstall)return;
 oldStatus=s;
 if(s==='ready'){
  btn.disabled=false;btn.textContent=active?'Masquer le mannequin 3D':'Afficher le mannequin 3D';
  if(!active)note.textContent='Module Studio installé • coiffures, vêtements, texture et animation';
  if(autoShowAfterInstall){autoShowAfterInstall=false;startPreview();}
 }else if(s==='downloading'){
  btn.disabled=true;note.textContent='Installation du Studio 3D complet en cours…';
 }else{
  btn.disabled=false;btn.textContent='Installer le modèle 3D Studio';
  note.textContent=s.startsWith('error')?'Erreur de téléchargement. Réessaie.':
   'Module optionnel distinct de l’APK • installation unique';
 }
}
btn.addEventListener('click',()=>{
 const status=bridge.makeHumanStudioState();
 if(active){stopPreview();return;}
 if(status==='ready'){startPreview();return;}
 if(status==='downloading')return;
 autoShowAfterInstall=true;btn.disabled=true;
 note.textContent='Téléchargement sécurisé des modèles 3D Studio…';
 bridge.makeHumanStudioInstall();
});
hairSel.addEventListener('change',saveChoice);
clothSel.addEventListener('change',saveChoice);
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
window.addEventListener('mon-evolution-studio-ready',updateStatus);
setInterval(()=>{if(section.hidden)return;updateStatus();},1400);
updateStatus();
// Do NOT automatically reveal the model merely because a download exists.
})();