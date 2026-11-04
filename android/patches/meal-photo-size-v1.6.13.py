#!/usr/bin/env python3
"""Mon Evolution 1.6.13: medium-size responsive meal photos with aspect ratio preserved."""
from pathlib import Path
root=Path("android/source-1.6.13/app")
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def update(path, old, new):
    source=path.read_text(encoding="utf-8")
    count=source.count(old)
    if count!=1:raise AssertionError(f"{path} expected 1, got {count}: {old[:110]!r}")
    path.write_text(source.replace(old,new),encoding="utf-8")
update(g,"versionCode 28","versionCode 29")
update(g,"versionName '1.6.12'","versionName '1.6.13'")
update(m,'android:versionCode="28" android:versionName="1.6.12"','android:versionCode="29" android:versionName="1.6.13"')
update(j,"MonEvolutionIMC/1.6.12","MonEvolutionIMC/1.6.13")
update(h,'Version installée : <strong>1.6.12</strong>','Version installée : <strong>1.6.13</strong>')
update(h,'const installed="1.6.12";','const installed="1.6.13";')
update(h,"image.style.cssText='display:block;width:100%;max-width:100%;height:auto;max-height:none;object-fit:contain;border-radius:12px;margin:12px 0';",
         "image.style.cssText='display:block;width:auto;max-width:min(100%,320px);height:auto;max-height:320px;object-fit:contain;border-radius:12px;margin:12px 0';")
update(h,"img.style.cssText='display:block;width:100%;max-width:100%;height:auto;max-height:none;border-radius:9px;object-fit:contain;margin:10px 0';",
         "img.style.cssText='display:block;width:auto;max-width:min(100%,320px);height:auto;max-height:320px;border-radius:9px;object-fit:contain;margin:10px 0';")
print("v1.6.13: compact 320px photo previews with original aspect ratio")
