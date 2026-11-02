#!/usr/bin/env python3
from pathlib import Path
p=Path("android/source-1.6.7/app")
j=p/"src/main/java/fr/monevolution/app/MainActivity.java"
h=p/"src/main/assets/index.html"
g=p/"build.gradle"
m=p/"src/main/AndroidManifest.xml"
def R(path,a,b):
 s=path.read_text(encoding="utf-8")
 assert s.count(a)==1,(str(path),s.count(a),a[:70])
 path.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 22","versionCode 23")
R(g,"versionName '1.6.6'","versionName '1.6.7'")
R(m,'android:versionCode="22" android:versionName="1.6.6"','android:versionCode="23" android:versionName="1.6.7"')
R(h,'Version installée : <strong>1.6.6</strong>','Version installée : <strong>1.6.7</strong>')
R(h,'const installed="1.6.6";','const installed="1.6.7";')
R(j,'MonEvolutionIMC/1.6.6','MonEvolutionIMC/1.6.7')
R(j,'    private String pendingShareJson;','    private String pendingShareJson;\n    private volatile String pendingReceivedPassword="";')
crypto=r"""
    private javax.crypto.SecretKey secretKey() throws Exception {
        java.security.KeyStore store=java.security.KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        java.security.Key k=store.getKey("mon_evolution_secrets",null);
        if(k!=null)return (javax.crypto.SecretKey)k;
        javax.crypto.KeyGenerator gen=javax.crypto.KeyGenerator.getInstance("AES","AndroidKeyStore");
        gen.init(new android.security.keystore.KeyGenParameterSpec.Builder("mon_evolution_secrets",
            android.security.keystore.KeyProperties.PURPOSE_ENCRYPT |
            android.security.keystore.KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes("GCM").setEncryptionPaddings("NoPadding").setKeySize(256).build());
        return gen.generateKey();
    }
    private void saveSecret(String name,String value) throws Exception {
        if(value==null || value.length()<10 || value.length()>512)throw new Exception("Invalid secret");
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.ENCRYPT_MODE,secretKey());
        JSONObject o=new JSONObject();
        o.put("iv",android.util.Base64.encodeToString(c.getIV(),2));
        o.put("data",android.util.Base64.encodeToString(c.doFinal(value.getBytes(StandardCharsets.UTF_8)),2));
        getPreferences(MODE_PRIVATE).edit().putString(name,o.toString()).apply();
    }
    private String readSecret(String name) throws Exception {
        String raw=getPreferences(MODE_PRIVATE).getString(name,null);
        if(raw==null)return null;
        JSONObject o=new JSONObject(raw);
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.DECRYPT_MODE,secretKey(),
            new javax.crypto.spec.GCMParameterSpec(128,android.util.Base64.decode(o.getString("iv"),0)));
        return new String(c.doFinal(android.util.Base64.decode(o.getString("data"),0)),StandardCharsets.UTF_8);
    }
    private javax.crypto.SecretKey deriveKey(String password,byte[] salt) throws Exception {
        if(password==null || password.length()<10 || password.length()>512)throw new Exception("Mot de passe nécessaire");
        javax.crypto.spec.PBEKeySpec spec=new javax.crypto.spec.PBEKeySpec(password.toCharArray(),salt,210000,256);
        byte[] raw=javax.crypto.SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
        spec.clearPassword();
        javax.crypto.SecretKey key=new javax.crypto.spec.SecretKeySpec(raw,"AES");
        java.util.Arrays.fill(raw,(byte)0);
        return key;
    }
    private String encryptShared(String plain,String password) throws Exception {
        byte[] salt=new byte[16],nonce=new byte[12];
        java.security.SecureRandom random=new java.security.SecureRandom();
        random.nextBytes(salt);random.nextBytes(nonce);
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.ENCRYPT_MODE,deriveKey(password,salt),
            new javax.crypto.spec.GCMParameterSpec(128,nonce));
        c.updateAAD("mon-evolution-chiffre-v1".getBytes(StandardCharsets.UTF_8));
        JSONObject result=new JSONObject();
        result.put("format","mon-evolution-chiffre");
        result.put("version",1);result.put("iterations",210000);
        result.put("alg","AES-256-GCM");
        result.put("salt",android.util.Base64.encodeToString(salt,2));
        result.put("nonce",android.util.Base64.encodeToString(nonce,2));
        result.put("data",android.util.Base64.encodeToString(c.doFinal(plain.getBytes(StandardCharsets.UTF_8)),2));
        return result.toString();
    }
    private JSONObject decodeShared(String raw,String password) throws Exception {
        JSONObject o=new JSONObject(raw);
        if("mon-evolution-lecture-seule".equals(o.optString("format"))){
            validateReceived(o);return o;
        }
        if(!"mon-evolution-chiffre".equals(o.optString("format"))
            ||o.optInt("version")!=1 ||o.optInt("iterations")!=210000
            ||!"AES-256-GCM".equals(o.optString("alg")))
            throw new Exception("Format non reconnu");
        byte[] salt=android.util.Base64.decode(o.getString("salt"),0);
        byte[] nonce=android.util.Base64.decode(o.getString("nonce"),0);
        byte[] ciphertext=android.util.Base64.decode(o.getString("data"),0);
        if(salt.length!=16 || nonce.length!=12 || ciphertext.length>40000000)
            throw new Exception("Enveloppe invalide");
        javax.crypto.Cipher c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        c.init(javax.crypto.Cipher.DECRYPT_MODE,deriveKey(password,salt),
            new javax.crypto.spec.GCMParameterSpec(128,nonce));
        c.updateAAD("mon-evolution-chiffre-v1".getBytes(StandardCharsets.UTF_8));
        JSONObject doc=new JSONObject(new String(c.doFinal(ciphertext),StandardCharsets.UTF_8));
        validateReceived(doc);
        return doc;
    }
"""
R(j,'    private String driveFileId(String url) {',crypto+'\n    private String driveFileId(String url) {')
R(j,'        return result;\n    }\n\n    // Independent of private backup:',
'''        return encryptShared(result,readSecret("share_pass_"+id));
    }

    // Independent of private backup:''')
