#!/usr/bin/env python3
"""v1.6.2: invitation web URL -> Android deep link -> consent -> add received profile.
All links are restricted to Google Drive file IDs and never automatically
grant read access to a private Google Drive file.
"""
from pathlib import Path

root=Path("android/source-1.6.2/app")
manifest=root/"src/main/AndroidManifest.xml"
gradle=root/"build.gradle"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
html=root/"src/main/assets/index.html"

def rep(path,old,new):
    s=path.read_text(encoding="utf-8")
    count=s.count(old)
    assert count==1,f"Expected one match, found {count} for {old[:110]!r} in {path}"
    path.write_text(s.replace(old,new),encoding="utf-8")

rep(manifest,'android:versionCode="17" android:versionName="1.6.1"',
             'android:versionCode="18" android:versionName="1.6.2"')
rep(gradle,"versionCode 17","versionCode 18")
rep(gradle,"versionName '1.6.1'","versionName '1.6.2'")
rep(html,'const installed="1.6.1";','const installed="1.6.2";')
rep(html,'Version installée : <strong>1.6.1</strong>','Version installée : <strong>1.6.2</strong>')
rep(html,'Version installée : 1.6.1. Vérifie sur GitHub',
         'Version installée : 1.6.2. Vérifie sur GitHub')

rep(manifest,'<activity android:name=".MainActivity" android:exported="true">',
'''<activity android:name=".MainActivity" android:exported="true" android:launchMode="singleTop">''')
rep(manifest,'''      </intent-filter>
    </activity>''',
'''      </intent-filter>
      <!-- Only the app-specific custom scheme is received by this Activity.
           HTTPS invitations are handled by the GitHub Pages landing page. -->
      <intent-filter>
        <action android:name="android.intent.action.VIEW"/>
        <category android:name="android.intent.category.DEFAULT"/>
        <category android:name="android.intent.category.BROWSABLE"/>
        <data android:scheme="monevolution" android:host="share"/>
      </intent-filter>
    </activity>''')

rep(java,'    private String pendingProgressJson;',
'''    private String pendingProgressJson;
    private String pendingInvitationId;
    private boolean appPageReady=false;''')
rep(java,'''        super.onCreate(state);
        // Android 15''',
'''        super.onCreate(state);
        pendingInvitationId=extractInvitationFileId(getIntent());
        // Android 15''')
rep(java,'''        web.setWebViewClient(new WebViewClient() {
            private boolean handleUri(Uri uri) {''',
'''        web.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view,String url) {
                super.onPageFinished(view,url);
                if(url!=null && url.startsWith("file:///android_asset/index.html")) {
                    appPageReady=true;
                    deliverInvitation();
                }
            }
            private boolean handleUri(Uri uri) {''')
methods=r'''
    // All externally supplied deep links are parsed and validated by Android
    // before any data reaches the JavaScript UI. No automatic addition.
    private String extractInvitationFileId(Intent intent) {
        if(intent==null || !Intent.ACTION_VIEW.equals(intent.getAction()))return null;
        Uri uri=intent.getData();
        if(uri==null || !"monevolution".equalsIgnoreCase(uri.getScheme())
            || !"share".equalsIgnoreCase(uri.getHost()))return null;
        String id=uri.getQueryParameter("file");
        return id!=null && id.matches("[A-Za-z0-9_-]{10,200}")?id:null;
    }

    private void deliverInvitation() {
        if(!appPageReady || pendingInvitationId==null)return;
        String fileId=pendingInvitationId;
        pendingInvitationId=null;
        web.evaluateJavascript("window.receiveShareInvitation("+JSONObject.quote(fileId)+")",null);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        String fileId=extractInvitationFileId(intent);
        if(fileId!=null){
            pendingInvitationId=fileId;
            if(appPageReady)deliverInvitation();
        }
    }

'''
rep(java,"    public class Bridge {",methods+"    public class Bridge {")
inviteMethod=r'''        @JavascriptInterface public String getInvitationLink(String profileId) {
            String drive=getShareLink(profileId);
            String id=driveFileId(drive);
            if(id==null)return "";
            // The public landing page contains no personal data. The file ID
            // itself grants no read permission unless the Drive owner permits it.
            return "https://thedwarfy01.github.io/mon-evolution/share.html?file="+id;
        }
'''
rep(java,"        @JavascriptInterface public void copyShareLink(String id) {",
         inviteMethod+"        @JavascriptInterface public void copyShareLink(String id) {")
source=java.read_text(encoding="utf-8")
assert source.count("final String url=getShareLink(id);")==2
java.write_text(source.replace("final String url=getShareLink(id);",
                              "final String url=getInvitationLink(id);"),encoding="utf-8")
rep(java,"web.evaluateJavascript(\"showMessage('Lien Google Drive copié ✓')\",null);",
         "web.evaluateJavascript(\"showMessage('Lien d’invitation copié ✓')\",null);")
rep(java,'send.putExtra(Intent.EXTRA_SUBJECT,"Profil Mon Évolution IMC en lecture seule");',
         'send.putExtra(Intent.EXTRA_SUBJECT,"Invitation à mon profil Mon Évolution IMC");')
rep(java,'send.putExtra(Intent.EXTRA_TEXT,"Voici mon profil Mon Évolution IMC en lecture seule :\\n"+url);',
         'send.putExtra(Intent.EXTRA_TEXT,"Je t’invite à consulter mon profil Mon Évolution IMC en lecture seule. Ouvre ce lien sur ton téléphone, puis choisis « Ouvrir dans Mon Évolution » :\\n"+url);')

