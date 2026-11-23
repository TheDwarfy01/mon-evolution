import test from 'node:test';
import assert from 'node:assert/strict';
import {hideMaskFor,coveredTriangle,behindOpaqueGarment,BODY_ZONE} from './clothing-coverage.mjs';
test('jeans cover both legs and hips, and shirts cover torso',()=>{
 const jeans=hideMaskFor(['clothing_jeans.glb']);
 assert.notEqual(jeans&BODY_ZONE.legs,0);
 assert.notEqual(jeans&BODY_ZONE.hips,0);
 assert.notEqual(jeans&BODY_ZONE.shorts,0);
 const top=hideMaskFor(['clothing_tshirt.glb']);
 assert.notEqual(top&BODY_ZONE.torso,0);
 assert.notEqual(top&BODY_ZONE.shirt,0);
});
test('two body triangle vertices in covered zone hide ragged seam',()=>{
 const mask=hideMaskFor(['clothing_jeans.glb']);
 assert.equal(coveredTriangle([BODY_ZONE.hips,BODY_ZONE.legs,0],mask),true);
 assert.equal(coveredTriangle([BODY_ZONE.hips,0,0],mask),false);
 assert.equal(coveredTriangle([0,0,0],mask),false);
});
test('opaque clothing hides only anatomically plausible areas',()=>{
 const jeans=['clothing_jeans.glb'];
 assert.equal(behindOpaqueGarment(.42,.13,jeans),true);
 assert.equal(behindOpaqueGarment(.70,.13,jeans),false);
 assert.equal(behindOpaqueGarment(.42,.4,jeans),false);
 assert.equal(behindOpaqueGarment(.55,.12,['clothing_tshirt.glb']),false);
 assert.equal(behindOpaqueGarment(.62,.12,['clothing_tshirt.glb']),true);
 assert.equal(behindOpaqueGarment(.62,.4,['clothing_tshirt.glb']),false);
});
test('no garment means no masked skin; photo/data never affected',()=>{
 assert.equal(hideMaskFor([]),0);
 assert.equal(coveredTriangle([BODY_ZONE.legs,BODY_ZONE.legs,0],0),false);
 assert.equal(behindOpaqueGarment(.4,.1,[]),false);
});
