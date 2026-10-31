#!/usr/bin/env python3
"""v1.6.4: robust read-only Google Drive public file loading.

Drive preview pages are not the raw JSON file. Try multiple Google-hosted
download endpoints with strict redirect allowlist and descriptive status.
Never change Drive permissions or expose a private Google access token.
"""
from pathlib import Path
root=Path("android/source-1.6.4/app")
jpath=root/"src/main/java/fr/monevolution/app/MainActivity.java"
hpath=root/"src/main/assets/index.html"
manifest=root/"src/main/AndroidManifest.xml"
gradle=root/"build.gradle"

def rep(path,a,b):
    s=path.read_text(encoding="utf-8")
    count=s.count(a)
    assert count==1, f"Expected exactly one occurrence ({count}) in {path}: {a[:95]!r}"
    path.write_text(s.replace(a,b),encoding="utf-8")

rep(manifest, 'android:versionCode="19" android:versionName="1.6.3"',
              'android:versionCode="20" android:versionName="1.6.4"')
rep(gradle, 'versionCode 19','versionCode 20')
rep(gradle, "versionName '1.6.3'", "versionName '1.6.4'")
rep(hpath,'const installed="1.6.3";','const installed="1.6.4";')
rep(hpath,'Version installée : <strong>1.6.3</strong>',
          'Version installée : <strong>1.6.4</strong>')
rep(hpath,'Version installée : 1.6.3. Vérifie sur GitHub',
          'Version installée : 1.6.4. Vérifie sur GitHub')

# Keep the Google Drive resource key in invitations when present.
rep(jpath,
    'return "https://thedwarfy01.github.io/mon-evolution/share.html?file="+id;',
    '''String key=driveResourceKey(drive);
            return "https://thedwarfy01.github.io/mon-evolution/share.html?file="+id
                +(key==null?"":"&resourcekey="+Uri.encode(key));''')
rep(jpath,'    private String pendingInvitationId;',
          '    private String pendingInvitationId;\n    private String pendingInvitationResourceKey;')
rep(jpath,
    'pendingInvitationId=extractInvitationFileId(getIntent());',
    'pendingInvitationId=extractInvitationFileId(getIntent());\n        pendingInvitationResourceKey=extractInvitationResourceKey(getIntent());')
rep(jpath,'    private void deliverInvitation() {',
'''    private String extractInvitationResourceKey(Intent intent) {
        try {
            if(intent==null)return null;
            Uri uri=intent.getData();
            if(uri==null)return null;
            String value=uri.getQueryParameter("resourcekey");
            return value!=null && value.matches("[A-Za-z0-9_-]{3,200}")?value:null;
        }catch(Exception ignored){return null;}
    }

    private void deliverInvitation() {''')
rep(jpath,'''        String fileId=pendingInvitationId;
        pendingInvitationId=null;
        web.evaluateJavascript("window.receiveShareInvitation("+JSONObject.quote(fileId)+")",null);''',
'''        String fileId=pendingInvitationId;
        String resourceKey=pendingInvitationResourceKey;
        pendingInvitationId=null;
        pendingInvitationResourceKey=null;
        web.evaluateJavascript("window.receiveShareInvitation("+JSONObject.quote(fileId)
            +","+JSONObject.quote(resourceKey==null?"":resourceKey)+")",null);''')
rep(jpath,'''        if(fileId!=null){
            pendingInvitationId=fileId;
            if(appPageReady)deliverInvitation();
        }''',
'''        if(fileId!=null){
            pendingInvitationId=fileId;
            pendingInvitationResourceKey=extractInvitationResourceKey(intent);
            if(appPageReady)deliverInvitation();
        }''')
rep(jpath,'''byte[] body=fetchPublicProfile(id);''',
          '''byte[] body=fetchPublicProfile(id,driveResourceKey(url));''')
rep(jpath,'''body=fetchPublicProfile(fileId);''',
          '''body=fetchPublicProfile(fileId,driveResourceKey(source));''')
rep(jpath,
    '''String source="https://drive.google.com/file/d/"+id+"/view";''',
    '''String resourceKey=driveResourceKey(url);
                    String source="https://drive.google.com/file/d/"+id+"/view"
                        +(resourceKey==null?"":"?resourcekey="+Uri.encode(resourceKey));''')

