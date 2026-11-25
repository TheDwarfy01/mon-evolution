// Anny visual controls only; never write inferred measurements to a profile.
import {REGIONS,validMeasure} from './measurement-morph.mjs';
import {estimateVisualMeasurements} from './visual-defaults.mjs';
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
export function annySnapshot(p,mode,display){
 if(!p||p.child||!['male','female'].includes(p.sex)||!(p.height>=45&&p.height<=240&&p.weight>1&&p.weight<=500))return null;
 const bmi=p.weight/(p.height/100)**2;
 const mass=mode==='neutral'?0:clamp((bmi-23)/(bmi>=23?30:11),-1,1);
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
