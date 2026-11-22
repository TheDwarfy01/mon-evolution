#!/usr/bin/env python3
"""Mon Evolution IMC v1.6.111 — align Profil below Amis and Partages below Version."""
from pathlib import Path
import shutil
root=Path("android/source-1.6.111/app/src/main/assets")
page=root/"index.html"
s=page.read_text(encoding="utf-8")
assert '<script src="header-shortcuts.js"></script>' in s
assert '<script src="status-topbar.js"></script>' in s
assert '<script src="reference-layout.js"></script>' in s
assert s.count("</body></html>")==1
assert "align-header-actions.js" not in s
shutil.copyfile("android/ui/align-header-actions.js",root/"align-header-actions.js")
s=s.replace("</body></html>",'<script src="align-header-actions.js"></script>\n</body></html>')
page.write_text(s,encoding="utf-8")
assert s.count('<script src="align-header-actions.js"></script>')==1
assert s.index('<script src="align-header-actions.js"></script>')>s.index('<script src="status-topbar.js"></script>')
print("Profil aligned with Amis; Partages aligned with Version; UI events retained.")
