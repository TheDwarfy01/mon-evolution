#!/usr/bin/env python3
"""v1.6.85: native two-finger zoom of date and value axes on ALL SVG charts."""
from pathlib import Path
page=Path('android/source-1.6.85/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

start=s.index('function graph(target,series,opts={}){')
stop=s.index(' function weeklyRecords(p){',start)
part=s[start:stop]
assert part.count('  if(opts.touchZoom){')==2, 'Previous legacy graph zoom handler changed'
# The legacy handler zoomed only the latest datapoints and used a shared zoom
# factor across unrelated graphs. Replaced with viewport zoom per graph.
part=part.replace('  if(opts.touchZoom){','  if(false&&opts.touchZoom){')

origin='  const padY=(maxY-minY)*.09;minY-=padY;maxY+=padY;'
viewport=r'''  const padY=(maxY-minY)*.09;minY-=padY;maxY+=padY;
  // Record bounds of this chart before applying its stored zoom. Both axes
  // subsequently use the exact same ranges for axis labels and plotted data.
  const graphZoomStore=window.MonEvolutionGraphZoom||
   (window.MonEvolutionGraphZoom={views:new Map()});
  const graphId=(typeof unifiedCurrent==='string'?unifiedCurrent:'local')+'|'+
   (typeof view==='string'?view:'weight')+'|'+(opts.title||'graph');
  const originalViewport={xMin:minX,xMax:maxX,yMin:minY,yMax:maxY};
  const bounded=(v,low,high)=>Math.max(low,Math.min(high,v));
  const requested=graphZoomStore.views.get(graphId);
  if(requested){
   const totalX=Math.max(1,originalViewport.xMax-originalViewport.xMin);
   const totalY=Math.max(.1,originalViewport.yMax-originalViewport.yMin);
   const spanX=bounded(requested.xMax-requested.xMin,totalX/14,totalX);
   const spanY=bounded(requested.yMax-requested.yMin,totalY/14,totalY);
   minX=bounded(requested.xMin,originalViewport.xMin,originalViewport.xMax-spanX);
   maxX=minX+spanX;
   minY=bounded(requested.yMin,originalViewport.yMin,originalViewport.yMax-spanY);
   maxY=minY+spanY;
   if(spanX>=totalX-.001&&spanY>=totalY-.001){
    graphZoomStore.views.delete(graphId);
    minX=originalViewport.xMin;maxX=originalViewport.xMax;
    minY=originalViewport.yMin;maxY=originalViewport.yMax;
   }
  }
  const currentViewport={xMin:minX,xMax:maxX,yMin:minY,yMax:maxY};'''
assert part.count(origin)==1,'Graph viewport anchor moved'
part=part.replace(origin,viewport,1)

# Attach handlers to the SVG itself. One finger continues to scroll the page.
# Two fingers preview visually, then redraw chart with real X/Y axes after
# release. A different panel has its own independent zoom and reset button.
endmark='\n }\n'
assert part.endswith(endmark),'Graph closing brace unexpected'
handlers=r'''  // Two-finger pinch: magnify/contract the visible date and weight/IMC/height
  // bounds, anchored to the midpoint between the fingers.
  root.style.touchAction='pan-y';
  root.style.userSelect='none';
  let graphGesture=null;
  const distance=touches=>Math.hypot(touches[1].clientX-touches[0].clientX,
   touches[1].clientY-touches[0].clientY);
  root.addEventListener('touchstart',event=>{
   if(event.touches.length!==2)return;
   const r=root.getBoundingClientRect();
   if(!r.width||!r.height)return;
   const cx=(event.touches[0].clientX+event.touches[1].clientX)/2;
   const cy=(event.touches[0].clientY+event.touches[1].clientY)/2;
   const fx=bounded(((cx-r.left)/r.width*width-left)/(width-left-right),0,1);
   const fy=bounded(((cy-r.top)/r.height*height-top)/(height-top-bottom),0,1);
   graphGesture={
    distance:Math.max(10,distance(event.touches)),
    scale:1,fx,fy,
    centerX:bounded((cx-r.left)/r.width,0,1),
    centerY:bounded((cy-r.top)/r.height,0,1),
    worldX:currentViewport.xMin+fx*(currentViewport.xMax-currentViewport.xMin),
    worldY:currentViewport.yMax-fy*(currentViewport.yMax-currentViewport.yMin)
   };
   if(event.cancelable)event.preventDefault();
  },{passive:false});
  root.addEventListener('touchmove',event=>{
   if(!graphGesture||event.touches.length!==2)return;
   const g=graphGesture;
   g.scale=bounded(distance(event.touches)/g.distance,.15,15);
   const preview=bounded(g.scale,.5,2.5);
   root.style.transformOrigin=(g.centerX*100)+'% '+(g.centerY*100)+'%';
   root.style.transform='scale('+preview+')';
   if(event.cancelable)event.preventDefault();
  },{passive:false});
  const applyGraphPinch=event=>{
   if(!graphGesture||(event.touches&&event.touches.length>=2))return;
   const g=graphGesture;graphGesture=null;root.style.transform='';
   if(Math.abs(g.scale-1)<.03)return;
   const fullX=Math.max(1,originalViewport.xMax-originalViewport.xMin);
   const fullY=Math.max(.1,originalViewport.yMax-originalViewport.yMin);
   const spanX=bounded((currentViewport.xMax-currentViewport.xMin)/g.scale,fullX/14,fullX);
   const spanY=bounded((currentViewport.yMax-currentViewport.yMin)/g.scale,fullY/14,fullY);
   if(spanX>=fullX-.001&&spanY>=fullY-.001){
    graphZoomStore.views.delete(graphId);
   }else{
    const newX=bounded(g.worldX-g.fx*spanX,originalViewport.xMin,originalViewport.xMax-spanX);
    const newY=bounded(g.worldY-(1-g.fy)*spanY,originalViewport.yMin,originalViewport.yMax-spanY);
    graphZoomStore.views.set(graphId,{xMin:newX,xMax:newX+spanX,yMin:newY,yMax:newY+spanY});
   }
   redraw();
   if(event.cancelable)event.preventDefault();
  };
  root.addEventListener('touchend',applyGraphPinch,{passive:false});
  root.addEventListener('touchcancel',applyGraphPinch,{passive:false});
  if(graphZoomStore.views.has(graphId)){
   const totalX=originalViewport.xMax-originalViewport.xMin;
   const factor=totalX/Math.max(1,currentViewport.xMax-currentViewport.xMin);
   const reset=button('↺ Zoom '+factor.toFixed(1).replace('.',',')+'× · Réinitialiser',false,()=>{
    graphZoomStore.views.delete(graphId);redraw();
   });
   reset.className='advanced-pinch-reset';
   reset.style.cssText='display:block;margin:10px 0;padding:8px 13px;min-height:38px;border:1px solid #78cabb;border-radius:11px;color:#e7fff9;background:#215047;font-size:12px';
   target.append(reset);
  }
'''
part=part[:-len(endmark)]+'\n'+handlers+' }\n'
assert part.count("graphZoomStore.views.set(graphId")==1
assert part.count("root.addEventListener('touchend',applyGraphPinch")==1
assert part.count("  if(false&&opts.touchZoom){")==2
s=s[:start]+part+s[stop:]

# The compact front-page chart already supports X/Y zoom. A more actionable
# instruction helps users discover that the axes (not merely the SVG) change.
old="zoomHelp.textContent='Écartez deux doigts pour agrandir, rapprochez-les pour réduire.';"
new="zoomHelp.textContent='Zoomez avec deux doigts : écartez pour resserrer les échelles de dates et de valeurs, rapprochez pour les élargir.';"
if s.count(old)!=1:raise AssertionError('Front chart gesture help not found')
s=s.replace(old,new,1)

# The main advanced graph previously advertised pinch zoom only in its section.
# The new handler also applies to pediatric curves, comparisons, monthly charts,
# adult reference charts and other plots using graph().
style=r'''
<style id="mon-evolution-global-pinch-v185">
#advanced-weight-panel .advanced-graph,
#advanced-friend-graphs .advanced-graph,
#chart .advanced-graph{touch-action:pan-y;user-select:none;transform-origin:center center}
#chart .advanced-pinch-reset{width:auto;max-width:100%;white-space:normal}
</style>
'''
assert s.count('</head>')==1
s=s.replace('</head>',style+'</head>',1)
assert 'mon-evolution-global-pinch-v185' in s
assert "Zoom '+factor.toFixed(1)" in s
assert 'currentViewport.xMax-currentViewport.xMin' in s
assert 'currentViewport.yMax-currentViewport.yMin' in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.85: zoom tactile X/Y par graphe, repères recalculés, réinitialisation')
