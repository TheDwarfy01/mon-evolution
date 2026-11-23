/* Topology-safe skin hiding for opaque garments.
 * We never shorten an indexed geometry. glTF primitive groups and material
 * draw ranges reference index offsets, so compacting the index buffer causes
 * dropped triangles, holes and the wrong material on neighboring surfaces.
 */
export function maskIndexedTriangles(original, shouldHide){
 if(!original || !Number.isInteger(original.length) || original.length%3!==0)
  throw new TypeError('Indexed triangles required');
 if(typeof shouldHide!=='function')throw new TypeError('Triangle predicate required');
 const result=new original.constructor(original);
 for(let i=0;i<original.length;i+=3){
  const a=original[i],b=original[i+1],c=original[i+2];
  if(shouldHide(a,b,c,i)){
   // Replace the triangle with a zero-area triangle; keep exact offsets.
   result[i+1]=a;result[i+2]=a;
  }
 }
 return result;
}
const EXPOSED_ARM_BONE=/(?:arm|wrist|hand|finger|thumb|shoulder|clavicle)/i;
/* Skinning weights are a more reliable indicator than 2D proximity to torso.
 * Sleeves should not cause missing elbows, forearms, wrists or hands.
 */
export function touchesExposedArm(vertices,skinIndices,skinWeights,boneNames){
 if(!skinIndices||!skinWeights||!Array.isArray(boneNames))return false;
 for(const vertex of vertices){
  for(let influence=0;influence<4;influence++){
   const weight=skinWeights.getComponent(vertex,influence);
   if(!Number.isFinite(weight)||weight<.12)continue;
   const bone=boneNames[skinIndices.getComponent(vertex,influence)|0];
   if(typeof bone==='string'&&EXPOSED_ARM_BONE.test(bone))return true;
  }
 }
 return false;
}

/* Keep the underarm surface visible at the sleeve opening.
 * Wide body and fitted shirt morphs can separate at the armpit:
 * masking adjacent torso triangles creates dark triangular holes.
 * Only the lateral upper torso of a worn shirt is protected.
 */
export function touchesSleeveOpening(vertices,position,minY,height,files){
 if(!(height>.1)||!position||!Array.isArray(files))return false;
 if(!files.some(f=>['clothing_tshirt.glb','clothing_shirt.glb',
   'clothing_hoodie.glb'].includes(f)))return false;
 const xs=[],ys=[];
 for(const vertex of vertices){
  const x=position.getX(vertex),y=position.getY(vertex);
  if(!Number.isFinite(x)||!Number.isFinite(y))return false;
  xs.push(Math.abs(x)/height);ys.push((y-minY)/height);
 }
 const outer=Math.max(...xs),inner=Math.min(...xs);
 const low=Math.min(...ys),high=Math.max(...ys);
 // Keep a slightly wider armpit band intact. Prefer continuous visible skin
 // to aggressive triangle removal at sleeve edges when morphs vary.
 return high>=.58&&low<=.84&&outer>=.112&&
  (inner>=.070||outer>=.150);
}
