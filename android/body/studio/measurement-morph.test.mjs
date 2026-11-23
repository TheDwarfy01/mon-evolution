import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS,latestMeasurements,visualRatios,deformPosition,validMeasure} from './measurement-morph.mjs';
import {estimateVisualMeasurements} from './visual-defaults.mjs';
test('all nine measurements survive their own latest dated record',()=>{
 const p={bodyMeasurements:[
  {date:'2026-01-12',waist:86,hips:102,chest:109,arm:36},
  {date:'2026-02-19',waist:83,belly:88,thigh:54},
  {date:'2026-03-02',neck:39,calf:39,forearm:29}
 ]};
 assert.equal(REGIONS.length,9);
 assert.deepEqual(latestMeasurements(p),{
  waist:83,hips:102,chest:109,arm:36,belly:88,thigh:54,neck:39,calf:39,forearm:29
 });
});
test('invalid circumference entries never influence avatar deformation',()=>{
 const p={bodyMeasurements:[
  {date:'2026-02-02',waist:90,arm:28},
  {date:'2026-03-02',waist:-23,arm:9999},
 ]};
 assert.equal(latestMeasurements(p).waist,90);
 assert.equal(latestMeasurements(p).arm,28);
 assert.equal(validMeasure('waist',null),false);
 assert.equal(validMeasure('waist',100),true);
});
test('every measured body area visibly and independently affects its region',()=>{
 const h=175,kg=75,meshHeight=1.75;
 for(const r of REGIONS){
  const baseline=h*r.base;
  const ratio=visualRatios({[r.key]:baseline*1.2},h,kg,false);
  assert.ok(ratio[r.key]>1, 'ratio must react: '+r.key);
  const [x,y,z]=[r.x*(meshHeight/1.75),r.y*meshHeight,r.z*(meshHeight/1.75)];
  const moved=deformPosition(x,y,z,0,meshHeight,ratio);
  assert.ok(Math.abs(moved[0]-x)+Math.abs(moved[2]-z)>.00005,
     'measure should move its own landmark: '+r.key);
 }
});
test('geometry transforms are reversible and bounded',()=>{
 const start=[.18,1.05,.10];
 assert.deepEqual(deformPosition(...start,0,1.75,{}),start);
 const extreme=visualRatios({waist:260,hips:300,belly:300},175,90,false);
 const moved=deformPosition(...start,0,1.75,extreme);
 assert.ok(moved.every(Number.isFinite));
 assert.ok(Math.abs(moved[0]/start[0])<1.5);
 assert.ok(Math.abs(moved[2]/start[2])<1.5);
});
test('child measurements do not use adult BMI thresholds',()=>{
 const a=visualRatios({waist:65},130,30,true);
 const b=visualRatios({waist:65},130,45,true);
 assert.equal(a.waist,b.waist);
});

test('waist, belly and hips morph at anatomically distinct torso heights',()=>{
 const regs=Object.fromEntries(REGIONS.map(r=>[r.key,r]));
 assert.ok(regs.waist.y>regs.belly.y&&regs.belly.y>regs.hips.y);
 assert.ok(regs.waist.y>.63&&regs.belly.y>.59&&regs.hips.y>.55);
 const H=1.659,x=.075,z=.14;
 for(const [key,center,far] of [['waist',.643,.43],['belly',.600,.43],['hips',.557,.35]]){
  const ratios=visualRatios({[key]:180},170,85,false);
  const deform=yn=>{
   const [nx,,nz]=deformPosition(x,yn*H,z,0,H,ratios);
   return Math.hypot(nx-x,nz-z);
  };
  assert.ok(deform(center)>deform(far)*4,key+' should expand its intended torso zone');
 }
});
test('changing belly circumference expands real abdomen without editing the groin',()=>{
 const H=1.659,x=.07,z=.13;
 const measured=visualRatios({belly:113},170,85,false);
 const at=yn=>deformPosition(x,H*yn,z,0,H,measured)[2];
 assert.ok(at(.6)>z+.005,'abdomen gets bigger with belly measurement');
 assert.ok(Math.abs(at(.45)-z)<Math.abs(at(.6)-z)*.20,'pelvic crease not belly center');
 assert.deepEqual(deformPosition(x,H*.6,z,0,H,{}),[x,H*.6,z],'neutral reset is unchanged');
});

test('estimated-mode deformation has a meaningful weight response without changing measured mode',()=>{
 const h=170,H=1.659,kg=116;
 const input=estimate=>({belly:estimate,waist:estimate*.88,hips:estimate});
 const measures=input(132),estimated=visualRatios(measures,h,kg,false,true);
 const previous=visualRatios(measures,h,kg,false);
 assert.ok(estimated.belly>previous.belly+.08,'high-BMI estimate must not be normalized away');
 const x=.075,y=H*.60,z=.135;
 const est=deformPosition(x,y,z,0,H,estimated,true);
 const old=deformPosition(x,y,z,0,H,previous);
 assert.ok(est[2]>old[2]+.006,'weight estimated torso must actually appear fuller');
 const neutral=deformPosition(x,y,z,0,H,{},true);
 assert.deepEqual(neutral,[x,y,z]);
 const normal=deformPosition(x,y,z,0,H,previous,false);
 assert.deepEqual(normal,old,'measured mode must stay unchanged');
});
test('weight-estimated shape responds smoothly across adult weight changes',()=>{
 const H=1.659,h=170,x=.08,y=H*.60,z=.13;
 const weights=[65,75,85,95,105,116,130],depths=[];
 for(const weight of weights){
  const values=estimateVisualMeasurements({height:h,weight,age:40,sex:'male',child:false});
  const ratios=visualRatios(values,h,weight,false,true);
  const point=deformPosition(x,y,z,0,H,ratios,true);
  depths.push(point[2]);assert.ok(point.every(Number.isFinite));
 }
 for(let i=1;i<depths.length;i++)assert.ok(depths[i]>=depths[i-1]-1e-8,'weight increase should not shrink belly');
 assert.ok(depths.at(-1)>depths[0]+.025);
});
