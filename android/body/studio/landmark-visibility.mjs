/* Angle-aware landmark density. No measurement values or mesh transforms are changed.
 * Circumference fields stay available in the form regardless of visibility.
 */
const VIEWS=Object.freeze({
 front:['neck','chest','waist','belly','thigh','calf'],
 side:['neck','arm','waist','belly','thigh','calf'],
 back:['neck','arm','waist','hips','thigh','calf']
});
const HIDDEN_FROM_REAR=new Set(['chest','belly']);
export function landmarkView(yaw){
 const angle=Number.isFinite(yaw)?yaw:0;
 const c=Math.cos(angle);
 if(c<-.35)return 'back';
 if(c>.35)return 'front';
 return 'side';
}
export function visibleLandmark(key,yaw,expanded=false){
 const view=landmarkView(yaw);
 // A belly/chest point on a back-facing body is anatomically misleading.
 if(view==='back'&&HIDDEN_FROM_REAR.has(key))return false;
 if(expanded)return true;
 return VIEWS[view].includes(key);
}
export function visibleLandmarkKeys(keys,yaw,expanded=false){
 return keys.filter(key=>visibleLandmark(key,yaw,expanded));
}
