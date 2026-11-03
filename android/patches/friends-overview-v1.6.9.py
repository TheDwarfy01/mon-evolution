#!/usr/bin/env python3
"""v1.6.9: show all received friends' summaries without switching personal profile."""
from pathlib import Path
root=Path("android/source-1.6.9/app")
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
html=root/"src/main/assets/index.html"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
def rep(path,old,new):
    source=path.read_text(encoding="utf-8")
    occurrences=source.count(old)
    if occurrences!=1:
        raise AssertionError(f"{path}: {occurrences} occurrences of {old[:100]!r}")
    path.write_text(source.replace(old,new),encoding="utf-8")
rep(gradle,"versionCode 24","versionCode 25")
rep(gradle,"versionName '1.6.8'","versionName '1.6.9'")
rep(manifest,'android:versionCode="24" android:versionName="1.6.8"','android:versionCode="25" android:versionName="1.6.9"')
rep(html,'Version installée : <strong>1.6.8</strong>','Version installée : <strong>1.6.9</strong>')
rep(html,'const installed="1.6.8";','const installed="1.6.9";')
rep(java,'MonEvolutionIMC/1.6.8','MonEvolutionIMC/1.6.9')

# Keep strictly limited, read-only preview metadata locally. Never update a
# personal profile or write these received fields into a private backup.
helper = '''
    private void fillFriendOverview(JSONObject entry,JSONObject document) throws Exception {
        JSONObject profile=document.getJSONObject("profile");
        JSONArray weights=profile.getJSONArray("entries");
        JSONObject first=null,last=null;
        for(int i=0;i<weights.length();i++){
            JSONObject current=weights.getJSONObject(i);
            if(first==null || current.getString("date").compareTo(first.getString("date"))<0)first=current;
            if(last==null || current.getString("date").compareTo(last.getString("date"))>0)last=current;
        }
        if(first==null || last==null)throw new Exception("Missing weights");
        entry.put("previewStart",first.getDouble("weight"));
        entry.put("previewCurrent",last.getDouble("weight"));
        entry.put("previewGoal",profile.getDouble("goal"));
        entry.put("previewDate",last.getString("date"));
        entry.put("previewCount",weights.length());
    }

    @JavascriptInterface public void refreshFriendsOverview() {
        io.execute(() -> {
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
                            if(driveId==null)continue;
                            raw=new String(fetchPublicProfile(driveId,driveResourceKey(source)),StandardCharsets.UTF_8);
                        } else if("private".equals(kind)){
                            raw=readSafJson(Uri.parse(source),40_000_000);
                        } else continue;
                        JSONObject doc=decodeShared(raw,readSecret("receive_pass_"+id));
                        fillFriendOverview(item,doc);
                        synchronized(MainActivity.this){
                            JSONArray latest=new JSONArray(prefs.getString("received_profiles","[]"));
                            for(int n=0;n<latest.length();n++){
                                JSONObject found=latest.getJSONObject(n);
                                if(id.equals(found.optString("key"))){
                                    fillFriendOverview(found,doc);
                                    prefs.edit().putString("received_profiles",latest.toString()).apply();
                                    break;
                                }
                            }
                        }
                        js("friendsOverviewUpdated()");
                    }catch(Exception ignored){
                        // An inaccessible Drive file must not remove an existing preview.
                    }
                }
            }catch(Exception ignored){ }
            js("friendsOverviewUpdated()");
        });
    }
'''
rep(java,'        @JavascriptInterface public String listReceivedProfiles() {',
    helper+'\n        @JavascriptInterface public String listReceivedProfiles() {')
rep(java,'''                entry.put("name",name);
                prefs.edit().putString("received_profiles",list.toString()).apply();''',
'''                entry.put("name",name);
                fillFriendOverview(entry,doc);
                prefs.edit().putString("received_profiles",list.toString()).apply();''')
rep(java,'''        item.put("source",source);
        list.put(item);''',
'''        item.put("source",source);
        fillFriendOverview(item,doc);
        list.put(item);''')

