#!/usr/bin/env python3
"""Build-time v1.5.5 patch: open both GitHub Release page and APK in external browser."""
from pathlib import Path

BASE = Path('/tmp/mon-evolution-src/app')
manifest = BASE / 'src/main/AndroidManifest.xml'
gradle = BASE / 'build.gradle'
html = BASE / 'src/main/assets/index.html'
java = BASE / 'src/main/java/fr/monevolution/app/MainActivity.java'

def change(path, before, after):
    content = path.read_text(encoding='utf-8')
    count = content.count(before)
    assert count == 1, f'Expected exactly one match ({count} found) for {before[:65]!r} in {path}'
    path.write_text(content.replace(before, after), encoding='utf-8')

change(manifest, 'android:versionCode="9" android:versionName="1.5.3"',
       'android:versionCode="11" android:versionName="1.5.5"')
change(gradle, 'versionCode 9', 'versionCode 11')
change(gradle, "versionName '1.5.3'", "versionName '1.5.5'")
change(html, "const installed='1.5.3';", "const installed='1.5.5';")
change(html, 'Version installée : <strong>1.5.3</strong>',
       'Version installée : <strong>1.5.5</strong>')
change(html, 'Version installée : 1.5.2. Vérifie sur GitHub',
       'Version installée : 1.5.5. Vérifie sur GitHub')

bridge = r'''    public class Bridge {
        @JavascriptInterface public void openOfficialUrl(String url) {
            if (url == null) return;
            String prefix = "https://github.com/TheDwarfy01/mon-evolution/releases";
            boolean valid = prefix.equals(url)
                || url.matches("https://github\\.com/TheDwarfy01/mon-evolution/releases/tag/v[0-9]+(\\.[0-9]+){1,3}")
                || url.matches("https://github\\.com/TheDwarfy01/mon-evolution/releases/download/v[0-9]+(\\.[0-9]+){1,3}/Mon_Evolution_IMC_v[0-9]+(\\.[0-9]+){1,3}\\.apk");
            if (!valid) return;
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    intent.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(intent);
                } catch (android.content.ActivityNotFoundException ignored) { }
            });
        }
'''
change(java, '    public class Bridge {\n', bridge)

# Both actions are available when an update is found. The release PAGE is primary.
change(html, 'Lien de téléchargement officiel à copier :',
       'Page GitHub de la nouvelle version (recommandée) et téléchargement direct :')
change(html,
       'Pour installer la nouvelle version, ouvre son lien dans Chrome. Si le bouton ne lance pas le téléchargement, copie le lien ci-dessous :',
       "Ouvre la page GitHub, puis choisis l'APK dans Assets. Le lien direct est aussi disponible.")
change(html,
       '<button id="update-copy" class="secondary" type="button">Copier le lien pour Chrome</button>',
       '<button id="update-page-open" class="primary" type="button" style="margin:12px 0 6px">🌐 Ouvrir la page GitHub</button>\\n<button id="update-direct-open" class="secondary" type="button" style="width:100%;margin:6px 0 12px">⬇ Télécharger l’APK directement</button>\\n<button id="update-copy" class="secondary" type="button">Copier le lien de la page GitHub</button>')
change(html,
       '<button id="update-check" class="secondary" type="button">↻ Rechercher une mise à jour</button>',
       '<button id="update-check" class="secondary" type="button">↻ Rechercher une mise à jour</button>\\n<button id="releases-home" class="secondary" type="button" style="margin-top:8px">🌐 Toutes les versions sur GitHub</button>')

