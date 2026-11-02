#!/usr/bin/env python3
"""v1.6.8: 6 character share code (4 digits, 1 uppercase, 1 symbol), preserving support for existing stronger passwords."""
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
# Exact six-character new code. Old 10+ character passwords remain readable.
replace(j,'    private void saveSecret(String name,String value) throws Exception {',
'''    private boolean validSixCode(String input) {
        if(input==null || input.length()!=6)return false;
        int digits=0,uppercase=0,symbols=0;
        for(char c:input.toCharArray()){
            if(c>='0' && c<='9')digits++;
            else if(c>='A' && c<='Z')uppercase++;
            else if("!@#$%&*?._-".indexOf(c)>=0)symbols++;
            else return false;
        }
        return digits==4 && uppercase==1 && symbols==1;
    }
    private void saveSecret(String name,String value) throws Exception {''')
replace(j,'if(value==null || value.length()<10 || value.length()>512)throw new Exception("Invalid secret");',
'''if(value==null || !(validSixCode(value) || (value.length()>=10 && value.length()<=512)))
            throw new Exception("Invalid secret");''')
replace(j,'if(password==null || password.length()<10 || password.length()>512)throw new Exception("Mot de passe nécessaire");',
'''if(password==null || !(validSixCode(password) || (password.length()>=10 && password.length()<=512)))
            throw new Exception("Code à 6 caractères ou ancien mot de passe nécessaire");''')
s=j.read_text(encoding="utf-8")
old='if(pass!=null && pass.length()>=10)saveSecret("receive_pass_"+key,pass);'
assert s.count(old)==2, s.count(old)
s=s.replace(old,'if(pass!=null && (validSixCode(pass) || pass.length()>=10))saveSecret("receive_pass_"+key,pass);')
j.write_text(s,encoding="utf-8")
replace(h,"  const input=$('crypt-input');input.value='';",
'''  const input=$('crypt-input');input.value='';
  input.inputMode='text';
  input.maxLength=creating?6:512;
  input.placeholder=creating?'4 chiffres + 1 majuscule + 1 symbole':'Code à 6 caractères ou ancien mot de passe';''')
replace(h,"   if(creating && pass.length<10){$('crypt-error').textContent='Au moins 10 caractères';return;}",
'''   if(creating && !/^(?=(?:[^0-9]*[0-9]){4}[^0-9]*$)(?=[^A-Z]*[A-Z][^A-Z]*$)(?=[^!@#$%&*?._-]*[!@#$%&*?._-][^!@#$%&*?._-]*$)[0-9A-Z!@#$%&*?._-]{6}$/.test(pass)){
    $('crypt-error').textContent='Saisis exactement 4 chiffres, 1 majuscule et 1 symbole (! @ # $ % & * ? . _ -), dans n’importe quel ordre.';return;
   }
   if(!creating && !(/^(?=(?:[^0-9]*[0-9]){4}[^0-9]*$)(?=[^A-Z]*[A-Z][^A-Z]*$)(?=[^!@#$%&*?._-]*[!@#$%&*?._-][^!@#$%&*?._-]*$)[0-9A-Z!@#$%&*?._-]{6}$/.test(pass) || pass.length>=10)){
    $('crypt-error').textContent='4 chiffres, 1 majuscule, 1 symbole, ou ancien mot de passe.';return;
   }''')
replace(h,"'<p>Le lien reste inchangé. Envoie le mot de passe séparément au destinataire.</p>'+",
"""'<p>Le lien reste inchangé. Envoie le code séparément. Attention : 6 caractères offrent une protection limitée si une copie du fichier est récupérée.</p>'+""")
replace(h,"<p class=\"notice\">🔒 Le fichier est chiffré AES-256-GCM. Le lien Google Drive ne change pas. Envoie le mot de passe séparément.</p>",
"<p class=\"notice\">🔒 Fichier chiffré AES-256-GCM. Le lien ne change pas. Envoie le code à 6 caractères séparément : ce code court ne résiste pas à une attaque hors ligne prolongée.</p>")
print("v1.6.8: 4 digits + uppercase + symbol, legacy password support, UI validation")
