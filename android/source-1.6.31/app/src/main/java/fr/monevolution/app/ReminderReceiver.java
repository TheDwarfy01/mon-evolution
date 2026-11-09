package fr.monevolution.app;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import org.json.JSONArray;
import java.util.Calendar;

public class ReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL = "mon_evolution_reminders";
    private static final String[] TYPES = {"meals","photos","breakfast","lunch","dinner","weight","injection"};
    private static boolean valid(String t) {if(t!=null&&t.matches("water(?:[0-9]|1[0-9]|2[0-3])"))return true;for(String s:TYPES)if(s.equals(t))return true;return false;}
    private static boolean weekly(String t){return "weight".equals(t)||"injection".equals(t);}
    private static String token(String id,String type){return id+"|"+type;}
    private static SharedPreferences prefs(Context c){return c.getSharedPreferences("reminders",Context.MODE_PRIVATE);}
    public static void configure(Context context, String type, boolean enabled, int hour, int minute, int weekday) {
        if (!type.equals("weight") && !type.equals("meals")) return;
        if (hour<0||hour>23||minute<0||minute>59||weekday<1||weekday>7) return;
        SharedPreferences p=prefs(context);
        p.edit().putBoolean(type+"_enabled",enabled).putInt(type+"_hour",hour).putInt(type+"_minute",minute).putInt(type+"_weekday",weekday).apply();
        schedule(context,type);
    }
    public static void schedule(Context context, String type) {
        SharedPreferences p=prefs(context);
        int request=type.equals("weight")?2101:2102;
        Intent intent=new Intent(context,ReminderReceiver.class).putExtra("type",type);
        PendingIntent pending=PendingIntent.getBroadcast(context,request,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarm=(AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        if(alarm==null)return;
        alarm.cancel(pending);
        if(!p.getBoolean(type+"_enabled",false))return;
        Calendar when=Calendar.getInstance();
        when.set(Calendar.HOUR_OF_DAY,p.getInt(type+"_hour",type.equals("weight")?9:20));
        when.set(Calendar.MINUTE,p.getInt(type+"_minute",0));when.set(Calendar.SECOND,0);when.set(Calendar.MILLISECOND,0);
        if(type.equals("weight"))when.set(Calendar.DAY_OF_WEEK,p.getInt(type+"_weekday",Calendar.SUNDAY));
        while(when.getTimeInMillis()<=System.currentTimeMillis())when.add(Calendar.DAY_OF_YEAR,type.equals("weight")?7:1);
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when.getTimeInMillis(),pending);
    }
    public static void configurePersonal(Context context,String id,String name,String type,boolean enabled,int hour,int minute,int weekday){
        if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}")||!valid(type)||hour<0||hour>23||minute<0||minute>59||weekday<1||weekday>7)return;
        SharedPreferences p=prefs(context);
        String key="v2_"+token(id,type);
        String index=p.getString("v2_index","[]");
        try{
            JSONArray existing=new JSONArray(index);
            boolean found=false;for(int i=0;i<existing.length();i++)if(token(id,type).equals(existing.optString(i))){found=true;break;}
            if(!found){existing.put(token(id,type));index=existing.toString();}
        }catch(Exception ignored){index="[\""+token(id,type)+"\"]";}
        p.edit().putBoolean(key+"_enabled",enabled).putInt(key+"_hour",hour).putInt(key+"_minute",minute)
            .putInt(key+"_weekday",weekday).putString("v2_name_"+id,(name==null?"Profil":name).substring(0,Math.min(40,name==null?6:name.length())))
            .putString("v2_index",index).apply();
        schedulePersonal(context,id,type);
    }
    private static PendingIntent pendingPersonal(Context context,String id,String type){
        Intent intent=new Intent(context,ReminderReceiver.class);
        intent.setData(Uri.parse("monevolution-reminder://personal/"+id+"/"+type));
        intent.putExtra("reminder_id",id).putExtra("reminder_type",type);
        return PendingIntent.getBroadcast(context,0,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
    }
    public static void schedulePersonal(Context context,String id,String type){
        if(id==null||!id.matches("[a-zA-Z0-9_-]{1,75}")||!valid(type))return;
        AlarmManager alarm=(AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        if(alarm==null)return;
        PendingIntent pending=pendingPersonal(context,id,type);
        alarm.cancel(pending);
        SharedPreferences p=prefs(context);String key="v2_"+token(id,type);
        if(!p.getBoolean(key+"_enabled",false))return;
        Calendar when=Calendar.getInstance();
        when.set(Calendar.SECOND,0);when.set(Calendar.MILLISECOND,0);
        when.set(Calendar.HOUR_OF_DAY,p.getInt(key+"_hour",20));when.set(Calendar.MINUTE,p.getInt(key+"_minute",0));
        if(weekly(type)){
            // Calendar day of week: Sunday=1 through Saturday=7.
            int target=p.getInt(key+"_weekday",Calendar.MONDAY);
            int today=when.get(Calendar.DAY_OF_WEEK);
            when.add(Calendar.DAY_OF_YEAR,(target-today+7)%7);
            if(when.getTimeInMillis()<=System.currentTimeMillis())when.add(Calendar.DAY_OF_YEAR,7);
        }else if(when.getTimeInMillis()<=System.currentTimeMillis())when.add(Calendar.DAY_OF_YEAR,1);
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when.getTimeInMillis(),pending);
    }
    private static void scheduleAll(Context context){
        schedule(context,"weight");schedule(context,"meals");
        try{
            JSONArray list=new JSONArray(prefs(context).getString("v2_index","[]"));
            for(int i=0;i<list.length();i++){
                String[] key=list.optString(i).split("\\|",2);
                if(key.length==2)schedulePersonal(context,key[0],key[1]);
            }
        }catch(Exception ignored){}
    }
    private static void notify(Context context,String id,String type){
        if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)return;
        NotificationManager manager=(NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE);
        if(manager==null)return;
        if(Build.VERSION.SDK_INT>=26)manager.createNotificationChannel(new NotificationChannel(CHANNEL,"Rappels Mon Évolution",NotificationManager.IMPORTANCE_DEFAULT));
        String[] labels;
        if(type!=null && type.startsWith("water"))labels=new String[]{"💧 Pause hydratation","Pense à boire un peu d’eau si tu en as envie."};
        else switch(type){
            case "weight":labels=new String[]{"Jour de pesée","Pense à enregistrer ton poids."};break;
            case "injection":labels=new String[]{"Rappel de ton injection","Vérifie ton traitement prescrit et ton calendrier."};break;
            case "photos":labels=new String[]{"Photos des repas","Pense à ajouter les photos de tes repas."};break;
            case "breakfast":labels=new String[]{"Petit-déjeuner","Pense à noter ton petit-déjeuner."};break;
            case "lunch":labels=new String[]{"Déjeuner","Pense à noter ton déjeuner."};break;
            case "dinner":labels=new String[]{"Dîner","Pense à noter ton dîner."};break;
            default:labels=new String[]{"Journal alimentaire","As-tu noté tes repas aujourd'hui ?"};
        }
        String name=id==null?"":prefs(context).getString("v2_name_"+id,"");
        Intent open=new Intent(context,MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent action=PendingIntent.getActivity(context,0,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder n=Build.VERSION.SDK_INT>=26?new Notification.Builder(context,CHANNEL):new Notification.Builder(context);
        n.setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(labels[0]+(name.isEmpty()?"":" · "+name)).setContentText(labels[1])
            .setAutoCancel(true).setContentIntent(action);
        manager.notify(3100+Math.abs((id==null?type:token(id,type)).hashCode()%200000),n.build());
    }
    @Override public void onReceive(Context context,Intent intent){
        String action=intent.getAction();
        if(Intent.ACTION_BOOT_COMPLETED.equals(action)||Intent.ACTION_TIMEZONE_CHANGED.equals(action)||Intent.ACTION_TIME_CHANGED.equals(action)){
            scheduleAll(context);return;
        }
        String id=intent.getStringExtra("reminder_id");
        String type=id!=null?intent.getStringExtra("reminder_type"):intent.getStringExtra("type");
        if(id!=null){
            if(!id.matches("[a-zA-Z0-9_-]{1,75}")||!valid(type))return;
            schedulePersonal(context,id,type);
            if(prefs(context).getBoolean("v2_"+token(id,type)+"_enabled",false))notify(context,id,type);
        }else if("weight".equals(type)||"meals".equals(type)){
            schedule(context,type);
            if(prefs(context).getBoolean(type+"_enabled",false))notify(context,null,type);
        }
    }
}
