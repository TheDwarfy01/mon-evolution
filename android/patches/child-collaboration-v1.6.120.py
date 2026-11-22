#!/usr/bin/env python3
"""v1.6.120: opt-in writable minor-only collaboration via private Android SAF.
Owner's profiles remain local; received edits do not enter other local profiles.
All writes re-read and validate the encrypted document first. No public write.
"""
from pathlib import Path
import shutil

assets=Path("android/source-1.6.120/app/src/main/assets")
java=Path("android/source-1.6.120/app/src/main/java/fr/monevolution/app/MainActivity.java")
source=java.read_text(encoding="utf-8")
def swap(old,new):
    global source
    count=source.count(old)
    if count!=1: raise AssertionError(f'Expected one {old[:85]!r}, found {count}')
    source=source.replace(old,new)

bridge=r'''
        @JavascriptInterface public boolean childEditEnabled(String id) {
            return id!=null && id.matches("[a-zA-Z0-9_-]{1,75}") &&
                getPreferences(MODE_PRIVATE).getBoolean("child_edit_"+id,false);
        }
        @JavascriptInterface public void setChildEditEnabled(String id,boolean value) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            SharedPreferences.Editor edit=prefs.edit().putBoolean("child_edit_"+id,value);
            if(!prefs.contains("child_revision_"+id))edit.putLong("child_revision_"+id,0);
            edit.apply();
        }
        // SAF exposes only the chosen private document, never other profiles.
        @JavascriptInterface public void updateReceivedChild(String key,String payload) {
            if(!isReceivedSaved(key)||payload==null||payload.length()>20000){
                childResult(key,"denied",null);return;
            }
            io.execute(()->{
                try {
                    JSONObject request=new JSONObject(payload);
                    String date=request.getString("date");
                    if(!date.matches("\\d{4}-\\d{2}-\\d{2}")
                        ||date.compareTo(new java.text.SimpleDateFormat("yyyy-MM-dd",
                            java.util.Locale.US).format(new java.util.Date()))>0)
                        throw new SecurityException("bad date");
                    JSONArray list=new JSONArray(getPreferences(MODE_PRIVATE)
                        .getString("received_profiles","[]"));
                    JSONObject item=null;
                    for(int i=0;i<list.length();i++){
                        JSONObject candidate=list.getJSONObject(i);
                        if(key.equals(candidate.optString("key"))){item=candidate;break;}
                    }
                    if(item==null||!"private".equals(item.optString("kind")))
                        throw new SecurityException("Private Drive file required");
                    Uri uri=Uri.parse(item.getString("source"));
                    // A revoked Drive Editor permission will also fail writeShared.
                    boolean writable=false;
                    for(android.content.UriPermission grant:
                        getContentResolver().getPersistedUriPermissions()){
                        if(uri.equals(grant.getUri())&&grant.isWritePermission())
                            writable=true;
                    }
                    if(!writable){childResult(key,"access",null);return;}
                    JSONObject doc=readFriendDocument(item,key);
                    JSONObject policy=doc.optJSONObject("collaboration");
                    JSONObject p=doc.getJSONObject("profile");
                    if(policy==null||!policy.optBoolean("editable",false)||
                       !policy.optString("profileId","").matches("[a-zA-Z0-9_-]{1,75}")||
                       !isMinorProfile(p)){
                        childResult(key,"denied",null);return;
                    }
                    JSONArray entries=p.getJSONArray("entries");
                    JSONObject row=null;
                    for(int i=0;i<entries.length();i++){
                        JSONObject old=entries.getJSONObject(i);
                        if(date.equals(old.optString("date")) && (row==null || old.optLong("id",0)>=row.optLong("id",0)))row=old;
                    }
                    boolean changeWeight=request.has("weight"),changeHeight=request.has("heightCm");
                    String kind=request.optString("mealKey","");
                    boolean changeMeal=!kind.isEmpty();
                    if(!changeWeight&&!changeHeight&&!changeMeal)
                        throw new SecurityException("Nothing to change");
                    if(changeWeight||changeHeight){
                        String expected=request.optString("expectedRow","");
                        if(row==null && !expected.isEmpty() ||
                           row!=null && expected.isEmpty()){
                            childResult(key,"conflict",null);return;
                        }
                        if(row!=null){
                            JSONObject previous=new JSONObject(expected);
                            if(changeWeight &&
                              (!previous.has("weight") ||
                               Math.abs(previous.optDouble("weight",-1)-row.optDouble("weight",-2))>0.00001)){
                                childResult(key,"conflict",null);return;
                            }
                            if(changeHeight &&
                              (previous.has("heightCm")!=row.has("heightCm") ||
                               (row.has("heightCm") &&
                                Math.abs(previous.optDouble("heightCm",-1)-row.optDouble("heightCm",-2))>0.00001))){
                                childResult(key,"conflict",null);return;
                            }
                        }
                        if(row==null && !changeWeight)throw new SecurityException("Missing first weight");
                        if(row==null){
                            if(entries.length()>=20000)throw new SecurityException("Too many weights");
                            row=new JSONObject();
                            row.put("id",System.currentTimeMillis());
                            row.put("date",date);
                            row.put("note","");
                            entries.put(row);
                        }
                        if(changeWeight){
                            double w=request.getDouble("weight");
                            if(!Double.isFinite(w)||w<1||w>400)
                                throw new SecurityException("Invalid weight");
                            row.put("weight",w);
                        }
                        if(changeHeight){
                            double h=request.getDouble("heightCm");
                            if(!Double.isFinite(h)||h<45||h>250)
                                throw new SecurityException("Invalid height");
                            row.put("heightCm",h);
                            p.put("height",h);
                        }
                    }
                    if(changeMeal){
                        if(!java.util.Arrays.asList("morning","morningSnack","lunch",
                              "afternoonSnack","dinner","eveningSnack").contains(kind))
                            throw new SecurityException("Invalid meal key");
                        String value=request.getString("mealText");
                        if(value.length()>3000)throw new SecurityException("Meal too long");
                        JSONObject meals=p.optJSONObject("meals");
                        if(meals==null){meals=new JSONObject();p.put("meals",meals);}
                        JSONObject day=meals.optJSONObject(date);
                        if(day==null){day=new JSONObject();meals.put(date,day);}
                        String previous=day.optString(kind,"");
                        if(!previous.equals(request.optString("expectedMeal",""))){
                            childResult(key,"conflict",null);return;
                        }
                        day.put(kind,value);
                    }
                    long revision=policy.optLong("revision",0);
                    if(revision<0 || revision>=Integer.MAX_VALUE)
                        throw new SecurityException("Revision invalid");
                    policy.put("revision",revision+1);
                    policy.put("lastChange","parent");
                    doc.put("exportedAt",new java.text.SimpleDateFormat(
                        "yyyy-MM-dd'T'HH:mm:ss'Z'",java.util.Locale.US)
                        {{setTimeZone(java.util.TimeZone.getTimeZone("UTC"));}}
                        .format(new java.util.Date()));
                    validateReceived(doc);
                    String encrypted=encryptShared(doc.toString(),readSecret("receive_pass_"+key));
                    writeShared(uri,encrypted);
                    updateFriendSummary(key,doc);
                    childResult(key,"ok",doc);
                }catch(SecurityException bad){childResult(key,"denied",null);}
                catch(Exception error){childResult(key,"error",null);}
            });
        }
        @JavascriptInterface public void syncOwnedChild(String id) {
            if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            io.execute(()->{
                try {
                    SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                    String value=prefs.getString("share_uri_"+id,null);
                    if(value==null||!prefs.contains("child_revision_"+id))
                        throw new Exception("Not linked");
                    JSONObject doc=decodeShared(readSafJson(Uri.parse(value),40_000_000),
                        readSecret("share_pass_"+id));
                    if(!isMinorProfile(doc.getJSONObject("profile")))
                        throw new Exception("Not a child");
                    JSONObject receivedPolicy=doc.optJSONObject("collaboration");
                    if(receivedPolicy!=null && !id.equals(receivedPolicy.optString("profileId",id)))
                        throw new Exception("Wrong profile");
                    JSONObject policy=doc.optJSONObject("collaboration");
                    long actual=policy==null?0:policy.optLong("revision",0);
                    long known=prefs.getLong("child_revision_"+id,0);
                    if(actual==known) {
                        js("childOwnerSyncResult("+JSONObject.quote(id)+",'uptodate',null)");
                        return;
                    }
                    prefs.edit().putLong("child_pending_revision_"+id,actual).apply();
                    String b64=android.util.Base64.encodeToString(doc.toString()
                        .getBytes(StandardCharsets.UTF_8),android.util.Base64.NO_WRAP);
                    js("childOwnerSyncResult("+JSONObject.quote(id)+",'update',"+
                       JSONObject.quote(b64)+")");
                }catch(Exception e){
                    js("childOwnerSyncResult("+JSONObject.quote(id)+",'error',null)");
                }
            });
        }
        @JavascriptInterface public boolean ackOwnedChild(String id,long revision) {
            if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}")||revision<0)return false;
            SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            if(prefs.getLong("child_pending_revision_"+id,-1)!=revision)return false;
            prefs.edit().putLong("child_revision_"+id,revision)
                .remove("child_pending_revision_"+id).apply();
            return true;
        }
'''
swap('        @JavascriptInterface public String sharedStatus(String id) {',
     bridge+'        @JavascriptInterface public String sharedStatus(String id) {')

