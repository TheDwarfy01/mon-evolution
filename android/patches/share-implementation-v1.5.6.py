#!/usr/bin/env python3
"""Add private single-profile SAF sharing/read-only support to Android v1.5.6."""
from pathlib import Path

base=Path('/tmp/mon-evolution-src/app')
manifest=base/'src/main/AndroidManifest.xml'
gradle=base/'build.gradle'
html=base/'src/main/assets/index.html'
java=base/'src/main/java/fr/monevolution/app/MainActivity.java'

def replace(path,old,new):
    txt=path.read_text(encoding='utf-8')
    n=txt.count(old)
    assert n==1, f'Expected one occurrence of {old[:70]!r} in {path}, found {n}'
    path.write_text(txt.replace(old,new), encoding='utf-8')

replace(manifest,'android:versionCode="9" android:versionName="1.5.3"',
                 'android:versionCode="12" android:versionName="1.5.6"')
replace(gradle,'versionCode 9','versionCode 12')
replace(gradle,"versionName '1.5.3'","versionName '1.5.6'")
replace(html,"const installed='1.5.3';","const installed='1.5.6';")
replace(html,'Version installée : <strong>1.5.3</strong>','Version installée : <strong>1.5.6</strong>')
replace(html,'Version installée : 1.5.2. Vérifie sur GitHub','Version installée : 1.5.6. Vérifie sur GitHub')
# Keep v1.5.5's two-button Github feature, JS bridge and neutral start screen.
replace(html,'Lien de téléchargement officiel à copier :',
             'Page GitHub de la nouvelle version (recommandée) et téléchargement direct :')
replace(html,
       'Pour installer la nouvelle version, ouvre son lien dans Chrome. Si le bouton ne lance pas le téléchargement, copie le lien ci-dessous :',
       "Ouvre la page GitHub, puis choisis l’APK dans Assets. Le lien direct est aussi disponible.")
replace(html,'<button id="update-check" class="secondary" type="button">↻ Rechercher une mise à jour</button>',
             '<button id="update-check" class="secondary" type="button">↻ Rechercher une mise à jour</button>\\n<button id="releases-home" class="secondary" type="button" style="margin-top:8px">🌐 Toutes les versions sur GitHub</button>')
replace(html,'<button id="update-copy" class="secondary" type="button">Copier le lien pour Chrome</button>',
             '<button id="update-page-open" class="primary" type="button" style="margin:12px 0 6px">🌐 Ouvrir la page GitHub</button>\\n<button id="update-direct-open" class="secondary" type="button" style="width:100%;margin:6px 0 12px">⬇ Télécharger l’APK directement</button>\\n<button id="update-copy" class="secondary" type="button">Copier le lien de la page GitHub</button>')

update_source=Path('android/patches/updates-v1.5.6.js').read_text(encoding='utf-8')
txt=html.read_text(encoding='utf-8')
start=txt.index('<script>\n// GitHub Pages hosts a tiny public version file: no account is sent to this endpoint.')
end=txt.index('</script>',start)+len('</script>')
txt=txt[:start]+update_source+txt[end:]
html.write_text(txt,encoding='utf-8')

replace(java,'    private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44;',
    '    private static final int SAVE = 41, LOAD = 42, PDF = 43, PHOTO = 44, SHARE_CREATE = 45, SHARE_OPEN = 46;')
replace(java,'    private String pendingPhotoToken;',
    '    private String pendingPhotoToken;\n    private String pendingShareId;\n    private String pendingShareJson;')
replace(java,'''    public class Bridge {
''',Path('android/patches/share-bridge-v1.5.6.java.txt').read_text(encoding='utf-8'))
replace(java,'''        @JavascriptInterface public void autoSave(String json) {
            String value = getPreferences(MODE_PRIVATE).getString(BACKUP_URI, null);''',
'''        @JavascriptInterface public void autoSave(String json) {
            updateSharedFiles(json);
            String value = getPreferences(MODE_PRIVATE).getString(BACKUP_URI, null);''')
replace(java,'''            } else if (request == LOAD) {
                byte[] bytes;''',
'''            } else if (request == SHARE_CREATE) {
                String id = pendingShareId, json = pendingShareJson;
                if (id == null || json == null) throw new Exception("Aucun profil à partager");
                boolean retained = persistUri(uri, true);
                String payload = makeSharedDocument(id, new JSONObject(json).getJSONObject("profile"));
                writeShared(uri, payload);
                if (retained) getPreferences(MODE_PRIVATE).edit()
                    .putString("share_uri_" + id, uri.toString()).apply();
                web.evaluateJavascript("shareCreated(" + retained + ")", null);
            } else if (request == SHARE_OPEN) {
                persistUri(uri, false);
                getPreferences(MODE_PRIVATE).edit()
                    .putString("received_share_uri", uri.toString()).apply();
                loadShared(uri);
            } else if (request == LOAD) {
                byte[] bytes;''')
replace(java,'''        } catch (Exception e) {
            web.evaluateJavascript("showMessage('Opération impossible : vérifie le fichier ou Google Drive')", null);
        } finally {
            pendingJson = null;''',
'''        } catch (Exception e) {
            if (request == SHARE_CREATE) {
                web.evaluateJavascript("sharedUpdateFailed()", null);
            } else if (request == SHARE_OPEN) {
                web.evaluateJavascript("sharedReadFailed()", null);
            } else {
                web.evaluateJavascript("showMessage('Opération impossible : vérifie le fichier ou Google Drive')", null);
            }
        } finally {
            pendingShareId = null;
            pendingShareJson = null;
            pendingJson = null;''')
replace(java,'''    private String stringHash(String value) throws Exception {''',
    Path('android/patches/share-helpers-v1.5.6.java.txt').read_text(encoding='utf-8')+
    '''    private String stringHash(String value) throws Exception {''')
replace(html,"function shareCreated(){shareStatus();alert('Fichier créé ! Dans Google Drive, retrouve le fichier « mon-evolution-partage-… » et partage-le uniquement avec les personnes choisies, avec le rôle Lecteur.')};",
"""function shareCreated(persistent){shareStatus();alert(persistent?
'Fichier de partage créé ! Ouvre Google Drive et partage-le uniquement avec les destinataires choisis, avec le rôle Lecteur. Les modifications de ce profil actualiseront ce fichier.':
'Fichier créé ! Le fournisseur de stockage ne permet pas la mise à jour automatique. Pour une synchronisation, crée le fichier dans Google Drive.');};""")
replace(html,"AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));",
"""AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));""") # no-op exact check

src=html.read_text(encoding='utf-8')
assert "id=\"setup-screen\"" in src
assert "createShare" in java.read_text() and "openShared" in java.read_text()
assert "name:'Mario',height:181" not in src
assert 'android:icon="@drawable/ic_launcher"' in manifest.read_text()
print("v1.5.6: read-only Drive share + receiver + automatic refresh + GitHub update buttons ready")
