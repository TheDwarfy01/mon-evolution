import test from 'node:test';
import assert from 'node:assert/strict';
import {estimatedThighIntensity,softenInnerThigh} from './thigh-fill.mjs';
const h=1.75,y=.32*h,x=.063*h;
test('estimated heavier adult gets moderate symmetric upper-inner thigh fill',()=>{
 const i=estimatedThighIntensity(170,87);
 assert.ok(i>0);
 const a=softenInnerThigh(x,y,.11,0,h,i),b=softenInnerThigh(-x,y,.11,0,h,i);
 assert.ok(a[0]>h*.01&&a[0]<x);assert.ok(b[0]<0);assert.ok(Math.abs(a[0]+b[0])<1e-9);
});
test('neutral, measured, children, outer thighs and knees remain unchanged',()=>{
 assert.equal(estimatedThighIntensity(130,34,true),0);
 assert.deepEqual(softenInnerThigh(x,y,.1,0,h,0),[x,y,.1]);
 assert.deepEqual(softenInnerThigh(x,.61*h,.1,0,h,1),[x,.61*h,.1]);
 assert.deepEqual(softenInnerThigh(.25*h,y,.1,0,h,1),[.25*h,y,.1]);
});
test('no gap inversion and no modification to bone-height or depth',()=>{
 for(let j=0;j<200;j++){
  const x=(.010+j*.001)*h,v=softenInnerThigh(x,y,.12,0,h,1);
  assert.ok(v.every(Number.isFinite));
  assert.ok(v[0]>=h*.010-1e-8&&v[0]<=x+1e-8&&x-v[0]<h*.02);
  assert.equal(v[1],y);assert.equal(v[2],.12);
 }
});
