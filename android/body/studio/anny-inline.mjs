// Vertex indices measured on the signed Anny 1.6.161 GLBs (native 13718 vertices).
// Front and back anchors are attached to the morphing vertex, never fixed screen coordinates.
export const ANNY_ANCHORS=Object.freeze({
 male:{neck:[7500,8162],chest:[1762,3911],arm:[10016,9975],forearm:[10224,10133],waist:[4141,4024],belly:[10780,10975],hips:[4332,4218],thigh:[4532,4530],calf:[11324,11322]},
 female:{neck:[7505,8137],chest:[1780,3910],arm:[8402,8408],forearm:[10265,10112],waist:[4142,4128],belly:[10772,10797],hips:[4326,4218],thigh:[4520,4496],calf:[11333,11345]}
});
const clamp=v=>Number.isFinite(v)?Math.max(-1,Math.min(1,v)):0;
export function annyWeights(snap){
 const mass=clamp(snap.mass), weights=new Array(20).fill(0);
 for(let i=0;i<9;i++){
  const v=clamp(snap.regions[i]?.local);
  weights[2*i]=Math.max(0,v);weights[2*i+1]=Math.max(0,-v);
 }
 if(mass>0){
  for(let i=0;i<18;i+=2)weights[i]*=1-.35*mass;
  weights[10]*=1-.55*mass;
 }
 weights[18]=Math.max(0,mass);weights[19]=Math.max(0,-mass);
 return weights;
}
export function visualIndex(mass){return Math.round(100+(mass>=0?200:35)*clamp(mass));}

// Explicit allowlist shared by the asset selection and validation paths.
export const ANNY_FILES=Object.freeze({male:'anny-male-long-morph.glb',female:'anny-female-long-morph.glb'});
export function annyFile(sex){return sex==='male'||sex==='female'?ANNY_FILES[sex]:null;}
export function isAnnyFile(name){return name===ANNY_FILES.male||name===ANNY_FILES.female;}
