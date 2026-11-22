#!/usr/bin/env python3
"""Add real JPEG profile portrait rotation/mirror to IMC v1.6.112.
Changes only photo pixels on user click; does not modify other profile/meal data.
"""
from pathlib import Path
import shutil

root=Path("android/source-1.6.112/app/src/main/assets")
html=root/"index.html"
source=html.read_text(encoding="utf-8")
anchor="</body></html>"
assert source.count(anchor)==1, "HTML document end is not unique"
assert 'id="avatar-choose"' in source and 'id="avatar-display"' in source
assert '<script src="local-ai.js"></script>' in source, "Install after Gemma integration"
assert 'avatar-rotate.js' not in source
shutil.copyfile("android/ai/avatar-rotate.js",root/"avatar-rotate.js")
script=(root/"avatar-rotate.js").read_text(encoding="utf-8")
assert "target.avatar = result;" in script
assert "originalRender.apply(this,arguments)" in script
assert "jpeg.length < 250000" in script
source=source.replace(anchor,'<script src="avatar-rotate.js"></script>\n'+anchor)
html.write_text(source,encoding="utf-8")
print("Avatar rotation (left, right, mirror) installed for v1.6.112; original profiles and meals intact")
