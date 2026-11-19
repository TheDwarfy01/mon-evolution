#!/usr/bin/env python3
"""v1.6.87: realtime pointer-captured pinch zoom; larger plots; adaptive adult labels."""
from pathlib import Path
p=Path('android/source-1.6.87/app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
def one(a,b):
 global s
 n=s.count(a)
 if n!=1:raise AssertionError('Anchor '+str(n)+': '+repr(a[:100]))
 s=s.replace(a,b,1)

one("const width=430,height=330,left=52,right=13,top=23,bottom=44;",
    "const width=430,height=420,left=52,right=13,top=23,bottom=48;")
one("const W=400,H=295,L=48,R=13,T=18,B=43,chartW=W-L-R,chartH=H-T-B;",
    "const W=400,H=375,L=48,R=13,T=18,B=46,chartW=W-L-R,chartH=H-T-B;")

a=s.index('function graph(target,series,opts={}){')
b=s.index(' function weeklyRecords(p){',a)
part=s[a:b]
root="  const root=svg('svg',{viewBox:'0 0 '+width+' '+height,class:'advanced-graph',role:'img','aria-label':opts.title||'Graphique du poids'},target);"
if part.count(root)!=1:raise AssertionError('SVG root not found')
part=part.replace(root,"""  const liveHolder=node('div','advanced-graph-live');
  target.append(liveHolder);
  const root=svg('svg',{viewBox:'0 0 '+width+' '+height,class:'advanced-graph',role:'img','aria-label':opts.title||'Graphique du poids'},liveHolder);""",1)
start=part.index('  // Two-finger pinch: magnify/contract')
end=part.index('  if(graphZoomStore.views.has(graphId)){',start)
new=r'''  // Pointer capture remains on a stable div even when the SVG is redrawn.
  if(!opts.livePinchFrame){
   liveHolder.style.touchAction='pan-y';
   let gesture=null;
   const fingers=new Map();
   const dist=()=>{
    const f=[...fingers.values()];
    return Math.hypot(f[1].x-f[0].x,f[1].y-f[0].y);
   };
   const recalc=g=>{
    const fullX=Math.max(1,originalViewport.xMax-originalViewport.xMin);
    const fullY=Math.max(.1,originalViewport.yMax-originalViewport.yMin);
    const spanX=bounded((currentViewport.xMax-currentViewport.xMin)/g.scale,fullX/14,fullX);
    const spanY=bounded((currentViewport.yMax-currentViewport.yMin)/g.scale,fullY/14,fullY);
    if(spanX>=fullX-.001&&spanY>=fullY-.001){
     graphZoomStore.views.delete(graphId);
    }else{
     const x=bounded(g.worldX-g.fx*spanX,originalViewport.xMin,originalViewport.xMax-spanX);
     const y=bounded(g.worldY-(1-g.fy)*spanY,originalViewport.yMin,originalViewport.yMax-spanY);
     graphZoomStore.views.set(graphId,{xMin:x,xMax:x+spanX,yMin:y,yMax:y+spanY});
    }
   };
   liveHolder.addEventListener('pointerdown',e=>{
    if(e.pointerType!=='touch')return;
    fingers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    try{liveHolder.setPointerCapture(e.pointerId)}catch(err){}
    if(fingers.size!==2)return;
    const box=liveHolder.querySelector('svg')?.getBoundingClientRect();
    if(!box?.width||!box.height)return;
    const f=[...fingers.values()];
    const cx=(f[0].x+f[1].x)/2,cy=(f[0].y+f[1].y)/2;
    const fx=bounded(((cx-box.left)/box.width*width-left)/(width-left-right),0,1);
    const fy=bounded(((cy-box.top)/box.height*height-top)/(height-top-bottom),0,1);
    gesture={active:true,pending:false,scale:1,start:Math.max(10,dist()),fx,fy,
     worldX:currentViewport.xMin+fx*(currentViewport.xMax-currentViewport.xMin),
     worldY:currentViewport.yMax-fy*(currentViewport.yMax-currentViewport.yMin)};
    if(e.cancelable)e.preventDefault();
   });
   liveHolder.addEventListener('pointermove',e=>{
    if(!fingers.has(e.pointerId))return;
    fingers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(!gesture||fingers.size!==2)return;
    const g=gesture;
    g.scale=bounded(dist()/g.start,.15,15);
    recalc(g);
    if(!g.pending){
     g.pending=true;
     requestAnimationFrame(()=>{
      g.pending=false;
      if(!g.active||!liveHolder.isConnected)return;
      const tmp=document.createElement('div');
      graph(tmp,series,{...opts,livePinchFrame:true});
      const fresh=tmp.querySelector('svg.advanced-graph');
      if(fresh)liveHolder.replaceChildren(fresh);
     });
    }
    if(e.cancelable)e.preventDefault();
   });
   const finish=e=>{
    if(!fingers.has(e.pointerId))return;
    fingers.delete(e.pointerId);
    if(!gesture||fingers.size>=2)return;
    const g=gesture;g.active=false;gesture=null;
    if(Math.abs(g.scale-1)<.03)return;
    recalc(g);
    redraw();
    if(e.cancelable)e.preventDefault();
   };
   liveHolder.addEventListener('pointerup',finish);
   liveHolder.addEventListener('pointercancel',finish);
'''
part=part[:start]+new+part[end:]
tail=part.index('  if(graphZoomStore.views.has(graphId)){',start)
close=part.index('  }\n }\n',tail)
part=part[:close+4]+'  }\n'+part[close+4:]
assert "graph(tmp,series,{...opts,livePinchFrame:true})" in part
assert "graph(tmp,series,{...opts,livePinchFrame:true})" in part
assert "liveHolder.setPointerCapture" in part
s=s[:a]+part+s[b:]

# Compact main chart: capture pointers on the fixed parent, then redraw
# the SVG and its numeric axes every animation frame, not on touchend.
a=s.index('function pinchDistance(touches){')
b=s.index('function enrichHistory(){',a)
main=r'''const overviewFingers=new Map();
const overviewDistance=()=>{
 const f=[...overviewFingers.values()];
 return Math.hypot(f[1].x-f[0].x,f[1].y-f[0].y);
};
const updateOverview=g=>{
 const base=g.base,view=g.view;
 const bx=base.xMax-base.xMin,by=base.yMax-base.yMin;
 const sx=clamp((view.xMax-view.xMin)/g.factor,bx/8,bx);
 const sy=clamp((view.yMax-view.yMin)/g.factor,by/8,by);
 const xMin=clamp(g.worldX-g.fx*sx,base.xMin,base.xMax-sx);
 const yMax=clamp(g.worldY+g.fy*sy,base.yMin+sy,base.yMax);
 pinchViewport=Math.abs(sx-bx)<1&&Math.abs(sy-by)<.000001?null:
  {xMin,xMax:xMin+sx,yMin:yMax-sy,yMax};
};
plot.style.touchAction='pan-y';
plot.addEventListener('pointerdown',e=>{
 if(e.pointerType!=='touch')return;
 overviewFingers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 try{plot.setPointerCapture(e.pointerId)}catch(err){}
 if(overviewFingers.size!==2||!frameState)return;
 const svg=plot.querySelector('svg');
 if(!svg)return;
 const r=svg.getBoundingClientRect(),f=frameState;
 if(!r.width||!r.height)return;
 const pts=[...overviewFingers.values()];
 const mx=(pts[0].x+pts[1].x)/2,my=(pts[0].y+pts[1].y)/2;
 const fx=clamp(((mx-r.left)/r.width*f.W-f.L)/(f.W-f.L-f.R),0,1);
 const fy=clamp(((my-r.top)/r.height*f.H-f.T)/(f.H-f.T-f.B),0,1);
 pinchGesture={active:true,pending:false,
  start:Math.max(10,overviewDistance()),factor:1,
  base:{...f.base},view:{...f.view},fx,fy,
  worldX:f.view.xMin+fx*(f.view.xMax-f.view.xMin),
  worldY:f.view.yMax-fy*(f.view.yMax-f.view.yMin)};
 if(e.cancelable)e.preventDefault();
});
plot.addEventListener('pointermove',e=>{
 if(!overviewFingers.has(e.pointerId))return;
 overviewFingers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 if(!pinchGesture||overviewFingers.size!==2)return;
 const g=pinchGesture;
 g.factor=clamp(overviewDistance()/g.start,.2,12);
 updateOverview(g);
 if(!g.pending){
  g.pending=true;
  requestAnimationFrame(()=>{
   g.pending=false;
   if(g.active)draw(plot,lastRenderedSeries,metric,lastRenderedProjection);
  });
 }
 if(e.cancelable)e.preventDefault();
});
const finishOverview=e=>{
 if(!overviewFingers.has(e.pointerId))return;
 overviewFingers.delete(e.pointerId);
 if(!pinchGesture||overviewFingers.size>=2)return;
 const g=pinchGesture;g.active=false;pinchGesture=null;
 if(Math.abs(g.factor-1)>=.03)updateOverview(g);
 draw(plot,lastRenderedSeries,metric,lastRenderedProjection);
 zoomButton.textContent=pinchViewport?'Zoom '+((g.base.xMax-g.base.xMin)/
  Math.max(1,pinchViewport.xMax-pinchViewport.xMin)).toFixed(1).replace('.',',')+'×':'Zoom';
 pointInfo.textContent=pinchViewport?'Zoom en temps réel : dates et valeurs ajustées.':'Touchez un point pour voir la date et la mesure exacte.';
 if(e.cancelable)e.preventDefault();
};
plot.addEventListener('pointerup',finishOverview);
plot.addEventListener('pointercancel',finishOverview);
'''
s=s[:a]+main+s[b:]
assert "svg.style.transform='scale(" not in s

# Resize both graph types; change edit/create sex labels according to birth.
addon=r'''
<style id="mon-evolution-realtime-pinch-v187">
#advanced-weight-panel .advanced-graph,
#advanced-friend-graphs .advanced-graph,
#chart .advanced-graph{width:100%;height:auto;max-height:none!important;transform:none!important;touch-action:pan-y}
#evo-v159-graph .evo-v159-chart svg{
 width:100%;height:auto;max-height:none!important;
 transform:none!important;touch-action:pan-y}
#evo-v159-graph .evo-v159-chart{max-height:none!important;overflow:hidden}
#advanced-weight-panel .advanced-graph-live,
#advanced-friend-graphs .advanced-graph-live,
#chart .advanced-graph-live{touch-action:pan-y;overflow:hidden;width:100%;min-width:0}
</style>
<script>
(function(){
 'use strict';
 const eb=document.getElementById('edit-birth'),es=document.getElementById('edit-sex');
 const nb=document.getElementById('new-birth'),ns=document.getElementById('new-sex');
 const labels=(sex,birth)=>{
  if(!sex||!birth)return;
  const child=window.MonEvolutionChild?.isChildBirth?.(birth.value)===true;
  const male=sex.querySelector('option[value="male"]');
  const female=sex.querySelector('option[value="female"]');
  const unknown=sex.querySelector('option[value="unknown"]');
  if(male)male.textContent=child?'Garçon':'Homme';
  if(female)female.textContent=child?'Fille':'Femme';
  if(unknown)unknown.textContent='Non précisé';
 };
 const update=()=>{labels(es,eb);labels(ns,nb)};
 for(const el of [eb,nb]){
  el?.addEventListener('input',update);
  el?.addEventListener('change',update);
 }
 const previous=render;
 render=function(){const result=previous();update();return result};
 update();
})();
</script>
'''
if s.count('</body></html>')!=1:raise AssertionError('Body end')
s=s.replace('</body></html>',addon+'\n</body></html>',1)
assert 'width=430,height=420' in s
assert 'W=400,H=375' in s
assert "child?'Garçon':'Homme'" in s
assert "child?'Fille':'Femme'" in s
p.write_text(s,encoding='utf-8')
print('PASS 1.6.87: zoom X/Y temps reel, graphes agrandis, sexes adaptes a la naissance')
