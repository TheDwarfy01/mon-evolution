// Anny visual controls only; never write inferred measurements to a profile.
import {REGIONS,validMeasure} from './measurement-morph.mjs';
import {estimateVisualMeasurements} from './visual-defaults.mjs';
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
// Artistic anchors on the adult native Anny morph, not clinical body shapes.
// Piecewise interpolation preserves continuity, including at BMI class limits.
export const ADULT_BMI_ANCHORS=Object.freeze([
 [12,-1],[16.5,-.65],[18.5,-.40],[23,0],[25,.10],
 [30,.28],[35,.44],[40,.60],[50,.78],[60,.90],[70,.96],[83,1]
].map(Object.freeze));
export function adultMassForBmi(bmi){
 if(!Number.isFinite(bmi))return 0;
 const a=ADULT_BMI_ANCHORS;
 if(bmi<=a[0][0])return a[0][1];
 if(bmi>=a.at(-1)[0])return a.at(-1)[1];
 for(let i=1;i<a.length;i++){
  if(bmi<=a[i][0]){
   const [x0,y0]=a[i-1],[x1,y1]=a[i];
   return y0+(y1-y0)*(bmi-x0)/(x1-x0);
  }
 }
 return 1;
}
export function annySnapshot(p,mode,display){
 if(!p||p.child||!['male','female'].includes(p.sex)||!(p.height>=45&&p.height<=240&&p.weight>1&&p.weight<=500))return null;
 const bmi=p.weight/(p.height/100)**2;
 const mass=mode==='neutral'?0:adultMassForBmi(bmi);
 const expected=estimateVisualMeasurements(p)||{};
 const estimated=new Set(display.estimatedKeys||[]);
 const values=display.values||{};
 const regions=REGIONS.map(r=>{
  const value=validMeasure(r.key,values[r.key])?values[r.key]:null;
  const target=expected[r.key];
  const local=mode==='neutral'||value===null||estimated.has(r.key)||!(target>0)?0:clamp((value/target-1)/.35,-1,1);
  return {key:r.key,label:r.label,value,estimated:estimated.has(r.key),local};
 });
 const color=(v,d)=>typeof v==='string'&&/^#[0-9a-f]{6}$/i.test(v)?v:d;
 return {id:String(p.id),sex:p.sex,mode,mass,regions,skin:color(p.skin,'#D99E78'),hair:color(p.hair,'#4A2D22'),eyes:color(p.eyes,'#593826')};
}
