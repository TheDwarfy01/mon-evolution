#!/usr/bin/env python3
"""v1.6.108: move actual Profile and Partagés tabs into the top-right header."""
from pathlib import Path
import shutil
root=Path("android/source-1.6.108/app/src/main/assets")
page=root/"index.html"
source=page.read_text(encoding="utf-8")
assert '<script src="measurements-ui.js"></script>' in source, "Mensurations must be present"
assert 'class="header-greeting"' in source, "Existing header greeting must be present"
assert 'data-tab="profiles"' in source and "sharedNav.dataset.tab='shared'" in source, "Both tabs must exist"
assert 'header-shortcuts.js' not in source
shutil.copyfile("android/ui/header-shortcuts.js",root/"header-shortcuts.js")
source=source.replace("</body></html>",'<script src="header-shortcuts.js"></script>\n</body></html>')
assert source.count('<script src="header-shortcuts.js"></script>')==1
page.write_text(source,encoding="utf-8")
print("v1.6.108: profile/shared original buttons moved top-right; greeting replaced, data unchanged")