R(j,'        @JavascriptInterface public void createShare(String profileId, String json) {',
'''        @JavascriptInterface public boolean saveSharePassword(String id,String pass) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return false;
            try{saveSecret("share_pass_"+id,pass);return true;}catch(Exception e){return false;}
        }
        @JavascriptInterface public boolean hasSharePassword(String id){
            return id!=null && getPreferences(MODE_PRIVATE).contains("share_pass_"+id);
        }
        @JavascriptInterface public void loadSharedPublicPassword(String url,String pass){
            pendingReceivedPassword=pass==null?"":pass;
            loadSharedPublic(url);
        }
        @JavascriptInterface public void openSharedPassword(String pass){
            pendingReceivedPassword=pass==null?"":pass;
            openShared();
        }
        @JavascriptInterface public void createShare(String profileId, String json) {''')
R(j,'        @JavascriptInterface public void loadSharedPublic(String url) {\n            String id=driveFileId(url);',
'''        @JavascriptInterface public void loadSharedPublic(String url) {
            final String pass=pendingReceivedPassword;
            pendingReceivedPassword="";
            String id=driveFileId(url);''')
R(j,'''                    JSONObject doc=new JSONObject(new String(body,StandardCharsets.UTF_8));
                    if(!"mon-evolution-lecture-seule".equals(doc.optString("format"))
                        || doc.optInt("version")!=1)
                        throw new Exception("Not an app share");
                    validateReceived(doc);''',
'''                    JSONObject doc=decodeShared(new String(body,StandardCharsets.UTF_8),pass);''')
R(j,'''                    String key=registerReceived("public",source,doc);
                    String b64=android.util.Base64.encodeToString(body,android.util.Base64.NO_WRAP);''',
'''                    String key=registerReceived("public",source,doc);
                    if(pass!=null && pass.length()>=10)saveSecret("receive_pass_"+key,pass);
                    byte[] clear=doc.toString().getBytes(StandardCharsets.UTF_8);
                    String b64=android.util.Base64.encodeToString(clear,android.util.Base64.NO_WRAP);''')
R(j,'''                    JSONObject doc=new JSONObject(new String(body,StandardCharsets.UTF_8));
                    validateReceived(doc);
                    registerReceived(kind,source,doc);''',
'''                    JSONObject doc=decodeShared(new String(body,StandardCharsets.UTF_8),
                        readSecret("receive_pass_"+key));
                    registerReceived(kind,source,doc);
                    body=doc.toString().getBytes(StandardCharsets.UTF_8);''')
R(j,'''                String raw=readSafJson(uri,40_000_000);
                JSONObject doc=new JSONObject(raw);
                validateReceived(doc);
                String key=registerReceived("private",uri.toString(),doc);''',
'''                String raw=readSafJson(uri,40_000_000);
                String pass=pendingReceivedPassword;
                pendingReceivedPassword="";
                JSONObject doc=decodeShared(raw,pass);
                String key=registerReceived("private",uri.toString(),doc);
                if(pass!=null && pass.length()>=10)saveSecret("receive_pass_"+key,pass);
                raw=doc.toString();''')
