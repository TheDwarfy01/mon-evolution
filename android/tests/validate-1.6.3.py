#!/usr/bin/env python3
"""Static regression checks for Mon Evolution IMC v1.6.3.
Run before Gradle compilation. The test is intentionally independent of Android SDK.
"""
from pathlib import Path
import re, subprocess, tempfile, os, json, sys
root=Path("android/source-1.6.3/app")
html=(root/"src/main/assets/index.html").read_text(encoding="utf-8")
java=(root/"src/main/java/fr/monevolution/app/MainActivity.java").read_text(encoding="utf-8")
reminders=(root/"src/main/java/fr/monevolution/app/ReminderReceiver.java").read_text(encoding="utf-8")
manifest=(root/"src/main/AndroidManifest.xml").read_text(encoding="utf-8")
gradle=(root/"build.gradle").read_text(encoding="utf-8")
assert 'versionName="1.6.3"' in manifest
assert "versionName '1.6.3'" in gradle and "versionCode 19" in gradle
assert "getContentResolver().openOutputStream" in java
assert 'android:icon="@drawable/ic_launcher"' in manifest
assert (root/"src/main/res/drawable/ic_launcher.xml").is_file()

# All referenced form controls must exist once; this catches empty/missing panels.
ids=re.findall(r'\bid=["\x27]([A-Za-z0-9_-]+)["\x27]',html)
assert len(ids)==len(set(ids)),f"Duplicate IDs: {[x for x in ids if ids.count(x)>1]}"
referenced=set(re.findall(r"\$\('([A-Za-z0-9_-]+)'\)",html))
referenced|=set(re.findall(r"document\.getElementById\('([A-Za-z0-9_-]+)'\)",html))
missing=referenced-set(ids)
assert not missing,f"Missing HTML controls: {sorted(missing)}"
assert '<script src="https://' not in html and "script.src='https://" not in html
assert 'AndroidBackup.checkLatestVersion()' in html
assert 'checkLatestVersion()' in java
assert "api.github.com/repos/TheDwarfy01/mon-evolution/releases/latest" in java
assert "shouldOverrideUrlLoading" in java
assert "setAllowUniversalAccessFromFileURLs(false)" in java

# Privacy boundaries: no profile merge silently overwrites a local measurement;
# no remote or local delete silently triggers a backup upload.
assert 'if(sync)AndroidBackup.autoSave(backupPayload())' in html
assert "save(false);" in html
assert 'stopShare?.(p.id)' in html
assert 'deleteProfileOnDrive' in java and 'deleteActiveShare' in java
assert 'DocumentsContract.deleteDocument' in java
assert 'known.equals(fileHash(uri))' in java
assert 'loadSharedPublic' in java and 'fetchPublicProfile' in java
assert 'id="shared-public-url"' in html
assert 'id="unified-profile-picker"' in html
assert 'id="setup-received"' in html
assert 'id="forget-received"' in html
assert 'sharedLoaded(base64,receivedKey)' in html
assert 'listReceivedProfiles' in java
assert 'selectReceivedProfile' in java
assert 'forgetReceivedProfile' in java
assert 'registerReceived' in java
assert 'received_profiles' in java
assert 'received_selected' in java
assert '"private".equals(kind)' in java
assert '"public".equals(kind)' in java
assert 'source.equals(entry.optString("source"))' in java
assert 'received_selected",key' in java
assert 'forgetReceivedProfile' in html

assert 'id="shared-open"' in html
assert 'id="share-link-send"' in html
assert 'id="share-link-copy"' in html
assert 'validDriveShareLink' in java
assert 'linkExistingBackup' in java and 'linkExistingShare' in java
# Invitation web -> Android app -> confirmation (no silent import).
landing=Path("share.html").read_text(encoding="utf-8")
assert 'id="open-app"' in landing
assert 'id="drive-link"' in landing
assert 'scheme=monevolution;package=fr.monevolution.app' in landing
assert 'file=' in landing and 'new URLSearchParams' in landing
assert 'noindex,nofollow' in landing
assert '<data android:scheme="monevolution" android:host="share"/>' in manifest
assert 'android:launchMode="singleTop"' in manifest
assert 'onNewIntent(Intent intent)' in java
assert 'onPageFinished(WebView view,String url)' in java
assert 'extractInvitationFileId' in java
assert 'matches("[A-Za-z0-9_-]{10,200}")' in java
assert 'getInvitationLink(String profileId)' in java
assert 'https://thedwarfy01.github.io/mon-evolution/share.html?file=' in java
assert 'final String url=getInvitationLink(id);' in java
assert 'id="share-invite-preview"' in html
assert "Firefox ou DuckDuckGo" in html
assert "Chrome peut bloquer le téléchargement" in html
assert "ouvre-le dans Firefox ou DuckDuckGo" in html
assert 'window.receiveShareInvitation=function(fileId)' in html
assert "invite-accept" in html and "invite-private" in html and "invite-cancel" in html
assert "window.AndroidBackup?.loadSharedPublic?." in html
assert "window.AndroidBackup.openShared()" in html
assert 'panel.hidden=true' in html
assert 'window.onReceivedProfileLoaded=function(key,name)' in html
# The landing page does not fetch personal data or embed any shared JSON.
assert 'fetch(' not in landing and 'XMLHttpRequest' not in landing

