#!/usr/bin/env python3
"""v1.6.76: replace moving trend by arithmetic mean of the visible weigh-ins."""
from pathlib import Path
page=Path("android/source-1.6.76/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
label="Moyenne glissante des pesées (tendance)"
assert s.count(label)==1, "Missing moving-average option"
s=s.replace(label,"Moyenne des pesées",1)
start=s.index("  if(trend){",s.index(" function primaryGraph(target,p){"))
end=s.index("  if(referenceBand){",start)
section=s[start:end]
assert "trendPoints" in section and "Tendance (7 jours / 3 pesées)" in section, "Unexpected trend body"
new="""  if(trend){
   // Mean of the measurements belonging to the actually selected period.
   // rangeRows() includes a pre-period anchor for other graphs; exclude it here.
   const cutoff=period==='all'?-Infinity:utc(last.date)-Number(period)*DAY;
   const meanRows=rows.filter(r=>utc(r.date)>=cutoff);
   if(meanRows.length){
    const mean=meanRows.reduce((sum,r)=>sum+r.weight,0)/meanRows.length;
    const firstX=days(origin,meanRows[0].date),lastX=days(origin,meanRows.at(-1).date);
    series.push({label:'Moyenne des pesées · '+fmt1(mean)+' kg',
     color:colors[2],dashed:true,points:[
      {x:firstX,y:mean},{x:Math.max(firstX+.001,lastX),y:mean}
     ]});
   }
  }
"""
s=s[:start]+new+s[end:]
assert "Tendance (7 jours / 3 pesées)" not in s
assert "Moyenne des pesées" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.76: moyenne arithmétique sur la période sélectionnée")
