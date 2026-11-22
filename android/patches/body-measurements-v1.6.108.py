#!/usr/bin/env python3
"""Integrate opt-in adult body measurements in Mon Évolution IMC 1.6.108.
No migration and no modification to existing profiles, weights or meals. """
from pathlib import Path
import shutil
root=Path("android/source-1.6.108/app/src/main/assets")
html=root/"index.html"
source=html.read_text(encoding="utf-8")
nav='<button data-tab="meals">☷ Repas</button>'
assert source.count(nav)==1, "Meal navigation anchor missing"
source=source.replace(nav,'<button data-tab="body-measurements">📏 Mensurations</button>'+nav)
section='<section id="meals" hidden>'
assert source.count(section)==1, "Meals section anchor missing"
source=source.replace(section,'<section id="body-measurements" hidden></section>\n'+section)
end='</body></html>'
assert source.count(end)==1
assert '<script src="backup-conflict.js"></script>' in source
assert '<script src="avatar-rotate.js"></script>' in source
assert '<script src="local-ai.js"></script>' in source
shutil.copyfile("android/body/measurements-ui.js",root/"measurements-ui.js")
script=(root/"measurements-ui.js").read_text(encoding="utf-8")
for fragment in [
 "bodyMeasurements","bodyAppearance","'Carnation'","'Couleur des cheveux'",
 "'Couleur des yeux'","photoPicked=function(token,photo)",
 "function renderGraph()", "function renderHistory()"
]:
 assert fragment in script,fragment
source=source.replace(end,'<script src="measurements-ui.js"></script>\n'+end)
html.write_text(source,encoding="utf-8")
print("v1.6.108: adult-only measurements + male/female vector mannequins + colors + graph + photos installed")
