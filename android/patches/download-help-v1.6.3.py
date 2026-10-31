#!/usr/bin/env python3
"""v1.6.3: inform Samsung users that Firefox/DuckDuckGo can download APKs
when Chrome blocks the transfer; keep both GitHub Releases routes.
"""
from pathlib import Path
root=Path("android/source-1.6.3/app")
html=root/"src/main/assets/index.html"
manifest=root/"src/main/AndroidManifest.xml"
gradle=root/"build.gradle"

def once(path,old,new):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    assert count==1,f"Expected exactly one occurrence, got {count} of {old[:110]!r} in {path}"
    path.write_text(content.replace(old,new),encoding="utf-8")

once(manifest,'android:versionCode="18" android:versionName="1.6.2"',
              'android:versionCode="19" android:versionName="1.6.3"')
once(gradle,"versionCode 18","versionCode 19")
once(gradle,"versionName '1.6.2'","versionName '1.6.3'")
once(html,'const installed="1.6.2";','const installed="1.6.3";')
once(html,'Version installée : <strong>1.6.2</strong>',
          'Version installée : <strong>1.6.3</strong>')
once(html,'Version installée : 1.6.2. Vérifie sur GitHub',
          'Version installée : 1.6.3. Vérifie sur GitHub')
once(html,
     "Ouvre la page GitHub, puis choisis l’APK dans Assets. Le lien direct est aussi disponible.",
     "Sur certains Samsung, Chrome peut bloquer le téléchargement des APK. Si cela arrive, ouvre ce lien dans Firefox ou DuckDuckGo, puis choisis l’APK dans Assets. Le téléchargement direct reste disponible.")
once(html,
     'Lien GitHub sélectionné : copie-le puis ouvre Chrome.',
     'Lien GitHub sélectionné : ouvre-le dans Firefox ou DuckDuckGo si Chrome bloque le téléchargement.')
once(html,
     '<p class="notice">Page GitHub de la nouvelle version (recommandée) et téléchargement direct :</p>',
     '<p class="notice">Téléchargement depuis GitHub Releases : page de la version recommandée ou APK direct. Si Chrome bloque sur ton Samsung, essaie Firefox ou DuckDuckGo.</p>')

content=html.read_text(encoding="utf-8")
assert 'Firefox ou DuckDuckGo' in content
assert 'id="update-direct-open"' in content and 'id="update-page-open"' in content
assert 'getInvitationLink' not in content or 'share-invite-preview' in content
assert '1.6.3' in content
print("v1.6.3: Firefox/DuckDuckGo suggested for Samsung APK download.")
