#!/usr/bin/env python3
"""v1.6.20 advanced analytical graphs and secure on-demand comparison bridge."""
from pathlib import Path
root=Path("android/source-1.6.20/app")
h=root/"src/main/assets/index.html"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1:raise AssertionError(f"{path}: {n} matches for {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 35","versionCode 36")
R(g,"versionName '1.6.19'","versionName '1.6.20'")
R(m,'android:versionCode="35" android:versionName="1.6.19"','android:versionCode="36" android:versionName="1.6.20"')
R(j,"MonEvolutionIMC/1.6.19","MonEvolutionIMC/1.6.20")
R(h,'Version installée : <strong>1.6.19</strong>','Version installée : <strong>1.6.20</strong>')
R(h,'const installed="1.6.19";','const installed="1.6.20";')
# Preserve selected friend and its read-only tabs. Add specialized graph rendering
# only when a friend opens the 'Courbe' page.
R(h,'''  area.append(section);
  showUnifiedTab(tab);
  // showUnifiedTab may render editable personal meal fields in the background;''',
'''  area.append(section);
  if(tab==='chart')window.onFriendChartView?.(section);
  showUnifiedTab(tab);
  // showUnifiedTab may render editable personal meal fields in the background;''')
# Asynchronous comparison reads do not alter selected profile or the share file.
R(j,'        @JavascriptInterface public void selectReceivedProfile(String key) {',
'''        @JavascriptInterface public void loadComparisonProfile(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return;
            io.execute(() -> {
                try {
                    JSONArray saved=new JSONArray(getPreferences(MODE_PRIVATE)
                        .getString("received_profiles","[]"));
                    JSONObject item=null;
                    for(int i=0;i<saved.length();i++){
                        JSONObject candidate=saved.getJSONObject(i);
                        if(key.equals(candidate.optString("key"))){item=candidate;break;}
                    }
                    if(item==null)throw new Exception("Profil non enregistré");
                    String kind=item.getString("kind"),source=item.getString("source");
                    String raw;
                    if("public".equals(kind)){
                        String file=driveFileId(source);
                        if(file==null)throw new Exception("Lien invalide");
                        raw=new String(fetchPublicProfile(file,driveResourceKey(source)),
                            StandardCharsets.UTF_8);
                    }else if("private".equals(kind)){
                        raw=readSafJson(Uri.parse(source),40_000_000);
                    }else throw new Exception("Type non autorisé");
                    JSONObject doc=decodeShared(raw,readSecret("receive_pass_"+key));
                    validateReceived(doc);
                    JSONObject received=doc.getJSONObject("profile");
                    // Comparison is restricted to read-only weight measures.
                    JSONObject output=new JSONObject();
                    output.put("name",received.getString("name"));
                    output.put("height",received.getDouble("height"));
                    output.put("goal",received.getDouble("goal"));
                    output.put("entries",received.getJSONArray("entries"));
                    String b64=android.util.Base64.encodeToString(
                        output.toString().getBytes(StandardCharsets.UTF_8),
                        android.util.Base64.NO_WRAP);
                    js("comparisonProfileLoaded("+JSONObject.quote(key)+","+
                       JSONObject.quote(b64)+")");
                }catch(Exception e){
                    js("comparisonProfileFailed("+JSONObject.quote(key)+")");
                }
            });
        }
        @JavascriptInterface public void selectReceivedProfile(String key) {''')
src=Path("android/patches/advanced-weight-graphs-v1.6.20.js").read_text(encoding="utf-8")
if "</script>" in src:raise AssertionError("Source must not contain closing script tags")
R(h,'</body></html>','<script>\n'+src+'\n</script>\n</body></html>')
assert "loadComparisonProfile" in j.read_text(encoding="utf-8")
print("v1.6.20 advanced weight graphs and secure comparison bridge added")
