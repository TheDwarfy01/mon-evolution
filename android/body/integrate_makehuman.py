#!/usr/bin/env python3
"""Connect cached MakeHuman CC0 data to the Android WebView without bundling it.
Run after all existing version-specific patches, before Android compilation.
"""
import shutil
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: integrate_makehuman.py android/source-1.6.122")
root=Path(sys.argv[1])
assets=root/"app/src/main/assets"
activity=root/"app/src/main/java/fr/monevolution/app/MainActivity.java"
if not assets.is_dir() or not activity.is_file():
    raise RuntimeError("Android source directory is incomplete")

for name in ("makehuman-morph-adapter.js", "makehuman-viewer.js",
             "makehuman-table-mode.js", "intermediate-goal-icons-v125.js"):
    shutil.copyfile("android/body/"+name, assets/name)
html=assets/"index.html"
src=html.read_text(encoding="utf-8")
needle="</body></html>"
assert src.count(needle)==1, "Main HTML footer missing"
assert "makehuman-viewer.js" not in src, "MakeHuman already installed"
# Remove the old photographic male/female model and its base64 masks
# from the published APK. Other photographs, including meal photos,
# progress photos and avatars, are untouched.
for deprecated in ("models-hq-inline.js", "studio-mask-data.js",
                   "photoreal-models.js"):
    src=src.replace('<script src="'+deprecated+'"></script>', '')
    asset=assets/deprecated
    if asset.exists():
        asset.unlink()
for obsolete in ("models-hq-v2.webp", "studio-skin-mask.png",
                 "studio-hair-mask.png", "studio-eyes-mask.png"):
    asset=assets/obsolete
    if asset.exists():
        asset.unlink()
src=src.replace(needle, """<script src="makehuman-morph-adapter.js"></script>
<script src="makehuman-viewer.js"></script>
<script src="makehuman-table-mode.js"></script>
<script src="intermediate-goal-icons-v125.js"></script>
</body></html>""")
html.write_text(src,encoding="utf-8")

