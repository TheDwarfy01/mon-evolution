import test from 'node:test';
import assert from 'node:assert/strict';
import {initialView,boundedView,pinchView,gestureDirection,needsRecenter} from './studio-zoom.mjs';
test('pinch zoom is bounded and returning to 100% recenters',()=>{
 const a=[{x:100,y:200},{x:200,y:200}],b=[{x:50,y:200},{x:250,y:200}];
 const v=pinchView(initialView(),a,b,300,400);assert.equal(v.zoom,2);
 assert.equal(pinchView(v,b,a,300,400).zoom,1);
 assert.deepEqual(boundedView(8,50,-50),{zoom:3,x:.8,y:-.8});
 assert.deepEqual(boundedView(.2,4,4),initialView());
});
test('moving two fingers together pans without changing zoom',()=>{
 const a=[{x:100,y:100},{x:200,y:100}],b=[{x:120,y:140},{x:220,y:140}];
 const v=pinchView({zoom:2,x:0,y:0},a,b,300,400);
 assert.equal(v.zoom,2);assert.ok(v.x<0&&v.y>0);
});

test('single finger axis lock and recenter visibility',()=>{
 assert.equal(gestureDirection(2,3),'pending');
 assert.equal(gestureDirection(30,8),'rotate');
 assert.equal(gestureDirection(-30,8),'rotate');
 assert.equal(gestureDirection(6,-30),'scroll');
 assert.equal(gestureDirection(20,20),'scroll');
 assert.equal(needsRecenter(initialView()),false);
 assert.equal(needsRecenter({zoom:2,x:0,y:0}),true);
 assert.equal(needsRecenter({zoom:1.1,x:.02,y:0}),true);
});
