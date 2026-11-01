#!/usr/bin/env python3
"""Mon Evolution IMC v1.6.5: reliable private Drive import and explicit recovery."""
from pathlib import Path
root=Path("android/source-1.6.5/app")
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
html=root/"src/main/assets/index.html"
manifest=root/"src/main/AndroidManifest.xml"
gradle=root/"build.gradle"
def change(path,old,new,n=1):
    raw=path.read_text(encoding="utf-8")
    count=raw.count(old)
    if count!=n:
        raise RuntimeError(f"{path}: expected {n} occurrences, found {count} for {old[:100]!r}")
    path.write_text(raw.replace(old,new),encoding="utf-8")
change(gradle,"versionCode 20","versionCode 21")
change(gradle,"versionName '1.6.4'","versionName '1.6.5'")
change(manifest,'android:versionCode="20" android:versionName="1.6.4"','android:versionCode="21" android:versionName="1.6.5"')
change(html,'Version installée : <strong>1.6.4</strong>','Version installée : <strong>1.6.5</strong>')
change(html,'const installed="1.6.4";','const installed="1.6.5";')
change(java,'MonEvolutionIMC/1.6.4','MonEvolutionIMC/1.6.5')
# The Drive document provider may expose *.json as text/plain or octet-stream.
# Strict MIME matching hid otherwise valid shared documents.
change(java,'''        @JavascriptInterface public void openShared() {
            runOnUiThread(() -> {
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");''',
'''        @JavascriptInterface public void openShared() {
            runOnUiThread(() -> {
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                // Google Drive does not always report .json as application/json.
                // Accept the chosen document and validate its JSON contents.
                intent.setType("*/*");''')
# Make the fallback actually actionable, rather than only displaying an error.
change(html,''' $('shared-state').textContent=msg;
 alert(msg);
}
$('open-share').onclick''',
''' $('shared-state').textContent=msg+' Si tu vois le fichier dans Google Drive, utilise « Accès privé : choisir le fichier Google Drive » ou « Ou choisir un fichier Drive privé ».';
 const button=$('shared-url-load');
 if(button){button.disabled=false;button.textContent='Charger le profil depuis l’URL';}
 const fallback=$('shared-open');
 if(fallback){fallback.hidden=false;fallback.focus();}
 alert(msg+'\\n\\nTu peux importer le document via « Ou choisir un fichier Drive privé ».');
}
$('open-share').onclick''')
change(html,''' $('shared-state').textContent='Lecture du profil partagé…';
 AndroidBackup.loadSharedPublic(u);''',
''' $('shared-state').textContent='Lecture du profil partagé…';
 $('shared-url-load').disabled=true;
 $('shared-url-load').textContent='Lecture Google Drive en cours…';
 AndroidBackup.loadSharedPublic(u);''')
change(html,'''  $('shared-state').textContent='Dernière synchronisation : '+new Date(doc.exportedAt||Date.now()).toLocaleString('fr-FR');''',
'''  $('shared-url-load').disabled=false;
  $('shared-url-load').textContent='Charger le profil depuis l’URL';
  $('shared-state').textContent='Dernière synchronisation : '+new Date(doc.exportedAt||Date.now()).toLocaleString('fr-FR');''')
# Give a useful error if a Drive document cannot be read.
change(html,'''function sharedReadFailed(){message('Impossible de lire ce fichier partagé dans Google Drive')}''',
'''function sharedReadFailed(){
 $('shared-state').textContent='Impossible de lire le profil sélectionné. Vérifie que c’est le fichier mon-evolution-partage-…json, avec le bon compte Google et un accès Lecteur.';
 message('Fichier de partage illisible ou accès Google Drive refusé');
}''')
# Reveal private import right after accepting a share invitation.
change(html,'''   $('shared-state').textContent='Lecture du profil partagé…';
   const source='https://drive.google.com/file/d/'+pendingId+'/view' ''',
'''   $('shared-state').textContent='Lecture du lien… Si le fichier est privé, utilise le bouton « Accès privé : choisir le fichier Google Drive ».';
   const source='https://drive.google.com/file/d/'+pendingId+'/view' ''')
assert 'intent.setType("*/*")' in java.read_text(encoding="utf-8")
assert 'const installed="1.6.5"' in html.read_text(encoding="utf-8")
print("v1.6.5 patch applied: private Drive selection, error guidance, import state.")
