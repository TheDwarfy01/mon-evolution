#!/usr/bin/env python3
"""Place existing friends/version live statuses next to the header motto, IMC 1.6.112."""
from pathlib import Path
import shutil
root=Path("android/source-1.6.112/app/src/main/assets")
page=root/"index.html"
s=page.read_text(encoding="utf-8")
assert "<header><div class=\"upper\">TON PARCOURS, À TON RYTHME</div>" in s
assert "id='friends-release-status-row'" in s
assert "id='friends-auto-sync-status'" in s
assert "id='release-auto-check-status'" in s
assert "id='about-info-trigger'" in s
assert s.count('</body></html>')==1
assert 'status-topbar.js' not in s
shutil.copyfile("android/ui/status-topbar.js",root/"status-topbar.js")
s=s.replace('</body></html>','<script src="status-topbar.js"></script>\n</body></html>')
page.write_text(s,encoding="utf-8")
print("v1.6.112: original Amis/Version/Info widgets relocated in compact upper header; callbacks preserved.")
