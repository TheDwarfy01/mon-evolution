import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS} from './measurement-morph.mjs';
import {anatomicalAnchor,requiredAnatomicalBones} from './landmark-bones.mjs';
const J={
 neck_01:[0,1.36,0],head:[0,1.49,0],
 spine_03:[0,1.15,0],spine_02:[0,1.03,0],spine_01:[0,.97,0],pelvis:[0,.86,0],
 upperarm_l:[.25,1.3,0],lowerarm_l:[.38,1.07,0],hand_l:[.44,.84,0],
 thigh_r:[-.115,.82,0],calf_r:[-.12,.43,0],foot_r:[-.125,.09,0]
};
test('real skeleton provides each of nine measurement zones',()=>{
 assert.equal(REGIONS.length,9);
 for(const r of REGIONS)assert.ok(anatomicalAnchor(r.key,J)?.every(Number.isFinite),r.key);
 assert.ok(requiredAnatomicalBones().includes('lowerarm_l'));
});
test('neck, upper arm and forearm stay between corresponding bones',()=>{
 const neck=anatomicalAnchor('neck',J),arm=anatomicalAnchor('arm',J),fore=anatomicalAnchor('forearm',J);
 assert.ok(neck[1]>1.36&&neck[1]<1.49);
 assert.ok(arm[1]<1.3&&arm[1]>1.07&&arm[0]>.25);
 assert.ok(fore[1]<1.07&&fore[1]>.84&&fore[0]>.38);
});
test('belly is above pelvis; thigh between pelvis and knee, calf between knee and ankle',()=>{
 const bel=anatomicalAnchor('belly',J),thigh=anatomicalAnchor('thigh',J),calf=anatomicalAnchor('calf',J);
 assert.ok(bel[1]>.86&&bel[1]<.97);
 assert.ok(thigh[1]>.43&&thigh[1]<.82);
 assert.ok(calf[1]>.09&&calf[1]<.43);
 assert.ok(thigh[0]<0&&calf[0]<0);
});
test('missing or nonfinite rig data fails safely to legacy anchors',()=>{
 assert.equal(anatomicalAnchor('arm',{}),null);
 assert.equal(anatomicalAnchor('neck',{neck_01:[0,NaN,0],head:[0,2,0]}),null);
});
