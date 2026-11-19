#!/usr/bin/env python3
"""v1.6.84: draw the final gold goal across the entire visible chart period."""
from pathlib import Path
path=Path('android/source-1.6.84/app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')
a=s.index(" function primaryGraph(target,p){")
b=s.index(" function progressGraph(target,p){",a)
part=s[a:b]
before="""  graph(target,series,{title:'Poids réel, tendance, objectif, repère et projection',xMin:minWindow,xMax:maxWindow,yMode:advancedZoom,touchZoom:true});"""
after="""  // The horizontal final goal is an ongoing reference, not a dated segment.
  // Extend it to the exact displayed x-axis limits, including future dates
  // added by the intermediate dated objective or the forecast.
  const finalGoalLine=series.find(item=>item.label==='Objectif');
  if(finalGoalLine){
   const from=Number.isFinite(minWindow)?minWindow:0;
   const through=Number.isFinite(maxWindow)?Math.max(from+1,maxWindow):Math.max(from+1,wEnd);
   finalGoalLine.points=[{x:from,y:p.goal},{x:through,y:p.goal}];
  }
  graph(target,series,{title:'Poids réel, tendance, objectif, repère et projection',xMin:minWindow,xMax:maxWindow,yMode:advancedZoom,touchZoom:true});"""
assert part.count(before)==1,"Chart anchor not unique"
part=part.replace(before,after,1)
assert "Trajectoire de l’objectif intermédiaire" in part
assert "finalGoalLine.points=[{x:from,y:p.goal},{x:through,y:p.goal}]" in part
s=s[:a]+part+s[b:]
path.write_text(s,encoding='utf-8')
print('PASS v1.6.84: full-width horizontal adult final goal, dated segment unchanged')
