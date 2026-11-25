import test from 'node:test';
import assert from 'node:assert/strict';
import {annySnapshot,adultMassForBmi,ADULT_BMI_ANCHORS} from './anny-profile.mjs';
const p={id:'p1',sex:'male',child:false,age:40,height:175,weight:130,skin:'#123456'};
test('adult selection and nine independent regions',()=>{
 const s=annySnapshot(p,'estimated',{values:{belly:150},estimatedKeys:[]});
 assert.equal(s.sex,'male');assert.equal(s.regions.length,9);assert.ok(s.mass>0);
 assert.equal(s.regions[5].value,150);assert.equal(s.skin,'#123456');
 assert.equal(annySnapshot({...p,sex:'female'},'estimated',{values:{}}).sex,'female');
 assert.equal(annySnapshot({...p,child:true},'estimated',{values:{}}),null);
});
test('neutral and estimates never become measurements or double deformation',()=>{
 const src={values:{belly:150},estimatedKeys:['belly']};
 const n=annySnapshot(p,'neutral',{values:{}});
 assert.equal(n.mass,0);assert.ok(n.regions.every(r=>r.local===0&&r.value===null));
 const e=annySnapshot(p,'estimated',src);assert.equal(e.regions[5].local,0);assert.equal(e.regions[5].estimated,true);
 assert.equal(src.values.belly,150);
});

test('adult BMI landmarks remain continuous, strictly growing until the cap',()=>{
 for(const [bmi,mass] of ADULT_BMI_ANCHORS){
  assert.ok(Math.abs(adultMassForBmi(bmi)-mass)<1e-9);
  assert.ok(Math.abs(adultMassForBmi(bmi+.0001)-adultMassForBmi(bmi-.0001))<.0001);
 }
 for(let bmi=12.1;bmi<83;bmi+=.1)assert.ok(adultMassForBmi(bmi)>adultMassForBmi(bmi-.1));
 assert.equal(adultMassForBmi(100),1);assert.equal(adultMassForBmi(5),-1);
 assert.equal(adultMassForBmi(NaN),0);
});
test('same BMI at different heights or weights produces the same global morph',()=>{
 const at=(bmi,height,sex='male')=>annySnapshot({...p,sex,height,weight:bmi*(height/100)**2},'estimated',{values:{}}).mass;
 for(const bmi of [18.5,23,25,30,35,40,50,60,70,83]){
  assert.ok(Math.abs(at(bmi,150)-at(bmi,190))<1e-9);
  assert.ok(Math.abs(at(bmi,170,'female')-at(bmi,170))<1e-9);
 }
 assert.ok(at(40,175)>at(30,175)+.25);
 assert.ok(at(60,175)>at(40,175));
 assert.ok(at(40,175)<1);
});
test('actual measurements still adjust the local native target, not global BMI',()=>{
 const empty=annySnapshot(p,'measured',{values:{}});
 const real=annySnapshot(p,'measured',{values:{thigh:120,belly:180}});
 assert.equal(real.mass,empty.mass);assert.ok(real.regions[7].local>0);assert.ok(real.regions[5].local>0);
 assert.equal(real.regions[7].value,120);
 assert.equal(real.regions[0].local,0);
});