assert 'else delete record[key]' in html
assert "exportCsv" in java and "exportSingleProfile" in java
assert 'csvCell' in html
assert 'exportProgressPdf' in java and 'export-progress-pdf' in html
assert 'setAndAllowWhileIdle' in reminders
assert 'TIMEZONE_CHANGED' in manifest
assert 'location.reload()' in html

# Syntax-check EACH inline JS block using Node, which is available in GitHub Actions.
scripts=re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',html)
assert len(scripts)>=8,f"Unexpected inline script count {len(scripts)}"
with tempfile.TemporaryDirectory() as tmp:
    for n,script in enumerate(scripts):
        file=Path(tmp)/f"script-{n:02d}.js"
        file.write_text(script,encoding="utf-8")
        subprocess.run(["node","--check",str(file)],check=True,capture_output=True,text=True)

# Behavioral checks for two high-risk pure helpers.
def between(a,b):
    start=html.index(a)
    end=html.index(b,start)
    return html[start:end]
code=between("function mergeRestore(incoming){","function restoreBase64(base64)")
csv=between("function csvCell(value){","$('export-weights').onclick")
tests=r'''
const assert=require("assert");
let data={active:"p1",profiles:[{
 id:"p1",name:"Local",height:180,goal:80,
 entries:[{id:1,date:"2026-10-01",weight:100,note:"local"}],
 meals:{"2026-10-01":{lunch:"local"}}
}]};
const validate=(v)=>assert.ok(Array.isArray(v.profiles));
const confirm=(msg)=>true;
'''
tests+=code+"\n"+csv+'''
let result=mergeRestore({active:"p1",profiles:[{
 id:"p1",name:"Local",height:180,goal:80,
 entries:[{id:1,date:"2026-10-01",weight:90,note:"remote"},
          {id:2,date:"2026-10-02",weight:99,note:"new"}],
 meals:{"2026-10-01":{lunch:"remote"},"2026-10-02":{dinner:"new"}}
}]});
assert.equal(result.addedWeights,1);
assert.equal(result.addedDays,1);
assert.ok(result.conflicts>=2);
assert.equal(result.merged.profiles[0].entries.find(x=>x.id===1).weight,100);
assert.equal(result.merged.profiles[0].meals["2026-10-01"].lunch,"local");
assert.equal(result.merged.profiles[0].entries.find(x=>x.id===2).weight,99);
let separate=mergeRestore({active:"p1",profiles:[{
 id:"p1",name:"Different person",height:170,goal:75,
 entries:[{id:1,date:"2026-10-01",weight:70,note:"private"}],
 meals:{}
}]});
assert.equal(separate.merged.profiles.length,2);
assert.equal(separate.merged.profiles[0].name,"Local");
assert.equal(separate.merged.profiles[1].name,"Different person");
assert.notEqual(separate.merged.profiles[1].id,"p1");
assert.ok(separate.conflicts>0);
assert.ok(csvCell("=SUM(1,2)").startsWith("\\\"'=SUM"));
assert.ok(csvCell('a"b').includes('a""b'));
console.log("Behavioral merge & CSV tests passed");
'''
with tempfile.TemporaryDirectory() as tmp:
    f=Path(tmp)/"regression.js"
    f.write_text(tests,encoding="utf-8")
    result=subprocess.run(["node",str(f)],capture_output=True,text=True)
    if result.returncode:
        print(result.stdout);print(result.stderr);sys.exit(result.returncode)
    print(result.stdout.strip())


# Validate the public landing page's inline JavaScript, independently.
with tempfile.TemporaryDirectory() as tmp:
    scripts=re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',landing)
    assert len(scripts)==1
    f=Path(tmp)/"landing.js"
    f.write_text(scripts[0],encoding="utf-8")
    subprocess.run(["node","--check",str(f)],check=True,capture_output=True,text=True)
print("Success: v1.6.3 invitation deep link, private fallback and regression checks.")
