import test from 'node:test';
import assert from 'node:assert/strict';
import {isBodySkinMaterial,applyUniformBodySkin} from './skin-material.mjs';
const mock=(name,map)=>({
 name,map,userData:{},color:{value:'',set(v){this.value=v;}},needsUpdate:false,
 normalMap:{id:'normal'},roughness:.73
});
test('exposed skin is uniformly coloured despite distinct baked albedo maps',()=>{
 const face=mock('Skin',{id:'base-body-atlas'});
 const legs=mock('Skin',{id:'another-original-atlas'});
 for(const material of [face,legs])
  assert.equal(applyUniformBodySkin(material,'base','#D6A081'),true);
 assert.equal(face.color.value,'#D6A081');
 assert.equal(legs.color.value,'#D6A081');
 assert.equal(face.map,null);assert.equal(legs.map,null);
 assert.equal(face.roughness,.73);assert.equal(face.normalMap.id,'normal');
});
test('changing the skin shade updates the same material for all exposed body parts',()=>{
 const material=mock('Skin',{id:'original'});
 for(const colour of ['#D99E78','#51372C','#E7D0BE']){
  assert.equal(applyUniformBodySkin(material,'base',colour),true);
  assert.equal(material.color.value,colour);
  assert.equal(material.map,null);
 }
 assert.equal(material.userData.studioOriginalSkinDiffuseMap.id,'original');
});
test('iris, eyebrows, hair and clothing retain their source diffuse textures',()=>{
 for(const [mesh,name] of [['Eyes','Iris'],['Eyes','Eye'],['Eyebrows','Eyebrow'],
 ['Teeth','Teeth'],['Tongue','Tongue'],['clothing','Skin-like cloth'],
 ['hair','Skin-toned hair']]){
  const map={id:mesh},mat=mock(name,map);
  assert.equal(applyUniformBodySkin(mat,mesh,'#FFF'),false,mesh);
  assert.equal(mat.map,map);
  assert.equal(mat.needsUpdate,false);
 }
 assert.equal(isBodySkinMaterial('base','Skin'),true);
 assert.equal(isBodySkinMaterial('Eyes','Iris'),false);
});
