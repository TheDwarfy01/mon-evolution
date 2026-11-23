import test from 'node:test';
import assert from 'node:assert/strict';
import {studioVisibilityKey,isStudioEnabled,setStudioEnabled} from './visibility-preference.mjs';
function storage(){
 const map=new Map();
 return {getItem:k=>map.has(k)?map.get(k):null,setItem:(k,v)=>map.set(k,v)};
}
test('visibility persists when Studio reopens with the same profile',()=>{
 const shared=storage();
 assert.equal(isStudioEnabled('mario',shared),false);
 assert.equal(setStudioEnabled('mario',true,shared),true);
 assert.equal(isStudioEnabled('mario',shared),true);
 assert.equal(isStudioEnabled('mia',shared),false);
 // A new runtime instance reads the same storage just as an APK relaunch does.
 assert.equal(isStudioEnabled('mario',shared),true);
 assert.equal(setStudioEnabled('mario',false,shared),true);
 assert.equal(isStudioEnabled('mario',shared),false);
});
test('unknown profile does not implicitly enable the 3D viewer',()=>{
 const s=storage();assert.equal(studioVisibilityKey(''),null);
 assert.equal(isStudioEnabled(undefined,s),false);
 assert.equal(setStudioEnabled('',true,s),false);
});
test('denied storage access degrades safely to manual activation',()=>{
 const denied={getItem(){throw Error('Denied')},setItem(){throw Error('Denied')}};
 assert.equal(isStudioEnabled('demo',denied),false);
 assert.equal(setStudioEnabled('demo',true,denied),false);
});