# Show diagnostic categories instead of misleading "check access" for every error.
rep(jpath,
    '''                }catch(Exception e){js("sharedPublicFailed()");}
            });
        }''',
    '''                }catch(Exception e){
                    String reason=e.getMessage();
                    String code="invalid_json";
                    if("html".equals(reason))code="html";
                    else if("forbidden".equals(reason))code="forbidden";
                    else if("notfound".equals(reason))code="notfound";
                    else if("network".equals(reason))code="network";
                    else if("too_large".equals(reason))code="too_large";
                    js("sharedPublicFailed("+JSONObject.quote(code)+")");
                }
            });
        }''')

j=jpath.read_text(encoding="utf-8")
start=j.index("    private byte[] fetchPublicProfile(String id) throws Exception {")
end=j.index("    private String httpRead(String address,int limit) throws Exception {",start)
new_method=r'''    private String driveResourceKey(String link) {
        if(link==null)return null;
        try{
            Uri uri=Uri.parse(link);
            if(!"https".equalsIgnoreCase(uri.getScheme()) ||
               !"drive.google.com".equalsIgnoreCase(uri.getHost()))return null;
            String value=uri.getQueryParameter("resourcekey");
            return value!=null && value.matches("[A-Za-z0-9_-]{3,200}")?value:null;
        }catch(Exception ignored){return null;}
    }

    private boolean googleDriveDownloadHost(java.net.URL target) {
        if(!"https".equalsIgnoreCase(target.getProtocol()))return false;
        String host=target.getHost().toLowerCase(java.util.Locale.ROOT);
        return host.equals("drive.google.com")
            || host.equals("drive.usercontent.google.com")
            || host.equals("docs.google.com")
            || host.endsWith(".googleusercontent.com");
    }

    // Google Drive may return an HTML preview instead of the public JSON file.
    // These Google-hosted download forms are compatibility fallbacks, not a
    // replacement for an authenticated Google Drive API integration.
    private byte[] fetchPublicProfile(String id,String key) throws Exception {
        if(id==null || !id.matches("[A-Za-z0-9_-]{10,200}"))
            throw new Exception("notfound");
        if(key!=null && !key.matches("[A-Za-z0-9_-]{3,200}"))
            throw new Exception("forbidden");
        String suffix=key==null?"":"&resourcekey="+Uri.encode(key);
        String[] endpoints={
            "https://drive.usercontent.google.com/download?id="+id+"&export=download&confirm=t"+suffix,
            "https://drive.usercontent.google.com/download?id="+id+suffix,
            "https://drive.google.com/uc?export=download&id="+id+"&confirm=t"+suffix,
            "https://drive.google.com/uc?export=download&id="+id+suffix
        };
        String error="network";
        for(String endpoint:endpoints){
            try{
                byte[] body=downloadDriveCandidate(new java.net.URL(endpoint),id,key);
                String text=new String(body,StandardCharsets.UTF_8).trim();
                if(text.startsWith("\uFEFF"))text=text.substring(1).trim();
                if(!text.startsWith("{"))throw new Exception("html");
                JSONObject json;
                try{
                    json=new JSONObject(text);
                    if(!"mon-evolution-lecture-seule".equals(json.optString("format"))
                        || json.optInt("version")!=1)throw new Exception("invalid_json");
                    json.getJSONObject("profile").getJSONArray("entries");
                }catch(Exception ignored){throw new Exception("invalid_json");}
                return text.getBytes(StandardCharsets.UTF_8);
            }catch(Exception e){
                String code=e.getMessage();
                if("too_large".equals(code) || "invalid_json".equals(code))throw e;
                if("html".equals(code))error="html";
                else if("forbidden".equals(code)&&!"html".equals(error))error="forbidden";
                else if("notfound".equals(code)&&"network".equals(error))error="notfound";
            }
        }
        throw new Exception(error);
    }

    private byte[] downloadDriveCandidate(java.net.URL start,String fileId,String key)
        throws Exception {
        java.net.URL target=start;
        for(int hop=0;hop<7;hop++){
            if(!googleDriveDownloadHost(target))throw new Exception("forbidden");
            java.net.HttpURLConnection connection=
                (java.net.HttpURLConnection)target.openConnection();
            try{
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(15000);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept","application/json,application/octet-stream,*/*");
                connection.setRequestProperty("User-Agent","Mozilla/5.0 (Linux; Android 14) MonEvolutionIMC/1.6.4");
                if(key!=null)connection.setRequestProperty("X-Goog-Drive-Resource-Keys",
                    fileId+"/"+key);
                int status=connection.getResponseCode();
                if(status>=300&&status<400){
                    String location=connection.getHeaderField("Location");
                    if(location==null)throw new Exception("network");
                    target=new java.net.URL(target,location);
                    continue;
                }
                if(status==401||status==403)throw new Exception("forbidden");
                if(status==404||status==410)throw new Exception("notfound");
                if(status!=200)throw new Exception("network");
                try(InputStream in=connection.getInputStream()){
                    if(in==null)throw new Exception("network");
                    java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                    byte[] buffer=new byte[8192];
                    int read;
                    while((read=in.read(buffer))!=-1){
                        out.write(buffer,0,read);
                        if(out.size()>15_000_000)throw new Exception("too_large");
                    }
                    byte[] result=out.toByteArray();
                    String first=new String(result,0,Math.min(160,result.length),
                        StandardCharsets.UTF_8).trim().toLowerCase(java.util.Locale.ROOT);
                    if(first.startsWith("<!doctype")||first.startsWith("<html")
                        ||first.startsWith("<head")||first.startsWith("<body"))
                        throw new Exception("html");
                    return result;
                }
            }finally{connection.disconnect();}
        }
        throw new Exception("network");
    }
'''
j=j[:start]+new_method+j[end:]
jpath.write_text(j,encoding="utf-8")