R(j,'''                if(!"mon-evolution-lecture-seule".equals(document.optString("format"))
                    || document.optInt("version")!=1)
                    throw new Exception("Format du partage invalide");
                JSONObject existing=document.getJSONObject("profile");''',
'''                JSONObject existing=decodeShared(document.toString(),
                    readSecret("share_pass_"+pendingShareId)).getJSONObject("profile");''')
R(j,'''                    if(!"mon-evolution-lecture-seule".equals(json.optString("format"))
                        || json.optInt("version")!=1)throw new Exception("invalid_json");
                    json.getJSONObject("profile").getJSONArray("entries");''',
'''                    if(json.optInt("version")!=1)throw new Exception("invalid_json");
                    if("mon-evolution-lecture-seule".equals(json.optString("format")))
                        json.getJSONObject("profile").getJSONArray("entries");
                    else if("mon-evolution-chiffre".equals(json.optString("format")))
                        json.getString("data");
                    else throw new Exception("invalid_json");''')
# Masked password dialog; the link itself is not modified.
widget=r"""
<script>
(function(){
 const d=document.createElement('dialog');
 d.style.cssText='background:#122e43;color:white;border:1px solid #5791a1;border-radius:14px;padding:20px;max-width:90vw';
 d.innerHTML='<h3 id="crypt-title">Mot de passe du partage</h3>'+
 '<p>Le lien reste inchangé. Envoie le mot de passe séparément au destinataire.</p>'+
 '<input id="crypt-input" type="password" autocomplete="off" style="padding:12px;width:100%;border-radius:8px">'+
 '<p id="crypt-error" style="color:#ffbaba"></p>'+
 '<button type="button" class="primary" id="crypt-ok">Continuer</button>'+
 '<button type="button" class="secondary" id="crypt-cancel">Annuler</button>';
 document.body.append(d);
 window.askCrypt=(title,creating,callback)=>{
  $('crypt-title').textContent=title;
  $('crypt-error').textContent='';
  const input=$('crypt-input');input.value='';
  $('crypt-ok').onclick=()=>{
   const pass=input.value;
   if(creating && pass.length<10){$('crypt-error').textContent='Au moins 10 caractères';return;}
   d.close();input.value='';callback(pass);
  };
  $('crypt-cancel').onclick=()=>{d.close();input.value='';callback(null)};
  d.showModal();input.focus();
 };
})();
</script>
"""
R(h,'<script>\n// Incoming Android intent:',widget+'<script>\n// Incoming Android intent:')
R(h,''' AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));''',
''' const publish=()=>AndroidBackup.createShare(p.id,JSON.stringify({profile:{name:p.name,height:p.height,goal:p.goal,entries:p.entries,meals:p.meals||{}}}));
 if(AndroidBackup.hasSharePassword?.(p.id))publish();
 else askCrypt('Créer le mot de passe du fichier chiffré',true,pass=>{
  if(pass!==null && AndroidBackup.saveSharePassword(p.id,pass))publish();
 });''')
R(h,' AndroidBackup.loadSharedPublic(u);',
''' askCrypt('Mot de passe du profil partagé',false,pass=>{
  if(pass!==null)AndroidBackup.loadSharedPublicPassword(u,pass);
  else $('shared-url-load').disabled=false;
 });''')
R(h,"$('shared-open').onclick=()=>$('open-share').click();",
'''$('shared-open').onclick=()=>askCrypt('Mot de passe du fichier reçu',false,pass=>{
 if(pass!==null)window.AndroidBackup?.openSharedPassword?.(pass);
});''')
R(h,'''   window.AndroidBackup?.loadSharedPublic?.(source);''',
'''   askCrypt('Mot de passe du profil reçu',false,pass=>{
    if(pass!==null)window.AndroidBackup?.loadSharedPublicPassword?.(source,pass);
   });''')
R(h,'''   window.AndroidBackup.openShared();
 };''',
'''   $('shared-open').click();
 };''')
R(h,'<h3>🔗 Envoyer mon profil à un proche</h3>',
'''<h3>🔗 Envoyer mon profil à un proche</h3>
   <p class="notice">🔒 Le fichier est chiffré AES-256-GCM. Le lien Google Drive ne change pas. Envoie le mot de passe séparément.</p>''')
print("AES-256-GCM share encryption and password UI integrated")
