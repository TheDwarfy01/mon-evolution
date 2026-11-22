#!/usr/bin/env python3
"""v1.6.120: required preflight ONLY for user-opted-in editable child sharing.

The read-only mode and all other profiles are unchanged. Android verifies the
private SAF file, key, share identity and persisted grants. Google account
invitee and general-access settings cannot be read via SAF; owner attests to
those in the wizard, recipient proves the effective writable grant.
"""
from pathlib import Path
import shutil

assets=Path("android/source-1.6.120/app/src/main/assets")
java=Path("android/source-1.6.120/app/src/main/java/fr/monevolution/app/MainActivity.java")
src=java.read_text(encoding="utf-8")

def swap(old,new):
    global src
    n=src.count(old)
    if n!=1:raise AssertionError(f'Expected 1, saw {n} for {old[:100]}')
    src=src.replace(old,new)

# Toggling on is an INTENT, never by itself a grant to edit.
swap('''            SharedPreferences.Editor edit=prefs.edit().putBoolean("child_edit_"+id,value);''',
'''            SharedPreferences.Editor edit=prefs.edit()
                .putBoolean("child_edit_"+id,value)
                .putBoolean("child_setup_verified_"+id,false)
                .remove("child_preflight_at_"+id);''')

swap('''permission.put("editable",prefs.getBoolean("child_edit_"+id,false));''',
'''permission.put("editable",prefs.getBoolean("child_edit_"+id,false) &&
                prefs.getBoolean("child_setup_verified_"+id,false));''')

# JS cannot mark the setup as successful until native has checked the actual
# encrypted file in the past 60 seconds.
methods=r'''
        @JavascriptInterface public boolean childSetupVerified(String id) {
            return id!=null && id.matches("[a-zA-Z0-9_-]{1,75}") &&
                getPreferences(MODE_PRIVATE).getBoolean("child_setup_verified_"+id,false);
        }
        @JavascriptInterface public boolean completeOwnedChildSetup(String id) {
            if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}"))return false;
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            long at=prefs.getLong("child_preflight_at_"+id,0);
            if(!prefs.getBoolean("child_edit_"+id,false)||at<=0||
               System.currentTimeMillis()-at>60000)return false;
            return prefs.edit().putBoolean("child_setup_verified_"+id,true)
                .remove("child_preflight_at_"+id).commit();
        }
        @JavascriptInterface public void verifyOwnedChildShare(String id) {
            if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            io.execute(()->{
                JSONObject response=new JSONObject();
                SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                prefs.edit().remove("child_preflight_at_"+id).apply();
                try {
                    String reference=prefs.getString("share_uri_"+id,null);
                    boolean linked=reference!=null;
                    boolean password=prefs.contains("share_pass_"+id);
                    response.put("linked",linked);
                    response.put("password",password);
                    if(linked&&password){
                        Uri uri=Uri.parse(reference);
                        JSONObject doc=decodeShared(readSafJson(uri,40_000_000),
                            readSecret("share_pass_"+id));
                        JSONObject child=doc.getJSONObject("profile");
                        boolean isChild=isMinorProfile(child);
                        JSONObject policy=doc.optJSONObject("collaboration");
                        boolean same=policy!=null&&id.equals(policy.optString("profileId",""));
                        boolean read=safPersistedAccess(uri,false);
                        boolean write=safPersistedAccess(uri,true);
                        long actual=policy==null?0:policy.optLong("revision",0);
                        long known=prefs.getLong("child_revision_"+id,0);
                        boolean revisions=actual==known;
                        response.put("child",isChild);
                        response.put("sameProfile",same);
                        response.put("read",read);
                        response.put("write",write);
                        response.put("revisionMatches",revisions);
                        if(isChild&&same&&read&&write&&revisions&&
                           prefs.getBoolean("child_edit_"+id,false))
                            prefs.edit().putLong("child_preflight_at_"+id,
                                System.currentTimeMillis()).apply();
                    }
                }catch(Exception ignored){}
                js("childOwnerVerificationResult("+JSONObject.quote(id)+","+
                    JSONObject.quote(response.toString())+")");
            });
        }
        @JavascriptInterface public void verifyReceivedChildShare(String key) {
            if(key==null||!isReceivedSaved(key))return;
            io.execute(()->{
                JSONObject response=new JSONObject();
                SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                prefs.edit().putBoolean("child_receiver_verified_"+key,false).apply();
                try{
                    JSONArray saved=new JSONArray(prefs.getString("received_profiles","[]"));
                    JSONObject selected=null;
                    for(int i=0;i<saved.length();i++){
                        JSONObject item=saved.getJSONObject(i);
                        if(key.equals(item.optString("key"))){selected=item;break;}
                    }
                    boolean privateFile=selected!=null&&"private".equals(selected.optString("kind"));
                    response.put("private",privateFile);
                    if(privateFile){
                        Uri uri=Uri.parse(selected.getString("source"));
                        boolean read=safPersistedAccess(uri,false);
                        boolean write=safPersistedAccess(uri,true);
                        response.put("read",read);
                        response.put("write",write);
                        JSONObject doc=readFriendDocument(selected,key);
                        JSONObject child=doc.getJSONObject("profile");
                        JSONObject policy=doc.optJSONObject("collaboration");
                        boolean allowed=policy!=null&&policy.optBoolean("editable",false);
                        boolean isChild=isMinorProfile(child);
                        response.put("password",true);
                        response.put("editable",allowed);
                        response.put("child",isChild);
                        if(allowed&&isChild&&read&&write)
                            prefs.edit().putBoolean("child_receiver_verified_"+key,true).apply();
                    }
                }catch(Exception ignored){}
                js("childReceiverVerificationResult("+JSONObject.quote(key)+","+
                    JSONObject.quote(response.toString())+")");
            });
        }
'''
swap('''        @JavascriptInterface public void updateReceivedChild(String key,String payload) {''',
methods+'''        @JavascriptInterface public void updateReceivedChild(String key,String payload) {''')

