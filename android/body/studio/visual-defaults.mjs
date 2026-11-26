/* Cosmetic 3D defaults only. NEVER infer, store or report measurements
 * as though they had been taken with a tape measure. Weight + height +
 * sex + age do not uniquely identify an individual's circumferences.
 * Children's values are especially approximate and are NOT growth norms.
 */
import { REGIONS,validMeasure } from './measurement-morph.mjs';
export const VISUAL_MODES=Object.freeze(['measured','neutral','estimated','manual']);
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
 const bmi=weight/(metres*metres);
 // Artistic weight response ONLY. This is not an estimate of a person's
 // real circumference, and cannot substitute for a tape measurement.
 // The former cube-root formula cancelled height out and left a 116 kg
 // adult visually almost unchanged. Use weight *relative to height*
 // instead, with more expansion at belly/waist than at the extremities.
 // Keep existing estimates through BMI 53, then extend them gently rather
 // than freezing all regions at the old upper boundary. These are artwork
 // references only, not measured or population-predicted circumferences.
 const adultExcess=clamp(bmi-23,-11,30)+.30*clamp(bmi-53,0,30);
 const childDensity=clamp(17.5-age*.38,11.2,17.5);
 const baselineWeight=Math.pow(metres,3)*childDensity;
 const childBulk=Math.pow(clamp(weight/baselineWeight,.58,2.35),1/3);
 const artisticFactors={
  neck:.012,chest:.026,arm:.024,forearm:.019,
  waist:.032,belly:.036,hips:.029,thigh:.023,calf:.018
 };
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
  const childOrAdultBulk=child?childBulk:clamp(
   1+adultExcess*artisticFactors[r.key]+
   (r.key==='belly'?.0006*Math.max(0,Math.min(bmi,83)-30)**2:0)+
   (r.key==='thigh'?.006*clamp(bmi-40,0,43):0),
   .72,r.key==='belly'?2.25:r.key==='thigh'?2.15:1.96
  );
  const expected=height*r.base*childOrAdultBulk*coefficients[r.key];
  // Avoid illogical inputs and excessive mesh deformation at both extremes.
  const cm=round1(clamp(expected,r.min,r.max));
  if(!validMeasure(r.key,cm))return null;
  result[r.key]=cm;
 }
 return result;
}
