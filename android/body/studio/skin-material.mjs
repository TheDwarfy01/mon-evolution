/* Uniform, configurable skin tone for the original CC0 rig.
 * The GLB's original albedo map contains baked pigmentation variations.
 * Tinting that map causes inconsistent arms, face and exposed legs.
 */
export function isBodySkinMaterial(meshName,materialName){
 const mesh=String(meshName||'').toLowerCase(),mat=String(materialName||'').toLowerCase();
 return mat==='skin'||((mesh==='base'||mesh==='body')&&mat.includes('skin'));
}
export function applyUniformBodySkin(material,meshName,selectedColour){
 if(!material||!isBodySkinMaterial(meshName,material.name))return false;
 if(material.color&&typeof material.color.set==='function')
  material.color.set(selectedColour);
 if(material.map){
  material.userData=material.userData||{};
  material.userData.studioOriginalSkinDiffuseMap=material.map;
  material.map=null;
 }
 material.needsUpdate=true;
 return true;
}
