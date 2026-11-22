#!/usr/bin/env python3
"""Require reconciliation of linked Drive changes at startup before normal use.
Run after the legacy backup-conflict patch. Local and remote copies are preserved.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit('Usage: integrate_startup_backup.py android/source-1.6.126')
root=Path(sys.argv[1])/'app'
j=root/'src/main/java/fr/monevolution/app/MainActivity.java'
a=root/'src/main/assets'
source=j.read_text(encoding='utf-8')
assert source.count('public void readBackupForMerge()')==1
assert source.count('public void resolveBackupMerge(String mergedJson,String remoteHash,String originalLocalJson)')==1
assert 'verifyBackupOnStartup()' not in source
assert 'backupStartupVerified' not in source

# Native startup gate blocks ALL remote writes while the linked copy is unchecked.
anchor='    private boolean appPageReady=false;'
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'''
    // Cleared on each fresh app launch; local data remains writable.
    // Only remote writes wait for the backup's exact hash to be validated.
    private volatile boolean backupStartupVerified=false;
''',1)

anchor='        @JavascriptInterface public void disconnect() {'
assert source.count(anchor)==1
native=r'''
        @JavascriptInterface public void verifyBackupOnStartup() {
            final String reference=getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null);
            if(reference==null){
                backupStartupVerified=true;
                js("backupStartupChecked('unlinked')");
                return;
            }
            backupStartupVerified=false;
            io.execute(()->{
                try {
                    String remoteHash=fileHash(Uri.parse(reference));
                    if(!reference.equals(getPreferences(MODE_PRIVATE).getString(BACKUP_URI,null)))
                        throw new Exception("Fichier de sauvegarde remplacé");
                    String known=getPreferences(MODE_PRIVATE).getString(BACKUP_HASH,null);
                    if(known!=null && known.equals(remoteHash)){
                        backupStartupVerified=true;
                        js("backupStartupChecked('ready')");
                    }else {
                        backupStartupVerified=false;
                        js("backupStartupChecked('conflict')");
                    }
                }catch(Exception e){
                    backupStartupVerified=false;
                    js("backupStartupChecked('error')");
                }
            });
        }
'''
source=source.replace(anchor,native+anchor,1)
anchor='''            if (value == null) return;
            io.execute(() -> {
                try {
                    Uri uri = Uri.parse(value);
                    String knownHash = getPreferences(MODE_PRIVATE).getString(BACKUP_HASH, null);
                    String actualHash = fileHash(uri);
                    if (knownHash != null && !knownHash.equals(actualHash)) {'''
replacement='''            if (value == null) return;
            if (!backupStartupVerified) {
                js("backupConflict()");
                return;
            }
            io.execute(() -> {
                try {
                    Uri uri = Uri.parse(value);
                    String knownHash = getPreferences(MODE_PRIVATE).getString(BACKUP_HASH, null);
                    String actualHash = fileHash(uri);
                    if (knownHash == null || !knownHash.equals(actualHash)) {
                        backupStartupVerified=false;'''
assert source.count(anchor)==1, 'autosave hash check changed'
source=source.replace(anchor,replacement,1)

# Successful merges have verified the hash after persisting BOTH originals.
anchor='''                    js("backupMergeSaved()");'''
assert source.count(anchor)==1
source=source.replace(anchor,'''                    backupStartupVerified=true;
                    js("backupMergeSaved()");''',1)
anchor='''        @JavascriptInterface public void disconnect() {
            getPreferences(MODE_PRIVATE).edit().remove(BACKUP_URI).remove(BACKUP_HASH).remove(BACKUP_TIME).apply();'''
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'''
            backupStartupVerified=true;''',1)
# Linking a freshly created backup and relinking an existing one is safe only
# once their exact hashes have been saved, as in the original two callbacks.
for anchor in (
    '                web.evaluateJavascript("backupCompleted(" + persistent + ")", null);',
    '                web.evaluateJavascript("backupRelinked()",null);'
):
    assert source.count(anchor)==1,anchor
    source=source.replace(anchor,'                backupStartupVerified=true;\n'+anchor,1)

j.write_text(source,encoding='utf-8')
src=a/'backup-conflict.js'
assert src.exists(),'Conflict resolver must already be installed'
shutil.copyfile('android/sync/backup-conflict.js',src)
html=(a/'index.html').read_text(encoding='utf-8')
assert html.count('<script src="backup-conflict.js"></script>')==1
assert 'verifyBackupOnStartup()' in source
assert 'backupStartupChecked' in src.read_text(encoding='utf-8')
assert 'commit(\'local\',true)' in src.read_text(encoding='utf-8')
print('Startup backup verification gate and non-destructive automatic merge installed:',root)
