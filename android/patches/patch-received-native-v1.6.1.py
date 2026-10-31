#!/usr/bin/env python3
"""Native portion of Mon Evolution 1.6.1 shared-profile switcher."""
from pathlib import Path

app=Path("android/source-1.6.0/app")
jpath=Path("android/source-1.6.1/app/src/main/java/fr/monevolution/app/MainActivity.java")
jpath.parent.mkdir(parents=True,exist_ok=True)
j=(app/"src/main/java/fr/monevolution/app/MainActivity.java").read_text(encoding="utf-8")

def rep(a,b):
    global j
    count=j.count(a)
    assert count==1,(count,a[:95])
    j=j.replace(a,b)

newmethods=Path("android/patches/received-profiles-v1.6.1.java.txt").read_text(encoding="utf-8")
rep("        @JavascriptInterface public void loadSharedPublic(String url) {",newmethods+"        @JavascriptInterface public void loadSharedPublic(String url) {")
rep('''                    doc.getJSONObject("profile").getJSONArray("entries");
                    String b64=android.util.Base64.encodeToString(body,android.util.Base64.NO_WRAP);
                    getPreferences(MODE_PRIVATE).edit()
                        .putString("received_public_url","https://drive.google.com/file/d/"+id+"/view")
                        .remove("received_share_uri").apply();
                    js("sharedLoaded("+JSONObject.quote(b64)+")");''',
'''                    validateReceived(doc);
                    String source="https://drive.google.com/file/d/"+id+"/view";
                    String key=registerReceived("public",source,doc);
                    String b64=android.util.Base64.encodeToString(body,android.util.Base64.NO_WRAP);
                    getPreferences(MODE_PRIVATE).edit()
                        .remove("received_public_url").remove("received_share_uri")
                        .putString("received_selected",key).apply();
                    js("sharedLoaded("+JSONObject.quote(b64)+","+JSONObject.quote(key)+")");''')
rep('''        @JavascriptInterface public void refreshShared() {
            String publicUrl=getPreferences(MODE_PRIVATE).getString("received_public_url",null);
            if(publicUrl!=null) {loadSharedPublic(publicUrl);return;}
            String value=getPreferences(MODE_PRIVATE).getString("received_share_uri", null);
            if(value!=null)loadShared(Uri.parse(value));
        }''',
'''        @JavascriptInterface public void refreshShared() {
            String key=getPreferences(MODE_PRIVATE).getString("received_selected",null);
            if(key!=null){selectReceivedProfile(key);return;}
            String publicUrl=getPreferences(MODE_PRIVATE).getString("received_public_url",null);
            if(publicUrl!=null){loadSharedPublic(publicUrl);return;}
            String value=getPreferences(MODE_PRIVATE).getString("received_share_uri",null);
            if(value!=null)loadShared(Uri.parse(value));
        }''')
rep('''            } else if (request == SHARE_OPEN) {
                persistUri(uri, false);
                getPreferences(MODE_PRIVATE).edit()
                    .remove("received_public_url")
                    .putString("received_share_uri", uri.toString()).apply();
                loadShared(uri);''',
'''            } else if (request == SHARE_OPEN) {
                if(!persistUri(uri,false))
                    throw new Exception("Le fournisseur ne permet pas de conserver l’accès");
                getPreferences(MODE_PRIVATE).edit()
                    .remove("received_public_url").remove("received_share_uri").apply();
                loadShared(uri);''')
