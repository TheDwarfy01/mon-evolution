#!/usr/bin/env python3
"""Repair IMC v1.6.111 navigation for shared adult profiles and small screens.
Preserves actual native actions and all existing profile / meal data.
"""
from pathlib import Path
import shutil
root=Path('android/source-1.6.111/app/src/main/assets')
index=root/'index.html'
s=index.read_text(encoding='utf-8')
# Existing read-only shared navigation intercepts ALL tabs before Mensurations
# can handle them, causing the tab to disappear or inadvertently select a local user.
before="""   if(!unifiedCurrent.startsWith('received:'))return;
   e.preventDefault();e.stopImmediatePropagation();
   displayFriendTab(nav.dataset.tab);
"""
after="""   if(!unifiedCurrent.startsWith('received:'))return;
   e.preventDefault();e.stopImmediatePropagation();
   if(nav.dataset.tab==='body-measurements'){
     // Measurements never become editable in shared/received mode.
     window.showSharedBodyMeasurements?.();
     return;
   }
   displayFriendTab(nav.dataset.tab);
"""
assert s.count(before)==1, 'Shared navigation handler has changed'
s=s.replace(before,after)
assert s.count('</body></html>')==1
assert '<script src="measurements-ui.js"></script>' in s
assert '<script src="header-shortcuts.js"></script>' in s
assert 'nav-readable.js' not in s
shutil.copyfile('android/ui/nav-readable.js',root/'nav-readable.js')
assert 'imc-nav-icon' in (root/'nav-readable.js').read_text(encoding='utf-8')
s=s.replace('</body></html>','<script src="nav-readable.js"></script>\n</body></html>')
index.write_text(s,encoding='utf-8')
print('Navigation IMC 1.6.111 restored: Mensurations stays visible for shared profiles (read-only), and nav icons are 22px.')
