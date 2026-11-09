#!/usr/bin/env python3
"""v1.6.29: explicit timestamped shared-sync status and startup release checking."""
from pathlib import Path
root=Path("android/source-1.6.29/app")
h=root/"src/main/assets/index.html";j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle";m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8");count=s.count(old)
 if count!=1:raise AssertionError(f"{path}: found {count} occurrences of {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 44","versionCode 45")
R(g,"versionName '1.6.28'","versionName '1.6.29'")
R(m,'android:versionCode="44" android:versionName="1.6.28"','android:versionCode="45" android:versionName="1.6.29"')
R(j,'MonEvolutionIMC/1.6.28','MonEvolutionIMC/1.6.29')
R(h,'Version installée : <strong>1.6.28</strong>','Version installée : <strong>1.6.29</strong>')
R(h,'const installed="1.6.28";','const installed="1.6.29";')
# Precisely replace the JNI bridge handler, keeping decryption & old cached previews.
java=j.read_text(encoding="utf-8")
a=java.index('    @JavascriptInterface public void refreshFriendsOverview() {')
b=java.index('        @JavascriptInterface public String receivedAvatar(',a)
old=java[a:b]
new=r'''    @JavascriptInterface public void refreshFriendsOverview() {
        io.execute(() -> {
            int succeeded=0,failed=0;
            try {
                android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
                JSONArray saved=new JSONArray(prefs.getString("received_profiles","[]"));
                int count=Math.min(saved.length(),30);
                for(int i=0;i<count;i++){
                    try{
                        JSONObject item=saved.getJSONObject(i);
                        String kind=item.getString("kind");
                        String source=item.getString("source");
                        String id=item.getString("key");
                        String raw;
                        if("public".equals(kind)){
                            String driveId=driveFileId(source);
                            if(driveId==null)throw new Exception("Invalid Drive link");
                            raw=new String(fetchPublicProfile(driveId,driveResourceKey(source)),StandardCharsets.UTF_8);
                        } else if("private".equals(kind)){
                            raw=readSafJson(Uri.parse(source),40_000_000);
                        } else throw new Exception("Unknown share");
                        JSONObject doc=decodeShared(raw,readSecret("receive_pass_"+id));
                        synchronized(MainActivity.this){
                            JSONArray latest=new JSONArray(prefs.getString("received_profiles","[]"));
                            boolean found=false;
                            for(int n=0;n<latest.length();n++){
                                JSONObject entry=latest.getJSONObject(n);
                                if(id.equals(entry.optString("key"))){
                                    fillFriendOverview(entry,doc);
                                    prefs.edit().putString("received_profiles",latest.toString()).apply();
                                    found=true;
                                    break;
                                }
                            }
                            if(!found)throw new Exception("Share removed");
                        }
                        succeeded++;
                        js("friendsOverviewUpdated()");
                    }catch(Exception ignored){
                        // Preserve previously saved data when offline or not authorized.
                        failed++;
                    }
                }
            }catch(Exception ignored){failed++;}
            js("friendsOverviewUpdated()");
            js("friendsOverviewSyncFinished("+succeeded+","+failed+")");
        });
    }

'''
R(j,old,new)
# Drop the old ambiguous startup status script. Replace with precise persistent status.
html=h.read_text(encoding="utf-8")
start=html.index('<script>\n(function(){\n  // Every WebView startup (cold application launch)')
end=html.index('</script>',start)+len('</script>')
previous=html[start:end]
replacement=r'''<style>
#friends-auto-sync-status,#release-auto-check-status{font-size:10px;line-height:1.3;color:#b5d3dc;margin:2px 0!important}
#release-auto-check-status.available{color:#a8f5cb;text-decoration:underline;cursor:pointer}
</style>
<script>
(function(){
 const chooser=$('visual-profile-picker');
 const sync=document.createElement('p');sync.id='friends-auto-sync-status';sync.setAttribute('role','status');sync.setAttribute('aria-live','polite');
 const update=document.createElement('p');update.id='release-auto-check-status';update.setAttribute('role','status');update.setAttribute('aria-live','polite');
 if(chooser){chooser.insertAdjacentElement('afterend',sync);sync.insertAdjacentElement('afterend',update)}
 const fmtDate=timestamp=>new Date(timestamp).toLocaleString('fr-FR',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
 const store=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch(e){}};
 const load=key=>{try{return JSON.parse(localStorage.getItem(key)||'null')}catch(e){return null}};
 const oldSync=load('last-friends-sync-v1');
 const oldUpdate=load('last-release-check-v1');
 if(oldSync?.at)sync.textContent='Amis · '+oldSync.status+' · '+fmtDate(oldSync.at);
 if(oldUpdate?.at)update.textContent='Version · '+oldUpdate.status+' · '+fmtDate(oldUpdate.at);
 let syncStarted=false,updateStarted=false;
 const oldFriendsUpdated=window.friendsOverviewUpdated;
 window.friendsOverviewUpdated=function(){
  if(typeof oldFriendsUpdated==='function')oldFriendsUpdated();
  // Only the final native callback may finish a sync; per-friend progress
  // callbacks must not claim completion.
 };
 window.friendsOverviewSyncFinished=function(success,fail){
  success=Number(success)||0;fail=Number(fail)||0;
  const now=Date.now();
  let status;
  if(fail===0)status='Terminé ('+success+' sur '+success+')';
  else if(success)status='Partiel ('+success+' réussis, '+fail+' en erreur)';
  else status='Erreur ('+fail+' profil'+(fail>1?'s':'')+')';
  sync.textContent='Amis · '+status+' · '+fmtDate(now);
  store('last-friends-sync-v1',{status,at:now});
 };
 const oldReceived=window.receiveUpdateVersion;
 window.receiveUpdateVersion=function(version){
  if(typeof oldReceived==='function')oldReceived(version);
  const latest=String(version||''),installed='1.6.29';
  const pieces=v=>v.split('.').map(Number);
  const a=pieces(latest),b=pieces(installed);
  const newer=/^\d+(?:\.\d+){1,3}$/.test(latest)&&a.some((x,i)=>x>(b[i]||0)&&a.slice(0,i).every((n,j)=>n===(b[j]||0)));
  const status=newer?'Nouvelle v'+latest+' disponible':'À jour (v'+installed+')';
  const now=Date.now();
  update.textContent='Version · '+status+' · '+fmtDate(now);
  update.classList.toggle('available',newer);
  if(newer){
   const url='https://github.com/TheDwarfy01/mon-evolution/releases/tag/v'+latest;
   update.onclick=()=>window.AndroidBackup?.openOfficialUrl?.(url);
   update.setAttribute('role','button');update.tabIndex=0;
   update.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();update.click()}};
  } else {update.onclick=null;update.removeAttribute('role');update.removeAttribute('tabindex');update.onkeydown=null}
  store('last-release-check-v1',{status,at:now});
 };
 const oldFailed=window.updateVersionFailed;
 window.updateVersionFailed=function(){
  if(typeof oldFailed==='function')oldFailed();
  const now=Date.now(),status='Erreur de vérification';
  update.textContent='Version · '+status+' · '+fmtDate(now);
  update.classList.remove('available');update.onclick=null;
  store('last-release-check-v1',{status,at:now});
 };
 function start(){
  if(!syncStarted){
   syncStarted=true;
   const count=getReceivedList().length;
   if(count&&window.AndroidBackup?.refreshFriendsOverview){
    sync.textContent='Amis · Synchronisation en cours · '+fmtDate(Date.now());
    AndroidBackup.refreshFriendsOverview();
   }else if(!count)sync.textContent='Amis · Aucun profil partagé';
  }
  if(!updateStarted){
   updateStarted=true;
   if(window.AndroidBackup?.checkLatestVersion){
    update.textContent='Version · Vérification en cours · '+fmtDate(Date.now());
    AndroidBackup.checkLatestVersion();
   }else update.textContent='Version · Vérification indisponible';
  }
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
 else start();
})();
</script>'''
R(h,previous,replacement)
print("v1.6.29: per-friend success/failure counts; saved timestamped statuses; startup GitHub version check")
