/* Cosmetic 3D defaults only. NEVER infer, store or report measurements
 * as though they had been taken with a tape measure. Weight + height +
 * sex + age do not uniquely identify an individual's circumferences.
 * Children's values are especially approximate and are NOT growth norms.
 */
import { REGIONS,validMeasure } from './measurement-morph.mjs';
export const VISUAL_MODES=Object.freeze(['measured','neutral','estimated']);
const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
const round1=v=>Math.round(v*10)/10;
export function visualModeKey(profileId){
 if((typeof profileId!=='string'&&typeof profileId!=='number')||
    !String(profileId)||String(profileId).length>128)return null;
 return 'mon-evolution-studio-body-mode-v1:'+String(profileId);
}
export function readVisualMode(id,store){
 const key=visualModeKey(id);
 if(!key)return 'measured';
 try{const value=store?.getItem(key);return VISUAL_MODES.includes(value)?value:'measured';}
 catch{return 'measured';}
}
export function writeVisualMode(id,mode,store){
 const key=visualModeKey(id);
 if(!key||!VISUAL_MODES.includes(mode))return false;
 try{store?.setItem(key,mode);return true;}catch{return false;}
}
export function estimateVisualMeasurements({height,weight,age,sex,child}={}){
 if(!Number.isFinite(height)||height<45||height>240||
    !Number.isFinite(weight)||weight<=1||weight>500||
    !Number.isFinite(age)||age<0||age>105||
    (sex!=='male'&&sex!=='female'))return null;
 const metres=height/100;
 // Purely aesthetic volume scaling, deliberately not an anthropometric fit.
 // Cubic-root scaling makes the shape change smoothly with a new weight.
 const adultDensity=sex==='male'?14.2:13.7;
 const childDensity=clamp(17.5-age*.38,11.2,17.5);
 const baselineWeight=Math.pow(metres,3)*(child?childDensity:adultDensity);
 const bulk=Math.pow(clamp(weight/baselineWeight,.58,2.35),1/3);
 const young=child?clamp((12-age)/12,0,1):0;
 const adultFemale=sex==='female'?1:0;
 // Coefficients reflect artwork proportions, NOT population averages.
 const coefficients={
  neck:1+(young*.12)-(adultFemale*.05),
  chest:1+(adultFemale?-.035:.035)+(young*.03),
  arm:1-(adultFemale*.085)-(young*.05),
  forearm:1-(adultFemale*.065)-(young*.04),
  waist:1+(adultFemale?-.055:.025)+(young*.06),
  belly:1+(adultFemale?-.02:.02)+(young*.08),
  hips:1+(adultFemale?.065:-.015)+(young*.025),
  thigh:1+(adultFemale?.025:0)+(young*.005),
  calf:1-(adultFemale*.03)-(young*.025)
 };
 const result={};
 for(const r of REGIONS){
  const expected=height*r.base*bulk*coefficients[r.key];
  // Avoid illogical inputs and excessive mesh deformation at both extremes.
  const cm=round1(clamp(expected,r.min,r.max));
  if(!validMeasure(r.key,cm))return null;
  result[r.key]=cm;
 }
 return result;
}
