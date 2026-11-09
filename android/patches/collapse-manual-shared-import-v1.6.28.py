#!/usr/bin/env python3
"""v1.6.28: hide legacy manual import form behind an advanced expander."""
from pathlib import Path
root=Path("android/source-1.6.28/app")
h=root/"src/main/assets/index.html";g=root/"build.gradle";m=root/"src/main/AndroidManifest.xml";j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8"); n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} occurrences for {a[:95]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 43","versionCode 44")
R(g,"versionName '1.6.27'","versionName '1.6.28'")
R(m,'android:versionCode="43" android:versionName="1.6.27"','android:versionCode="44" android:versionName="1.6.28"')
R(j,"MonEvolutionIMC/1.6.27","MonEvolutionIMC/1.6.28")
R(h,'Version installée : <strong>1.6.27</strong>','Version installée : <strong>1.6.28</strong>')
R(h,'const installed="1.6.27";','const installed="1.6.28";')
snippet=r"""
<style>
#shared-manual-import{margin:12px 0 18px}
#shared-manual-import>summary{cursor:pointer;list-style:none;font-size:13px;color:#cce7f2;background:#1b3b51;border:1px solid #355b73;padding:13px 16px;border-radius:12px}
#shared-manual-import>summary::-webkit-details-marker{display:none}
#shared-manual-import>summary:after{content:'⌄';float:right}
#shared-manual-import[open]>summary:after{content:'⌃'}
#shared-manual-import>.card{margin-top:9px}
</style>
<script>
(function(){
 const input=$('shared-public-url');
 const section=$('shared');
 const panel=input?.closest('.card');
 if(!section||!panel||!section.contains(panel))return;
 const details=document.createElement('details');details.id='shared-manual-import';
 const summary=document.createElement('summary');summary.textContent='⚙ Importation manuelle (avancé)';
 details.append(summary);
 // Move (never duplicate) the existing card to retain URL import, private
 // Drive file selection, refresh and original click handlers and permissions.
 section.insertBefore(details,panel);
 details.append(panel);
})();
</script>
"""
R(h,'</body></html>',snippet+'</body></html>')
print("v1.6.28: manual URL and Drive import now optional and collapsed")
