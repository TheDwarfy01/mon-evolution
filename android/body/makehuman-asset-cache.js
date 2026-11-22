/* Optional MakeHuman asset cache. No assets are bundled with the APK.
 * Downloads only from an explicitly configured HTTPS manifest; verifies SHA-256.
 * IndexedDB persists across ordinary app upgrades, not uninstall/data clearing.
 */
(function(g){
'use strict';
const DB='mon-evolution-avatar-assets',STORE='files',VERSION=1;
function db(){
 return new Promise((resolve,reject)=>{
  const req=indexedDB.open(DB,VERSION);
  req.onupgradeneeded=()=>{const d=req.result;if(!d.objectStoreNames.contains(STORE))d.createObjectStore(STORE);};
  req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
 });
}
async function get(key){
 const d=await db();try{return await new Promise((ok,no)=>{const t=d.transaction(STORE,'readonly'),r=t.objectStore(STORE).get(key);r.onsuccess=()=>ok(r.result||null);r.onerror=()=>no(r.error);});}finally{d.close();}
}
async function put(key,value){
 const d=await db();try{await new Promise((ok,no)=>{const t=d.transaction(STORE,'readwrite');t.objectStore(STORE).put(value,key);t.oncomplete=ok;t.onerror=()=>no(t.error);});}finally{d.close();}
}
async function digest(buffer){
 const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',buffer));
 return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}
async function load(url,expectedSha256){
 if(!/^https:\/\//i.test(url))throw Error('HTTPS required');
 if(!/^[a-f0-9]{64}$/i.test(expectedSha256))throw Error('Invalid SHA-256');
 const key=expectedSha256.toLowerCase(),saved=await get(key);
 if(saved&&await digest(saved)===key)return {buffer:saved,downloaded:false};
 const response=await fetch(url,{cache:'no-store'});
 if(!response.ok)throw Error('Avatar asset HTTP '+response.status);
 const buffer=await response.arrayBuffer();
 if(await digest(buffer)!==key)throw Error('Avatar asset integrity check failed');
 await put(key,buffer);
 return {buffer,downloaded:true};
}
g.MonEvolutionAvatarAssets={load,get};
})(typeof window!=='undefined'?window:globalThis);
