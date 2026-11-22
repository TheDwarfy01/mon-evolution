/* Mon Évolution IMC — WebGL MakeHuman viewer, opt-in offline pack.
 * Mesh and all 24 morph targets are derived from CC0 MakeHuman assets.
 * No adult BMI classifications are applied to children's silhouettes.
 */
(()=>{
'use strict';
const section=document.getElementById('body-measurements');
const stage=document.getElementById('bm-model');
if(!section||!stage)return;
const bridge=window.AndroidBackup, morph=window.MonEvolutionBodyMorph;
if(!bridge || typeof bridge.makeHumanState!=='function' || !morph)return;
const css=document.createElement('style');
css.textContent=[
 '#bm-model{position:relative!important}',
 '#bm-model canvas.bm-makehuman-canvas{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:2!important;display:none;touch-action:pan-y;pointer-events:auto;border-radius:12px}',
 '#bm-model.bm-makehuman-active canvas.bm-photo-canvas{display:none!important}',
 '#bm-model.bm-makehuman-active canvas.bm-makehuman-canvas{display:block!important}',
 '.bm-mh-panel{position:absolute;bottom:8px;left:8px;right:8px;z-index:9;display:flex;align-items:center;justify-content:center;gap:7px;flex-wrap:wrap;pointer-events:none}',
 '.bm-mh-panel button{pointer-events:auto;background:#134d58;color:#e6fff9;border:1px solid #77efd4;border-radius:999px;padding:7px 12px;font-size:12px;max-width:98%}',
 '.bm-mh-panel span{padding:5px 8px;color:#e5fff9;text-align:center;border-radius:6px;background:#092e42dd;font-size:11px}'
].join('\n');
document.head.append(css);
const canvas=document.createElement('canvas');
canvas.className='bm-makehuman-canvas';
canvas.setAttribute('role','img');
canvas.setAttribute('aria-label','Silhouette 3D indicative fondée sur les mesures enregistrées');
stage.append(canvas);
const panel=document.createElement('div');
panel.className='bm-mh-panel';
const button=document.createElement('button');
button.type='button';button.textContent='Installer le mannequin 3D';
const note=document.createElement('span');
note.textContent='Module 3D optionnel • téléchargement unique';
panel.append(button,note);stage.append(panel);
let pack=null,gl=null,renderer=null,loading=false,currentKey='',yaw=0,gesture=null,failed=false;
const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
const hex=s=>{
 const m=/^#([0-9a-fA-F]{6})$/.exec(s||'');
 const h=m?m[1]:'D99E78';
 return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255);
};
function person(){
 const p=typeof profile==='function'?profile():null;
 if(!p)return null;
 const values=Array.isArray(p.entries)?p.entries.filter(e=>Number.isFinite(+e.weight))
     .slice().sort((a,b)=>String(a.date).localeCompare(String(b.date))):[];
 const last=values.at(-1),first=values[0];
 if(!last)return null;
 const birth=typeof p.birthDate==='string'?p.birthDate:null;
 let ageYears=NaN;
 if(birth&&/^\d{4}-\d{2}-\d{2}$/.test(birth)){
  ageYears=(Date.now()-new Date(birth+'T12:00:00').getTime())/31556952000;
 }
 const child=Number.isFinite(ageYears)&&ageYears<18;
 const a=p.bodyAppearance||{};
 const dateRecords=Array.isArray(p.bodyMeasurements)?p.bodyMeasurements.filter(r=>r&&r.date)
   .slice().sort((x,y)=>x.date.localeCompare(y.date)):[];
 const measures=dateRecords.at(-1)||{};
 const params=morph.parameters({height:+p.height,weight:+last.weight,
   birthDate:birth||'',isChild:child,waist:measures.waist,hips:measures.hips,chest:measures.chest});
 if(!params.valid)return null;
 const model=a.model==='female'?'female':a.model==='male'?'male':
   p.sex==='female'?'female':'male';
 let weight;
 if(child){
   // Change is relative to the person's OWN earliest recorded weight,
   // not an adult BMI threshold, medical diagnosis, or weight-loss goal.
   weight=.5;
   if(first&&first.weight>0){
     const delta=Math.log(Math.max(.05,+last.weight/+first.weight));
     weight=clamp(.5+delta*.28,.12,.88);
   }
 }else{
   weight=clamp((params.bmi-16)/23,0,1);
   if(Number.isFinite(+measures.waist)&&Number.isFinite(+measures.hips)&&+measures.hips>0){
     weight=clamp(weight+(+measures.waist/+measures.hips-.83)*.14,0,1);
   }
 }
 return {id:p.id,model,child,ageYears:Number.isFinite(ageYears)?ageYears:35,
   weight,skin:a.skin||'#D99E78',hair:a.hair||'#4A2D22',
   eyes:a.eyes||'#593826',height:+p.height,
   date:last.date,kg:+last.weight};
}
async function readPack(){
 const bytes=bridge.makeHumanBytes();
 if(!(bytes>100000&&bytes<=12000000))throw Error('Taille du pack incorrecte');
 const output=new Uint8Array(bytes);
 for(let i=0;i<bytes;i+=49152){
   const chunk=bridge.makeHumanReadChunk(i);
   if(typeof chunk!=='string'||!chunk)throw Error('Fichier 3D incomplet');
   const raw=atob(chunk);
   for(let k=0;k<raw.length;k++)output[i+k]=raw.charCodeAt(k);
   if(i%393216===0)await new Promise(ok=>setTimeout(ok,0));
 }
 if(typeof DecompressionStream!=='function')throw Error('Android WebView ne supporte pas la décompression');
 const ds=new DecompressionStream('gzip');
 const json=await new Response(new Blob([output]).stream().pipeThrough(ds)).text();
 const obj=JSON.parse(json);
 if(obj.version!==1||obj.license!=='CC0-1.0'||obj.bodyVertices!==13380
    ||!Array.isArray(obj.positions)||obj.positions.length!==obj.bodyVertices
    ||!Array.isArray(obj.triangles)||obj.triangles.length<20000
    ||typeof obj.targets!=='object')throw Error('Pack MakeHuman invalide');
 return obj;
}
const shaders={
 vert:"attribute vec3 aPos;attribute vec3 aNorm;attribute vec3 aColor;uniform float uYaw;uniform float uAspect;uniform float uZoom;varying vec3 vColor;varying vec3 vNorm;void main(){float c=cos(uYaw),s=sin(uYaw);vec3 p=vec3(aPos.x*c+aPos.z*s,aPos.y,-aPos.x*s+aPos.z*c);vNorm=normalize(vec3(aNorm.x*c+aNorm.z*s,aNorm.y,-aNorm.x*s+aNorm.z*c));vColor=aColor;gl_Position=vec4(p.x*1.85*uZoom/uAspect,p.y*1.91*uZoom,-p.z*.35,1.0);}",
 frag:"precision mediump float;varying vec3 vColor;varying vec3 vNorm;void main(){vec3 l=normalize(vec3(-.45,.6,.9));float bright=.49+.51*abs(dot(normalize(vNorm),l));gl_FragColor=vec4(vColor*bright,1.0);}"
};
function shader(type,src){
 const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);
 if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s)||'Shader');
 return s;
}
function initGl(){
 gl=canvas.getContext('webgl',{alpha:true,antialias:true,preserveDrawingBuffer:false})
   ||canvas.getContext('experimental-webgl');
 if(!gl)throw Error('WebGL indisponible sur ce smartphone');
 const program=gl.createProgram();
 gl.attachShader(program,shader(gl.VERTEX_SHADER,shaders.vert));
 gl.attachShader(program,shader(gl.FRAGMENT_SHADER,shaders.frag));
 gl.linkProgram(program);
 if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('WebGL link');
 gl.useProgram(program);
 const attrs=['aPos','aNorm','aColor'].map(n=>gl.getAttribLocation(program,n));
 const buffers=attrs.map(()=>gl.createBuffer());
 for(let i=0;i<3;i++){
   gl.bindBuffer(gl.ARRAY_BUFFER,buffers[i]);
   gl.enableVertexAttribArray(attrs[i]);gl.vertexAttribPointer(attrs[i],3,gl.FLOAT,false,0,0);
 }
 const faces=new Uint16Array(pack.triangles);
 const ibo=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ibo);
 gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,faces,gl.STATIC_DRAW);
 gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);
 gl.disable(gl.CULL_FACE);
 gl.clearColor(0,0,0,0);
 return {program,attrs,buffers,count:faces.length,
  uYaw:gl.getUniformLocation(program,'uYaw'),uAspect:gl.getUniformLocation(program,'uAspect'),
  uZoom:gl.getUniformLocation(program,'uZoom'),zoom:1};
}
function axisWeight(age){
 // Smoothly interpolate MakeHuman age macro targets, with no adult BMI logic.
 const knots=[{a:0,n:'baby'},{a:6,n:'child'},
              {a:20,n:'young'},{a:75,n:'old'}];
 for(let i=0;i<knots.length-1;i++){
   if(age<=knots[i+1].a){
     const t=clamp((age-knots[i].a)/(knots[i+1].a-knots[i].a),0,1);
     return [[knots[i].n,1-t],[knots[i+1].n,t]];
   }
 }
 return [['old',1]];
}
function axisMass(weight){
 if(weight<=.5)return [['minweight',1-weight*2],['averageweight',weight*2]];
 return [['averageweight',(1-weight)*2],['maxweight',(weight-.5)*2]];
}
function updateGeometry(p){
 const n=pack.bodyVertices, coords=pack.positions;
 const points=new Float32Array(n*3);
 let yMin=Infinity,yMax=-Infinity;
 for(let i=0;i<n;i++){
   const q=coords[i];points[i*3]=q[0];points[i*3+1]=q[1];points[i*3+2]=q[2];
 }
 for(const [age,aw] of axisWeight(p.ageYears)){
  // Apply the matching MakeHuman phenotype before the mass modifiers.
  const identity=pack.targets[p.model+'-'+age+'-identity'];
  if(identity&&aw>0){
   for(let k=0;k<identity.length;k+=4){
    const i=identity[k]*3;
    if(i<0||i+2>=points.length)continue;
    points[i]+=identity[k+1]*aw;
    points[i+1]+=identity[k+2]*aw;
    points[i+2]+=identity[k+3]*aw;
   }
  }
  for(const [mass,mw] of axisMass(p.weight)){
   const list=pack.targets[p.model+'-'+age+'-'+mass],influence=aw*mw;
   if(!list||influence<=0)continue;
   for(let k=0;k<list.length;k+=4){
    const i=list[k]*3;
    if(i<0||i+2>=points.length)continue;
    points[i]+=list[k+1]*influence;
    points[i+1]+=list[k+2]*influence;
    points[i+2]+=list[k+3]*influence;
   }
  }
 }
 for(let i=1;i<points.length;i+=3){yMin=Math.min(yMin,points[i]);yMax=Math.max(yMax,points[i]);}
 const height=Math.max(.001,yMax-yMin),center=(yMax+yMin)/2;
 const norm=new Float32Array(n*3),colors=new Float32Array(n*3);
 const skin=hex(p.skin),hair=hex(p.hair),shirt=[.16,.51,.57],leggings=[.12,.23,.32];
 for(let i=0;i<n;i++){
   const j=i*3,y=(points[j+1]-yMin)/height,x=Math.abs(points[j])/height,z=points[j+2]/height;
   const upper=y>.82,scalp=y>.965,
     shortSleeve=y>.61&&y<.79&&x>.24;
   let material=skin;
   if(scalp)material=hair;
   else if(upper||shortSleeve)material=skin;
   else if(y>.56)material=shirt;
   else material=leggings;
   // The body is illustrated in opaque sportwear, including for children.
   if(upper&&y>.902&&y<.927&&x>.018&&x<.065&&z>.04)material=hex(p.eyes);
   for(let t=0;t<3;t++)colors[j+t]=material[t];
   points[j]=(points[j])/height;
   points[j+1]=(points[j+1]-center)/height;
   points[j+2]=(points[j+2])/height;
 }
 const idx=pack.triangles;
 for(let f=0;f<idx.length;f+=3){
   const ai=idx[f]*3,bi=idx[f+1]*3,ci=idx[f+2]*3;
   const ux=points[bi]-points[ai],uy=points[bi+1]-points[ai+1],uz=points[bi+2]-points[ai+2];
   const vx=points[ci]-points[ai],vy=points[ci+1]-points[ai+1],vz=points[ci+2]-points[ai+2];
   const nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
   for(const k of [ai,bi,ci]){norm[k]+=nx;norm[k+1]+=ny;norm[k+2]+=nz;}
 }
 for(let j=0;j<norm.length;j+=3){
   const length=Math.hypot(norm[j],norm[j+1],norm[j+2])||1;
   norm[j]/=length;norm[j+1]/=length;norm[j+2]/=length;
 }
 [points,norm,colors].forEach((buffer,i)=>{
   gl.bindBuffer(gl.ARRAY_BUFFER,renderer.buffers[i]);
   gl.bufferData(gl.ARRAY_BUFFER,buffer,gl.DYNAMIC_DRAW);
   gl.vertexAttribPointer(renderer.attrs[i],3,gl.FLOAT,false,0,0);
 });
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.getParameter(gl.ELEMENT_ARRAY_BUFFER_BINDING));
}
function draw(){
 if(!pack||!renderer||section.hidden)return;
 const w=Math.max(2,Math.floor(canvas.clientWidth*Math.min(devicePixelRatio||1,2)));
 const h=Math.max(2,Math.floor(canvas.clientHeight*Math.min(devicePixelRatio||1,2)));
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
 gl.useProgram(renderer.program);
 gl.uniform1f(renderer.uYaw,yaw);
 gl.uniform1f(renderer.uAspect,w/h);
 gl.uniform1f(renderer.uZoom,renderer.zoom);
 for(let i=0;i<3;i++){
  gl.bindBuffer(gl.ARRAY_BUFFER,renderer.buffers[i]);
  gl.enableVertexAttribArray(renderer.attrs[i]);
  gl.vertexAttribPointer(renderer.attrs[i],3,gl.FLOAT,false,0,0);
 }
 gl.drawElements(gl.TRIANGLES,renderer.count,gl.UNSIGNED_SHORT,0);
}
function refresh(){
 if(!pack||!renderer||section.hidden)return;
 const p=person();
 if(!p){note.textContent='Renseigne taille et poids dans ton profil';return;}
 const key=[p.id,p.model,p.child,p.ageYears.toFixed(3),p.weight.toFixed(4),p.height,
   p.skin,p.hair,p.eyes,p.date,p.kg].join('|');
 if(key!==currentKey){
  currentKey=key;updateGeometry(p);
  note.textContent='Silhouette indicative · '+(p.child?'croissance':'corpulence')+' · tourner avec le doigt';
 }
 draw();
}
async function activate(){
 if(loading||pack)return;
 loading=true;button.disabled=true;note.textContent='Chargement du mannequin MakeHuman…';
 try{
  pack=await readPack();renderer=initGl();
  stage.classList.add('bm-makehuman-active');
  button.textContent='Mannequin 3D activé';
  button.style.display='none';failed=false;currentKey='';refresh();
 }catch(e){
  pack=null;failed=true;button.textContent='Réessayer le modèle 3D';
  button.style.display='';button.disabled=false;
  note.textContent='Mode photo conservé : '+String(e.message||'erreur 3D');
 }finally{loading=false;button.disabled=false;}
}
button.addEventListener('click',()=>{
 try{
  if(bridge.makeHumanState()==='ready'){activate();return;}
  failed=false;note.textContent='Téléchargement du modèle 3D (une seule fois)…';
  button.disabled=true;
  bridge.makeHumanInstall();
 }catch(e){button.disabled=false;note.textContent='Téléchargement impossible';}
});
let lastStatus='';
function tick(){
 if(section.hidden)return;
 try{
  const status=bridge.makeHumanState();
  if(status==='ready'&&!pack&&!loading&&!failed){activate();return;}
  if(status!==lastStatus){
   lastStatus=status;
   if(status==='downloading'){button.disabled=true;note.textContent='Téléchargement MakeHuman en cours…';}
   else if(status.startsWith('error')){button.disabled=false;note.textContent='Erreur de téléchargement · réessayer';}
   else if(status==='missing'){button.disabled=false;note.textContent='Installer une seule fois · disponible ensuite hors ligne';}
  }
  refresh();
 }catch(e){/* never break the original 2D viewer */}
}
canvas.addEventListener('pointerdown',e=>{
 if(!pack)return;
 gesture={x:e.clientX,yaw};canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove',e=>{
 if(!gesture)return;
 yaw=gesture.yaw+(e.clientX-gesture.x)*.012;draw();
});
canvas.addEventListener('pointerup',()=>{gesture=null;});
canvas.addEventListener('pointercancel',()=>{gesture=null;});
window.addEventListener('resize',draw);
window.addEventListener('mon-evolution-appearance-changed',()=>{currentKey='';refresh();});
window.addEventListener('mon-evolution-makehuman-ready',tick);
setInterval(tick,1250);
tick();
})();