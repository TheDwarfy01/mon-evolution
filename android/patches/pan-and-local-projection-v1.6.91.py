#!/usr/bin/env python3
"""v1.6.91: fluid two-finger pan, larger charts, goal trajectory clipped to visible window."""
from pathlib import Path

page=Path('android/source-1.6.91/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

def one(old,new,label):
 global s
 n=s.count(old)
 if n!=1:
  raise AssertionError(f'{label}: expected 1 anchor, found {n}: {old[:100]!r}')
 s=s.replace(old,new,1)

# Taller charts on both the detailed and main views; keep full available width.
one('const width=430,height=420,left=52,right=13,top=23,bottom=48;',
    'const width=430,height=490,left=49,right=10,top=23,bottom=48;', 'detailed chart size')
one('const W=400,H=375,L=48,R=13,T=18,B=46,chartW=W-L-R,chartH=H-T-B;',
    'const W=400,H=455,L=44,R=9,T=18,B=48,chartW=W-L-R,chartH=H-T-B;', 'main chart size')

# Advanced charts: preserve gesture midpoint movement as a world-coordinate pan,
# updating live as both fingers move with or without a distance change.
one('const x=bounded(g.worldX-g.fx*spanX,originalViewport.xMin,originalViewport.xMax-spanX);',
    'const x=bounded(g.worldX-g.fx*spanX-(g.panX||0)*spanX,originalViewport.xMin,originalViewport.xMax-spanX);',
    'detailed x pan')
one('const y=bounded(g.worldY-(1-g.fy)*spanY,originalViewport.yMin,originalViewport.yMax-spanY);',
    'const y=bounded(g.worldY-(1-g.fy)*spanY+(g.panY||0)*spanY,originalViewport.yMin,originalViewport.yMax-spanY);',
    'detailed y pan')
one('gesture={active:true,pending:false,scale:1,start:Math.max(10,dist()),fx,fy,',
    '''gesture={active:true,pending:false,scale:1,start:Math.max(10,dist()),fx,fy,
     startMidX:cx,startMidY:cy,panX:0,panY:0,
     pixelW:Math.max(1,box.width*(width-left-right)/width),
     pixelH:Math.max(1,box.height*(height-top-bottom)/height),''',
    'detailed gesture start')
one('''    g.scale=bounded(dist()/g.start,.15,15);
    recalc(g);''',
    '''    g.scale=bounded(dist()/g.start,.15,15);
    const pair=[...fingers.values()];
    const midX=(pair[0].x+pair[1].x)/2,midY=(pair[0].y+pair[1].y)/2;
    g.panX=(midX-g.startMidX)/g.pixelW;
    g.panY=(midY-g.startMidY)/g.pixelH;
    recalc(g);''', 'detailed live pan')

# Compact chart: keep the goal line, but do not zoom out to its far-away
# target date or target weight. Show its local segment in the current viewport.
one('const n=zoom?Math.min(30,project.days):project.days;',
    'const n=Math.min(zoom?30:45,project.days);', 'forecast horizon')

start=s.index('function draw(target,series,kind,project){')
end=s.index('const overviewFingers=new Map();',start)
part=s[start:end]
old=''' const values=pts.map(q=>q.v);
 if(extra)values.push(extra.v);
 if(goalChartVisible){
  const scale=kind==='bmi'?1/(metres*metres):1;
  values.push(scheduledGoal.weight*scale,scheduledGoal.startWeight*scale);
 }
 if(!zoom){
  if(healthState.enabled&&adult)values.push(...[18.5,25,30].map(cut=>kind==='bmi'?cut:cut*metres*metres));
  if(kind==='weight'&&!window.MonEvolutionChild?.isChildBirth?.(p.birthDate)&&Number.isFinite(Number(p.goal)))values.push(Number(p.goal));
 }'''
if part.count(old)!=1:raise AssertionError('Main chart baseline anchors changed')
new=''' // Prioritize real weigh-ins. Only the visible portion of an intermediate
 // target influences the automatic Y scale; remote targets cannot flatten it.
 const observedDays=Math.max(1,(last.t-pts[0].t)/86400000);
 const futureDays=mode==='forecast'?45:Math.min(30,Math.max(7,Math.round(observedDays*.3)));
 const chartRight=Math.max(last.t+86400000,last.t+futureDays*86400000,extra?.t||0);
 const values=pts.map(q=>q.v);
 if(extra)values.push(extra.v);
 if(goalChartVisible){
  const from=ts(scheduledGoal.startDate),to=ts(scheduledGoal.date);
  const visibleStart=Math.max(from,pts[0].t),visibleEnd=Math.min(to,chartRight);
  if(to>from&&visibleEnd>=visibleStart){
   const scale=kind==='bmi'?1/(metres*metres):1;
   for(const date of [visibleStart,visibleEnd]){
    const ratio=(date-from)/(to-from);
    values.push((scheduledGoal.startWeight+ratio*(scheduledGoal.weight-scheduledGoal.startWeight))*scale);
   }
  }
 }'''
part=part.replace(old,new,1)

old=''' const b={xMin:Math.min(pts[0].t,goalChartVisible?ts(scheduledGoal.startDate):Infinity),
  xMax:Math.max(pts[0].t+86400000,extra?.t||last.t,goalChartVisible?ts(scheduledGoal.date):0),
          yMin:Math.max(0,lo-padding),yMax:hi+padding};'''
new=''' const b={xMin:pts[0].t,xMax:chartRight,
          yMin:Math.max(0,lo-padding),yMax:hi+padding};'''
if part.count(old)!=1:raise AssertionError('Main chart axis bounds changed')
part=part.replace(old,new,1)

# Draw only the portion of the planned line contained inside current dates;
# the end marker is kept only when the real target date is in view.
a=part.index(' if(goalChartVisible){\n  const scale=kind=',part.index(' const dataLayer='))
b=part.index("\n if(pts.length>1)dataLayer.append(svgElement('polyline',{" ,a)
goal=part[a:b]
assert 'const begin=ts(scheduledGoal.startDate),finish=ts(scheduledGoal.date);' in goal
assert "stroke:'#f3a4cc'" in goal
goal=goal.replace(
 '  const x0=X(begin),x1=X(finish);\n  const y0=Y(scheduledGoal.startWeight*scale),y1=Y(scheduledGoal.weight*scale);',
 '''  const startDate=Math.max(begin,v.xMin),endDate=Math.min(finish,v.xMax);
  if(finish>begin&&endDate>=startDate){
   const startWeight=scheduledGoal.startWeight+
    (scheduledGoal.weight-scheduledGoal.startWeight)*(startDate-begin)/(finish-begin);
   const endWeight=scheduledGoal.startWeight+
    (scheduledGoal.weight-scheduledGoal.startWeight)*(endDate-begin)/(finish-begin);
   const x0=X(startDate),x1=X(endDate);
   const y0=Y(startWeight*scale),y1=Y(endWeight*scale);''',1)
goal=goal.replace(
 "  const targetPoint=svgElement('circle',{cx:x1,cy:y1,r:5.4,fill:'#f3a4cc'});",
 "  if(finish>=v.xMin&&finish<=v.xMax){\n  const targetPoint=svgElement('circle',{cx:x1,cy:y1,r:5.4,fill:'#f3a4cc'});",1)
goal=goal.replace('  targetPoint.append(targetTip);dataLayer.append(targetPoint);',
                  '  targetPoint.append(targetTip);dataLayer.append(targetPoint);\n  }',1)
assert goal.endswith(' }') and goal.count('if(finish>begin&&endDate>=startDate)')==1
goal=goal[:-2]+'  }\n }'
part=part[:a]+goal+part[b:]
s=s[:start]+part+s[end:]

# The main plot uses stable pointer capture: unlike zoom, dragging two fingers
# does not alter their separation. Use the center displacement in plot pixels.
one('const xMin=clamp(g.worldX-g.fx*sx,base.xMin,base.xMax-sx);',
    'const xMin=clamp(g.worldX-g.fx*sx-(g.panX||0)*sx,base.xMin,base.xMax-sx);',
    'main x pan')
one('const yMax=clamp(g.worldY+g.fy*sy,base.yMin+sy,base.yMax);',
    'const yMax=clamp(g.worldY+g.fy*sy+(g.panY||0)*sy,base.yMin+sy,base.yMax);',
    'main y pan')
one('''pinchGesture={active:true,pending:false,
  start:Math.max(10,overviewDistance()),factor:1,
  base:{...f.base},view:{...f.view},fx,fy,''',
    '''pinchGesture={active:true,pending:false,
  start:Math.max(10,overviewDistance()),factor:1,
  base:{...f.base},view:{...f.view},fx,fy,
  startMidX:mx,startMidY:my,panX:0,panY:0,
  pixelW:Math.max(1,r.width*(f.W-f.L-f.R)/f.W),
  pixelH:Math.max(1,r.height*(f.H-f.T-f.B)/f.H),''',
    'main gesture start')
one(''' g.factor=clamp(overviewDistance()/g.start,.2,12);
 updateOverview(g);''',
    ''' g.factor=clamp(overviewDistance()/g.start,.2,12);
 const fingers=[...overviewFingers.values()];
 const mx=(fingers[0].x+fingers[1].x)/2;
 const my=(fingers[0].y+fingers[1].y)/2;
 g.panX=(mx-g.startMidX)/g.pixelW;
 g.panY=(my-g.startMidY)/g.pixelH;
 updateOverview(g);''',
    'main live pan')
one(' if(Math.abs(g.factor-1)>=.03)updateOverview(g);',
    ' updateOverview(g);', 'main finish pan')
# Help text indicates both supported interactions.
one('Zoomez avec deux doigts : écartez pour resserrer les échelles de dates et de valeurs, rapprochez pour les élargir.',
    'Deux doigts : écartez pour zoomer et faites-les glisser ensemble pour déplacer les dates et les valeurs.',
    'gesture help')
assert 'panX=(mx-g.startMidX)/g.pixelW' in s
assert 'panX=(midX-g.startMidX)/g.pixelW' in s
assert 'xMax:chartRight' in s
assert 'if(finish>begin&&endDate>=startDate)' in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.91: 2-finger pan + live zoom, taller charts, goal clipped, realistic axes')
