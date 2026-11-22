#!/usr/bin/env python3
"""v1.6.109: received portrait rotation, quick measurements, offline photo mode.
Keep owner data read-only and avoid mutating existing profiles or backups.
"""
from pathlib import Path
import shutil
assets=Path("android/source-1.6.109/app/src/main/assets")
page=assets/"index.html"
source=page.read_text(encoding="utf-8")
assert source.count("</body></html>")==1
assert '<script src="measurements-ui.js"></script>' in source
assert '<script src="header-shortcuts.js"></script>' in source
scripts=[
 ("android/ui/received-portrait-rotate.js","received-portrait-rotate.js"),
 ("android/body/quick-measure.js","quick-measure.js"),
 ("android/body/photoreal-models.js","photoreal-models.js"),
]
for input_path,name in scripts:
    assert '<script src="'+name+'"></script>' not in source
    shutil.copyfile(input_path,assets/name)
    assert (assets/name).stat().st_size>1400
# Scripts need all app initializers and prior history callbacks in place.
source=source.replace("</body></html>",
  "\n".join('<script src="'+name+'"></script>' for _,name in scripts)+"\n</body></html>")
page.write_text(source,encoding="utf-8")
for _,name in scripts:
    assert source.count('<script src="'+name+'"></script>')==1
print("v1.6.109 JS: received-portrait rotation, quick measure dialog, photo mannequins")