rep(hpath,
'''function sharedPublicFailed(){alert('Le lien public n’a pas fourni un fichier JSON valide. Vérifie les autorisations Drive, ou choisis le fichier privé via le sélecteur Android. Certains liens Drive demandant une confirmation de téléchargement ne sont pas lisibles directement.');}''',
'''function sharedPublicFailed(reason){
 const errors={
  html:'Google Drive renvoie une page de prévisualisation plutôt que le fichier JSON. Essaie de sélectionner directement le fichier dans Google Drive.',
  forbidden:'Google Drive refuse le téléchargement direct (403). Vérifie les autorisations du fichier JSON lui-même, et pas seulement celles du dossier.',
  notfound:'Le fichier lié est introuvable. Demande à ton proche un nouveau lien vers le fichier JSON.',
  network:'La connexion à Google Drive a échoué. Vérifie la connexion et réessaie.',
  too_large:'Ce profil est trop volumineux pour être récupéré par un lien.',
  invalid_json:'Le document téléchargé ne contient pas un profil Mon Évolution compatible.',
  error:'Chargement impossible. Essaie de sélectionner le fichier directement dans Google Drive.'
 };
 const msg=errors[reason]||errors.error;
 $('shared-state').textContent=msg;
 alert(msg);
}''')

rep(hpath,''' let pendingId='';
 window.receiveShareInvitation=function(fileId){''',
''' let pendingId='';
 let pendingResourceKey='';
 window.receiveShareInvitation=function(fileId,resourceKey){''')
rep(hpath,
'''   const url='https://drive.google.com/file/d/'+fileId+'/view';
   $('shared-public-url').value=url;''',
'''   pendingResourceKey=typeof resourceKey==='string'&&/^[A-Za-z0-9_-]{3,200}$/.test(resourceKey)
      ?resourceKey:'';
   const url='https://drive.google.com/file/d/'+fileId+'/view'
      +(pendingResourceKey?'?resourcekey='+encodeURIComponent(pendingResourceKey):'');
   $('shared-public-url').value=url;''')
rep(hpath,
'''   window.AndroidBackup?.loadSharedPublic?.('https://drive.google.com/file/d/'+pendingId+'/view');''',
'''   const source='https://drive.google.com/file/d/'+pendingId+'/view'
     +(pendingResourceKey?'?resourcekey='+encodeURIComponent(pendingResourceKey):'');
   window.AndroidBackup?.loadSharedPublic?.(source);''')
rep(hpath,
'''   pendingId='';
   panel.hidden=true;
   $('shared-state').textContent='Invitation ignorée. Aucun profil n’a été ajouté.';''',
'''   pendingId='';
   pendingResourceKey='';
   panel.hidden=true;
   $('shared-state').textContent='Invitation ignorée. Aucun profil n’a été ajouté.';''')
rep(hpath,
''' window.onReceivedProfileLoaded=function(key,name){
   pendingId='';
   panel.hidden=true;''',
''' window.onReceivedProfileLoaded=function(key,name){
   pendingId='';
   pendingResourceKey='';
   panel.hidden=true;''')

assert "drive.usercontent.google.com/download?id=" in jpath.read_text(encoding="utf-8")
assert "fetchPublicProfile(id,driveResourceKey(url))" in jpath.read_text(encoding="utf-8")
assert "window.receiveShareInvitation=function(fileId,resourceKey)" in hpath.read_text(encoding="utf-8")
assert 'id="unified-profile-picker"' in hpath.read_text(encoding="utf-8")
print("Android v1.6.4 updated: Drive download fallbacks + resourcekey + detailed errors.")
