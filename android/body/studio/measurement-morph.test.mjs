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

test('high-BMI estimated upper arm gets thickness at humerus rather than only at shirt shoulder',()=>{
 const kg=116,cm=170,H=1.659;
 const estimatedValues=estimateVisualMeasurements({sex:'female',height:cm,weight:kg,age:40,child:false});
 const ratios=visualRatios(estimatedValues,cm,kg,false,true);
 // Approximate GLB upper arm: shoulder (.17,1.32), elbow (.33,1.14).
 const samples=[
  {label:'upper arm',x:.278,y:.745*H,z:.058},
  {label:'elbow',x:.329,y:.687*H,z:.055},
  {label:'forearm',x:.392,y:.638*H,z:.046}
 ];
 for(const sample of samples){
  const next=deformPosition(sample.x,sample.y,sample.z,0,H,ratios,true);
  assert.ok(next.every(Number.isFinite),sample.label+' finite');
  assert.ok(next[2]>sample.z+.004,sample.label+' gains circumference depth');
  assert.ok(Math.abs(next[0]-sample.x)<.08,sample.label+' does not jump');
 }
});
test('estimated torso does not over-inflate sleeves relative to the upper arm',()=>{
 const cm=170,kg=116,H=1.659;
 const m=estimateVisualMeasurements({sex:'female',height:cm,weight:kg,age:40,child:false});
 const ratio=visualRatios(m,cm,kg,false,true);
 const sleeve={x:.255,y:.76*H,z:.06};
 const elbow={x:.33,y:.69*H,z:.06};
 const grow=p=>deformPosition(p.x,p.y,p.z,0,H,ratio,true)[2]-p.z;
 assert.ok(grow(elbow)>.006,'upper arm is not starved');
 assert.ok(grow(sleeve)<.038,'shoulder sleeve does not balloon');
});
test('male and female measured profiles and all neutral profiles remain unchanged',()=>{
 const H=1.659;
 const measures={chest:140,arm:50,forearm:32,waist:120,belly:150};
 const ratios=visualRatios(measures,170,116,false,false);
 for(const x of [.16,.23,.29,.34,.40])for(const yn of [.62,.69,.75,.80]){
  const pos=[x,H*yn,.065];
  const old=deformPosition(...pos,0,H,ratios);
  assert.deepEqual(deformPosition(...pos,0,H,ratios,false),old);
  assert.deepEqual(deformPosition(...pos,0,H,{},false),pos);
  assert.deepEqual(deformPosition(...pos,0,H,{},true),pos);
 }
});
test('estimated arm response is continuous at side and shoulder transitions',()=>{
 const H=1.659,m=estimateVisualMeasurements({sex:'male',height:170,weight:116,age:40,child:false});
 const ratio=visualRatios(m,170,116,false,true);
 for(const x0 of [.18,.25,.35])for(const yn of [.59,.63,.70,.76,.82]){
  const a=deformPosition(x0,yn*H,.055,0,H,ratio,true);
  const b=deformPosition(x0+.0001,(yn+.0001)*H,.055,0,H,ratio,true);
  assert.ok(Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2])<.002,
   'no sharp seam x='+x0+' y='+yn);
 }
});

test('measured and estimated upper arms deform along the actual shoulder-elbow-wrist axis',()=>{
 const H=1.659,cm=170,kg=105;
 for(const estimated of [false,true]){
  const ratios=visualRatios({arm:49,forearm:35},cm,kg,false,estimated);
  const positions=[
   {name:'shoulder',yn:.795,x:.170,z:.045},
   {name:'upper arm',yn:.745,x:.245,z:.06},
   {name:'elbow',yn:.687,x:.331,z:.055},
   {name:'forearm',yn:.648,x:.395,z:.052},
   {name:'wrist',yn:.612,x:.453,z:.038}
  ];
  for(const p of positions){
   const a=deformPosition(p.x,p.yn*H,p.z,0,H,ratios,estimated);
   assert.ok(a.every(Number.isFinite),p.name);
   assert.ok(Math.abs(a[0]-p.x)<.065,p.name+' centre remains near rig joint');
   assert.ok(Math.abs(a[2]-p.z)<.035,p.name+' radial changes stay bounded');
  }
 }
});
test('left and right elbows and shoulder joints remain symmetric and continuous with new arm axis',()=>{
 const H=1.659,ratios={arm:1.3,forearm:1.25,chest:1.1};
 for(const estimated of [false,true]){
  for(const yn of [.60,.65,.687,.74,.795,.835]){
   for(const x of [.18,.25,.32,.39]){
    const a=deformPosition(x,H*yn,.056,0,H,ratios,estimated);
    const b=deformPosition(x+.0001,H*(yn+.0001),.056,0,H,ratios,estimated);
    const c=deformPosition(-x,H*yn,.056,0,H,ratios,estimated);
    assert.ok(Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2])<.003,
      'no jump around elbow or shoulder '+yn);
    assert.ok(Math.abs(a[0]+c[0])<1e-8 && Math.abs(a[2]-c[2])<1e-8,
      'left and right arms remain symmetric');
   }
  }
 }
});
