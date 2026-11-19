#!/usr/bin/env python3
"""v1.6.78: replace rolling moving average with least-squares trend line of visible weigh-ins."""
from pathlib import Path
page=Path("android/source-1.6.78/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
label="Moyenne glissante des pesées (tendance)"
assert s.count(label)==1, "Missing moving-average option"
s=s.replace(label,"Moyenne des pesées",1)
start=s.index("  if(trend){",s.index(" function primaryGraph(target,p){"))
end=s.index("  const goalPlan=window.MonEvolutionGoal?.get?.(p)||null;",start)
section=s[start:end]
assert "trendPoints" in section and "Tendance (7 jours / 3 pesées)" in section, "Unexpected trend body"
new="""  if(trend){
   // Mean of the measurements belonging to the actually selected period.
   // rangeRows() includes a pre-period anchor for other graphs; exclude it here.
   const cutoff=period==='all'?-Infinity:utc(last.date)-Number(period)*DAY;
   const meanRows=rows.filter(r=>utc(r.date)>=cutoff);
   if(meanRows.length>=2){
    // Régression linéaire de toutes les pesées visibles (moindres carrés).
    // Chaque mesure pèse autant, indépendamment du nombre de jours entre deux pesées.
    const samples=meanRows.map(r=>({x:days(origin,r.date),y:r.weight}));
    const count=samples.length;
    const avgX=samples.reduce((sum,q)=>sum+q.x,0)/count;
    const avgY=samples.reduce((sum,q)=>sum+q.y,0)/count;
    const covariance=samples.reduce((sum,q)=>sum+(q.x-avgX)*(q.y-avgY),0);
    const variance=samples.reduce((sum,q)=>sum+(q.x-avgX)**2,0);
    const slope=variance>0?covariance/variance:0;
    const firstX=samples[0].x,lastX=samples.at(-1).x;
    const line=x=>avgY+slope*(x-avgX);
    series.push({label:'Moyenne des pesées (tendance linéaire)',
     color:colors[2],dashed:true,points:[
      {x:firstX,y:line(firstX)},{x:Math.max(firstX+.001,lastX),y:line(lastX)}
     ]});
   }
  }
"""
s=s[:start]+new+s[end:]
assert "Tendance (7 jours / 3 pesées)" not in s
assert "Moyenne des pesées" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.78: droite de tendance (régression linéaire) sur la période sélectionnée")
