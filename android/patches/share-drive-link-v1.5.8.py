#!/usr/bin/env python3
"""v1.5.8: share a Google Drive link to the existing read-only profile file.
The Drive link is provided by the user after granting Reader access in Drive.
Android SAF document URI is NOT a public/supported Google Drive URL, so never
construct a fake share URL from it. No old files are deleted.
"""
from pathlib import Path

base=Path("/tmp/mon-evolution-src/app")
java=base/"src/main/java/fr/monevolution/app/MainActivity.java"
html=base/"src/main/assets/index.html"
manifest=base/"src/main/AndroidManifest.xml"
gradle=base/"build.gradle"

def rep(path,old,new):
    s=path.read_text(encoding="utf-8")
    count=s.count(old)
    assert count==1, f"Expected one occurrence of {old[:90]!r} in {path}, got {count}"
    path.write_text(s.replace(old,new),encoding="utf-8")

rep(manifest,'android:versionCode="13" android:versionName="1.5.7"',
             'android:versionCode="14" android:versionName="1.5.8"')
rep(gradle,'versionCode 13','versionCode 14')
rep(gradle,"versionName '1.5.7'","versionName '1.5.8'")
rep(html,"const installed='1.5.7';","const installed='1.5.8';")
rep(html,'Version installée : <strong>1.5.7</strong>','Version installée : <strong>1.5.8</strong>')
rep(html,'Version installée : 1.5.7. Vérifie sur GitHub','Version installée : 1.5.8. Vérifie sur GitHub')

# Add a strict, profile-scoped link to the SAF-backed share. Never auto-share
# the full private backup or guess a URL from Android's content:// provider URI.
bridge=String.raw if False else r'''        @JavascriptInterface public String getShareLink(String id) {
            if (id==null || !id.matches("[a-zA-Z0-9_-]{1,75}")) return "";
            if (!getPreferences(MODE_PRIVATE).contains("share_uri_"+id)) return "";
            return getPreferences(MODE_PRIVATE).getString("share_link_"+id,"");
        }
        @JavascriptInterface public boolean saveShareLink(String id,String url) {
            if (id==null || !id.matches("[a-zA-Z0-9_-]{1,75}")
                    || !getPreferences(MODE_PRIVATE).contains("share_uri_"+id)
                    || url==null || url.length()>1500) return false;
            String value=url.trim();
            if (!validDriveShareLink(value)) return false;
            getPreferences(MODE_PRIVATE).edit().putString("share_link_"+id,value).apply();
            return true;
        }
        @JavascriptInterface public void copyShareLink(String id) {
            final String url=getShareLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Colle d’abord le lien obtenu dans Google Drive')",null);
                    return;
                }
                android.content.ClipboardManager clipboard=
                    (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Lien du profil partagé",url));
                web.evaluateJavascript("showMessage('Lien Google Drive copié ✓')",null);
            });
        }
        @JavascriptInterface public void sendShareLink(String id) {
            final String url=getShareLink(id);
            runOnUiThread(() -> {
                if(url.isEmpty()){
                    web.evaluateJavascript("showMessage('Enregistre d’abord le lien Google Drive')",null);
                    return;
                }
                try {
                    Intent send=new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_SUBJECT,"Profil Mon Évolution IMC en lecture seule");
                    send.putExtra(Intent.EXTRA_TEXT,"Voici mon profil Mon Évolution IMC en lecture seule :\n"+url);
                    startActivity(Intent.createChooser(send,"Partager le lien du profil"));
                } catch(Exception e) {
                    web.evaluateJavascript("showMessage('Impossible d’ouvrir le partage Android')",null);
                }
            });
        }
        @JavascriptInterface public void openDrive() {
            runOnUiThread(() -> {
                try {
                    Intent open=new Intent(Intent.ACTION_VIEW,
                        Uri.parse("https://drive.google.com/drive/my-drive"));
                    open.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(open);
                } catch(Exception e){
                    web.evaluateJavascript("showMessage('Ouvre Google Drive depuis ton téléphone')",null);
                }
            });
        }
'''
rep(java,"        @JavascriptInterface public void openShared() {",
         bridge+"        @JavascriptInterface public void openShared() {")
# Separate static checks: only Drive file links; no arbitrary URL can be injected
# into Android's Share Sheet or system clipboard.
validator=r'''    private boolean validDriveShareLink(String url) {
        try {
            Uri uri=Uri.parse(url);
            if(!"https".equalsIgnoreCase(uri.getScheme())
                || !"drive.google.com".equalsIgnoreCase(uri.getHost())) return false;
            String path=uri.getPath();
            if(path==null)return false;
            if(path.matches("/file/d/[A-Za-z0-9_-]{10,200}(/view)?/?"))return true;
            String id=uri.getQueryParameter("id");
            return "/open".equals(path) && id!=null && id.matches("[A-Za-z0-9_-]{10,200}");
        }catch(Exception e){return false;}
    }

'''
rep(java,"    // Read an existing SAF document with a strict size cap, before linking.",
         validator+"    // Read an existing SAF document with a strict size cap, before linking.")

