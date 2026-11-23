import test from 'node:test';
import assert from 'node:assert/strict';
import {profileCategory,allowedOutfitsFor} from './profile-rules.mjs';
const now=new Date('2026-11-23T12:00:00Z').getTime();
test('profile sex is authoritative despite stale appearance sex',()=>{
 const m=profileCategory({sex:'male',birthDate:'1986-03-26',bodyAppearance:{model:'female'}},now);
 assert.equal(m.sex,'male');assert.equal(m.kind,'adult_male');
 const f=profileCategory({sex:'female',birthDate:'1991-02-11',bodyAppearance:{model:'male'}},now);
 assert.equal(f.sex,'female');assert.equal(f.kind,'adult_female');
});
test('children are categorized exclusively by their profile sex and birth date',()=>{
 assert.equal(profileCategory({sex:'male',birthDate:'2018-10-01'},now).kind,'child_male');
 assert.equal(profileCategory({sex:'female',birthDate:'2023-04-01'},now).kind,'child_female');
 assert.equal(profileCategory({sex:'female',birthDate:'2000-04-01'},now).kind,'adult_female');
});
test('unknown sex and invalid/missing birth date forbid 3D',()=>{
 for(const sex of ['',null,undefined,'unknown','unspecified','other']){
  assert.equal(profileCategory({sex,birthDate:'2018-04-01'},now),null);
 }
 for(const birthDate of ['',null,undefined,'2026-02-30','2030-01-01','2002-13-02']){
  assert.equal(profileCategory({sex:'male',birthDate},now),null);
 }
});
test('restrict outfits by age and sex, preventing incompatible outfits',()=>{
 assert.deepEqual(allowedOutfitsFor('adult_male'),['classic','summer']);
 assert.deepEqual(allowedOutfitsFor('adult_female'),['classic','summer','skirt']);
 assert.deepEqual(allowedOutfitsFor('child_male'),['classic','summer']);
 assert.deepEqual(allowedOutfitsFor('child_female'),['classic','summer']);
 assert.deepEqual(allowedOutfitsFor('unknown'),[]);
 assert.equal(allowedOutfitsFor('child_male').includes('skirt'),false);
 assert.equal(allowedOutfitsFor('adult_female').includes('shirt'),false);
});
