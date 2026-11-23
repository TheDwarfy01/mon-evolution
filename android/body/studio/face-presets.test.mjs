import test from 'node:test';
import assert from 'node:assert/strict';
import {FACE_CHOICES,faceMorphsFor} from './face-presets.mjs';
const nativeTargets=new Set([
 'face_nose_width_decr','face_nose_length_decr','face_jaw_width_decr',
 'face_cheekbones_incr','face_eye_size_incr','face_lips_incr','face_chin_decr'
]);
test('face alternatives use only morph targets confirmed in Studio GLB',()=>{
 assert.deepEqual(FACE_CHOICES.map(x=>x.id),['natural','soft']);
 for(const kind of ['adult_male','adult_female','child_male','child_female']){
  assert.deepEqual(faceMorphsFor(kind,'natural'),{});
  const soft=faceMorphsFor(kind,'soft');
  assert.ok(Object.keys(soft).length>=4,kind);
  for(const [name,strength] of Object.entries(soft)){
   assert.ok(nativeTargets.has(name),name);
   assert.ok(strength>=0&&strength<=.2,name);
  }
 }
});
test('invalid face, sex or missing data do not fabricate model changes',()=>{
 assert.deepEqual(faceMorphsFor('adult_other','soft'),{});
 assert.deepEqual(faceMorphsFor('adult_female','invalid'),{});
 assert.deepEqual(faceMorphsFor('child_male','natural'),{});
});
test('face influences are additive and do not mutate body morphs or measurements',()=>{
 const body={gender_female:1,weight_max:.6,age_child:0};
 const next={...body,...faceMorphsFor('adult_female','soft')};
 assert.deepEqual(body,{gender_female:1,weight_max:.6,age_child:0});
 for(const [key,value] of Object.entries(body))assert.equal(next[key],value);
});
