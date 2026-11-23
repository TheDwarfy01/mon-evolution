import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS,validMeasure,visualRatios,deformPosition} from './measurement-morph.mjs';
import {estimateVisualMeasurements,readVisualMode,writeVisualMode} from './visual-defaults.mjs';

function store(){
 const data=new Map();
 return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v)};
}
test('three 3D silhouette modes persist independently for each person and keep real entries',()=>{
 const s=store(),actual={waist:93,arm:35};
 assert.equal(readVisualMode('person1',s),'measured');
 assert.equal(writeVisualMode('person1','estimated',s),true);
 assert.equal(readVisualMode('person1',s),'estimated');
 assert.equal(readVisualMode('person2',s),'measured');
 assert.equal(writeVisualMode('person1','neutral',s),true);
 assert.equal(readVisualMode('person1',s),'neutral');
 assert.deepEqual(actual,{waist:93,arm:35},'never edit actual profile measurements');
 assert.equal(writeVisualMode('person1','danger',s),false);
});
test('adult male and female estimates have nine bounded cosmetic values',()=>{
 for(const [sex,height,weight] of [['male',175,75],['female',165,65]]){
  const values=estimateVisualMeasurements({sex,height,weight,age:39,child:false});
  assert.equal(Object.keys(values).length,9);
  for(const r of REGIONS)assert.equal(Boolean(validMeasure(r.key,values[r.key])),true,r.key);
 }
 const male=estimateVisualMeasurements({sex:'male',height:170,weight:70,age:35,child:false});
 const female=estimateVisualMeasurements({sex:'female',height:170,weight:70,age:35,child:false});
 assert.ok(male.chest>female.chest);
 assert.ok(male.waist>female.waist);
 assert.ok(male.arm>female.arm);
 assert.ok(female.hips>male.hips);
});
test('weight changes show a smooth 3D visual response without fake history records',()=>{
 const profile={sex:'female',height:165,age:45,child:false,weight:60};
 const a=estimateVisualMeasurements(profile);
 const b=estimateVisualMeasurements({...profile,weight:73});
 for(const r of REGIONS)assert.ok(b[r.key]>a[r.key],r.key+' must react to current weight');
 const H=1.75,r=REGIONS.find(x=>x.key==='waist');
 const x=r.x,y=r.y*H,z=r.z;
 const aa=deformPosition(x,y,z,0,H,visualRatios(a,profile.height,60));
 const bb=deformPosition(x,y,z,0,H,visualRatios(b,profile.height,73));
 assert.ok(Math.hypot(aa[0]-bb[0],aa[2]-bb[2])>.0001,'avatar must change');
 assert.deepEqual(deformPosition(x,y,z,0,H,{}),[x,y,z],'neutral mode resets deformation');
});
test('child profile only receives illustrative form, not adult size or clinical interpretation',()=>{
 const young=estimateVisualMeasurements({sex:'male',height:110,weight:19,age:5,child:true});
 const older=estimateVisualMeasurements({sex:'female',height:150,weight:44,age:13,child:true});
 assert.ok(young && older);
 for(const r of REGIONS){
  assert.ok(validMeasure(r.key,young[r.key]));
  assert.ok(validMeasure(r.key,older[r.key]));
 }
 assert.ok(young.chest<older.chest);
 assert.equal(estimateVisualMeasurements({sex:'unknown',height:150,weight:45,age:9,child:true}),null);
 assert.equal(estimateVisualMeasurements({sex:'male',height:0,weight:45,age:9,child:true}),null);
});
test('extreme but valid profiles still never exceed geometric measurement bounds',()=>{
 for(const sex of ['male','female'])for(const child of [true,false]){
  const a=estimateVisualMeasurements({sex,height:child?65:145,weight:child?4:35,age:child?1:80,child});
  const b=estimateVisualMeasurements({sex,height:child?180:220,weight:child?130:250,age:child?17:65,child});
  for(const data of [a,b])for(const r of REGIONS)assert.ok(validMeasure(r.key,data[r.key]),r.key);
 }
});

test('high-BMI adult estimated silhouette grows substantially versus the old near-neutral figure',()=>{
 const p={sex:'male',height:170,weight:116,age:40,child:false};
 const visual=estimateVisualMeasurements(p);
 // The previous cube-root estimate was ~95 cm at 116 kg, irrespective of height.
 assert.ok(visual.belly>=125&&visual.belly<=158,'belly visual equivalent should react to BMI');
 assert.ok(visual.waist>=108&&visual.hips>=122,'entire trunk should react');
 const low=estimateVisualMeasurements({...p,weight:80});
 assert.ok(visual.belly>low.belly+25);
 assert.ok(visual.thigh>low.thigh+10);
 assert.ok(visual.calf<visual.belly*.55,'do not enlarge extremities like the belly');
});
test('identical weight at different heights yields different adult appearance proportions',()=>{
 const a=estimateVisualMeasurements({height:155,weight:116,age:40,sex:'male',child:false});
 const b=estimateVisualMeasurements({height:195,weight:116,age:40,sex:'male',child:false});
 assert.ok(a.belly>b.belly+12,'BMI / height must matter: same weight is not same volume distribution');
});
test('estimated adult female shape remains a distinct sex-specific silhouette',()=>{
 const male=estimateVisualMeasurements({height:170,weight:116,age:40,sex:'male',child:false});
 const female=estimateVisualMeasurements({height:170,weight:116,age:40,sex:'female',child:false});
 assert.ok(male.waist>female.waist);
 assert.ok(female.hips>male.hips);
});

test('upper arm and forearm scale moderately with weight for female and male',()=>{
 for(const sex of ['female','male']){
  const light=estimateVisualMeasurements({sex,height:170,weight:70,age:40,child:false});
  const heavy=estimateVisualMeasurements({sex,height:170,weight:116,age:40,child:false});
  assert.ok(heavy.arm>light.arm+6);
  assert.ok(heavy.forearm>light.forearm+4);
  assert.ok(heavy.arm<heavy.belly*.45);
  assert.ok(heavy.forearm<heavy.arm);
 }
});
