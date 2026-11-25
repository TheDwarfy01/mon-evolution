import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('./reference-layout.js',import.meta.url),'utf8');
const start=source.indexOf(' function syncColorMode(){');
const end=source.indexOf(' nav.append(customize);',start);
const state={palette:{hidden:true},classes:new Set(),events:[]};
const button=()=>({attrs:{},setAttribute(k,v){this.attrs[k]=v;}});
const customize=button(),colorToggle=button();
const stage={classList:{toggle(k,v){if(v)state.classes.add(k);else state.classes.delete(k);}},getBoundingClientRect:()=>({top:0,bottom:300})};
vm.runInNewContext(source.slice(start,end),{palette:state.palette,customize,colorToggle,stage,window:{innerHeight:700,dispatchEvent:e=>state.events.push(e.type)},Event:class{constructor(type){this.type=type;}}});
test('open and close restore measurement mode without resetting palette',()=>{
 customize.onclick();assert.equal(state.palette.hidden,false);assert.ok(state.classes.has('bm-color-mode'));assert.equal(colorToggle.attrs['aria-expanded'],'true');
 colorToggle.onclick();assert.equal(state.palette.hidden,true);assert.ok(!state.classes.has('bm-color-mode'));assert.equal(customize.attrs['aria-expanded'],'false');
 assert.deepEqual(state.events,['mon-evolution-color-mode-changed','mon-evolution-color-mode-changed']);
});
