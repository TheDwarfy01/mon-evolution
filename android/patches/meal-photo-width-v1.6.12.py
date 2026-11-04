#!/usr/bin/env python3
"""Version 1.6.12: full-width proportional meal photos, personal and shared."""
from pathlib import Path
root=Path("android/source-1.6.12/app")
html=root/"src/main/assets/index.html"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def change(path,old,new):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise AssertionError(f"{path}: {n} occurrences of {old[:90]!r}")
    path.write_text(s.replace(old,new),encoding="utf-8")
change(gradle,"versionCode 27","versionCode 28")
change(gradle,"versionName '1.6.11'","versionName '1.6.12'")
change(manifest,'android:versionCode="27" android:versionName="1.6.11"','android:versionCode="28" android:versionName="1.6.12"')
change(java,"MonEvolutionIMC/1.6.11","MonEvolutionIMC/1.6.12")
change(html,'Version installée : <strong>1.6.11</strong>','Version installée : <strong>1.6.12</strong>')
change(html,'const installed="1.6.11";','const installed="1.6.12";')
change(html,"image.style.cssText='display:block;max-width:100%;max-height:190px;object-fit:contain;border-radius:12px;margin:9px 0';",
"""image.style.cssText='display:block;width:100%;max-width:100%;height:auto;max-height:none;object-fit:contain;border-radius:12px;margin:12px 0';""")
change(html,"img.style.cssText='max-width:100%;max-height:160px;border-radius:9px;object-fit:contain';",
"""img.style.cssText='display:block;width:100%;max-width:100%;height:auto;max-height:none;border-radius:9px;object-fit:contain;margin:10px 0';""")
print("OK v1.6.12: full-width uncropped photos in meals and shared profiles")
