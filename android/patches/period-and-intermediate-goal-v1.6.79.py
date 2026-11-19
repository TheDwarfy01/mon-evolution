#!/usr/bin/env python3
"""v1.6.79: period selection starts at 30 days; show intermediate goal independently from final goal."""
from pathlib import Path

page=Path('android/source-1.6.79/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')
assert s.count('const candidates=[7,14,30,60,90,180,365,730];')==1
s=s.replace('const candidates=[7,14,30,60,90,180,365,730];',
            'const candidates=[30,60,90,180,365,730];',1)
old="""const labels={'7':'7 jours','14':'14 jours','30':'30 jours','60':'60 jours',
   '90':'90 jours','180':'6 mois','365':'1 an','730':'2 ans',all:'Tout'};"""
new="""const labels={'30':'1 mois','60':'2 mois','90':'3 mois',
   '180':'6 mois','365':'1 an','730':'2 ans',all:'Tout'};"""
assert s.count(old)==1, 'Period label definitions not found'
s=s.replace(old,new,1)
a=s.index(' function primaryGraph(target,p){')
b=s.index(' function progressGraph(target,p){',a)
part=s[a:b]
assert part.count('  if(trend){')==1
assert "label:'Objectif'" in part
assert 'intermediateGoalWeight' in s, 'The goal model must be installed before chart patch'
part=part.replace('  if(trend){',
"""  // Final target stays gold; the intermediate target uses a distinct coral line.
  // This visual guide also works when the intermediate target has no target date.
  const intermediateWeight=Number(p.intermediateGoalWeight);
  if(Number.isFinite(intermediateWeight)&&intermediateWeight>=1&&intermediateWeight<=400
     &&Math.abs(intermediateWeight-p.goal)>.05){
   series.push({label:'Objectif intermédiaire · '+fmt1(intermediateWeight)+' kg',
    color:'#ff9f83',dashed:true,thin:false,
    points:[{x:0,y:intermediateWeight},{x:Math.max(1,wEnd),y:intermediateWeight}]});
  }
  if(trend){""",1)
# A dated objective already has a diagonal trajectory. Make the label and color
# explicit, so it cannot be confused with the horizontal final goal line.
assert part.count("label:'Trajectoire de l’objectif daté',color:'#f4d17a'")==1
part=part.replace("label:'Trajectoire de l’objectif daté',color:'#f4d17a'",
                  "label:'Trajectoire vers l’objectif intermédiaire daté',color:'#f3a4cc'",1)
s=s[:a]+part+s[b:]
assert s.count('const candidates=[30,60,90,180,365,730];')==1
assert 'Objectif intermédiaire · ' in s
assert 'Trajectoire vers l’objectif intermédiaire daté' in s
assert 'Objectif' in s
page.write_text(s,encoding='utf-8')
print('PASS: 30 jours minimum, objectif intermédiaire + trajectoire datée distincts')
