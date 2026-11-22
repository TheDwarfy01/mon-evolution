#!/usr/bin/env python3
"""v1.6.121: direct-file Google Drive sharing navigation for minor profiles.
The app cannot set Google Drive ACLs from a Storage Access Framework URI.
Open the EXACT linked document when available, never silently open Drive root.
"""
from pathlib import Path
import shutil
assets=Path("android/source-1.6.121/app/src/main/assets")
java=Path("android/source-1.6.121/app/src/main/java/fr/monevolution/app/MainActivity.java")
source=java.read_text(encoding="utf-8")
needle='        @JavascriptInterface public void verifyOwnedChildShare(String id) {'
assert source.count(needle)==1, "child collaboration verification bridge missing"
addon=r'''
        @JavascriptInterface public String childShareDocumentInfo(String id){
            JSONObject result=new JSONObject();
            try{
                if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))
                    return "{}";
                String stored=getPreferences(MODE_PRIVATE).getString("share_uri_"+id,null);
                boolean linked=stored!=null;
                result.put("linked",linked);
                result.put("name","mon-evolution-partage-"+id+".json");
                if(!linked)return result.toString();
                Uri uri=Uri.parse(stored);
                String authority=uri.getAuthority();
                if(authority!=null){
                    result.put("provider",authority.contains("docs")||authority.contains("drive")
                        ?"Google Drive":"Fichier Android relié");
                }
                // Try to display the selected document's actual name. The SAF
                // URI, not this name, is authoritative for the open action.
                try(android.database.Cursor cursor=getContentResolver().query(uri,
                    new String[]{android.provider.OpenableColumns.DISPLAY_NAME},
                    null,null,null)){
                    if(cursor!=null && cursor.moveToFirst()){
                        String actual=cursor.getString(0);
                        if(actual!=null && actual.length()>0 && actual.length()<250)
                            result.put("name",actual);
                    }
                }catch(Exception ignored){}
                result.put("savedLink",validDriveShareLink(getShareLink(id)));
            }catch(Exception ignored){}
            return result.toString();
        }
        @JavascriptInterface public void openChildShareDocument(String id){
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return;
            final String uriValue=getPreferences(MODE_PRIVATE).getString("share_uri_"+id,null);
            if(uriValue==null){
                js("childShareFileOpenResult("+JSONObject.quote(id)+",'missing')");
                return;
            }
            runOnUiThread(()->{
                try {
                    final String link=getShareLink(id);
                    Intent target;
                    if(validDriveShareLink(link)){
                        // A saved validated share URL points to the exact file,
                        // instead of the generic /drive/my-drive screen.
                        target=new Intent(Intent.ACTION_VIEW,Uri.parse(link));
                        target.addCategory(Intent.CATEGORY_BROWSABLE);
                        // Prefer the installed Drive app, but permit a browser.
                        Intent drive=new Intent(target);
                        drive.setPackage("com.google.android.apps.docs");
                        if(drive.resolveActivity(getPackageManager())!=null)target=drive;
                    }else{
                        // Before the user has manually saved the Drive URL, the
                        // persisted Android document URI is the exact reference.
                        Uri document=Uri.parse(uriValue);
                        if(!"content".equalsIgnoreCase(document.getScheme()))
                            throw new Exception("Unsupported document URI");
                        target=new Intent(Intent.ACTION_VIEW);
                        target.setDataAndType(document,"application/json");
                        target.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        Intent drive=new Intent(target);
                        drive.setPackage("com.google.android.apps.docs");
                        if(drive.resolveActivity(getPackageManager())!=null)
                            target=drive;
                        else if(target.resolveActivity(getPackageManager())==null){
                            js("childShareFileOpenResult("+JSONObject.quote(id)+",'need_link')");
                            return;
                        }
                    }
                    startActivity(target);
                    js("childShareFileOpenResult("+JSONObject.quote(id)+",'opened')");
                }catch(Exception error){
                    js("childShareFileOpenResult("+JSONObject.quote(id)+",'error')");
                }
            });
        }
'''
source=source.replace(needle,addon+needle)
java.write_text(source,encoding="utf-8")
page=assets/"index.html"
html=page.read_text(encoding="utf-8")
needle_html="</body></html>"
assert html.count(needle_html)==1 and "child-share-file-guide.js" not in html
page.write_text(html.replace(needle_html,
    '<script src="child-share-file-guide.js"></script>\n'+needle_html),
    encoding="utf-8")
shutil.copyfile("android/body/child-share-file-guide.js",
    assets/"child-share-file-guide.js")
print("v1.6.121: configured exact-file Drive action, create/relink wizard and editor gate")
