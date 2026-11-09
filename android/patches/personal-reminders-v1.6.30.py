#!/usr/bin/env python3
from pathlib import Path
root=Path("android/source-1.6.30/app")
h=root/"src/main/assets/index.html";g=root/"build.gradle";m=root/"src/main/AndroidManifest.xml";j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
rec=root/"src/main/java/fr/monevolution/app/ReminderReceiver.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} occurrences of {a[:100]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 45","versionCode 46")
R(g,"versionName '1.6.29'","versionName '1.6.30'")
R(m,'android:versionCode="45" android:versionName="1.6.29"','android:versionCode="46" android:versionName="1.6.30"')
R(j,"MonEvolutionIMC/1.6.29","MonEvolutionIMC/1.6.30")
R(h,'Version installée : <strong>1.6.29</strong>','Version installée : <strong>1.6.30</strong>')
R(h,'const installed="1.6.29";','const installed="1.6.30";')
R(h,"const latest=String(version||''),installed='1.6.29';","const latest=String(version||''),installed='1.6.30';")
rec.write_text(Path("android/patches/personal-reminder-receiver-v1.6.30.java").read_text(encoding="utf-8"),encoding="utf-8")
R(j,'        @JavascriptInterface public String reminderSettings() {',"""        @JavascriptInterface public String personalReminderSettings(String id) {
            if(id==null || !id.matches("[a-zA-Z0-9_-]{1,75}"))return "{}";
            SharedPreferences p=getSharedPreferences("reminders",MODE_PRIVATE);
            JSONObject result=new JSONObject();
            try {
                for(String type:new String[]{"meals","photos","breakfast","lunch","dinner","weight","injection"}){
                    String prefix="v2_"+id+"|"+type;
                    JSONObject item=new JSONObject();
                    item.put("enabled",p.getBoolean(prefix+"_enabled",false));
                    item.put("hour",p.getInt(prefix+"_hour",type.equals("weight")?9:20));
                    item.put("minute",p.getInt(prefix+"_minute",0));
                    item.put("weekday",p.getInt(prefix+"_weekday",Calendar.MONDAY));
                    result.put(type,item);
                }
            }catch(Exception ignored){}
            return result.toString();
        }
        @JavascriptInterface public void setPersonalReminder(String id,String name,String type,boolean enabled,int hour,int minute,int weekday){
            runOnUiThread(() -> {
                ReminderReceiver.configurePersonal(MainActivity.this,id,name,type,enabled,hour,minute,weekday);
                if(enabled&&android.os.Build.VERSION.SDK_INT>=33
                  &&checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
                    requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},72);
            });
        }
        @JavascriptInterface public String reminderSettings() {""")
# Use calendar qualified to avoid adding an import.
R(j,'p.getInt(prefix+"_weekday",Calendar.MONDAY)','p.getInt(prefix+"_weekday",java.util.Calendar.MONDAY)')
ui=Path("android/patches/personal-reminder-ui-v1.6.30.html").read_text(encoding="utf-8")
R(h,'</body></html>',ui+'</body></html>')
print("v1.6.30: personalized reminders and profile-first settings")
