#!/usr/bin/env node
// Checks run BEFORE APK compilation and publication; no external dependencies.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';

const dir=process.argv[2]||'android/source-1.6.31';
const asset=join(dir,'app/src/main/assets');
const html=readFileSync(join(asset,'index.html'),'utf8');
const java=readFileSync(join(dir,'app/src/main/java/fr/monevolution/app/MainActivity.java'),'utf8');
let count=0;
function check(condition,reason){assert.ok(condition,reason);count++}
function section(pattern,label){
 const i=html.indexOf(pattern);check(i>=0,'Missing UI: '+label);return i;
}
const scripts=[...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
check(scripts.length>=12,'HTML scripts present');
for(let n=0;n<scripts.length;n++){
 const [,attrs,code]=scripts[n];
 if(attrs.includes('src=')){
  const src=attrs.match(/src="([^"]+)"/)?.[1];
  check(!!src&&!src.includes('/')&&src.endsWith('.js'),'Local script only');
  new vm.Script(readFileSync(join(asset,src),'utf8'),{filename:src});
 }else if(code.trim()){
  new vm.Script(code,{filename:'inline-script-'+n});
 }
}
check(html.includes('<script src="quality-checks.js"></script>'),'Production integrity rules are loaded');
const scope={window:{}};
vm.runInNewContext(readFileSync(join(asset,'quality-checks.js'),'utf8'),scope);
const q=scope.window.MonEvolutionQuality;
check(!!q,'Integrity library exported');
const row={id:1,date:'2026-11-08',weight:87.5};
const profile={id:'p1',name:'Profil',height:181,goal:80,entries:[row]};
const backup={format:'mon-evolution',version:1,data:{profiles:[profile]}};
const share={format:'mon-evolution-lecture-seule',version:1,profile:{
 name:profile.name,height:profile.height,goal:profile.goal,entries:profile.entries}};
check(q.isBackupDocument(backup),'Valid backup accepted');
check(q.isSharedDocument(share),'Valid shared profile accepted');
check(!q.isBackupDocument({...backup,version:2}),'Unsupported backup version rejected');
check(!q.isBackupDocument({...backup,data:{profiles:[]}}),'Empty backup rejected');
check(!q.isBackupDocument({...backup,data:{profiles:[{...profile,entries:[]}]}}),'Missing measures rejected');
check(!q.isSharedDocument({...share,profile:{...share.profile,entries:[{...row,weight:-2}]}}),'Invalid weights rejected');
check(!q.isSharedDocument({...share,profile:{...share.profile,entries:[{...row,date:'broken'}]}}),'Invalid dates rejected');
check(!q.isSharedDocument({...share,format:'mon-evolution'}),'Full backup cannot masquerade as shared profile');
check(q.friendState('pending')==='pending'&&q.friendState('password')==='password','Friend state distinguishes pending and wrong password');
check(q.friendState('fake')==='unknown','Unknown error remains unknown');
const normal=q.normalWeightRange(181);
check(Math.abs(normal.low-60.60785)<0.002,'Normal BMI lower weight bound');
check(Math.abs(normal.high-81.9025)<0.002,'Normal BMI upper weight bound');
check(q.bmiCategory(23)==='Corpulence normale','Adult normal BMI category');
check(q.bmiCategory(37)==='Obésité II','Adult obesity BMI category');
const invite='https://thedwarfy01.github.io/mon-evolution/share.html?file=1234567890';
check(q.invitationState(true,invite,true)==='ready','Invitation ready only with key, link and file');
check(q.invitationState(true,invite,false)==='password','Missing password blocks invitation');
check(q.invitationState(true,'',true)==='link','Missing Drive link blocks invitation');
check(q.invitationState(false,invite,true)==='setup','Unlinked file blocks invitation');
for(const [fragment,name] of [
 ['function sharedLoaded(', 'received profile import'],
 ['window.receivedPasswordUpdateSucceeded', 'shared password validation callback'],
 ['function restoreBase64(', 'backup restoration'],
 ['MonEvolutionQuality?.isBackupDocument', 'backup preflight'],
 ['MonEvolutionQuality?.isSharedDocument', 'received document preflight'],
 ['friendSyncUpdated', 'friend synchronization status'],
 ['refreshFriendOverview', 'individual retry without navigation'],
 ["pending:['↻ Synchronisation en cours'", 'in-progress state'],
 ['share-everyday', 'direct invitation actions'],
 ['share-link-copy', 'copy invitation'],
 ['share-link-send', 'send invitation'],
 ['share-send-current-password', 'send the code separately'],
 ['verify-backup', 'read-only backup check'],
 ['backupVerificationResult', 'backup integrity callback'],
 ['healthZoom', 'chart zoom state'],
 ['Zoom sur mes mesures', 'local chart zoom'],
 ['Vue globale', 'global chart zoom'],
 ["c.addEventListener('click',show)", 'touch point details'],
 ['date:r.date', 'dated chart measure'],
 ["'clip-path':'url(#'+clipId+')'", 'clipped chart zoom'],
 ['share-copy-current-password', 'existing password recovery']
])section(fragment,name);
for(const [fragment,name] of [
 ['AES/GCM/NoPadding','encrypted share uses AES-GCM'],
 ['210000','PBKDF2 iteration count'],
 ['generateSharePassword()','random password generator'],
 ['copyCurrentSharePassword','copy current password'],
 ['sendCurrentSharePassword','send current password'],
 ['updateReceivedPassword','password change validation'],
 ['refreshFriendOverview','native one-friend retry'],
 ['friendsRefreshRunning','coalesced friend refresh'],
 ['recordReceivedSync(key,"pending")','friend pending status'],
 ['verifyLinkedBackup','native read-only verification'],
 ['backupVerificationStatus','backup verification persisted'],
 ['readSafJson(uri','SAF read']
])check(java.includes(fragment),'Native: '+name);
const verify=java.slice(java.indexOf('verifyLinkedBackup(){'),java.indexOf('@JavascriptInterface public void autoSave('));
check(!verify.includes('openOutputStream')&&!verify.includes('writeShared('),'Backup verification does not overwrite files');
// Roundtrip the encrypted document FORMAT (not a device-level Android test).
const password='SampleRng16!$XyZ';
const salt=crypto.randomBytes(16),nonce=crypto.randomBytes(12),plain=Buffer.from(JSON.stringify(share));
const key=crypto.pbkdf2Sync(password,salt,210000,32,'sha256');
const cipher=crypto.createCipheriv('aes-256-gcm',key,nonce);
cipher.setAAD(Buffer.from('mon-evolution-chiffre-v1'));
const encrypted=Buffer.concat([cipher.update(plain),cipher.final(),cipher.getAuthTag()]);
const decode=pass=>{
 const derived=crypto.pbkdf2Sync(pass,salt,210000,32,'sha256');
 const d=crypto.createDecipheriv('aes-256-gcm',derived,nonce);
 d.setAAD(Buffer.from('mon-evolution-chiffre-v1'));d.setAuthTag(encrypted.subarray(-16));
 return JSON.parse(Buffer.concat([d.update(encrypted.subarray(0,-16)),d.final()]).toString('utf8'));
};
check(q.isSharedDocument(decode(password)),'AES-256-GCM fixture can be decrypted and validated');
assert.throws(()=>decode('wrongPassword'),'Wrong password is rejected by authenticated encryption');count++;
console.log('PASS '+count+' automated checks: profiles, restoration, sharing, encryption fixture, graphs, sync, backups, HTML syntax.');
