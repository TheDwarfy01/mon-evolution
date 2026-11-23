import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS,visualRatios} from './measurement-morph.mjs';
import {markerLocalPosition,declutterMarkerPositions} from './landmark-projection.mjs';
const bounds={minY:0,height:1.75};
test('nine landmarks preserve finite position over a full 3D turn',()=>{
 for(const r of REGIONS){
  let previous=null;
  for(let step=0;step<=180;step++){
   const yaw=step*Math.PI/90;
   const now=markerLocalPosition(r,bounds,{},yaw);
   assert.equal(now.length,3);
   assert.ok(now.every(Number.isFinite),r.key+' non finite');
   if(previous)assert.ok(Math.hypot(...now.map((v,i)=>v-previous[i]))<.04,
    r.key+' jumped across the body');
   previous=now;
  }
 }
});
test('anatomical points adapt to measurement morph and neutral reset',()=>{
 const r=REGIONS.find(x=>x.key==='belly');
 const neutral=markerLocalPosition(r,bounds,{},Math.PI/4);
 const ratios=visualRatios({belly:250},170,75,false);
 const changed=markerLocalPosition(r,bounds,ratios,Math.PI/4);
 assert.notDeepEqual(changed,neutral);
 assert.deepEqual(markerLocalPosition(r,bounds,{},Math.PI/4),neutral);
});
test('front and rear points switch continuously without a ninety-degree flip',()=>{
 for(const r of REGIONS){
  const a=markerLocalPosition(r,bounds,{},Math.PI/2-.0001);
  const b=markerLocalPosition(r,bounds,{},Math.PI/2+.0001);
  assert.ok(Math.hypot(...a.map((v,i)=>v-b[i]))<.002,r.key+' orientation jump');
 }
});
test('no displacement occurs when points are already separated',()=>{
 const data=[{key:'neck',x:120,y:70},{key:'calf',x:140,y:400}];
 const result=declutterMarkerPositions(data,320,500);
 for(let i=0;i<data.length;i++)assert.equal(result[i].x,data[i].x);
});
test('colliding projected points get separated with bounded displacement',()=>{
 for(const [width,height] of [[320,510],[360,650],[700,850]]){
  const data=[
   {key:'waist',x:width*.52,y:height*.51},
   {key:'belly',x:width*.52+1,y:height*.51+1},
   {key:'hips',x:width*.52-1,y:height*.51-1},
   {key:'forearm',x:width*.52+3,y:height*.51+2}
  ];
  const out=declutterMarkerPositions(data,width,height);
  for(const m of out){
   assert.ok(Math.hypot(m.x-m.anchorX,m.y-m.anchorY)<=30.01,m.key+' displaced too far');
   assert.ok(m.x>=14&&m.y>=14&&m.x<=width-14&&m.y<=height-14);
  }
  for(let i=0;i<out.length;i++)for(let j=i+1;j<out.length;j++)
   assert.ok(Math.hypot(out[i].x-out[j].x,out[i].y-out[j].y)>=23,
    out[i].key+' overlaps '+out[j].key);
 }
});
