#!/usr/bin/env python3
"""v1.6.23: automatic async refresh of received profiles on every app launch."""
from pathlib import Path
root=Path("android/source-1.6.23/app")
html=root/"src/main/assets/index.html"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
def R(p,a,b):
 s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} occurrences: {a[:120]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(gradle,"versionCode 38","versionCode 39")
R(gradle,"versionName '1.6.22'","versionName '1.6.23'")
R(manifest,'android:versionCode="38" android:versionName="1.6.22"','android:versionCode="39" android:versionName="1.6.23"')
R(java,"MonEvolutionIMC/1.6.22","MonEvolutionIMC/1.6.23")
R(html,'Version installée : <strong>1.6.22</strong>','Version installée : <strong>1.6.23</strong>')
R(html,'const installed="1.6.22";','const installed="1.6.23";')
# refreshFriendsOverview already verifies/decrypts each authorized friend's Drive file
# on the executor, keeps old previews on errors, and notifies JS on each update.
# Add a startup-only invocation after all previous UI callbacks are registered.
snippet=r"""
<script>
(function(){
  // Every WebView startup (cold application launch): refresh all saved friends
  // without requiring the Shared tab or a manual press.
  // The Android bridge performs Drive/network I/O on a worker thread.
  let started=false;
  const label=document.createElement('p');
  label.id='friends-auto-sync-status';
  label.style.cssText='font-size:11px;color:#accfdd;margin:0 0 8px';
  label.setAttribute('role','status');
  label.setAttribute('aria-live','polite');
  const chooser=$('visual-profile-picker');
  if(chooser)chooser.insertAdjacentElement('afterend',label);
  function report(text){label.textContent=text}
  const oldUpdated=window.friendsOverviewUpdated;
  window.friendsOverviewUpdated=function(){
    if(typeof oldUpdated==='function')oldUpdated();
    const friends=getReceivedList();
    report(friends.length?'Profils partagés : synchronisation en cours ou terminée':'');
  };
  function syncReceivedOnLaunch(){
    if(started)return;started=true;
    if(!window.AndroidBackup?.refreshFriendsOverview)return;
    const friends=getReceivedList();
    if(!friends.length)return;
    report('↻ Actualisation des '+friends.length+' profils partagés…');
    // Async Java worker; does not block personal profiles or meal entry.
    window.AndroidBackup.refreshFriendsOverview();
  }
  if(document.readyState==='loading')
    document.addEventListener('DOMContentLoaded',syncReceivedOnLaunch,{once:true});
  else syncReceivedOnLaunch();
})();
</script>
"""
R(html,'</body></html>',snippet+'</body></html>')
print("v1.6.23: automatic background friend refresh initialized for every app start")
