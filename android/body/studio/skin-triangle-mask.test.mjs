import test from 'node:test';
import assert from 'node:assert/strict';
import {maskIndexedTriangles,touchesExposedArm} from './skin-triangle-mask.mjs';
import {REGIONS,latestMeasurements,visualRatios,deformPosition} from './measurement-morph.mjs';

function attr(rows){return {getComponent(vertex,influence){return rows[vertex]?.[influence]??0;}};}

test('masked skin keeps identical index length and exact GLB material-group boundaries',()=>{
 const original=new Uint16Array([0,1,2,3,4,5,6,7,8,9,10,11]);
 const groups=[{start:0,count:6,materialIndex:0},{start:6,count:6,materialIndex:1}];
 const masked=maskIndexedTriangles(original,(a,b,c,start)=>start===3||start===6);
 assert.deepEqual(Array.from(masked),[0,1,2,3,3,3,6,6,6,9,10,11]);
 assert.equal(masked.length,original.length);
 assert.deepEqual(Array.from(original),[0,1,2,3,4,5,6,7,8,9,10,11],
  'never mutate original indices');
 for(const {start,count} of groups)assert.ok(start+count<=masked.length);
 assert.deepEqual(Array.from(maskIndexedTriangles(original,()=>false)),Array.from(original),
  'changing outfit must be able to restore whole body');
});
test('indexed triangles mask many regions without corrupting subsequent draw offsets',()=>{
 const source=Uint32Array.from({length:30000},(_,i)=>i);
 const masked=maskIndexedTriangles(source,(a,b,c,i)=>i%12===0);
 assert.equal(masked.length,source.length);
 for(let i=0;i<source.length;i+=3){
  if(i%12===0)assert.deepEqual(Array.from(masked.slice(i,i+3)),[i,i,i]);
  else assert.deepEqual(Array.from(masked.slice(i,i+3)),[i,i+1,i+2]);
 }
});
test('protect elbow, forearm, wrist, hand and upper arm triangles from shirt masking',()=>{
 const names=['Spine2','CC_Base_L_Forearm','mixamorig:RightHand','UpperArm.R','CC_Base_L_Thigh'];
 const indices=attr([[0,4,0,0],[1,0,0,0],[2,0,0,0],[3,0,0,0]]);
 const weights=attr([[.90,.10,0,0],[.8,.2,0,0],[.9,.1,0,0],[.9,.1,0,0]]);
 assert.equal(touchesExposedArm([0,1,2],indices,weights,names),true);
 assert.equal(touchesExposedArm([0,0,0],indices,weights,names),false);
 assert.equal(touchesExposedArm([3,3,3],indices,weights,names),true);
 assert.equal(touchesExposedArm([1,2,3],null,null,names),false);
});
test('each of nine changed measurements updates mesh and restoring it reverses the result',()=>{
 const h=175,kg=75,H=1.75;
 for(const region of REGIONS){
  const baseline=h*region.base;
  const profile={bodyMeasurements:[{date:'2026-11-21',[region.key]:baseline*.90},
    {date:'2026-11-22',[region.key]:baseline*1.20}]};
  const first=latestMeasurements({bodyMeasurements:[profile.bodyMeasurements[0]]});
  const newest=latestMeasurements(profile);
  assert.notEqual(first[region.key],newest[region.key],region.key);
  const x=region.x*H/1.75, y=region.y*H, z=region.z*H/1.75;
  const before=deformPosition(x,y,z,0,H,visualRatios(first,h,kg));
  const after=deformPosition(x,y,z,0,H,visualRatios(newest,h,kg));
  const delta=Math.hypot(after[0]-before[0],after[2]-before[2]);
  assert.ok(delta>0.0002,region.key+' not visually updated by new measure');
  assert.deepEqual(deformPosition(x,y,z,0,H,{}),[x,y,z],
   region.key+' reset must restore original vertex');
 }
});
test('circumference morph is continuous through former hard arm/leg axis cutoffs',()=>{
 const height=1.75;
 const ratios={arm:1.22,forearm:1.2,hips:1.2,thigh:1.18};
 for(const y of [.35,.45,.51,.55,.65,.7,.8]){
  const x0=height*(.16+.08*.7),eps=1e-5,z=.12;
  const a=deformPosition(x0-eps,y*height,z,0,height,ratios);
  const b=deformPosition(x0+eps,y*height,z,0,height,ratios);
  assert.ok(a.every(Number.isFinite)&&b.every(Number.isFinite));
  assert.ok(Math.abs(a[0]-b[0])<.001,
   'morph jump near seam at relative height '+y);
 }
});
test('invalid geometry and non-protected triangles fail safe',()=>{
 assert.throws(()=>maskIndexedTriangles(Uint16Array.from([0,1]),()=>true),TypeError);
 assert.equal(touchesExposedArm([0],attr([[0,0,0,0]]),attr([[1,0,0,0]]),['Spine']),false);
});
