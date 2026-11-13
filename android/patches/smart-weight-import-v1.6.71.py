#!/usr/bin/env python3
"""v1.6.71 : reconnaît le JSON de pesées lors de Charger une sauvegarde.

Importation strictement limitée aux entrées du profil PERSONNEL sélectionné,
avec confirmation existante. Aucun changement de repas, photo ou paramètres.
"""
from pathlib import Path
p=Path("android/source-1.6.71/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
assert s.count("</body></html>")==1
assert "function restoreBase64(base64)" in s
assert "window.importWeightsOnlyBase64=function(base64)" in s
assert "remplacer-pesees-uniquement" in s

# Message clair dans l'UI du profil, proche du bon importateur.
s=s.replace("button.textContent='↧ Importer des pesées dans ce profil';",
"""button.textContent='↧ Importer des pesées (JSON) — ce profil uniquement';""",1)

# L'utilisateur peut importer par le sélecteur "Charger une sauvegarde" :
# rediriger le format mon-evolution-poids vers le VALIDATEUR EXISTANT.
# Ne pas modifier le format sauvegarde ou les données locales en cas d'erreur.
addon="""<script id="mon-evolution-smart-json-171">
(function(){
 'use strict';
 if(typeof window.restoreBase64!=='function')return;
 const previousRestore=window.restoreBase64;
 window.restoreBase64=function(base64){
  let obj=null;
  try{
   const raw=Uint8Array.from(atob(base64),ch=>ch.charCodeAt(0));
   obj=JSON.parse(new TextDecoder().decode(raw));
  }catch(e){
   return previousRestore.call(this,base64);
  }
  if(obj&&obj.format==='mon-evolution-poids'){
   if(typeof window.importWeightsOnlyBase64!=='function'){
    alert('Ce fichier contient uniquement des pesées. Ouvre Profils puis Importer des pesées (JSON).');
    return;
   }
   window.importWeightsOnlyBase64(base64);
   return;
  }
  return previousRestore.call(this,base64);
 };
})();
</script>
"""
s=s.replace("</body></html>",addon+"</body></html>")
assert "window.importWeightsOnlyBase64(base64)" in s
assert "return previousRestore.call(this,base64)" in s
assert "mon-evolution-smart-json-171" in s
p.write_text(s,encoding="utf-8")
print("PASS : JSON poids reconnu automatiquement ; appel de l'import ciblé avec confirmation")