swap('''            if(!isReceivedSaved(key)||payload==null||payload.length()>20000){''',
'''            if(!isReceivedSaved(key)||payload==null||payload.length()>20000||
               !getPreferences(MODE_PRIVATE).getBoolean("child_receiver_verified_"+key,false)){''')

# Helper is in MainActivity, not in the Bridge.
helper=r'''
    private boolean safPersistedAccess(Uri uri,boolean forWrite){
        if(uri==null)return false;
        for(android.content.UriPermission grant:
            getContentResolver().getPersistedUriPermissions()){
            if(uri.equals(grant.getUri())&&grant.isReadPermission()&&
                (!forWrite||grant.isWritePermission()))return true;
        }
        return false;
    }
'''
swap('''    private boolean isMinorProfile(JSONObject p) {''',
helper+'''    private boolean isMinorProfile(JSONObject p) {''')

# A successful preflight is not the same as a successfully published edit
# grant. Keep the wizard open until the existing asynchronous Drive write ends.
swap('''                        if(prefs.contains("child_revision_"+id))
                            prefs.edit().putLong("child_revision_"+id,
                                prefs.getLong("child_revision_"+id,0)+1).apply();
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));
                    } catch(Exception e) {
                        // A broken Drive permission must not interrupt meal editing.
                        js("sharedSyncFailed()");''',
'''                        if(prefs.contains("child_revision_"+id))
                            prefs.edit().putLong("child_revision_"+id,
                                prefs.getLong("child_revision_"+id,0)+1).apply();
                        if(prefs.getBoolean("child_setup_verified_"+id,false))
                            js("childOwnerSetupPublished("+JSONObject.quote(id)+")");
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));
                    } catch(Exception e) {
                        // This catch is outside the try's prefs declaration scope.
                        // Use the enclosing Activity preferences explicitly.
                        if(getPreferences(MODE_PRIVATE).getBoolean("child_setup_verified_"+id,false)){
                            getPreferences(MODE_PRIVATE).edit().putBoolean("child_setup_verified_"+id,false).apply();
                            js("childOwnerSetupPublishFailed("+JSONObject.quote(id)+")");
                        }
                        js("sharedSyncFailed()");''')

java.write_text(src,encoding="utf-8")
page=assets/"index.html"
html=page.read_text(encoding="utf-8")
needle="</body></html>"
assert html.count(needle)==1 and "child-share-verification.js" not in html
page.write_text(html.replace(needle,
    '<script src="child-share-verification.js"></script>\n'+needle),
    encoding="utf-8")
shutil.copyfile("android/body/child-share-verification.js",
    assets/"child-share-verification.js")
print("v1.6.120: optional child editing now requires mandatory secure native preflight")
