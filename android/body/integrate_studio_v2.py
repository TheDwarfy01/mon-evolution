#!/usr/bin/env python3
"""Replace v1 WebGL avatar with licensed CC0/Three.js Studio v2.

The offline renderer JS is bundled from npm Three.js by the release workflow.
The 3D assets are downloaded once into Android's private files area.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Usage: integrate_studio_v2.py android/source-1.6.127")
root=Path(sys.argv[1])/"app"
assets=root/"src/main/assets"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
src=assets/"index.html"
bundle=Path("android/body/makehuman-studio-bundle.js")
assert j.is_file() and src.is_file() and bundle.is_file()
shutil.copyfile(bundle,assets/"makehuman-studio-bundle.js")
html=src.read_text(encoding="utf-8")
assert html.count('<script src="makehuman-viewer.js"></script>')==1
html=html.replace('<script src="makehuman-viewer.js"></script>',
    '<script src="makehuman-studio-bundle.js"></script>')
src.write_text(html,encoding="utf-8")
old=assets/"makehuman-viewer.js"
if old.exists():old.unlink()

java=j.read_text(encoding="utf-8")
assert "makeHumanFetch(String address,int maxBytes)" in java
assert "makeHumanStudioInstall()" not in java
anchor="        @JavascriptInterface public void makeHumanInstall(){"
assert java.count(anchor)==1,anchor
addition=r'''
        // Isolated CC0 MakeHuman Studio v2 pack. APK updates do not erase it.
        private volatile String studioDownloadState="missing";
        private static final String STUDIO_ZIP="makehuman-studio-v2.zip";
        private static final String STUDIO_TAG="avatar-studio-v2";
        private File studioPath(){
            return new File(new File(getFilesDir(),"makehuman"),"studio-v2");
        }
        private boolean studioReady(){
            File d=studioPath();
            return new File(d,".ready").isFile() &&
                new File(d,"base_body_anim.glb").length()>1000000 &&
                new File(d,"clothing_tshirt.glb").length()>30000 &&
                new File(d,"clothing_jeans.glb").length()>30000 &&
                new File(d,"hair_short02.glb").length()>30000;
        }
        @JavascriptInterface public String makeHumanStudioState(){
            return studioReady()?"ready":studioDownloadState;
        }
        private boolean studioValidFile(String name){
            return name!=null &&
                name.matches("(?:base_body_anim|hair_(?:short02|short04|bob02|long01|ponytail01|braid01|afro01)|clothing_(?:tshirt|shirt|hoodie|jeans|shorts|skirt|shoes))\\.glb");
        }
        @JavascriptInterface public int makeHumanStudioBytes(String name){
            if(!studioValidFile(name)||!studioReady())return 0;
            File f=new File(studioPath(),name);
            return f.isFile()&&f.length()>0&&f.length()<14000000?(int)f.length():0;
        }
        @JavascriptInterface public String makeHumanStudioReadChunk(String name,int offset){
            if(!studioValidFile(name)||!studioReady())return "";
            File f=new File(studioPath(),name);
            if(!f.isFile()||offset<0||offset>=f.length()||f.length()>14000000)return "";
            final int count=(int)Math.min(49152,f.length()-offset);
            byte[] bytes=new byte[count];
            try(java.io.FileInputStream in=new java.io.FileInputStream(f)){
                long skipped=0;
                while(skipped<offset){
                    long n=in.skip(offset-skipped);
                    if(n<=0)return "";
                    skipped+=n;
                }
                int pos=0;
                while(pos<count){
                    int n=in.read(bytes,pos,count-pos);
                    if(n<0)return "";
                    pos+=n;
                }
                return android.util.Base64.encodeToString(bytes,android.util.Base64.NO_WRAP);
            }catch(Exception ex){return "";}
        }
        private void studioCleanDir(File directory){
            if(directory==null||!directory.exists())return;
            File root=new File(getFilesDir(),"makehuman");
            try{
                if(!directory.getCanonicalPath().startsWith(root.getCanonicalPath()+File.separator))return;
                if(directory.isDirectory()){
                    File[] children=directory.listFiles();
                    if(children!=null)for(File f:children)studioCleanDir(f);
                }
                directory.delete();
            }catch(Exception ignored){}
        }
        @JavascriptInterface public void makeHumanStudioInstall(){
            if(studioReady()||"downloading".equals(studioDownloadState))return;
            studioDownloadState="downloading";
            io.execute(()->{
                File parent=studioPath().getParentFile();
                File stage=new File(parent,"studio-v2-incomplete");
                try{
                    String base="https://github.com/TheDwarfy01/mon-evolution/releases/download/"
                        +STUDIO_TAG+"/"+STUDIO_ZIP;
                    String check=new String(makeHumanFetch(base+".sha256",1024),
                        java.nio.charset.StandardCharsets.US_ASCII);
                    String expected=check.trim().split("\\s+")[0].toLowerCase(java.util.Locale.ROOT);
                    if(!expected.matches("[a-f0-9]{64}"))
                        throw new java.io.IOException("Empreinte du module invalide");
                    byte[] archive=makeHumanFetch(base,60_000_000);
                    if(archive.length<9_000_000)
                        throw new java.io.IOException("Module 3D incomplet");
                    byte[] digest=java.security.MessageDigest.getInstance("SHA-256").digest(archive);
                    StringBuilder hash=new StringBuilder(64);
                    for(byte b:digest)hash.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
                    if(!expected.equals(hash.toString()))
                        throw new java.io.IOException("Module 3D non authentifié");
                    if(!parent.exists()&&!parent.mkdirs())
                        throw new java.io.IOException("Espace de stockage indisponible");
                    studioCleanDir(stage);
                    if(!stage.mkdir())throw new java.io.IOException("Dossier temporaire impossible");
                    int assetsRead=0;
                    long bytesRead=0;
                    try(java.util.zip.ZipInputStream unzip=new java.util.zip.ZipInputStream(
                           new java.io.ByteArrayInputStream(archive))){
                        java.util.zip.ZipEntry entry;
                        while((entry=unzip.getNextEntry())!=null){
                            String name=entry.getName();
                            if(entry.isDirectory()||name.contains("/")||name.contains("\\")||
                               name.contains("..")||name.startsWith(".")||
                               !(studioValidFile(name)||name.equals("manifest.json")||
                                 name.equals("LICENSE-CC0.txt"))){
                                throw new java.io.IOException("Entrée ZIP inconnue");
                            }
                            assetsRead++;
                            if(assetsRead>20)throw new java.io.IOException("Trop de ressources 3D");
                            File f=new File(stage,name);
                            int current=0,n;
                            byte[] buffer=new byte[32768];
                            try(java.io.FileOutputStream out=new java.io.FileOutputStream(f)){
                                while((n=unzip.read(buffer))!=-1){
                                    current+=n;
                                    bytesRead+=n;
                                    if(current>14_000_000||bytesRead>80_000_000)
                                        throw new java.io.IOException("Décompression refusée");
                                    out.write(buffer,0,n);
                                }
                                out.getFD().sync();
                            }
                            unzip.closeEntry();
                        }
                    }
                    if(assetsRead<15||new File(stage,"base_body_anim.glb").length()<1_000_000||
                       new File(stage,"clothing_tshirt.glb").length()<30000||
                       new File(stage,"hair_short02.glb").length()<30000)
                        throw new java.io.IOException("Ressources MakeHuman Studio incomplètes");
                    // Do not modify a previously verified pack before new installation.
                    if(studioPath().exists()&&!studioReady())
                        studioCleanDir(studioPath());
                    if(!stage.renameTo(studioPath()) && !studioReady())
                        throw new java.io.IOException("Activation du Studio impossible");
                    File marker=new File(studioPath(),".ready");
                    try(java.io.FileOutputStream out=new java.io.FileOutputStream(marker)){
                        out.write(expected.getBytes(StandardCharsets.US_ASCII));
                        out.getFD().sync();
                    }
                    if(!studioReady())throw new java.io.IOException("Module 3D non confirmé");
                    studioDownloadState="ready";
                }catch(Exception e){
                    studioCleanDir(stage);
                    studioDownloadState="error:"+e.getClass().getSimpleName();
                }
                runOnUiThread(()->{
                    if(web!=null)web.evaluateJavascript(
                      "window.dispatchEvent(new Event('mon-evolution-studio-ready'))",null);
                });
            });
        }

'''
java=java.replace(anchor,addition+anchor,1)
j.write_text(java,encoding="utf-8")
assert "makeHumanStudioState()" in java
assert '<script src="makehuman-studio-bundle.js"></script>' in html
print("OK: MakeHuman Studio v2 offline viewer + Android verified module installer integrated")
