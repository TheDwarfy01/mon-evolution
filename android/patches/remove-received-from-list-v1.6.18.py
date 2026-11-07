#!/usr/bin/env python3
"""v1.6.18 - Remove a single received friend from the Shared list safely."""
from pathlib import Path
root=Path("android/source-1.6.18/app")
html=root/"src/main/assets/index.html"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
gradle=root/"build.gradle"
manifest=root/"src/main/AndroidManifest.xml"
def replace(path,old,new):
 s=path.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1: raise AssertionError(f"{path}: {n} matches for {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
replace(gradle,"versionCode 33","versionCode 34")
replace(gradle,"versionName '1.6.17'","versionName '1.6.18'")
replace(manifest,'android:versionCode="33" android:versionName="1.6.17"','android:versionCode="34" android:versionName="1.6.18"')
replace(java,'MonEvolutionIMC/1.6.17','MonEvolutionIMC/1.6.18')
replace(html,'Version installée : <strong>1.6.17</strong>','Version installée : <strong>1.6.18</strong>')
replace(html,'const installed="1.6.17";','const installed="1.6.18";')
# The native bridge already supports safe per-friend deletion.
# This also erases the associated encrypted password locally.
replace(java,'''                    if(key.equals(prefs.getString("received_selected","")))
                        edit.remove("received_selected");
                    edit.apply();''',
'''                    if(key.equals(prefs.getString("received_selected","")))
                        edit.remove("received_selected");
                    edit.remove("receive_pass_"+key);
                    edit.apply();''')
replace(html,'''   div.append(button);
   choices.append(div);''',
'''   div.append(button);
   const remove=document.createElement('button');
   remove.type='button';
   remove.className='secondary';
   remove.style.cssText='width:100%;margin-top:8px';
   remove.textContent='Retirer ce partage';
   remove.setAttribute('aria-label','Retirer le profil partagé de '+friend.name);
   remove.onclick=()=>{
    const warning='Retirer « '+friend.name+' » de la liste des amis sur ce téléphone ?\\n\\nLe fichier Google Drive de ton ami et tes profils personnels ne seront pas supprimés.';
    if(!confirm(warning))return;
    if(!window.AndroidBackup?.forgetReceivedProfile?.(friend.key)){
     alert('Impossible de retirer le partage. Réessaie.');return;
    }
    const removedCurrent=unifiedCurrent==='received:'+friend.key;
    if(removedCurrent){
      $('shared-content').replaceChildren();
      unifiedCurrent='';
      localStorage.removeItem(unifiedStorageKey);
      const own=(data.profiles||[]).find(p=>p.id===data.active)||data.profiles?.[0];
      if(own)selectUnified('local:'+own.id);
      else updateUnifiedPicker();
    }else{
      updateUnifiedPicker(unifiedCurrent);
    }
    updateReceivedChoices();
    message('Partage retiré de ce téléphone ✓');
   };
   div.append(remove);
   choices.append(div);''')
print("Safe per-friend remove button added to Shared list; Drive untouched.")