rep('''    private void loadShared(Uri uri) {
        io.execute(() -> {
            try(InputStream in=getContentResolver().openInputStream(uri)) {
                if(in==null)throw new Exception("Fichier partagé inaccessible");
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                byte[] buffer=new byte[8192];
                int n;
                while((n=in.read(buffer))!=-1) {
                    out.write(buffer,0,n);
                    if(out.size()>40_000_000)throw new Exception("Fichier trop volumineux");
                }
                // Decode and validate in the read-only JS view.
                String encoded=android.util.Base64.encodeToString(
                    out.toByteArray(),android.util.Base64.NO_WRAP);
                runOnUiThread(() -> web.evaluateJavascript("sharedLoaded('"+encoded+"')",null));
            } catch(Exception e) {
                runOnUiThread(() -> web.evaluateJavascript("sharedReadFailed()",null));
            }
        });
    }''',
'''    private void loadShared(Uri uri) {
        io.execute(() -> {
            try {
                String raw=readSafJson(uri,40_000_000);
                JSONObject doc=new JSONObject(raw);
                validateReceived(doc);
                String key=registerReceived("private",uri.toString(),doc);
                getPreferences(MODE_PRIVATE).edit().putString("received_selected",key).apply();
                String encoded=android.util.Base64.encodeToString(
                    raw.getBytes(StandardCharsets.UTF_8),android.util.Base64.NO_WRAP);
                js("sharedLoaded("+JSONObject.quote(encoded)+","+JSONObject.quote(key)+")");
            }catch(Exception e){js("sharedReadFailed()");}
        });
    }''')
helpers=r'''    // The indexed list is local metadata. Never merge received profiles into the
    // editable backup data and never delete a remote document when forgetting one.
    private void validateReceived(JSONObject doc) throws Exception {
        if(!"mon-evolution-lecture-seule".equals(doc.optString("format"))
            || doc.optInt("version")!=1)throw new Exception("Format de partage invalide");
        JSONObject p=doc.getJSONObject("profile");
        String name=p.getString("name");
        if(name.trim().isEmpty() || name.length()>100)throw new Exception("Nom invalide");
        double height=p.getDouble("height"),goal=p.getDouble("goal");
        if(!Double.isFinite(height) || height<80 || height>250 ||
            !Double.isFinite(goal) || goal<25 || goal>400)
            throw new Exception("Données du profil invalides");
        JSONArray entries=p.getJSONArray("entries");
        if(entries.length()<1 || entries.length()>20000)
            throw new Exception("Historique invalide");
        for(int i=0;i<entries.length();i++){
            JSONObject e=entries.getJSONObject(i);
            double w=e.getDouble("weight");
            if(!Double.isFinite(w)||w<25||w>400||
                !e.getString("date").matches("\\d{4}-\\d{2}-\\d{2}"))
                throw new Exception("Pesée invalide");
        }
    }
    private synchronized String registerReceived(String kind,String source,JSONObject doc)
        throws Exception {
        validateReceived(doc);
        if(!"public".equals(kind)&&!"private".equals(kind))
            throw new Exception("Source de partage inconnue");
        if(source==null || source.length()>2500)
            throw new Exception("Lien Drive invalide");
        android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
        JSONArray list;
        try{list=new JSONArray(prefs.getString("received_profiles","[]"));}
        catch(Exception ignored){list=new JSONArray();}
        String name=doc.getJSONObject("profile").getString("name");
        for(int i=0;i<list.length();i++){
            JSONObject entry=list.getJSONObject(i);
            if(kind.equals(entry.optString("kind")) &&
                source.equals(entry.optString("source"))){
                entry.put("name",name);
                prefs.edit().putString("received_profiles",list.toString()).apply();
                return entry.getString("key");
            }
        }
        if(list.length()>=100)throw new Exception("Trop de profils partagés");
        String key=java.util.UUID.randomUUID().toString();
        JSONObject item=new JSONObject();
        item.put("key",key);
        item.put("name",name);
        item.put("kind",kind);
        item.put("source",source);
        list.put(item);
        prefs.edit().putString("received_profiles",list.toString()).apply();
        return key;
    }

'''
rep('    private String stringHash(String value) throws Exception {',
    helpers+'    private String stringHash(String value) throws Exception {')
jpath.write_text(j,encoding="utf-8")
print("Native receiver index patched (multiple private/public Drive sources, no writes to owner data).")