# A link becomes invalid if the app is linked to a different share file.
rep(java,
'''                if (retained) getPreferences(MODE_PRIVATE).edit()
                    .putString("share_uri_" + id, uri.toString()).apply();''',
'''                if (retained) getPreferences(MODE_PRIVATE).edit()
                    .remove("share_link_" + id)
                    .putString("share_uri_" + id, uri.toString()).apply();''')
rep(java,
'''                getPreferences(MODE_PRIVATE).edit()
                    .putString("share_uri_"+pendingShareId,uri.toString()).apply();''',
'''                getPreferences(MODE_PRIVATE).edit()
                    .remove("share_link_"+pendingShareId)
                    .putString("share_uri_"+pendingShareId,uri.toString()).apply();''')
rep(java,
'''            getPreferences(MODE_PRIVATE).edit().remove("share_uri_" + id).apply();''',
'''            getPreferences(MODE_PRIVATE).edit()
                .remove("share_uri_" + id).remove("share_link_" + id).apply();''')

# New UI appears only after creating or reconnecting the share document.
panel=r''' <div id="share-link-panel" style="display:none;margin-top:15px;border-top:1px solid #38576b;padding-top:15px">
   <h3>🔗 Envoyer mon profil à un proche</h3>
   <p class="notice">1. Dans Drive, retrouve le fichier « mon-evolution-partage-… ». Appuie sur ⋮ → Partager, invite les proches comme <strong>Lecteurs</strong> et copie le lien. Garde l’accès général sur <strong>Limité</strong>.</p>
   <button id="share-open-drive" class="secondary" type="button" style="width:100%">Ouvrir Google Drive</button>
   <label class="field">2. Colle ici le lien obtenu dans Google Drive
     <input id="share-link-input" type="url" maxlength="1500" placeholder="https://drive.google.com/file/d/…/view" autocomplete="off">
   </label>
   <button id="share-link-save" class="secondary" type="button" style="width:100%">Enregistrer ce lien</button>
   <div class="two" style="margin-top:12px">
     <button id="share-link-copy" class="secondary" type="button">Copier le lien</button>
     <button id="share-link-send" class="primary" type="button">Partager le lien</button>
   </div>
   <p class="notice">Le lien renvoie au même fichier Drive, qui sera actualisé avec ton profil. Seules les personnes autorisées dans Drive pourront le consulter. Sans autorisation Lecteur, le lien ne leur donnera pas accès.</p>
 </div>
'''
rep(html,
    ''' <button class="secondary" style="width:100%;margin-top:10px" id="stop-share">Désactiver les mises à jour</button>''',
    panel+''' <button class="secondary" style="width:100%;margin-top:10px" id="stop-share">Désactiver les mises à jour</button>''')
rep(html,
''' $('share-relink').textContent=linked?'Changer de fichier partagé relié':'↗ Relier un fichier partagé existant';
 $('share-photos').checked=!!window.AndroidBackup?.sharePhotosEnabled?.(id);''',
''' $('share-relink').textContent=linked?'Changer de fichier partagé relié':'↗ Relier un fichier partagé existant';
 $('share-link-panel').style.display=linked?'block':'none';
 const savedLink=linked?(window.AndroidBackup?.getShareLink?.(id)||''):'';
 $('share-link-input').value=savedLink;
 $('share-link-copy').disabled=!savedLink;
 $('share-link-send').disabled=!savedLink;
 $('share-photos').checked=!!window.AndroidBackup?.sharePhotosEnabled?.(id);''')
rep(html,
"""$('share-photos').onchange=()=>{""",
"""$('share-open-drive').onclick=()=>window.AndroidBackup?.openDrive?.();
$('share-link-save').onclick=()=>{
 if(!window.AndroidBackup?.saveShareLink)return message('Partage de lien indisponible sur Android');
 if(!AndroidBackup.saveShareLink(profile().id,$('share-link-input').value.trim()))
   return alert('Lien non reconnu. Copie le lien du fichier JSON depuis Google Drive (et pas celui du dossier).');
 shareStatus();
 message('Lien Drive enregistré pour ce profil ✓');
};
$('share-link-copy').onclick=()=>window.AndroidBackup?.copyShareLink?.(profile().id);
$('share-link-send').onclick=()=>window.AndroidBackup?.sendShareLink?.(profile().id);
$('share-photos').onchange=()=>{""")
# A text field is cleared if the user reselects a different file; valid and safe.
rep(html,
"""function shareCreated(persistent){shareStatus();alert(persistent?""",
"""function shareCreated(persistent){shareStatus();alert(persistent?""")  # existing hook, no behavior change

content=html.read_text(encoding='utf-8')
assert 'id="share-link-send"' in content and 'id="share-link-copy"' in content
assert 'share-link-panel' in content and "const installed='1.5.8';" in content
assert 'id="setup-screen"' in content and "name:'Mario',height:181" not in content
assert 'id="update-page-open"' in content and 'id="update-direct-open"' in content
source=java.read_text(encoding='utf-8')
for token in ('sendShareLink(String id)','saveShareLink(String id,String url)',
              'copyShareLink(String id)','getShareLink(String id)','validDriveShareLink'):
    assert token in source
print("v1.5.8: private Drive link can be copied or shared after user saves it.")
