#!/usr/bin/env python3
"""Mon Évolution 1.6.67 : bouton de période cyclique, police de boutons plus lisible, axe pertinent."""
from pathlib import Path
page=Path("android/source-1.6.67/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
def one(before,after):
 global s
 n=s.count(before)
 if n!=1: raise AssertionError(f"Ancre attendue une fois, trouvée {n}: {before[:105]}")
 s=s.replace(before,after,1)

one("""  if(periods.length>1){
   stepper(target,'Période affichée',labels[period]||'Tout',
    ()=>{period=periods[Math.max(0,index-1)];advancedPinch=1;redraw()},
    ()=>{period=periods[Math.min(periods.length-1,index+1)];advancedPinch=1;redraw()},
    index<=0,index>=periods.length-1);
  }else target.append(node('p','advanced-help','Tout l’historique est affiché : davantage de périodes seront proposées au fil des pesées.'));""",
"""  // Appui successif : 7 jours → 14 jours → 30 jours → … → Tout, selon les pesées.
  const periodRow=node('div','advanced-period-row');
  periodRow.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:12px;margin:14px 0 12px;flex-wrap:wrap';
  const periodTitle=node('span','','Période affichée');
  periodTitle.style.cssText='color:#cde6ef;font-size:14px;font-weight:650';
  const periodButton=button((labels[period]||'Tout')+' ↻',true,()=>{
   period=periods[(index+1)%periods.length];
   advancedPinch=1;
   redraw();
  });
  periodButton.className='advanced-period-cycle';
  periodButton.style.cssText='min-width:122px;min-height:46px;padding:10px 16px;border:1px solid #80e3d1;border-radius:12px;background:#28685e;color:#f4fffc;font-weight:650;white-space:nowrap';
  periodButton.setAttribute('aria-label','Période affichée : '+(labels[period]||'Tout')+'. Appuyer de nouveau pour changer de période.');
  periodRow.append(periodTitle,periodButton);
  target.append(periodRow);
  if(periods.length===1){
   const hint=node('p','advanced-help','Toute la période disponible est affichée. De nouvelles durées apparaîtront au fil des pesées.');
   hint.style.margin='0 0 10px';
   target.append(hint);
  }""")

# Le mode Tout ne doit pas étirer l'axe des X jusqu'à la date future des projections :
# cadrage sur les pesées, prolongement modéré de la tendance dans le graphe.
one("""  const maxWindow=windowSize===null?undefined:wEnd+Math.min(21,windowSize/4);""",
"""  const maxWindow=windowSize===null
    ?wEnd+Math.max(3,Math.min(7,wEnd/4))
    :wEnd+Math.min(21,windowSize/4);""")

# Amplifie la lisibilité de TOUS les boutons usuels, sans étirer la barre de navigation.
# Les boutons +/- restants sur les repères numériques gardent leur symbole grand.
style="""<style id="mon-evolution-readable-buttons-165">
button{font-size:15px!important}
header .nav button{font-size:13px!important}
#advanced-weight-panel button,#advanced-friend-graphs button{font-size:15px!important}
#advanced-weight-panel .advanced-stepper button,#advanced-friend-graphs .advanced-stepper button{font-size:23px!important}
#evo-v159-graph .evo-v159-modes button,
#evo-v159-graph .evo-v160-tools button{font-size:clamp(13px,3.6vw,15px)!important}
#advanced-weight-panel .advanced-controls button,#advanced-friend-graphs .advanced-controls button{
  min-height:43px;padding:10px 12px!important;line-height:1.25
}
#advanced-weight-panel .advanced-period-cycle,#advanced-friend-graphs .advanced-period-cycle{
  font-size:15px!important
}
@media(max-width:370px){
  #evo-v159-graph .evo-v159-modes button,
  #evo-v159-graph .evo-v160-tools button{font-size:13px!important}
}
</style>
"""
one("</head>",style+"</head>")
assert "periodButton=button(" in s
assert "stepper(target,'Période affichée'" not in s
assert "advanced-period-cycle" in s
assert "wEnd+Math.max(3,Math.min(7,wEnd/4))" in s
page.write_text(s,encoding="utf-8")
print("PASS : période cyclique, police 13–15px et projection hors cadrage limitée")
