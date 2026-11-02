#!/usr/bin/env python3
"""v1.6.8: 6 digit share PIN, preserving support for existing stronger passwords."""
from pathlib import Path
root=Path("android/source-1.6.8/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def replace(p,old,new):
 s=p.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1: raise RuntimeError(f"{p}: {n} occurrences of {old[:100]!r}")
 p.write_text(s.replace(old,new),encoding="utf-8")
replace(g,"versionCode 23","versionCode 24")
replace(g,"versionName '1.6.7'","versionName '1.6.8'")
replace(m,'android:versionCode="23" android:versionName="1.6.7"','android:versionCode="24" android:versionName="1.6.8"')
replace(j,'MonEvolutionIMC/1.6.7','MonEvolutionIMC/1.6.8')
replace(h,'Version installée : <strong>1.6.7</strong>','Version installée : <strong>1.6.8</strong>')
replace(h,'const installed="1.6.7";','const installed="1.6.8";')
# 6 digits for new PINs; legacy passwords remain valid for decryption/rotation.
replace(j,'if(value==null || value.length()<10 || value.length()>512)throw new Exception("Invalid secret");',
'''if(value==null || !(value.matches("[0-9]{6}") || (value.length()>=10 && value.length()<=512)))
            throw new Exception("Invalid secret");''')
replace(j,'if(password==null || password.length()<10 || password.length()>512)throw new Exception("Mot de passe nécessaire");',
'''if(password==null || !(password.matches("[0-9]{6}") || (password.length()>=10 && password.length()<=512)))
            throw new Exception("Code à 6 chiffres ou ancien mot de passe nécessaire");''')
replace(j,'if(pass!=null && pass.length()>=10)saveSecret("receive_pass_"+key,pass);',
'''if(pass!=null && (pass.matches("[0-9]{6}") || pass.length()>=10))
                        saveSecret("receive_pass_"+key,pass);''')
# Second occurrence differs indentation, so replace only first above then target residual.
s=j.read_text(encoding="utf-8")
s=s.replace('if(pass!=null && pass.length()>=10)saveSecret("receive_pass_"+key,pass);',
'''if(pass!=null && (pass.matches("[0-9]{6}") || pass.length()>=10))
                    saveSecret("receive_pass_"+key,pass);''')
j.write_text(s,encoding="utf-8")
replace(h,"'<input id=\"crypt-input\" type=\"password\" autocomplete=\"off\" style=\"padding:12px;width:100%;border-radius:8px\">'+",
"'<input id=\"crypt-input\" type=\"password\" autocomplete=\"off\" style=\"padding:12px;width:100%;border-radius:8px\">'+")
replace(h,"  const input=$('crypt-input');input.value='';",
'''  const input=$('crypt-input');input.value='';
  input.inputMode=creating?'numeric':'text';
  input.maxLength=creating?6:512;
  input.placeholder=creating?'Code à 6 chiffres':'Code à 6 chiffres ou ancien mot de passe';''')
replace(h,"   if(creating && pass.length<10){$('crypt-error').textContent='Au moins 10 caractères';return;}",
'''   if(creating && !/^[0-9]{6}$/.test(pass)){
    $('crypt-error').textContent='Saisis exactement 6 chiffres (000000 à 999999).';return;
   }
   if(!creating && !(/^[0-9]{6}$/.test(pass) || pass.length>=10)){
    $('crypt-error').textContent='Code à 6 chiffres ou ancien mot de passe.';return;
   }''')
replace(h,"'<p>Le lien reste inchangé. Envoie le mot de passe séparément au destinataire.</p>'+",
"""'<p>Le lien reste inchangé. Envoie le code séparément. Attention : 6 chiffres offrent une protection limitée si une copie du fichier est récupérée.</p>'+""")
replace(h,"<p class=\"notice\">🔒 Le fichier est chiffré AES-256-GCM. Le lien Google Drive ne change pas. Envoie le mot de passe séparément.</p>",
"<p class=\"notice\">🔒 Fichier chiffré AES-256-GCM. Le lien ne change pas. Envoie le code à 6 chiffres séparément : ce code court ne résiste pas à une attaque hors ligne prolongée.</p>")
print("v1.6.8: PIN six digits, legacy password support, UI validation")
