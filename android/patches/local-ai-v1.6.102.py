#!/usr/bin/env python3
"""Apply optional Gemma on-device meal AI after the existing v1.6.102 UI patches.

Never delete, migrate, or overwrite IMC profile/meal JSON. Signed APK upgrade only.
"""
from pathlib import Path
import shutil

root=Path("android/source-1.6.102")
app=root/"app"
def replace_exact(path, old, new):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    if count!=1:
        raise RuntimeError(f"{path}: expected 1 anchor, found {count}: {old[:100]}")
    path.write_text(content.replace(old,new),encoding="utf-8")

gradle=root/"build.gradle"
replace_exact(gradle,
    "id 'com.android.application' version '8.7.3' apply false",
    "id 'com.android.application' version '8.7.3' apply false\n    id 'org.jetbrains.kotlin.android' version '2.4.0' apply false")
app_gradle=app/"build.gradle"
replace_exact(app_gradle,
    "plugins { id 'com.android.application' }",
    "plugins { id 'com.android.application'; id 'org.jetbrains.kotlin.android' }")
with app_gradle.open("a",encoding="utf-8") as stream:
    stream.write("\n// Optional on-device Gemma inference. Model weights are NOT in the APK.\n"
                 "dependencies { implementation 'com.google.ai.edge.litertlm:litertlm-android:0.18.0' }\n")
with app_gradle.open("a",encoding="utf-8") as stream:
    stream.write("\n// Align Java compile target with LiteRT-LM Kotlin compiler.\n"
                 "android { compileOptions { sourceCompatibility JavaVersion.VERSION_17; targetCompatibility JavaVersion.VERSION_17 } }\n")
manifest=app/"src/main/AndroidManifest.xml"
replace_exact(manifest,
    '<application android:label="Mon Évolution IMC"',
    '<application android:label="Mon Évolution IMC"') if False else None
# CPU runtime only; model downloader uses existing Android INTERNET permission.
java=app/"src/main/java/fr/monevolution/app/MainActivity.java"
replace_exact(java,"    private WebView web;",
                  "    private WebView web;\n    private LocalMealAi mealAi;")
replace_exact(java,"        web = new WebView(this);",
                  "        web = new WebView(this);\n        mealAi = new LocalMealAi(this,web);")
replace_exact(java,"    public class Bridge {",
"""    public class Bridge {
        // Optional IA bridge; no existing profile/backup data is modified.
        @JavascriptInterface public String aiStatus() {
            return mealAi==null ? "{\\"state\\":\\"incompatible\\"}" : mealAi.status();
        }
        @JavascriptInterface public String aiDownload() {
            return mealAi==null ? "{\\"state\\":\\"incompatible\\"}" : mealAi.download();
        }
        @JavascriptInterface public String aiRemove() {
            return mealAi==null ? "{\\"state\\":\\"incompatible\\"}" : mealAi.remove();
        }
        @JavascriptInterface public void aiAnalyze(String token,String photo,String description) {
            if(mealAi!=null)mealAi.analyze(token,photo,description==null?"":description);
        }
""")
kotlin_target=app/"src/main/java/fr/monevolution/app/LocalMealAi.kt"
shutil.copyfile("android/ai/LocalMealAi.kt",kotlin_target)
assets=app/"src/main/assets"
shutil.copyfile("android/ai/local-ai.js",assets/"local-ai.js")
html=assets/"index.html"
replace_exact(html,"</body></html>",
                  '<script src="local-ai.js"></script>\n</body></html>')
# No changes to existing profile keys, meals, strict validators or storage format.
assert "const storage='mon-evolution-multiprofil-v1'" in html.read_text(encoding="utf-8")
assert "aiMeals" in (assets/"local-ai.js").read_text(encoding="utf-8")
assert "modelPath = file.absolutePath" in kotlin_target.read_text(encoding="utf-8")
assert "applicationId 'fr.monevolution.app'" in app_gradle.read_text(encoding="utf-8")
print("Optional Gemma LiteRT-LM: separate model, Android bridge, meal UI, no IMC data migration.")
