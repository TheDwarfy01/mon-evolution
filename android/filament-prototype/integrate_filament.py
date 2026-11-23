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
# SDK 37 updates only compilation APIs; keep targetSdk 35 / minSdk 24.
assert "compileSdk 35" in build and "targetSdk 35" in build and "minSdk 24" in build
build=build.replace("compileSdk 35","compileSdk 37",1)
build=build.replace("versionCode 159","versionCode 163",1)
build=build.replace("versionName '1.6.143'","versionName '1.6.147-filament-diagnostic'",1)
assert "filament-utils-android" not in build
build+="\n// Isolated Filament POC; only this experimental build resolves the library.\n"
build+="dependencies { implementation 'com.google.android.filament:filament-utils-android:1.81.0' }\n"
# Keep generated Java and Kotlin bytecode at 17, while using JDK21 javac to
# consume Filament's Java 21 dependencies.
build+="kotlin { compilerOptions { jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17 } }\n"

gradle.write_text(build,encoding="utf-8")

# AGP 9.1.1 is the minimum stable Android Gradle plugin for API 37.
# The existing Gemma AI patch configures Kotlin Gradle plugin 2.4.0.
# Preserve it for now using Google's temporary AGP 9 legacy options.
project_gradle=root.parent/"build.gradle"
project_build=project_gradle.read_text(encoding="utf-8")
assert "id 'com.android.application' version '8.7.3' apply false" in project_build
assert "id 'org.jetbrains.kotlin.android' version '2.4.0' apply false" in project_build
project_gradle.write_text(project_build.replace(
    "id 'com.android.application' version '8.7.3' apply false",
    "id 'com.android.application' version '9.1.1' apply false",1),encoding="utf-8")
# Filament-utils pulls AndroidX annotation; legacy IMC Gradle did not need
# AndroidX until this experiment, so enable it in the generated test project.
props=root.parent/"gradle.properties"
current=props.read_text(encoding="utf-8") if props.exists() else ""
if "android.useAndroidX=" in current:
    current="\n".join("android.useAndroidX=true" if line.startswith("android.useAndroidX=") else line
        for line in current.splitlines())+"\n"
else:
    current+="\nandroid.useAndroidX=true\n"
# Android Gradle Plugin 9's built-in Kotlin collides with the legacy kotlin
# Android plugin. Keep Gradle 9 compatibility without changing Gemma Kotlin.
current+="\nandroid.builtInKotlin=false\nandroid.newDsl=false\n"
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
# AGP 9 rejects minSdk/targetSdk declarations in AndroidManifest.xml.
# Their source of truth is the Gradle defaultConfig (24 and 35 respectively).
import re
xml,count=re.subn(r'<uses-sdk\b[^>]*?/>', '', xml)
assert count==1, "Expected exactly one legacy uses-sdk declaration"
xml=xml.replace(' package="fr.monevolution.app"', '')
xml=xml.replace('fr.monevolution.app.camera','fr.monevolution.filamenttest.camera')
# Do not intercept the production app's share links from a test install.
xml=xml.replace('android:scheme="monevolution"','android:scheme="monevolutionfilament"')
xml=xml.replace('android:label="Mon Évolution IMC"','android:label="IMC Filament TEST"')
# Move the launcher intent to the native Filament diagnostic. MainActivity still
# exists for JS bridge compatibility but it is not the startup screen, so no
# onboarding, profile creation, data restore or first-run migration is needed.
launcher='''      <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
      </intent-filter>'''
assert xml.count(launcher)==1,"Launcher marker unexpectedly changed"
xml=xml.replace(launcher,'',1)
filament_activity='''  <activity android:name=".FilamentPreviewActivity" android:exported="true">
      <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
      </intent-filter>
    </activity>'''
xml=xml.replace('</application>',filament_activity+'\n  </application>',1)
manifest.write_text(xml,encoding="utf-8")

shutil.copyfile(base/"filament-test.js",assets/"filament-test.js")
page=html.read_text(encoding="utf-8")
assert 'filament-test.js' not in page and '</body></html>' in page
page=page.replace('</body></html>',
    '<script src="filament-test.js"></script>\n</body></html>',1)
html.write_text(page,encoding="utf-8")
print("Experimental Filament 1.81 SDK 37 integration ready: isolated appId, unique provider, native viewer.")
