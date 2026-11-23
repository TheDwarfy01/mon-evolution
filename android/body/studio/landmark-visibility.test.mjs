import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS} from './measurement-morph.mjs';
import {landmarkView,visibleLandmark,visibleLandmarkKeys} from './landmark-visibility.mjs';
const keys=REGIONS.map(r=>r.key);
test('simplified front, side and back never show more than six landmarks',()=>{
 for(let step=0;step<=360;step++){
  const yaw=step*Math.PI/180;
  const shown=visibleLandmarkKeys(keys,yaw);
  assert.ok(shown.length<=6,'Too many markers at '+step+' degrees');
  assert.ok(shown.length>=4,'No landmarks at '+step+' degrees');
  assert.ok(shown.includes('neck'));
 }
});
test('front can expand to all nine saved circumference regions',()=>{
 assert.equal(landmarkView(0),'front');
 assert.deepEqual(visibleLandmarkKeys(keys,0,true),keys);
 assert.equal(visibleLandmarkKeys(keys,0).length,6);
});
test('back never exposes a chest or belly dot over buttocks/leg',()=>{
 for(const yaw of [Math.PI,Math.PI*.8,Math.PI*1.2,-Math.PI]){
  assert.equal(landmarkView(yaw),'back');
  for(const expanded of [false,true]){
   assert.equal(visibleLandmark('belly',yaw,expanded),false);
   assert.equal(visibleLandmark('chest',yaw,expanded),false);
  }
 }
});
test('side has a bounded set; detailed mode can still access hidden regions',()=>{
 assert.equal(landmarkView(Math.PI/2),'side');
 assert.equal(visibleLandmarkKeys(keys,Math.PI/2).length,6);
 assert.equal(visibleLandmarkKeys(keys,Math.PI/2,true).length,9);
});
test('visibility is periodic, stable on either direction of rotation',()=>{
 for(const yaw of [0,.5,1,1.5,2.5,3.1,4.2,5.8]){
  assert.deepEqual(visibleLandmarkKeys(keys,yaw),visibleLandmarkKeys(keys,yaw+2*Math.PI));
 }
});