java=activity.read_text(encoding="utf-8")
anchor="    public class Bridge {"
assert java.count(anchor)==1,"Expected exactly one AndroidBackup JS bridge"
assert "makeHumanInstall()" not in java,"MakeHuman bridge already installed"
bridge=r'''
        // MakeHuman data is installed independently in private application storage.
        // APK upgrades do not clear getFilesDir(); uninstalling the app does.
        private volatile String makeHumanDownloadState="missing";
        private static final String MH_PACK_TAG="avatar-pack-v1";
        private static final String MH_PACK_NAME="makehuman-pack-v1.json.gz";

        private File makeHumanFile(){
            File dir=new File(getFilesDir(),"makehuman");
            return new File(dir,MH_PACK_NAME);
        }
        @JavascriptInterface public String makeHumanState(){
            File pack=makeHumanFile();
            return pack.isFile()&&pack.length()>100000&&pack.length()<12000000
                 ?"ready":makeHumanDownloadState;
        }
        @JavascriptInterface public int makeHumanBytes(){
            File f=makeHumanFile();
            return f.isFile()&&f.length()<12000000?(int)f.length():0;
        }
        @JavascriptInterface public String makeHumanReadChunk(int offset){
            File file=makeHumanFile();
            if(!file.isFile()||offset<0||offset>file.length()||file.length()>12000000)return "";
            int count=(int)Math.min(49152,file.length()-offset);
            if(count==0)return "";
            byte[] buffer=new byte[count];
            try(java.io.FileInputStream in=new java.io.FileInputStream(file)){
                long skipped=0;
                while(skipped<offset){
                    long n=in.skip(offset-skipped);
                    if(n<=0)return "";
                    skipped+=n;
                }
                int pos=0;
                while(pos<count){
                    int n=in.read(buffer,pos,count-pos);
                    if(n<0)return "";
                    pos+=n;
                }
                return android.util.Base64.encodeToString(buffer,android.util.Base64.NO_WRAP);
            }catch(Exception err){
                return "";
            }
        }
        private byte[] makeHumanFetch(String address,int maxBytes) throws Exception{
            java.net.URL current=new java.net.URL(address);
            for(int redirects=0;redirects<7;redirects++){
                String domain=current.getHost().toLowerCase(java.util.Locale.ROOT);
                if(!"https".equalsIgnoreCase(current.getProtocol())||
                   !(domain.equals("github.com")||domain.endsWith(".githubusercontent.com"))){
                    throw new java.io.IOException("Hôte du module MakeHuman non autorisé");
                }
                java.net.HttpURLConnection c=(java.net.HttpURLConnection)current.openConnection();
                c.setInstanceFollowRedirects(false);
                c.setConnectTimeout(18000);
                c.setReadTimeout(45000);
                c.setRequestProperty("User-Agent","MonEvolutionIMC-MakeHuman/1.0");
                try{
                    int code=c.getResponseCode();
                    if(code==301||code==302||code==303||code==307||code==308){
                        String location=c.getHeaderField("Location");
                        if(location==null)throw new java.io.IOException("Redirection manquante");
                        current=new java.net.URL(current,location);
                        continue;
                    }
                    if(code!=200)throw new java.io.IOException("Téléchargement HTTP "+code);
                    if(c.getContentLengthLong()>maxBytes)
                        throw new java.io.IOException("Fichier trop volumineux");
                    try(java.io.InputStream in=c.getInputStream();
                        java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){
                        byte[] buffer=new byte[32768];
                        int n;
                        while((n=in.read(buffer))!=-1){
                            if(out.size()+n>maxBytes)
                                throw new java.io.IOException("Fichier trop volumineux");
                            out.write(buffer,0,n);
                        }
                        return out.toByteArray();
                    }
                }finally{c.disconnect();}
            }
            throw new java.io.IOException("Trop de redirections");
        }
        @JavascriptInterface public void makeHumanInstall(){
            if("ready".equals(makeHumanState())||
               "downloading".equals(makeHumanDownloadState))return;
            makeHumanDownloadState="downloading";
            io.execute(()->{
                File pack=makeHumanFile();
                File part=new File(pack.getParentFile(),MH_PACK_NAME+".part");
                try{
                    String base="https://github.com/TheDwarfy01/mon-evolution/releases/download/"
                               +MH_PACK_TAG+"/"+MH_PACK_NAME;
                    String line=new String(makeHumanFetch(base+".sha256",1024),
                                           java.nio.charset.StandardCharsets.US_ASCII);
                    String expected=line.trim().split("\\s+")[0].toLowerCase(java.util.Locale.ROOT);
                    if(!expected.matches("[a-f0-9]{64}"))
                        throw new java.io.IOException("Empreinte invalide");
                    byte[] data=makeHumanFetch(base,12000000);
                    if(data.length<100000)
                        throw new java.io.IOException("Modèle MakeHuman incomplet");
                    java.security.MessageDigest md=java.security.MessageDigest.getInstance("SHA-256");
                    byte[] hash=md.digest(data);
                    StringBuilder actual=new StringBuilder(64);
                    for(byte b:hash)actual.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
                    if(!expected.equals(actual.toString()))
                        throw new java.io.IOException("Intégrité du modèle incorrecte");
                    if(!pack.getParentFile().isDirectory() && !pack.getParentFile().mkdirs())
                        throw new java.io.IOException("Stockage du module impossible");
                    try(java.io.FileOutputStream out=new java.io.FileOutputStream(part)){
                        out.write(data);
                        out.getFD().sync();
                    }
                    if(!part.renameTo(pack))
                        throw new java.io.IOException("Impossible d'enregistrer le module");
                    makeHumanDownloadState="ready";
                }catch(Exception err){
                    part.delete();
                    makeHumanDownloadState="error:"+err.getClass().getSimpleName();
                }
                runOnUiThread(()->{
                    if(web!=null)web.evaluateJavascript(
                      "window.dispatchEvent(new Event('mon-evolution-makehuman-ready'))",null);
                });
            });
        }
'''
java=java.replace(anchor,anchor+"\n"+bridge,1)
activity.write_text(java,encoding="utf-8")
print("OK: MakeHuman WebGL viewer and persistent authenticated Android pack installer integrated:",root)