helpers=r'''
    private boolean isMinorProfile(JSONObject p) {
        try {
            String birth=p.optString("birthDate","");
            if(!birth.matches("\\d{4}-\\d{2}-\\d{2}"))return false;
            int year=Integer.parseInt(birth.substring(0,4));
            int month=Integer.parseInt(birth.substring(5,7));
            int day=Integer.parseInt(birth.substring(8,10));
            java.util.Calendar born=java.util.Calendar.getInstance();
            born.setLenient(false);born.clear();
            born.set(year,month-1,day);
            born.getTimeInMillis();
            java.util.Calendar now=java.util.Calendar.getInstance();
            if(born.after(now))return false;
            int age=now.get(java.util.Calendar.YEAR)-year;
            if(now.get(java.util.Calendar.MONTH)<month-1 ||
               (now.get(java.util.Calendar.MONTH)==month-1 &&
                now.get(java.util.Calendar.DAY_OF_MONTH)<day))age--;
            return age>=0&&age<18;
        }catch(Exception e){return false;}
    }
    private long childRevision(String id,Uri uri) throws Exception {
        JSONObject remote=decodeShared(readSafJson(uri,40_000_000),
            readSecret("share_pass_"+id));
        JSONObject policy=remote.optJSONObject("collaboration");
        if(policy!=null&&!id.equals(policy.optString("profileId",id)))
            throw new Exception("Another child profile");
        return policy==null?0:policy.optLong("revision",0);
    }
    private void childResult(String key,String status,JSONObject document) {
        try {
            String b64=document==null?"":android.util.Base64.encodeToString(
                document.toString().getBytes(StandardCharsets.UTF_8),
                android.util.Base64.NO_WRAP);
            js("childEditResult("+JSONObject.quote(key==null?"":key)+","+
                JSONObject.quote(status)+","+JSONObject.quote(b64)+")");
        }catch(Exception ignored){}
    }
'''
swap('    private String makeSharedDocument(String id, JSONObject input) throws Exception {',
     helpers+'    private String makeSharedDocument(String id, JSONObject input) throws Exception {')

