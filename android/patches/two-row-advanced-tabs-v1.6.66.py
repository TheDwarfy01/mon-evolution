#!/usr/bin/env python3
"""v1.6.66 - Les quatre vues sur une ligne, les deux zooms juste dessous."""
from pathlib import Path
page=Path('android/source-1.6.66/app/src/main/assets/index.html')
src=page.read_text(encoding='utf-8')
def single(before,after):
 global src
 count=src.count(before)
 assert count==1, f'Ancre manquante/ambigue ({count}): {before[:110]}'
 src=src.replace(before,after,1)
single(
 "  controls(target,[['Poids',view==='weight',()=>{view='weight';redraw()}],",
 "  const advancedTabs=controls(target,[['Poids',view==='weight',()=>{view='weight';redraw()}],"
)
single(
 "   ['Références',view==='health',()=>{view='health';redraw()}]]);",
 "   ['Références',view==='health',()=>{view='health';redraw()}]]);\n"
 "  advancedTabs.classList.add('advanced-view-tabs');"
)
single(
 "  target.append(sectionTitle('Évolution du poids'));",
 "  const advancedHeading=sectionTitle('Évolution du poids');"
)
single(
 "  periodRow.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:12px;margin:14px 0 12px;flex-wrap:wrap';",
 "  periodRow.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:14px 0 12px;flex-wrap:nowrap';"
)
single(
 "  periodRow.append(periodTitle,periodButton);\n  target.append(periodRow);",
 "  advancedHeading.style.cssText='margin:0;min-width:0;font-size:18px';\n"
 "  periodButton.setAttribute('title','Période affichée : appuyez pour changer');\n"
 "  periodRow.append(advancedHeading,periodButton);\n"
 "  target.append(periodRow);"
)
single(
 "  zoomRow.style.margin='8px 0 4px';",
 "  zoomRow.classList.add('advanced-zoom-row');\n"
 "  zoomRow.style.margin='9px 0 8px';\n"
 "  target.insertBefore(zoomRow,periodRow);"
)
css="""<style id="mon-evolution-two-rows-166">
#advanced-weight-panel .advanced-controls.advanced-view-tabs,
#advanced-friend-graphs .advanced-controls.advanced-view-tabs{
  display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;
  flex-wrap:nowrap;width:100%;margin:12px 0 5px;
}
#advanced-weight-panel .advanced-view-tabs button,
#advanced-friend-graphs .advanced-view-tabs button{
  min-width:0!important;width:100%!important;min-height:48px!important;
  box-sizing:border-box;white-space:normal;overflow-wrap:anywhere;
  padding:8px 2px!important;font-size:clamp(11px,3.15vw,15px)!important;line-height:1.14;
}
#advanced-weight-panel .advanced-controls.advanced-zoom-row,
#advanced-friend-graphs .advanced-controls.advanced-zoom-row{
  display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:8px;flex-wrap:nowrap;margin:4px 0 10px!important;width:100%;
}
#advanced-weight-panel .advanced-zoom-row button,
#advanced-friend-graphs .advanced-zoom-row button{
  width:100%;height:48px;min-width:0;padding:8px 5px!important;
  font-size:clamp(12px,3.4vw,15px)!important;line-height:1.2;white-space:normal;
}
#advanced-weight-panel .advanced-period-row,
#advanced-friend-graphs .advanced-period-row{gap:8px;margin:12px 0 10px!important}
#advanced-weight-panel .advanced-period-cycle,
#advanced-friend-graphs .advanced-period-cycle{min-width:104px!important;min-height:43px!important}
@media(max-width:340px){
 #advanced-weight-panel .advanced-view-tabs button,
 #advanced-friend-graphs .advanced-view-tabs button{font-size:10.5px!important;letter-spacing:-.025em}
}
</style>
"""
single("</head>",css+"</head>")
assert 'advancedTabs.classList.add' in src
assert "target.insertBefore(zoomRow,periodRow)" in src
assert 'grid-template-columns:repeat(4,minmax(0,1fr))' in src
assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in src
page.write_text(src,encoding='utf-8')
print('OK: 4 onglets sur une ligne, 2 zooms en-dessous, période intégrée au titre')
