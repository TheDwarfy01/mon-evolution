/* Personal *visual* circumference equivalents for weight-based 3D labels.
 * This is not a measurement, is never written into bodyMeasurements, and does
 * not alter a validated mesh or recorded measurements.
 */
const min=20,max=300;
const prefix='mon-evolution-visual-belly-equivalence-v1:';
const round1=n=>Math.round(n*10)/10;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function bellyVisualCalibrationKey(profileId){
 const s=String(profileId??'');
 return s.length>0&&s.length<=128?prefix+s:null;
}
export function readBellyVisualCalibration(profileId,store){
 const key=bellyVisualCalibrationKey(profileId);
 if(!key)return 1;
 try{
  const factor=Number(store?.getItem(key));
  return Number.isFinite(factor)&&factor>=.6&&factor<=2.2?factor:1;
 }catch{return 1;}
}
export function calibrateBellyVisualEquivalent(estimatedValue,factor){
 if(!Number.isFinite(estimatedValue)||estimatedValue<min||estimatedValue>max)return null;
 if(!Number.isFinite(factor)||factor<.6||factor>2.2)return round1(estimatedValue);
 return round1(clamp(estimatedValue*factor,min,max));
}
export function saveBellyVisualCalibration(profileId,estimatedValue,desiredValue,store){
 const key=bellyVisualCalibrationKey(profileId);
 if(!key||!Number.isFinite(estimatedValue)||estimatedValue<min||estimatedValue>max||
    !Number.isFinite(desiredValue)||desiredValue<min||desiredValue>max)return false;
 const ratio=desiredValue/estimatedValue;
 if(ratio<.6||ratio>2.2)return false;
 try{store?.setItem(key,String(ratio));return true;}catch{return false;}
}
export function clearBellyVisualCalibration(profileId,store){
 const key=bellyVisualCalibrationKey(profileId);
 if(!key)return false;
 try{store?.removeItem(key);return true;}catch{return false;}
}
