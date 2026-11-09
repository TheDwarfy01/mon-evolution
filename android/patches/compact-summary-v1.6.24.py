#!/usr/bin/env python3
"""v1.6.24: compact summary, single portrait chooser and friendly header."""
from pathlib import Path
root=Path("android/source-1.6.24/app")
h=root/"src/main/assets/index.html"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1:raise AssertionError(f"{path}: {n} occurrences for {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 39","versionCode 40")
R(g,"versionName '1.6.23'","versionName '1.6.24'")
R(m,'android:versionCode="39" android:versionName="1.6.23"','android:versionCode="40" android:versionName="1.6.24"')
R(j,"MonEvolutionIMC/1.6.23","MonEvolutionIMC/1.6.24")
R(h,'Version installée : <strong>1.6.23</strong>','Version installée : <strong>1.6.24</strong>')
R(h,'const installed="1.6.23";','const installed="1.6.24";')
# Preserve profile name in DOM for existing render() and other scripts.
R(h,'<h1>Mon Évolution ✦</h1>','<div class="brand-hello"><h1>Mon Évolution ✦</h1><span class="header-greeting">Bonjour 👋</span></div>')
# Preserve home date and existing functionality; only hide redundant name & portrait.
css=r"""
<style>
/* Compact home only: other tabs and shared read-only views stay unchanged. */
.brand-hello{display:flex;align-items:center;justify-content:space-between;gap:10px}
.brand-hello h1{font-size:23px;line-height:1.12;margin:0;white-space:nowrap;letter-spacing:-.03em}
.header-greeting{font-size:14px;color:#e8fbf8;font-weight:600;white-space:nowrap}
header{padding:13px 14px 0}
header .upper{font-size:9px;letter-spacing:.12em;margin-bottom:4px}
header .profile-global{margin-top:8px!important}
#visual-profile-picker{padding:5px 0 7px;gap:10px;min-height:0}
.profile-portrait-choice{min-width:65px;max-width:77px;padding:2px}
.profile-portrait-circle{width:46px;height:46px;margin-bottom:3px;font-size:19px}
.profile-portrait-name{font-size:11px}
.profile-portrait-kind{font-size:9px;margin-top:1px}
#visual-profile-picker-label{font-size:11px;margin-top:2px}
#friends-auto-sync-status:empty{display:none}
#friends-auto-sync-status{font-size:10px!important;margin:0!important}
#unified-add-received{padding:3px 0 4px!important;font-size:11px!important}
header .nav{margin-top:6px}
header .nav button{font-size:10.5px;padding:9px 1px}
main{padding:10px 12px 40px}
#home>h2{display:none!important}
#home>#header-avatar{display:none!important}
#home>#today{font-size:11px;line-height:1.2;margin:0 0 8px;color:#a5c9d9}
#home>.hero{margin-top:0;padding:13px 15px;border-radius:15px}
#home .hero>.spread:first-child{font-size:13px}
#home .weight{font-size:41px;line-height:1.1;margin:8px 0 3px}
#home .weight small{font-size:16px}
#home #last{font-size:11px;margin:3px 0 12px;line-height:1.25}
#home .hero>.spread{font-size:12px}
#home .bar{height:7px;margin-top:7px}
#home .hero>.two{gap:8px;margin-top:7px}
#home .tile{border-radius:10px;padding:9px 11px;margin:5px 0}
#home .tile span{font-size:10px}
#home .tile strong{font-size:18px;line-height:1.2;margin-top:4px}
#home #add{padding:11px;font-size:13px;margin-top:7px;border-radius:11px}
#home>.two{gap:8px;margin-top:7px}
#home>.two .tile{margin:0;padding:10px 11px}
#home .pill{font-size:10px;padding:5px 8px}
@media (max-width:360px){
 .brand-hello h1{font-size:20px}
 .header-greeting{font-size:12px}
 #home .tile strong{font-size:16px}
 header .nav button{font-size:9px}
}
@media (max-height:760px){
 header{padding-top:9px}
 #home .weight{font-size:38px}
 #home .hero{padding:11px 13px}
 #home .tile{padding:8px}
}
</style>
"""
R(h,'</body></html>',css+'</body></html>')
print("v1.6.24: removed duplicate greeting and hero avatar; compact overview")