swap('''        if(birth.matches("\\\\d{4}-\\\\d{2}-\\\\d{2}") && ("male".equals(sex)||"female".equals(sex))){
            profile.put("birthDate",birth);
            profile.put("sex",sex);
        }''',
'''        if(birth.matches("\\\\d{4}-\\\\d{2}-\\\\d{2}"))profile.put("birthDate",birth);
        if("male".equals(sex)||"female".equals(sex))profile.put("sex",sex);''')
swap('''        document.put("profile",profile);
        String result=document.toString();''',
'''        document.put("profile",profile);
        SharedPreferences prefs=getPreferences(MODE_PRIVATE);
        if(isMinorProfile(profile) && prefs.contains("child_revision_"+id)){
            JSONObject permission=new JSONObject();
            permission.put("profileId",id);
            permission.put("editable",prefs.getBoolean("child_edit_"+id,false));
            permission.put("revision",prefs.getLong("child_revision_"+id,0)+1);
            document.put("collaboration",permission);
        }
        String result=document.toString();''')

swap('''                                writeShared(Uri.parse(linked), payload);
                                runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));''',
'''                                SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                                if(prefs.contains("child_revision_"+profileId)){
                                    long known=prefs.getLong("child_revision_"+profileId,0);
                                    if(childRevision(profileId,Uri.parse(linked))!=known){
                                        js("childOwnerNeedsSync("+JSONObject.quote(profileId)+")");
                                        return;
                                    }
                                }
                                writeShared(Uri.parse(linked), payload);
                                if(prefs.contains("child_revision_"+profileId))
                                    prefs.edit().putLong("child_revision_"+profileId,
                                        prefs.getLong("child_revision_"+profileId,0)+1).apply();
                                runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));''')

