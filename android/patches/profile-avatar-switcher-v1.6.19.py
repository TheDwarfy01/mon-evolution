#!/usr/bin/env python3
"""v1.6.19: avatar-driven profile selector with encrypted shared avatars."""
from pathlib import Path
root=Path("android/source-1.6.19/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(p,a,b):
 s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} matches: {a[:100]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 34","versionCode 35")
R(g,"versionName '1.6.18'","versionName '1.6.19'")
R(m,'android:versionCode="34" android:versionName="1.6.18"','android:versionCode="35" android:versionName="1.6.19"')
R(j,"MonEvolutionIMC/1.6.18","MonEvolutionIMC/1.6.19")
R(h,'Version installée : <strong>1.6.18</strong>','Version installée : <strong>1.6.19</strong>')
R(h,'const installed="1.6.18";','const installed="1.6.19";')
R(h,'// Aucun portrait n\'est ajouté au document de partage en lecture seule.',
    '// Le portrait du profil choisi est inclus dans le document partagé chiffré.')
R(h,'Elle est incluse dans ta sauvegarde privée, mais pas dans le partage en lecture seule.',
    'Elle est incluse dans ta sauvegarde privée et dans le partage chiffré de ce seul profil.')
R(h,'La photo de profil et les autres profils ne sont jamais partagés.',
    'Seule la photo de ce profil est incluse dans le partage chiffré; aucun autre profil n’est envoyé.')

# Add portrait to outgoing share JSON (still AES-GCM ciphertext on Drive).
R(h,"AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));",
    "AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{},avatar:p.avatar||''}}));")
# Some versions use const publish=, but leave JSON specific and validated in patch.
R(j,'        // Whitelist: no photo de profil, no other profiles or backup private metadata.',
'''        // Include only this profile's chosen portrait, never any other profile.
        String avatar=input.optString("avatar","");
        if(avatar.startsWith("data:image/jpeg;base64,") && avatar.length()<250000)
            profile.put("avatar",avatar);
        // Whitelist: no other profiles or backup private metadata.''')
R(j,'        JSONArray entries=p.getJSONArray("entries");\n        if(entries.length()<1 || entries.length()>20000)',
'''        String avatar=p.optString("avatar","");
        if(!avatar.isEmpty() &&
            (!avatar.startsWith("data:image/jpeg;base64,") || avatar.length()>=250000))
            throw new Exception("Photo de profil invalide");
        JSONArray entries=p.getJSONArray("entries");
        if(entries.length()<1 || entries.length()>20000)''')
# Save received portrait in private app prefs only, not editable backup.
R(j,'    private void fillFriendOverview(JSONObject entry,JSONObject document) throws Exception {\n        JSONObject profile=document.getJSONObject("profile");',
'''    private void fillFriendOverview(JSONObject entry,JSONObject document) throws Exception {
        JSONObject profile=document.getJSONObject("profile");
        String key=entry.optString("key","");
        if(key.matches("[a-f0-9-]{36}")){
            String portrait=profile.optString("avatar","");
            if(portrait.startsWith("data:image/jpeg;base64,") && portrait.length()<250000)
                getPreferences(MODE_PRIVATE).edit().putString("friend_avatar_"+key,portrait).apply();
            else
                getPreferences(MODE_PRIVATE).edit().remove("friend_avatar_"+key).apply();
        }''')
R(j,'        @JavascriptInterface public String listReceivedProfiles() {',
'''        @JavascriptInterface public String receivedAvatar(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return "";
            return getPreferences(MODE_PRIVATE).getString("friend_avatar_"+key,"");
        }
        @JavascriptInterface public String listReceivedProfiles() {''')
R(j,'                    edit.remove("receive_pass_"+key);',
'''                    edit.remove("receive_pass_"+key);
                    edit.remove("friend_avatar_"+key);''')
# Existing friend card shows portrait instead of generic silhouette.
R(h,"    name.textContent='👤 '+friend.name;",
'''    const thumb=window.AndroidBackup?.receivedAvatar?.(friend.key)||'';
    if(/^data:image\/jpeg;base64,/.test(thumb) && thumb.length<250000){
      const avatar=document.createElement('img');avatar.src=thumb;avatar.alt='Photo de '+friend.name;
      avatar.style.cssText='width:56px;height:56px;object-fit:cover;border-radius:50%;border:2px solid #80e3cf;display:block;margin-bottom:8px';
      div.append(avatar);
    }
    name.textContent=friend.name;''')
# Avatar picker replaces the bulky select on screen; leave select accessible for fallback.
selector=r"""
<style>
#visual-profile-picker{display:flex;gap:14px;overflow-x:auto;padding:12px 2px 16px;scroll-snap-type:x proximity;align-items:flex-start}
.profile-portrait-choice{background:transparent;border:0;padding:3px 2px;min-width:74px;max-width:92px;color:#e3f7fb;text-align:center;flex:0 0 auto;scroll-snap-align:start}
.profile-portrait-circle{display:flex;align-items:center;justify-content:center;width:62px;height:62px;margin:0 auto 6px;border-radius:50%;border:2px solid #517d8d;background:#173a4f;overflow:hidden;font-size:23px;font-weight:700}
.profile-portrait-circle img{width:100%;height:100%;object-fit:cover}
.profile-portrait-choice[aria-pressed="true"] .profile-portrait-circle{border:3px solid #7ee3cf;box-shadow:0 0 0 3px rgba(126,227,207,.25)}
.profile-portrait-name{display:block;font-size:12px;line-height:1.25;overflow-wrap:anywhere}
.profile-portrait-kind{display:block;color:#acc5d5;font-size:10px;margin-top:3px}
#visual-profile-picker-label{font-size:13px;color:#cfe7f6;margin-top:7px}
</style>
<script>
(function(){
 const select=$('unified-profile-picker');
 if(!select)return;
 const wrap=select.parentElement;
 const oldLabel=wrap.querySelector('label[for="unified-profile-picker"]');
 if(oldLabel){oldLabel.textContent='Profil sélectionné';oldLabel.style.position='absolute';oldLabel.style.width='1px';oldLabel.style.height='1px';oldLabel.style.overflow='hidden';oldLabel.style.clipPath='inset(50%)';}
 // Preserve the native accessible select for keyboard and screen readers.
 select.style.cssText='position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none!important';
 const title=document.createElement('div');title.id='visual-profile-picker-label';title.textContent='Choisir un profil';
 const bar=document.createElement('div');bar.id='visual-profile-picker';bar.setAttribute('aria-label','Choisir un profil par sa photo');
 wrap.insertBefore(title,select);wrap.insertBefore(bar,select);
 function validPortrait(src){return typeof src==='string' && /^data:image\/jpeg;base64,/.test(src) && src.length<250000;}
 function paint(){
  bar.replaceChildren();
  const items=[
   ...(data.profiles||[]).map(p=>({id:'local:'+p.id,name:p.name,kind:'Personnel',avatar:p.avatar||''})),
   ...getReceivedList().map(p=>({id:'received:'+p.key,name:p.name,kind:'Partagé',avatar:window.AndroidBackup?.receivedAvatar?.(p.key)||''}))
  ];
  for(const p of items){
   const button=document.createElement('button');button.type='button';
   button.className='profile-portrait-choice';button.setAttribute('aria-pressed',String(unifiedCurrent===p.id));
   button.setAttribute('aria-label',p.name+', '+p.kind);
   const circle=document.createElement('span');circle.className='profile-portrait-circle';
   if(validPortrait(p.avatar)){
    const image=document.createElement('img');image.src=p.avatar;image.alt='';circle.append(image);
   }else{
    circle.textContent=(p.name||'?').trim().slice(0,1).toLocaleUpperCase('fr-FR');
   }
   const label=document.createElement('span');label.className='profile-portrait-name';label.textContent=p.name;
   const kind=document.createElement('span');kind.className='profile-portrait-kind';kind.textContent=p.kind;
   button.append(circle,label,kind);
   button.onclick=()=>{
    if(p.id===unifiedCurrent)return;
    selectUnified(p.id);
    paint();
   };
   bar.append(button);
  }
 }
 const originalUpdate=updateUnifiedPicker;
 updateUnifiedPicker=function(prefer){
  const result=originalUpdate(prefer);
  paint();return result;
 };
 const originalRenderAvatars=renderAvatars;
 renderAvatars=function(){originalRenderAvatars();paint()};
 const oldFriendsUpdate=window.friendsOverviewUpdated;
 window.friendsOverviewUpdated=function(){
  if(typeof oldFriendsUpdate==='function')oldFriendsUpdate();
  paint();
 };
 // Native import and refreshing already trigger onReceivedProfileLoaded.
 const oldLoaded=window.onReceivedProfileLoaded;
 window.onReceivedProfileLoaded=function(key,name){
  if(typeof oldLoaded==='function')oldLoaded(key,name);
  paint();
 };
 paint();
})();
</script>
"""
R(h,'</body></html>',selector+'</body></html>')
print("v1.6.19: avatar selector & encrypted shared profile portraits added")
