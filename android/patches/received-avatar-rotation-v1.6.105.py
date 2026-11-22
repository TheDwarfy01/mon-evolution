#!/usr/bin/env python3
"""IMC v1.6.105: local rotation for RECEIVED profile portraits.
Rotate during display without changing Drive owner data or shared documents.
"""
from pathlib import Path
root=Path("android/source-1.6.105/app/src/main/java/fr/monevolution/app")
source=root/"MainActivity.java"
s=source.read_text(encoding="utf-8")
old='''        @JavascriptInterface public String receivedAvatar(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return "";
            return getPreferences(MODE_PRIVATE).getString("friend_avatar_"+key,"");
        }'''
new='''        @JavascriptInterface public boolean rotateReceivedAvatar(String key,String action) {
            if(key==null || !key.matches("[a-f0-9-]{36}") ||
               action==null || !java.util.Arrays.asList("left","right","mirror","reset").contains(action))
                return false;
            android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            if(!prefs.contains("friend_avatar_"+key)) return false;
            int turns=prefs.getInt("friend_turns_"+key,0);
            boolean mirrored=prefs.getBoolean("friend_mirror_"+key,false);
            if("left".equals(action))turns=(turns+3)%4;
            else if("right".equals(action))turns=(turns+1)%4;
            else if("mirror".equals(action))mirrored=!mirrored;
            else {turns=0;mirrored=false;}
            prefs.edit().putInt("friend_turns_"+key,turns)
                .putBoolean("friend_mirror_"+key,mirrored).apply();
            return true;
        }
        @JavascriptInterface public String receivedAvatar(String key) {
            if(key==null || !key.matches("[a-f0-9-]{36}"))return "";
            android.content.SharedPreferences prefs=getPreferences(MODE_PRIVATE);
            String raw=prefs.getString("friend_avatar_"+key,"");
            if(!raw.startsWith("data:image/jpeg;base64,")||raw.length()>250000)return "";
            int turns=prefs.getInt("friend_turns_"+key,0)%4;
            boolean mirror=prefs.getBoolean("friend_mirror_"+key,false);
            if(turns==0&&!mirror)return raw;
            try {
                byte[] bytes=android.util.Base64.decode(
                    raw.substring("data:image/jpeg;base64,".length()),
                    android.util.Base64.DEFAULT);
                android.graphics.Bitmap photo=android.graphics.BitmapFactory
                    .decodeByteArray(bytes,0,bytes.length);
                if(photo==null)return raw;
                android.graphics.Matrix matrix=new android.graphics.Matrix();
                if(mirror)matrix.postScale(-1f,1f);
                if(turns!=0)matrix.postRotate(turns*90f);
                android.graphics.Bitmap turned=android.graphics.Bitmap.createBitmap(
                    photo,0,0,photo.getWidth(),photo.getHeight(),matrix,true);
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                turned.compress(android.graphics.Bitmap.CompressFormat.JPEG,83,out);
                if(out.size()>180000){
                    out.reset();
                    turned.compress(android.graphics.Bitmap.CompressFormat.JPEG,65,out);
                }
                String result="data:image/jpeg;base64,"+
                   android.util.Base64.encodeToString(out.toByteArray(),
                       android.util.Base64.NO_WRAP);
                if(turned!=photo)turned.recycle();
                photo.recycle();
                return result.length()<250000?result:raw;
            }catch(Exception ignored){return raw;}
        }'''
assert s.count(old)==1,"Native avatar getter not found"
s=s.replace(old,new)
cleanup='''                    edit.remove("friend_avatar_"+key);
                    edit.remove("received_sync_"+key);'''
assert s.count(cleanup)==1,"Cleanup match failed"
s=s.replace(cleanup,'''                    edit.remove("friend_avatar_"+key);
                    edit.remove("friend_turns_"+key);
                    edit.remove("friend_mirror_"+key);
                    edit.remove("received_sync_"+key);''')
source.write_text(s,encoding="utf-8")
print("Received avatar orientation stored locally per shared profile; never writes to owner's Drive")
