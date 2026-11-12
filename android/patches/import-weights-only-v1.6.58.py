#!/usr/bin/env python3
"""v1.6.58: import weight entries only into chosen active local profile."""
from pathlib import Path
root=Path("android/source-1.6.58/app")
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
h=root/"src/main/assets/index.html"
def R(f,a,b):
 s=f.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{f} : {n} matches for {a[:100]!r}")
 f.write_text(s.replace(a,b),encoding="utf-8")
R(j,"PROGRESS_PDF = 51, PHOTO_CAMERA = 52;","PROGRESS_PDF = 51, PHOTO_CAMERA = 52, IMPORT_WEIGHTS = 54;")
R(j,"        @JavascriptInterface public void load() {",'''        @JavascriptInterface public void importWeightsOnly() {
            runOnUiThread(() -> {
                Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("application/json");
                startActivityForResult(i,IMPORT_WEIGHTS);
            });
        }
        @JavascriptInterface public void load() {''')
R(j,"            if (request == LOAD) {",'''            if (request == IMPORT_WEIGHTS) {
                byte[] bytes;
                try(InputStream in=getContentResolver().openInputStream(uri)){
                    if(in==null)throw new Exception("Fichier inaccessible");
                    java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                    byte[] buffer=new byte[4096];int n;
                    while((n=in.read(buffer))!=-1){
                        out.write(buffer,0,n);
                        if(out.size()>1_000_000)throw new Exception("Fichier trop volumineux");
                    }
                    bytes=out.toByteArray();
                }
                String json=new String(bytes,StandardCharsets.UTF_8);
                JSONObject doc=new JSONObject(json);
                if(!"mon-evolution-poids".equals(doc.optString("format"))
                   ||doc.optInt("version")!=1
                   ||!"remplacer-pesees-uniquement".equals(doc.optString("mode")))
                    throw new Exception("Format poids uniquement requis");
                JSONArray weights=doc.getJSONArray("entries");
                if(weights.length()<1||weights.length()>20000)throw new Exception("Nombre de pesées invalide");
                for(int i=0;i<weights.length();i++){
                    JSONObject e=weights.getJSONObject(i);
                    if(!e.getString("date").matches("\\\\d{4}-\\\\d{2}-\\\\d{2}")
                     ||e.getDouble("weight")<1||e.getDouble("weight")>400
                     ||e.optString("note","").length()>120)
                        throw new Exception("Pesée invalide");
                }
                String encoded=android.util.Base64.encodeToString(bytes,android.util.Base64.NO_WRAP);
                web.evaluateJavascript("importWeightsOnlyBase64("+JSONObject.quote(encoded)+")",null);
            } else if (request == LOAD) {''')
ui=r"""
<style>
#weights-only-import{display:block;width:100%;margin:10px 0}
</style>
<script>
(function(){
 const exportButton=$('export-weights'),profilePanel=$('profiles');
 if(!exportButton||!profilePanel)return;
 const button=document.createElement('button');
 button.type='button';button.id='weights-only-import';button.className='secondary';
 button.textContent='↧ Importer des pesées dans ce profil';
 button.title='Remplace uniquement les pesées du profil sélectionné, sans modifier les repas, photos ou réglages.';
 exportButton.insertAdjacentElement('afterend',button);
 button.onclick=()=>{
  if(!window.AndroidBackup?.importWeightsOnly)return message('Mets à jour l’application pour importer les pesées');
  AndroidBackup.importWeightsOnly();
 };
 window.importWeightsOnlyBase64=function(base64){
  try{
   const json=decodeURIComponent(Array.prototype.map.call(atob(base64),c=>'%'+c.charCodeAt(0).toString(16).padStart(2,'0')).join(''));
   const obj=JSON.parse(json);
   if(obj?.format!=='mon-evolution-poids'||obj.version!==1||obj.mode!=='remplacer-pesees-uniquement'
      ||!Array.isArray(obj.entries)||obj.entries.length<1||obj.entries.length>20000)throw Error('format');
   const cleaned=obj.entries.map((e,i)=>{
    if(!e||typeof e.date!=='string'||!/^\\d{4}-\\d{2}-\\d{2}$/.test(e.date)
       ||!Number.isFinite(e.weight)||e.weight<1||e.weight>400
       ||(e.note!==undefined&&(typeof e.note!=='string'||e.note.length>120)))throw Error('pesée');
    return {id:Number.isSafeInteger(e.id)?e.id:Date.now()+i,date:e.date,weight:e.weight,note:e.note||''};
   });
   const p=profile();
   if(!p||!data.profiles.includes(p))throw Error('profil');
   const id=p.id;
   if(!confirm('Remplacer UNIQUEMENT les '+p.entries.length+' pesées actuelles du profil « '+p.name+' » par '+cleaned.length+' pesées importées ?\\n\\nLes autres profils, les repas, les photos, la taille, l’objectif et les paramètres seront conservés.'))return;
   // Resolve by ID again after confirmation to protect against a profile switch.
   const target=data.profiles.find(x=>x.id===id);
   if(!target)throw Error('profil changé');
   target.entries=cleaned;
   save();
   render();
   message(cleaned.length+' pesées importées ✓ Aucun repas ni autre profil modifié.');
  }catch(error){alert('Importation impossible : vérifie le fichier de pesées uniquement. Aucun profil n’a été modifié.');}
 };
})();
</script>
"""
# avoid Markdown/JS escaped regex errors in a Python raw text file.
ui=ui.replace("!/^\\\\d{4}-\\\\d{2}-\\\\d{2}$/","!/^\\d{4}-\\d{2}-\\d{2}$/")
R(h,"</body></html>",ui+"\n</body></html>")
print("v1.6.58 import only target profile weight entries")
