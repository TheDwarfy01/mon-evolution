#!/usr/bin/env python3
"""v1.6.74: remove duplicate advanced stats, report current-month loss, and default graphs to Tout."""
from pathlib import Path

page=Path("android/source-1.6.74/app/src/main/assets/index.html")
source=page.read_text(encoding="utf-8")

def replace_once(old,new):
 global source
 count=source.count(old)
 if count!=1:
  raise AssertionError(f"Expected one anchor, found {count}: {old[:100]!r}")
 source=source.replace(old,new,1)

# Keep the stat calculations and DOM nodes for compatibility, hide only the old card.
# Its PDF export controls are already moved into #summary-pdf-reports by the existing code.
replace_once(
 "let mode='recent',metric='weight',zoom=true,periodChoice='month';",
 "let mode='recent',metric='weight',zoom=true,periodChoice='all';"
)

# Same current-calendar-month measurement as the previous 'Évolution du mois' indicator.
# A negative number is a weight loss, a positive number a gain; no extrapolation.
replace_once(
 " tile('Restant',fmt(Math.max(0,last.weight-p.goal))+' kg');",
 """ const monthRows=r.filter(x=>x.date<=dateNow()&&x.date.startsWith(dateNow().slice(0,7)));
 const monthDelta=monthRows.length>=2?monthRows.at(-1).weight-monthRows[0].weight:null;
 const monthText=monthDelta===null?'—':(monthDelta>0?'+':'')+fmt(monthDelta)+' kg';
 tile('Perte par mois',monthText);"""
)

assert source.count('</body></html>')==1
addon=r"""
<style id="mon-evolution-summary-simplification-174">
/* The original advanced statistics card remains in the DOM for existing metrics. */
#home .legacy-advanced-stats{display:none!important}
</style>
<script>
(function(){
 'use strict';
 const advanced=document.getElementById('average-seven')?.closest('.card');
 if(advanced)advanced.classList.add('legacy-advanced-stats');
})();
</script>
"""
source=source.replace('</body></html>',addon+'\n</body></html>')
assert "tile('Perte par mois',monthText);" in source
assert "periodChoice='all'" in source
assert "legacy-advanced-stats" in source
page.write_text(source,encoding="utf-8")
print("OK 1.6.74: statistiques doublon supprimées, perte mensuelle, vue Tout")
