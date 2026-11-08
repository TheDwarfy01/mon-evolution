#!/usr/bin/env python3
"""v1.6.20: advanced weight analysis, local and authorized shared comparisons."""
from pathlib import Path
root=Path("android/source-1.6.20/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(p,a,b):
 s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1: raise AssertionError(f"{p}: {n} occurrences of {a[:110]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 35","versionCode 36")
R(g,"versionName '1.6.19'","versionName '1.6.20'")
R(m,'android:versionCode="35" android:versionName="1.6.19"','android:versionCode="36" android:versionName="1.6.20"')
R(j,'MonEvolutionIMC/1.6.19','MonEvolutionIMC/1.6.20')
R(h,'Version installée : <strong>1.6.19</strong>','Version installée : <strong>1.6.20</strong>')
R(h,'const installed="1.6.19";','const installed="1.6.20";')
R(j,'        @JavascriptInterface public String listReceivedProfiles() {',
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
                    if(item==null)throw new Exception("Profil introuvable");
                    String kind=item.getString("kind");
                    String source=item.getString("source");
                    String raw;
                    if("public".equals(kind)){
                        String driveId=driveFileId(source);
                        if(driveId==null)throw new Exception("Lien non valide");
                        raw=new String(fetchPublicProfile(driveId,driveResourceKey(source)),StandardCharsets.UTF_8);
                    }else if("private".equals(kind)){
                        raw=readSafJson(Uri.parse(source),40_000_000);
                    }else throw new Exception("Type non valide");
                    JSONObject document=decodeShared(raw,readSecret("receive_pass_"+key));
                    validateReceived(document);
                    JSONObject original=document.getJSONObject("profile");
                    JSONObject output=new JSONObject();
                    output.put("name",original.getString("name"));
                    output.put("goal",original.getDouble("goal"));
                    output.put("height",original.getDouble("height"));
                    output.put("entries",original.getJSONArray("entries"));
                    String encoded=android.util.Base64.encodeToString(
                        output.toString().getBytes(StandardCharsets.UTF_8),
                        android.util.Base64.NO_WRAP);
                    js("comparisonProfileLoaded("+JSONObject.quote(key)+","+
                        JSONObject.quote(encoded)+")");
                }catch(Exception error){
                    js("comparisonProfileFailed("+JSONObject.quote(key)+")");
                }
            });
        }

        @JavascriptInterface public String listReceivedProfiles() {''')
# Extend the friend's chart hook without disturbing its read-only other tabs.
R(h,"  area.append(section);\n  showUnifiedTab(tab);",
'''  area.append(section);
  showUnifiedTab(tab);
  if(tab==='chart' && typeof window.onFriendChartView==='function')
    window.onFriendChartView(section);''')
js=Path("android/patches/advanced-weight-graphs-v1.6.20.js").read_text(encoding="utf-8")
R(h,'</body></html>',"<script>\n"+js+"\n</script>\n</body></html>")
assert 'height:210px' in h.read_text(encoding="utf-8")
assert 'comparisonProfileLoaded' in h.read_text(encoding="utf-8")
print("v1.6.20: advanced graph tabs, weekly trends, projection and read-only friend comparisons ready")