# The stored original Drive URL remains available for owner editing.
rep(html,'''   <div class="two" style="margin-top:12px">
     <button id="share-link-copy" class="secondary" type="button">Copier le lien</button>
     <button id="share-link-send" class="primary" type="button">Partager le lien</button>
   </div>
   <p class="notice">Le lien renvoie au même fichier Drive, qui sera actualisé avec ton profil. Seules les personnes autorisées dans Drive pourront le consulter. Sans autorisation Lecteur, le lien ne leur donnera pas accès.</p>''',
'''   <label class="field">3. Lien d’invitation à envoyer
     <input id="share-invite-preview" readonly type="url" aria-label="Lien d’invitation Mon Évolution">
   </label>
   <div class="two" style="margin-top:12px">
     <button id="share-link-copy" class="secondary" type="button">Copier l’invitation</button>
     <button id="share-link-send" class="primary" type="button">Inviter un proche</button>
   </div>
   <p class="notice">Ce lien ouvre une page Mon Évolution qui propose de lancer l’application et d’ajouter ton profil après confirmation. L’accès au fichier reste soumis à tes autorisations Drive. Un lien privé nécessite un compte autorisé.</p>''')
rep(html,''' $('share-link-input').value=savedLink;
 $('share-link-copy').disabled=!savedLink;
 $('share-link-send').disabled=!savedLink;''',
''' $('share-link-input').value=savedLink;
 const invitation=linked?(window.AndroidBackup?.getInvitationLink?.(id)||''):'';
 $('share-invite-preview').value=invitation;
 $('share-link-copy').disabled=!invitation;
 $('share-link-send').disabled=!invitation;''')
# An invitation panel appears only when the browser opened the app using an
# authenticated link. A human must tap "Add" before downloading the JSON.
block=r'''
<script>
// Incoming Android intent: only a validated Google Drive file ID is accepted.
// The user must explicitly choose whether to add this profile.
(function(){
 const section=$('shared');
 const panel=document.createElement('div');
 panel.id='incoming-invitation';
 panel.className='card';
 panel.hidden=true;
 panel.innerHTML='<h3>✉ Invitation à un profil partagé</h3>'+
 '<p class="notice">Un proche t’invite à consulter son profil en lecture seule. '+
 'Aucune donnée de ton téléphone ne sera remplacée. Confirme avant de l’ajouter.</p>'+
 '<button id="invite-accept" class="primary" type="button">Ajouter ce profil</button>'+
 '<button id="invite-private" class="secondary" style="width:100%;margin-top:10px" type="button">Accès privé : choisir le fichier Google Drive</button>'+
 '<button id="invite-cancel" class="secondary" style="width:100%;margin-top:10px" type="button">Ignorer cette invitation</button>'+
 '<p class="notice">Si le propriétaire n’a autorisé que certaines adresses Gmail, '+
 'le téléchargement par URL peut échouer : dans ce cas, choisis le fichier privé '+
 'avec le compte Google qui a reçu l’autorisation.</p>';
 section.insertBefore(panel,section.querySelector('.card'));
 let pendingId='';
 window.receiveShareInvitation=function(fileId){
   if(typeof fileId!=='string'||!(/^[A-Za-z0-9_-]{10,200}$/).test(fileId))return;
   pendingId=fileId;
   const url='https://drive.google.com/file/d/'+fileId+'/view';
   $('shared-public-url').value=url;
   document.body.classList.remove('needs-setup');
   showUnifiedTab('shared');
   panel.hidden=false;
   $('shared-state').textContent='Invitation reçue : confirme pour ajouter ce profil.';
   panel.scrollIntoView({block:'start'});
 };
 $('invite-accept').onclick=()=>{
   if(!pendingId)return;
   $('shared-state').textContent='Lecture du profil partagé…';
   window.AndroidBackup?.loadSharedPublic?.('https://drive.google.com/file/d/'+pendingId+'/view');
 };
 $('invite-private').onclick=()=>{
   if(!pendingId)return;
   if(!window.AndroidBackup?.openShared)return alert('Ouverture Drive indisponible.');
   window.AndroidBackup.openShared();
 };
 $('invite-cancel').onclick=()=>{
   pendingId='';
   panel.hidden=true;
   $('shared-state').textContent='Invitation ignorée. Aucun profil n’a été ajouté.';
 };
 const priorLoaded=window.onReceivedProfileLoaded;
 window.onReceivedProfileLoaded=function(key,name){
   pendingId='';
   panel.hidden=true;
   if(typeof priorLoaded==='function')priorLoaded(key,name);
 };
})();
</script>
'''
assert html.read_text(encoding="utf-8").endswith("</body></html>")
source=html.read_text(encoding="utf-8")
html.write_text(source.replace("</body></html>",block+"</body></html>"),encoding="utf-8")

assert 'versionName="1.6.2"' in manifest.read_text(encoding="utf-8")
assert "versionCode 18" in gradle.read_text(encoding="utf-8")
assert "getInvitationLink" in java.read_text(encoding="utf-8")
assert "onNewIntent" in java.read_text(encoding="utf-8")
assert 'id="incoming-invitation"' not in html.read_text(encoding="utf-8") # created in JS DOM, not pre-rendered
assert "window.receiveShareInvitation" in html.read_text(encoding="utf-8")
assert 'id="share-invite-preview"' in html.read_text(encoding="utf-8")
assert "share-invite-preview" in html.read_text(encoding="utf-8")
print("v1.6.2 invitation flow: validated Android deep link, consent, private Drive fallback.")
