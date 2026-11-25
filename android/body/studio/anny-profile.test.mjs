import test from 'node:test';
import assert from 'node:assert/strict';
import {annySnapshot} from './anny-profile.mjs';
const p={id:'p1',sex:'male',child:false,age:40,height:175,weight:130,skin:'#123456'};
test('adult selection and nine independent regions',()=>{
 const s=annySnapshot(p,'estimated',{values:{belly:150},estimatedKeys:[]});
 assert.equal(s.sex,'male');assert.equal(s.regions.length,9);assert.ok(s.mass>0);
 assert.equal(s.regions[5].value,150);assert.equal(s.skin,'#123456');
 assert.equal(annySnapshot({...p,sex:'female'},'estimated',{values:{}}).sex,'female');
 assert.equal(annySnapshot({...p,child:true},'estimated',{values:{}}),null);
});
test('neutral and estimates never become measurements or double deformation',()=>{
 const src={values:{belly:150},estimatedKeys:['belly']};
 const n=annySnapshot(p,'neutral',{values:{}});
 assert.equal(n.mass,0);assert.ok(n.regions.every(r=>r.local===0&&r.value===null));
 const e=annySnapshot(p,'estimated',src);assert.equal(e.regions[5].local,0);assert.equal(e.regions[5].estimated,true);
 assert.equal(src.values.belly,150);
});
