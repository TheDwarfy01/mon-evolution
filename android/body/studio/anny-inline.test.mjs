import test from 'node:test';
import assert from 'node:assert/strict';
import {ANNY_ANCHORS,annyWeights,visualIndex} from './anny-inline.mjs';
import {REGIONS} from './measurement-morph.mjs';
const snap={mass:.8,regions:REGIONS.map(r=>({local:r.key==='belly'?1:r.key==='arm'?-.5:0}))};
test('same 20 target formula as validated native Anny viewer',()=>{
 const v=annyWeights(snap);assert.equal(v.length,20);assert.equal(v[18],.8);
 assert.equal(v[5],.5);assert.ok(v[10]>.3&&v[10]<.5);
 assert.ok(v.every(x=>Number.isFinite(x)&&x>=0&&x<=1));
});
test('neutral and weight limits',()=>{
 assert.deepEqual(annyWeights({mass:0,regions:[]}),Array(20).fill(0));
 assert.equal(visualIndex(-1),65);assert.equal(visualIndex(0),100);assert.equal(visualIndex(1),200);
 assert.equal(annyWeights({mass:-10,regions:[]})[19],1);
});
test('both meshes have all nine real front/back anchors',()=>{
 for(const sex of ['male','female'])for(const r of REGIONS){
  const ids=ANNY_ANCHORS[sex][r.key];assert.equal(ids.length,2);
  assert.ok(ids.every(i=>Number.isInteger(i)&&i>=0&&i<13718));
 }
});
