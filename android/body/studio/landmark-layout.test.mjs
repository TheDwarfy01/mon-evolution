import test from 'node:test';
import assert from 'node:assert/strict';
import {REGIONS} from './measurement-morph.mjs';
import {layoutLandmarkCallouts} from './landmark-layout.mjs';
function anchors(w,h){
 return REGIONS.map(r=>({key:r.key,side:r.x<0?'left':'right',x:w*.5+r.x*w*.65,
  y:(1-r.y)*h}));
}
function assertLayout(w,h){
 const output=layoutLandmarkCallouts(anchors(w,h),w,h,{labelWidth:w<330?91:103,labelHeight:34,gap:6});
 assert.equal(output.length,9);
 for(const p of output){
  assert.ok(p.left>=0&&p.top>=0&&p.left+p.width<=w+1&&p.top+p.height<=h+1,
   p.key+' out of bounds');
  assert.ok(Number.isFinite(p.connectorX)&&Number.isFinite(p.connectorY));
 }
 for(const side of ['left','right']){
  const sorted=output.filter(p=>p.side===side).sort((a,b)=>a.top-b.top);
  for(let i=1;i<sorted.length;i++)
   assert.ok(sorted[i].top>=sorted[i-1].top+sorted[i-1].height-0.1,
    side+' labels overlap: '+sorted[i-1].key+' '+sorted[i].key);
 }
}
test('always visible labels avoid collision on Galaxy/compact and tablet dimensions',()=>{
 for(const [w,h] of [[300,525],[345,565],[390,595],[700,650]])assertLayout(w,h);
});
test('callout labels maintain a stable leader position while body rotates',()=>{
 const front=layoutLandmarkCallouts(anchors(335,565),335,565);
 const back=layoutLandmarkCallouts(anchors(335,565).map(p=>({...p,x:335-p.x})),335,565);
 assert.equal(front.length,9);
 assert.equal(back.length,9);
 for(const layout of [front,back])
  assert.deepEqual(new Set(layout.map(item=>item.key)),new Set(REGIONS.map(r=>r.key)));
});
