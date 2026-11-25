#!/usr/bin/env python3
"""Convert the already tested Anny diagnostic into an installable IMC upgrade."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])/'app'
assets=root/'src/main/assets'
java=root/'src/main/java/fr/monevolution/app'
def change(s,a,b):
    assert s.count(a)==1, (a,s.count(a))
    return s.replace(a,b,1)
p=root/'build.gradle';s=p.read_text()
s=change(s,"applicationId 'fr.monevolution.annytest'","applicationId 'fr.monevolution.app'")
s=change(s,"versionName '1.6.160-anny-test'","versionName '1.6.165'")
s=change(s,'versionCode 176','versionCode 181')
p.write_text(s)
p=java/'CameraPhotoProvider.java'
p.write_text(p.read_text().replace('fr.monevolution.annytest.camera','fr.monevolution.app.camera'))
p=root/'src/main/AndroidManifest.xml';s=p.read_text()
s=s.replace('fr.monevolution.annytest.camera','fr.monevolution.app.camera').replace('IMC Anny TEST','Mon Évolution IMC').replace('monevolutionanny','monevolution')
launcher='''      <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
      </intent-filter>'''
assert s.count(launcher)==1
s=s.replace(launcher,'',1)
s=change(s,'android:name=".FilamentPreviewActivity" android:exported="true"','android:name=".FilamentPreviewActivity" android:exported="false"')
anchor=re.search(r'<activity\b[^>]*android:name="\.MainActivity"[^>]*>',s)
assert anchor
s=s[:anchor.end()]+'\n'+launcher+s[anchor.end():]
s=re.sub(r'android:versionCode="\d+"','android:versionCode="181"',s,count=1)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="1.6.165"',s,count=1)
p.write_text(s)
p=assets/'index.html';s=p.read_text()
s=change(s,'<script src="filament-test.js"></script>','')
p.write_text(s.replace('1.6.143','1.6.165'))
(assets/'filament-test.js').unlink()
p=java/'MainActivity.java';s=p.read_text()
a='''        @JavascriptInterface public void openFilamentPreview(){
            runOnUiThread(()->startActivity(new android.content.Intent(
                MainActivity.this,FilamentPreviewActivity.class)));
        }'''
b='''        private boolean allowedAnnyAsset(String name){
            return "anny-male-long-morph.glb".equals(name)||"anny-female-long-morph.glb".equals(name);
        }
        @JavascriptInterface public int annyAssetBytes(String name){
            if(!allowedAnnyAsset(name))return 0;
            try(java.io.InputStream in=getAssets().open(name)){
                return in.available();
            }catch(Exception ex){return 0;}
        }
        @JavascriptInterface public String annyAssetReadChunk(String name,int offset){
            if(!allowedAnnyAsset(name)||offset<0||offset>=14000000)return "";
            try(java.io.InputStream in=getAssets().open(name)){
                long skipped=0;
                while(skipped<offset){long n=in.skip(offset-skipped);if(n<=0)return "";skipped+=n;}
                byte[] bytes=new byte[49152];int read=0;
                while(read<bytes.length){int n=in.read(bytes,read,bytes.length-read);if(n<=0)break;read+=n;}
                return read==0?"":android.util.Base64.encodeToString(bytes,0,read,android.util.Base64.NO_WRAP);
            }catch(Exception ex){return "";}
        }
        @JavascriptInterface public void openAnnyProfile(String snapshot){
            if(snapshot==null||snapshot.length()>12000)return;
            try {
                org.json.JSONObject data=new org.json.JSONObject(snapshot);
                String sex=data.optString("sex");
                if(!"male".equals(sex)&&!"female".equals(sex))return;
                if(data.optJSONArray("regions")==null||data.optJSONArray("regions").length()!=9)return;
                runOnUiThread(()->{
                    android.content.Intent intent=new android.content.Intent(MainActivity.this,FilamentPreviewActivity.class);
                    intent.putExtra("annyProfile",snapshot);
                    startActivityForResult(intent, 8617);
                });
            }catch(Exception ignored){}
        }'''
s=change(s,a,b)
a='super.onActivityResult(request, result, data);'
b=a+'''
        if(request==8617){
            if(result==RESULT_OK&&data!=null){
                String id=data.getStringExtra("profileId"),key=data.getStringExtra("measureKey");
                if(id!=null&&key!=null&&web!=null)
                    web.evaluateJavascript("window.annyFocusMeasurement&&window.annyFocusMeasurement("+
                        org.json.JSONObject.quote(id)+","+org.json.JSONObject.quote(key)+")",null);
            }
            return;
        }'''
s=change(s,a,b);p.write_text(s)
p=java/'FilamentPreviewActivity.java';s=p.read_text()
s=change(s,'private int outfitChoice=0;', '''private int outfitChoice=0;
    private org.json.JSONObject profileSnapshot;
    private float[] profileSkin,profileHair,profileEyes;
    private static float[] rgb(String hex,int fallback){
        int c=fallback;
        try{c=Color.parseColor(hex);}catch(Exception ignored){}
        return new float[]{Color.red(c)/255f,Color.green(c)/255f,Color.blue(c)/255f,1f};
    }
    private boolean readProfile(){
        try{
            profileSnapshot=new org.json.JSONObject(getIntent().getStringExtra("annyProfile"));
            String sex=profileSnapshot.getString("sex");
            if(!"male".equals(sex)&&!"female".equals(sex))return false;
            globalMass=(float)Math.max(-1,Math.min(1,profileSnapshot.getDouble("mass")));
            org.json.JSONArray regions=profileSnapshot.getJSONArray("regions");
            if(regions.length()!=9)return false;
            for(int i=0;i<9;i++)morphValues[i]=(float)Math.max(-1,Math.min(1,regions.getJSONObject(i).getDouble("local")));
            profileSkin=rgb(profileSnapshot.optString("skin"),0xffD99E78);
            profileHair=rgb(profileSnapshot.optString("hair"),0xff4A2D22);
            profileEyes=rgb(profileSnapshot.optString("eyes"),0xff593826);
            return true;
        }catch(Exception e){return false;}
    }
    private void editRegion(int index){
        try{
            org.json.JSONObject region=profileSnapshot.getJSONArray("regions").getJSONObject(index);
            android.content.Intent result=new android.content.Intent();
            result.putExtra("profileId",profileSnapshot.getString("id"));
            result.putExtra("measureKey",region.getString("key"));
            setResult(RESULT_OK,result);
            finish();
        }catch(Exception ignored){}
    }
    private void addProfileMeasurements(LinearLayout root){
        LinearLayout line=new LinearLayout(this);
        Spinner selector=new Spinner(this);
        String[] labels=new String[9];
        org.json.JSONArray regions=profileSnapshot.optJSONArray("regions");
        for(int i=0;i<9;i++){
            org.json.JSONObject r=regions.optJSONObject(i);
            String value=r==null||r.isNull("value")?"—":(r.optBoolean("estimated")?"≈ ":"")+
                String.format(java.util.Locale.FRANCE,"%.1f cm",r.optDouble("value"));
            labels[i]=MORPH_LABELS[i]+" · "+value;
        }
        selector.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,labels));
        selector.setBackgroundColor(Color.rgb(222,232,235));
        line.addView(selector,new LinearLayout.LayoutParams(0,dp(this,48),1f));
        Button edit=new Button(this);edit.setAllCaps(false);edit.setText("Modifier");
        edit.setOnClickListener(v->editRegion(selector.getSelectedItemPosition()));
        line.addView(edit);
        root.addView(line);
    }''')
s=change(s,'super.onCreate(savedInstanceState);','super.onCreate(savedInstanceState);\n        if(!readProfile()){finish();return;}')
s=s.replace('ANNY · ESSAI 1.6.160','Mon Évolution IMC · 3D Anny').replace('Test local Anny · aucun profil requis.','Chargement du mannequin…')
s=change(s,'root.addView(modes);','// The active profile selects the correct adult model automatically.')
s=change(s,'root.addView(morphPanel);','morphPanel.setVisibility(android.view.View.GONE);')
s=change(s,'root.addView(colorsRow);','// Existing IMC appearance preferences remain authoritative.')
s=change(s,'root.addView(help);','root.addView(help);\n        addProfileMeasurements(root);')
a=s.index('        help.setText(');z=s.index('\n',a)
s=s[:a]+'''        help.setText("Silhouette indicative selon les données du profil. Les estimations ne sont pas des mesures réelles.");'''+s[z:]
s=s.replace('Quitter le test','Retour aux mensurations')
s=change(s,'switchModel("anny-male-long-morph.glb","Homme Anny");',
'''switchModel("female".equals(profileSnapshot.optString("sex"))?"anny-female-long-morph.glb":"anny-male-long-morph.glb",
                "female".equals(profileSnapshot.optString("sex"))?"Femme":"Homme");''')
s=s.replace('skinPalette[skinChoice]);','profileSkin);').replace('hairPalette[hairChoice]);','profileHair);')
s=s.replace('eyeChoice==0?new float[]{.27f,.19f,.12f,1f}:eyePalette[eyeChoice]);','profileEyes);')
assert 'profileSkin);' in s and 'profileHair);' in s and 'profileEyes);' in s
# Hide diagnostic counters from the app UI, retaining error reports.
s=change(s,'status.setText(message);','status.setText(loadError.isEmpty()&&lastRenderError.isEmpty()?currentLabel+" · 3D locale":message);')
s=change(s,'status.setText(label+" · "+bytes.length+" octets · GPU en cours");','status.setText(label+" · chargement 3D…");')
p.write_text(s)
for sex in ('male','female'):
    for outfit in ('long','sport'):
        file=assets/f'anny-{sex}-{outfit}-morph.glb'
        assert file.is_file() and file.stat().st_size>10000
        with file.open('rb') as f: assert f.read(4)==b'glTF'
assert 'fr.monevolution.annytest' not in (root/'build.gradle').read_text()
assert 'openAnnyProfile' in (java/'MainActivity.java').read_text()
assert 'monevolutionanny' not in (root/'src/main/AndroidManifest.xml').read_text()
print('Official IMC identity, existing launcher, Anny bundled assets and profile bridge verified.')