s = html.read_text(encoding='utf-8')
start = s.index('<script>\n// GitHub Pages hosts a tiny public version file: no account is sent to this endpoint.')
end = s.index('</script>', start) + len('</script>')
new_script = r'''<script>
// GitHub Pages serves metadata only. Actual APK files live on GitHub Releases.
(function () {
  const installed='1.5.5';
  const releases='https://github.com/TheDwarfy01/mon-evolution/releases';
  const versionPattern=/^\d+(?:\.\d+){1,3}$/;
  const releasePage=v=>releases+'/tag/v'+v;
  const releaseApk=v=>releases+'/download/v'+v+'/Mon_Evolution_IMC_v'+v+'.apk';
  const legacyApk=v=>'https://thedwarfy01.github.io/mon-evolution/downloads/Mon_Evolution_IMC_v'+v+'.apk';
  function openOfficial(url){
    if(window.AndroidBackup?.openOfficialUrl){
      AndroidBackup.openOfficialUrl(url);
    }else{
      window.open(url,'_blank','noopener,noreferrer');
    }
  }
  function compareVersion(a,b){
    const x=String(a).split('.').map(Number),y=String(b).split('.').map(Number);
    for(let i=0;i<Math.max(x.length,y.length);i++){
      if((x[i]||0)!==(y[i]||0))return (x[i]||0)>(y[i]||0)?1:-1;
    }
    return 0;
  }
  const check=document.getElementById('update-check');
  const pageButton=document.getElementById('update-page-open');
  const directButton=document.getElementById('update-direct-open');
  const copyButton=document.getElementById('update-copy');
  const urlInput=document.getElementById('update-url');
  let latestVersion='';
  document.getElementById('releases-home').addEventListener('click',()=>openOfficial(releases));
  pageButton.addEventListener('click',()=>{
    if(versionPattern.test(latestVersion))openOfficial(releasePage(latestVersion));
  });
  directButton.addEventListener('click',()=>{
    if(versionPattern.test(latestVersion))openOfficial(releaseApk(latestVersion));
  });
  copyButton.addEventListener('click',()=>{
    if(!versionPattern.test(latestVersion))return;
    urlInput.value=releasePage(latestVersion);
    urlInput.focus();urlInput.select();
    try{document.execCommand('copy')}catch(_){}
    document.getElementById('update-status').textContent='Lien de la page GitHub sélectionné. Ouvre-le dans Chrome.';
  });
  check.addEventListener('click',function(){
    const status=document.getElementById('update-status');
    const box=document.getElementById('update-offer');
    status.textContent='Recherche de la dernière version publiée…';
    box.style.display='none';
    latestVersion='';
    let finished=false;
    const script=document.createElement('script');
    const watchdog=setTimeout(()=>finish('Vérification indisponible. Ouvre directement la page GitHub.'),12000);
    function finish(txt){
      if(finished)return;
      finished=true;
      clearTimeout(watchdog);
      status.textContent=txt;
      script.remove();
    }
    window.__monEvolutionVersionCallback=function(info){
      const v=String(info?.version||'');
      if(!versionPattern.test(v)||!info.published||(
         info.url!==releaseApk(v) && info.url!==legacyApk(v))){
        finish('Informations de mise à jour invalides.');return;
      }
      if(compareVersion(v,installed)>0){
        latestVersion=v;
        document.getElementById('update-details').textContent='Nouvelle version disponible : '+v;
        urlInput.value=releasePage(v);
        box.style.display='block';
        finish('Version '+v+' disponible sur GitHub Releases.');
      }else{
        finish('Aucune mise à jour plus récente publiée sur GitHub.');
      }
    };
    script.onerror=()=>finish('Connexion impossible. Tu peux ouvrir la page GitHub.');
    script.src='https://thedwarfy01.github.io/mon-evolution/version.js?cache='+Date.now();
    document.head.appendChild(script);
  });
})();
</script>'''
s = s[:start] + new_script + s[end:]
assert s.count('id="update-page-open"') == 1
assert s.count('id="update-direct-open"') == 1
assert s.count('openOfficialUrl') >= 1
assert "name:'Mario',height:181" not in s and '119,9' not in s
assert 'id="setup-screen"' in s
assert 'android:icon="@drawable/ic_launcher"' in manifest.read_text(encoding='utf-8')
assert (BASE/'src/main/res/drawable/ic_launcher.xml').is_file()
html.write_text(s, encoding='utf-8')
print('Correctif 1.5.5 appliqué : deux boutons, navigateur Android, versionCode 11.')
