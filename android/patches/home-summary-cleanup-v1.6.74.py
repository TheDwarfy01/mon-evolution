#!/usr/bin/env python3
"""Simplify the home summary without changing saved data or render computations."""
from pathlib import Path

page=Path("android/source-1.6.74/app/src/main/assets/index.html")
source=page.read_text(encoding="utf-8")
assert source.count("</body></html>")==1
for expected in ('id="lost"', 'id="remaining"', 'id="bmi"', 'id="count"', 'id="delta"', 'id="add"'):
    assert expected in source, expected
assert "mon-evolution-summary-cleanup-174" not in source
addon=r'''
<style id="mon-evolution-summary-cleanup-174">
/* Remove the redundant loss pill; keep its DOM ID for existing render code. */
#home .hero #delta{display:none!important}
/* The original four-metric strip remains in the DOM for calculation compatibility. */
#home > .two{display:none!important}
/* Show only the useful balance figures inside the current-weight card. */
#home .hero .summary-balance{margin:9px 0 15px;gap:12px}
#home .hero .summary-balance .tile{min-width:0;margin:0;padding:15px}
#home .hero .summary-balance .tile strong{font-variant-numeric:tabular-nums}
@media(max-width:360px){
  #home .hero .summary-balance{gap:8px}
  #home .hero .summary-balance .tile{padding:12px}
  #home .hero .summary-balance .tile strong{font-size:19px}
}
</style>
<script>
(function(){
  'use strict';
  const hero=document.querySelector('#home .hero');
  const add=document.getElementById('add');
  const lost=document.getElementById('lost')?.closest('.tile');
  const remaining=document.getElementById('remaining')?.closest('.tile');
  if(!hero||!add||!lost||!remaining)return;
  const balance=document.createElement('div');
  balance.className='two summary-balance';
  balance.setAttribute('aria-label','Bilan du poids');
  balance.append(lost,remaining);
  add.before(balance);
})();
</script>
'''
page.write_text(source.replace("</body></html>",addon+"\n</body></html>"),encoding="utf-8")
updated=page.read_text(encoding="utf-8")
assert "mon-evolution-summary-cleanup-174" in updated
assert "balance.append(lost,remaining)" in updated
