#!/usr/bin/env python3
"""Run after successful signing + publication of v1.5.6 GitHub Release."""
from pathlib import Path
import re

version='1.5.6'
page='https://github.com/TheDwarfy01/mon-evolution/releases/tag/v'+version
apk='https://github.com/TheDwarfy01/mon-evolution/releases/download/v'+version+'/Mon_Evolution_IMC_v'+version+'.apk'

Path('version.js').write_text("""// Mon Évolution IMC — dernière version sur GitHub Releases.
window.__monEvolutionVersionCallback?.({
  version: "1.5.6",
  published: true,
  url: "https://github.com/TheDwarfy01/mon-evolution/releases/download/v1.5.6/Mon_Evolution_IMC_v1.5.6.apk"
});
// Les anciennes versions utilisent un champ de lien unique : prioriser la
// page GitHub (Assets), qui fonctionne sur Samsung.
(function(){
  var input=document.getElementById('update-url');
  var offer=document.getElementById('update-offer');
  if(input && offer && offer.style.display==='block'){
    input.value="https://github.com/TheDwarfy01/mon-evolution/releases/tag/v1.5.6";
    var status=document.getElementById('update-status');
    if(status)status.textContent="Version 1.5.6 disponible : ouvre la page GitHub puis Assets.";
  }
})();
""", encoding='utf-8')

site=Path('index.html')
html=site.read_text(encoding='utf-8')
# Replace the sole download CTA, retaining both paths.
html=re.sub(r'<p><a href="https://github\\.com/TheDwarfy01/mon-evolution/releases/download/v[0-9.]+/Mon_Evolution_IMC_v[0-9.]+\\.apk">Téléchargement APK direct \\(alternative\\)</a></p>','',html)
pattern=r'<p><a class="button" href="[^"]+"(?: download)?>Télécharger Mon Évolution IMC v[0-9.]+(?: \\(page GitHub\\))?</a></p>'
replacement='<p><a class="button" href="'+page+'">Télécharger Mon Évolution IMC v1.5.6 (page GitHub)</a></p><p><a href="'+apk+'">Téléchargement APK direct (alternative)</a></p>'
html,count=re.subn(pattern,lambda _:replacement,html)
assert count==1, f'Expected exactly one site download CTA, got {count}'
html=re.sub(r'<p class="note">Version 1\.5\.[0-9]+ :.*?</p>',
    '<p class="note">Version 1.5.6 : partage Google Drive en lecture seule opérationnel, avec mises à jour du profil. Téléchargement via la page GitHub Releases (recommandé sur Samsung) ou lien APK direct. Mise à jour sans désinstallation.</p>',html)
site.write_text(html,encoding='utf-8')
print('Version.js et page de téléchargement actualisés pour v1.5.6.')