# The prior version automatically selected the last received profile on Shared tab.
# This version never changes the active personal profile merely by opening Shared.
before = ''' function updateReceivedChoices(){
  const saved=getReceivedList();
  choices.replaceChildren();
  if(!saved.length){
   status.textContent='Aucun profil partagé enregistré sur ce téléphone. Ouvre une invitation ou importe un fichier Drive.';
   return;
  }
  status.textContent=saved.length===1?'1 profil partagé enregistré':'Profils partagés enregistrés : '+saved.length;
  for(const item of saved){
   const button=document.createElement('button');
   button.type='button';button.className='secondary';
   button.style.cssText='width:100%;margin-top:10px';
   button.textContent='👤 '+item.name+' · Consulter en lecture seule';
   button.onclick=()=>selectUnified('received:'+item.key);
   choices.append(button);
  }
 }
 const oldClick=sharedNav.onclick;
 sharedNav.onclick=()=>{
  if(typeof oldClick==='function')oldClick();
  updateReceivedChoices();
  const saved=getReceivedList();
  const preferred=window.AndroidBackup?.receivedSelected?.()||'';
  const selected=saved.find(item=>item.key===preferred)||saved[0];
  if(selected && !unifiedCurrent.startsWith('received:')){
   // Show last received summary rather than a blank Shared tab.
   selectUnified('received:'+selected.key);
  }
 };'''
after = ''' function updateReceivedChoices(){
  const saved=getReceivedList();
  choices.replaceChildren();
  if(!saved.length){
   status.textContent='Aucun ami enregistré. Ouvre une invitation pour ajouter un profil.';
   return;
  }
  status.textContent=saved.length===1?'1 ami partagé':'Mes amis · '+saved.length+' profils partagés';
  for(const friend of saved){
   const div=document.createElement('div');
   div.className='card';
   div.style.cssText='margin-top:12px;padding:16px';
   const name=document.createElement('h3');
   name.textContent='👤 '+friend.name;
   div.append(name);
   const details=document.createElement('p');
   details.className='notice';
   if(Number.isFinite(friend.previewCurrent)&&Number.isFinite(friend.previewGoal)&&Number.isFinite(friend.previewStart)){
    const lost=friend.previewStart-friend.previewCurrent;
    details.textContent='Actuel : '+fmt(friend.previewCurrent)+' kg · Objectif : '+fmt(friend.previewGoal)+' kg · Évolution : '+(lost>=0?'−':'+')+fmt(Math.abs(lost))+' kg · Mesure : '+friend.previewDate;
   }else{
    details.textContent='Résumé non synchronisé. Actualise les résumés pour afficher ses mesures.';
   }
   div.append(details);
   const button=document.createElement('button');
   button.type='button';button.className='secondary';
   button.style.cssText='width:100%;margin-top:8px';
   button.textContent='Consulter le profil complet';
   button.onclick=()=>selectUnified('received:'+friend.key);
   div.append(button);
   choices.append(div);
  }
 }
 const reload=document.createElement('button');
 reload.className='secondary';
 reload.type='button';
 reload.style.cssText='width:100%;margin-top:10px';
 reload.textContent='↻ Actualiser les résumés des amis';
 reload.onclick=()=>{
  status.textContent='Actualisation des résumés depuis Google Drive…';
  window.AndroidBackup?.refreshFriendsOverview?.();
 };
 card.append(reload);
 window.friendsOverviewUpdated=()=>updateReceivedChoices();
 const oldClick=sharedNav.onclick;
 sharedNav.onclick=()=>{
  if(typeof oldClick==='function')oldClick();
  updateReceivedChoices();
  // Preserve Mario · Personnel; do not invoke selectUnified here.
  window.AndroidBackup?.refreshFriendsOverview?.();
 };'''
rep(html,before,after)
assert 'window.friendsOverviewUpdated' in html.read_text(encoding="utf-8")
print("v1.6.9: friends overview list, refresh, no personal profile switch.")
