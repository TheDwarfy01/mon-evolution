#!/usr/bin/env python3
"""Integrate an isolated Filament GLB diagnostic into the fully patched v1.6.143 app.
Run after the existing release steps, just before compilation. Experimental only.
The production Studio Three.js viewer and user profile schema are left unchanged.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Usage: integrate_filament.py android/source-1.6.143")
root=Path(sys.argv[1])/"app"
base=Path(__file__).resolve().parent
assets=root/"src/main/assets"
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
camera=root/"src/main/java/fr/monevolution/app/CameraPhotoProvider.java"
manifest=root/"src/main/AndroidManifest.xml"
gradle=root/"build.gradle"
html=assets/"index.html"
assert all(p.is_file() for p in (java,camera,manifest,gradle,html))
assert (base/"FilamentPreviewActivity.java").is_file()
assert (base/"filament-test.js").is_file()

# Side-by-side test app: no access to the installed production application's
# data, no backup restoration, and no overwrite of the stable APK.
build=gradle.read_text(encoding="utf-8")
assert "versionCode 159" in build and "versionName '1.6.143'" in build
assert "applicationId 'fr.monevolution.app'" in build
build=build.replace("applicationId 'fr.monevolution.app'","applicationId 'fr.monevolution.filamenttest'",1)
build=build.replace("versionCode 159","versionCode 160",1)
build=build.replace("versionName '1.6.143'","versionName '1.6.144-filament-test'",1)
assert "filament-utils-android" not in build
build+="\n// Isolated Filament POC; only this experimental build resolves the library.\n"
build+="dependencies { implementation 'com.google.android.filament:filament-utils-android:1.81.0' }\n"
gradle.write_text(build,encoding="utf-8")
# Filament-utils pulls AndroidX annotation; legacy IMC Gradle did not need
# AndroidX until this experiment, so enable it in the generated test project.
props=root.parent/"gradle.properties"
current=props.read_text(encoding="utf-8") if props.exists() else ""
if "android.useAndroidX=" in current:
    current="\n".join("android.useAndroidX=true" if line.startswith("android.useAndroidX=") else line
        for line in current.splitlines())+"\n"
else:
    current+="\nandroid.useAndroidX=true\n"
props.write_text(current,encoding="utf-8")
# Maven Central can return HTTP 429 on shared GitHub runners. Prefer Google's
# documented public mirror for app dependencies, retaining normal repositories
# as fallbacks. This affects only the generated experimental project.
settings=root.parent/"settings.gradle"
configuration=settings.read_text(encoding="utf-8")
needle="repositories { google(); mavenCentral() }"
assert needle in configuration, "Unexpected settings.gradle repository structure"
configuration=configuration.replace(needle,
    "repositories { google(); maven { url 'https://maven-central.storage-download.googleapis.com/maven2/' }; mavenCentral() }")
settings.write_text(configuration,encoding="utf-8")



source=java.read_text(encoding="utf-8")
anchor="        @JavascriptInterface public void makeHumanStudioInstall(){"
assert source.count(anchor)==1
addition="""        @JavascriptInterface public void openFilamentPreview(){
            runOnUiThread(()->startActivity(new android.content.Intent(
                MainActivity.this,FilamentPreviewActivity.class)));
        }

"""
java.write_text(source.replace(anchor,addition+anchor,1),encoding="utf-8")
shutil.copyfile(base/"FilamentPreviewActivity.java",java.with_name("FilamentPreviewActivity.java"))

# A unique content provider authority is essential if production IMC remains installed.
cam=camera.read_text(encoding="utf-8")
assert 'fr.monevolution.app.camera' in cam
camera.write_text(cam.replace('fr.monevolution.app.camera',
    'fr.monevolution.filamenttest.camera'),encoding="utf-8")
xml=manifest.read_text(encoding="utf-8")
assert 'fr.monevolution.app.camera' in xml and '</application>' in xml
xml=xml.replace('fr.monevolution.app.camera','fr.monevolution.filamenttest.camera')
# Do not intercept the production app's share links from a test install.
xml=xml.replace('android:scheme="monevolution"','android:scheme="monevolutionfilament"')
xml=xml.replace('android:label="Mon Évolution IMC"','android:label="IMC Filament TEST"')
xml=xml.replace('</application>',
    '  <activity android:name=".FilamentPreviewActivity" android:exported="false"/>\n  </application>',1)
manifest.write_text(xml,encoding="utf-8")

shutil.copyfile(base/"filament-test.js",assets/"filament-test.js")
page=html.read_text(encoding="utf-8")
assert 'filament-test.js' not in page and '</body></html>' in page
page=page.replace('</body></html>',
    '<script src="filament-test.js"></script>\n</body></html>',1)
html.write_text(page,encoding="utf-8")
print("Experimental Filament 1.81 integration ready: isolated appId, unique provider, native viewer.")
