#!/usr/bin/env python3
"""Add safe, opt-in resolution of a changed backup document for IMC v1.6.101.
The app never merges automatically: user must review and confirm. """
from pathlib import Path
import shutil

root = Path('android/source-1.6.101/app')
java = root/'src/main/java/fr/monevolution/app/MainActivity.java'
html = root/'src/main/assets/index.html'
source = java.read_text(encoding='utf-8')
anchor = '        @JavascriptInterface public void disconnect() {'
assert source.count(anchor) == 1
bridge = r'''
        // Read the currently linked backup without writing to or restoring it.
        @JavascriptInterface public void readBackupForMerge() {
            final String reference=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            if(reference==null){js("backupMergeReadFailed('Aucun fichier relié.')");return;}
            io.execute(()->{
                try {
                    // Do not trust the file extension: verify the document contents.
                    Uri uri=Uri.parse(reference);
                    String raw=readSafJson(uri,40_000_000);
                    JSONObject wrapper=new JSONObject(raw);
                    if(!"mon-evolution".equals(wrapper.optString("format"))
                        ||wrapper.optInt("version")!=1)
                        throw new Exception("Format incompatible");
                    JSONArray profiles=wrapper.getJSONObject("data").getJSONArray("profiles");
                    if(profiles.length()<1||profiles.length()>50)
                        throw new Exception("Nombre de profils incorrect");
                    // Store no remote data; let JS validate all profiles before offering a merge.
                    String fingerprint=stringHash(raw);
                    String b64=android.util.Base64.encodeToString(
                        raw.getBytes(StandardCharsets.UTF_8),android.util.Base64.NO_WRAP);
                    if(!reference.equals(getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null)))
                        throw new Exception("Fichier relié changé");
                    js("backupMergeLoaded("+JSONObject.quote(b64)+","+
                        JSONObject.quote(fingerprint)+")");
                }catch(Exception e){
                    js("backupMergeReadFailed("+JSONObject.quote(
                        "Lecture impossible ou sauvegarde invalide.")+")");
                }
            });
        }

        // Commit a user-confirmed merge only if the remote copy is still unchanged.
        @JavascriptInterface public void resolveBackupMerge(String mergedJson,String remoteHash,String originalLocalJson) {
            if(mergedJson==null||mergedJson.length()>50_000_000||
               originalLocalJson==null||originalLocalJson.length()>50_000_000||
               remoteHash==null||remoteHash.length()>180){
                js("backupMergeSaveFailed('Paramètres invalides.')");return;
            }
            final String reference=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            if(reference==null){js("backupMergeSaveFailed('Sauvegarde déconnectée.')");return;}
            io.execute(()->{
                try {
                    JSONObject wrapper=new JSONObject(mergedJson);
                    if(!"mon-evolution".equals(wrapper.optString("format"))||
                       wrapper.optInt("version")!=1)
                        throw new Exception("Format de fusion invalide");
                    JSONArray profiles=wrapper.getJSONObject("data").getJSONArray("profiles");
                    if(profiles.length()<1 || profiles.length()>50)
                        throw new Exception("Profils fusionnés invalides");
                    for(int k=0;k<profiles.length();k++){
                        JSONObject p=profiles.getJSONObject(k);
                        if(p.optString("id","").isEmpty() || p.optString("name","").isEmpty()
                            || p.getJSONArray("entries").length()<1)
                            throw new Exception("Profil fusionné invalide");
                    }
                    if(!reference.equals(getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null)))
                        throw new Exception("Sauvegarde reliée modifiée pendant la fusion");
                    Uri uri=Uri.parse(reference);
                    // Re-read immediately before write to avoid overwriting a newer update.
                    String remoteBefore=readSafJson(uri,40_000_000);
                    String currentHash=stringHash(remoteBefore);
                    if(!remoteHash.equals(currentHash))
                        throw new Exception("Le fichier Drive a encore changé. Relance la comparaison.");
                    // Archive both originals in app-private storage BEFORE touching Drive.
                    // This protects edited values that cannot be safely reconciled.
                    File snapshots=new File(getFilesDir(),"sync-archives");
                    if(!snapshots.isDirectory() && !snapshots.mkdirs())
                        throw new Exception("Impossible de créer les copies de sécurité");
                    long stamp=System.currentTimeMillis();
                    File localCopy=new File(snapshots,"local-before-"+stamp+".json");
                    File remoteCopy=new File(snapshots,"drive-before-"+stamp+".json");
                    try(FileOutputStream out=new FileOutputStream(localCopy)){
                        out.write(originalLocalJson.getBytes(StandardCharsets.UTF_8));
                        out.getFD().sync();
                    }
                    try(FileOutputStream out=new FileOutputStream(remoteCopy)){
                        out.write(remoteBefore.getBytes(StandardCharsets.UTF_8));
                        out.getFD().sync();
                    }
                    if(!remoteHash.equals(fileHash(uri)))
                        throw new Exception("Drive modifié pendant les copies de sécurité. Relance la fusion.");
                    try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")) {
                        if(out==null)throw new Exception("Fichier en lecture seule");
                        out.write(mergedJson.getBytes(StandardCharsets.UTF_8));
                    }
                    // Verify the provider really stored our bytes before declaring success.
                    if(!stringHash(mergedJson).equals(fileHash(uri)))
                        throw new Exception("Écriture non confirmée par le stockage.");
                    getPreferences(MODE_PRIVATE).edit()
                        .putString(BACKUP_HASH,stringHash(mergedJson))
                        .putLong(BACKUP_TIME,System.currentTimeMillis())
                        .putString(BACKUP_VERIFY_STATE,"ok")
                        .putLong(BACKUP_VERIFIED_AT,System.currentTimeMillis())
                        .putString(BACKUP_VERIFY_INFO,"Fusion confirmée et relue.")
                        .apply();
                    js("backupMergeSaved()");
                }catch(Exception e){
                    js("backupMergeSaveFailed("+JSONObject.quote(
                        e.getMessage()==null?"Échec du stockage.":e.getMessage())+")");
                }
            });
        }
'''
source=source.replace(anchor,bridge+anchor)
java.write_text(source,encoding='utf-8')
page=html.read_text(encoding='utf-8')
assert page.count('</body></html>')==1
assert 'avatar-rotate.js' in page and 'local-ai.js' in page
shutil.copyfile('android/sync/backup-conflict.js',root/'src/main/assets/backup-conflict.js')
page=page.replace('</body></html>','<script src="backup-conflict.js"></script>\n</body></html>')
html.write_text(page,encoding='utf-8')
assert 'readBackupForMerge()' in source
assert 'resolveBackupMerge(String mergedJson,String remoteHash,String originalLocalJson)' in source
assert 'remoteHash.equals(currentHash)' in source
print('Safe conflict resolution added to 1.6.101')
