#!/usr/bin/env python3
"""v1.6.112 — reproduce the approved Mensurations reference design.
Keep a SINGLE photorealistic adult figure and retain one optional color palette
(peau, cheveux, yeux). Do not disturb saved measurements.
"""
from pathlib import Path
import shutil
root=Path("android/source-1.6.112/app/src/main/assets")
page=root/"index.html"
s=page.read_text(encoding="utf-8")
for required in ('<script src="measurements-ui.js"></script>',
                 '<script src="quick-measure.js"></script>',
                 '<script src="photoreal-models.js"></script>',
                 '<script src="status-topbar.js"></script>'):
    assert required in s, required
assert s.count("</body></html>")==1
assert "reference-layout.js" not in s
shutil.copyfile("android/body/reference-layout.js",root/"reference-layout.js")
photo=(root/"photoreal-models.js").read_text(encoding="utf-8")
layout=(root/"reference-layout.js").read_text(encoding="utf-8")
for token in ("recolor(pixels,state)","models-hq-v2.webp","const BASE=","f.arms.some","bm-photo-canvas"):
    assert token in photo,token
for token in ("bm-measure-lines","bm-silhouette-shortcuts","bm-ref-side","bm-palette-header"):
    assert token in layout,token
assert "vectorBtn" not in photo and "bm-mode-selector" not in photo, "Legacy two-mannequin switch must be removed"
s=s.replace("</body></html>",'<script src="reference-layout.js"></script>\n</body></html>')
page.write_text(s,encoding="utf-8")
print("v1.6.112: two high-definition studio models, live skin/hair/eye customization and dotted anatomical guides.")
