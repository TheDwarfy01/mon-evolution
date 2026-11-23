/* Persist 3D visibility by profile in WebView localStorage.
 * The option stays enabled across app launches and APK upgrades,
 * but only for the person who explicitly activated it.
 */
export function studioVisibilityKey(profileId){
 if(typeof profileId!=='string'||!profileId||profileId.length>128)return null;
 return 'mon-evolution-studio-visible-v2:'+profileId;
}
export function isStudioEnabled(profileId,storage){
 const key=studioVisibilityKey(profileId);
 if(!key)return false;
 try{return storage?.getItem(key)==='1';}catch{return false;}
}
export function setStudioEnabled(profileId,enabled,storage){
 const key=studioVisibilityKey(profileId);
 if(!key)return false;
 try{storage?.setItem(key,enabled?'1':'0');return true;}catch{return false;}
}
