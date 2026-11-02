#!/usr/bin/env python3
"""v1.6.6: opening an invitation automatically imports the read-only profile."""
from pathlib import Path
root=Path("android/source-1.6.6/app")
html=root/"src/main/assets/index.html"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"

def replace(path,old,new):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1: raise AssertionError(f"{path}: expected 1 anchor, found {n}: {old[:110]!r}")
    path.write_text(s.replace(old,new),encoding="utf-8")

replace(gradle,"versionCode 21","versionCode 22")
replace(gradle,"versionName '1.6.5'","versionName '1.6.6'")
replace(manifest,'android:versionCode="21" android:versionName="1.6.5"','android:versionCode="22" android:versionName="1.6.6"')
replace(java,'MonEvolutionIMC/1.6.5','MonEvolutionIMC/1.6.6')
replace(html,'Version installée : <strong>1.6.5</strong>','Version installée : <strong>1.6.6</strong>')
replace(html,'const installed="1.6.5";','const installed="1.6.6";')
replace(html,'// The user must explicitly choose whether to add this profile.','// Opening an invitation is the explicit action; import immediately in read-only mode.')
replace(html,'Aucune donnée de ton téléphone ne sera remplacée. Confirme avant de l’ajouter.','Aucune donnée de ton téléphone ne sera remplacée. Importation automatique…')
replace(html,"$('shared-state').textContent='Invitation reçue : confirme pour ajouter ce profil.';","$('shared-state').textContent='Invitation reçue : chargement automatique du profil partagé…';")
replace(html,"   panel.scrollIntoView({block:'start'});","   panel.scrollIntoView({block:'start'});\n   $('invite-accept').click();")
assert "   $('invite-accept').click();" in html.read_text(encoding="utf-8")
assert "versionCode 22" in gradle.read_text(encoding="utf-8")
print("Version 1.6.6: incoming link -> direct read-only import")