swap('''                writeShared(uri, payload);
                if (retained) getPreferences(MODE_PRIVATE).edit()''',
'''                writeShared(uri, payload);
                if(getPreferences(MODE_PRIVATE).contains("child_revision_"+id))
                    getPreferences(MODE_PRIVATE).edit().putLong("child_revision_"+id,
                        getPreferences(MODE_PRIVATE).getLong("child_revision_"+id,0)+1).apply();
                if (retained) getPreferences(MODE_PRIVATE).edit()''')

swap('''                    try {
                        String document=makeSharedDocument(id,p);
                        writeShared(Uri.parse(value),document);
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));''',
'''                    try {
                        SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                        if(prefs.contains("child_revision_"+id)){
                            long known=prefs.getLong("child_revision_"+id,0);
                            if(childRevision(id,Uri.parse(value))!=known){
                                js("childOwnerNeedsSync("+JSONObject.quote(id)+")");
                                continue;
                            }
                        }
                        String document=makeSharedDocument(id,p);
                        writeShared(Uri.parse(value),document);
                        if(prefs.contains("child_revision_"+id))
                            prefs.edit().putLong("child_revision_"+id,
                                prefs.getLong("child_revision_"+id,0)+1).apply();
                        runOnUiThread(() -> web.evaluateJavascript("sharedUpdated()",null));''')

swap('''                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, SHARE_OPEN);''',
'''                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, SHARE_OPEN);''')
swap('''            } else if (request == SHARE_OPEN) {
                if(!persistUri(uri,false))
                    throw new Exception("Le fournisseur ne permet pas de conserver l’accès");''',
'''            } else if (request == SHARE_OPEN) {
                if(!persistUri(uri,false))
                    throw new Exception("Le fournisseur ne permet pas de conserver l’accès");
                // Optional: a Reader may still open. Only Drive Editors get write permission.
                persistUri(uri,true);''')

# Invitation wording must reflect the permission granted to the selected child.
swap(r'''                    send.putExtra(Intent.EXTRA_TEXT,"Je t’invite à consulter mon profil Mon Évolution IMC en lecture seule. Ouvre ce lien sur ton téléphone, puis choisis « Ouvrir dans Mon Évolution » :\n"+url);''',
r'''                    String introduction=getPreferences(MODE_PRIVATE)
                        .getBoolean("child_edit_"+id,false)
                        ? "Je t’invite à modifier le suivi de notre enfant dans Mon Évolution IMC. Il faut un accès Éditeur privé au fichier Google Drive."
                        : "Je t’invite à consulter mon profil Mon Évolution IMC en lecture seule.";
                    send.putExtra(Intent.EXTRA_TEXT,introduction+
                        " Ouvre ce lien sur ton téléphone, puis choisis « Ouvrir dans Mon Évolution » :\n"+url);''')

java.write_text(source,encoding="utf-8")
html=assets/"index.html"
s=html.read_text(encoding="utf-8")
needle="</body></html>"
assert s.count(needle)==1
assert "child-collaboration.js" not in s
s=s.replace(needle,'<script src="child-collaboration.js"></script>\n'+needle)
html.write_text(s,encoding="utf-8")
shutil.copyfile("android/body/child-collaboration.js",assets/"child-collaboration.js")
print("v1.6.120: private child editing and conflict-aware owner synchronization installed")
