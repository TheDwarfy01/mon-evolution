import test from 'node:test';
import assert from 'node:assert/strict';
import {recordVisualOverrides,readVisualOverrides,resolveVisualMeasurements} from './visual-overrides.mjs';
const storage=()=>{const data=new Map();return {getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};};
const profile={id:'p1',height:170,weight:85,age:39,sex:'male',child:false,
 measurements:{belly:250,waist:190},records:[
  {date:'2026-11-21',belly:250,waist:190},
  {date:'2026-11-23',belly:110}]};
test('estimated starts with estimates despite implausible historic entries',()=>{
 const out=resolveVisualMeasurements(profile,'estimated',{});
 assert.notEqual(out.values.belly,250);
 assert.ok(out.estimatedKeys.includes('belly'));
});
test('a manually saved belly overrides only belly and removes its approximation sign',()=>{
 const s=storage();
 assert.equal(recordVisualOverrides('p1','2026-11-23',['belly'],s),true);
 const out=resolveVisualMeasurements(profile,'estimated',readVisualOverrides('p1',s));
 assert.equal(out.values.belly,110);
 assert.ok(!out.estimatedKeys.includes('belly'));
 assert.ok(out.estimatedKeys.includes('waist'));
 assert.notEqual(out.values.waist,190);
});
test('mode changes and deletion never turn estimates into recorded observations',()=>{
 const dates={belly:'2026-11-23'};
 const measured=resolveVisualMeasurements(profile,'measured',dates);
 assert.equal(measured.values.belly,250);
 assert.deepEqual(resolveVisualMeasurements(profile,'neutral',dates).values,{});
 const deleted=resolveVisualMeasurements({...profile,records:[profile.records[0]]},'estimated',dates);
 assert.ok(deleted.estimatedKeys.includes('belly'));
 assert.notEqual(deleted.values.belly,110);
 assert.equal(profile.records[1].belly,110);
});
test('manual date reference persists without saving measurements twice',()=>{
 const s=storage();
 assert.ok(recordVisualOverrides('p1','2026-11-23',['waist','belly'],s));
 assert.deepEqual(readVisualOverrides('p1',s),{waist:'2026-11-23',belly:'2026-11-23'});
 assert.equal(recordVisualOverrides('p1','oops',['belly'],s),false);
 assert.equal(recordVisualOverrides('p1','2026-11-23',['badKey'],s),false);
});
