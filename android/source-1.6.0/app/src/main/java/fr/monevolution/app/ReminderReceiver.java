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
import android.os.Build;
import java.util.Calendar;

public class ReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL = "mon_evolution_reminders";
    public static void configure(Context context, String type, boolean enabled, int hour, int minute, int weekday) {
        if (!type.equals("weight") && !type.equals("meals")) return;
        if (hour<0||hour>23||minute<0||minute>59||weekday<1||weekday>7) return;
        SharedPreferences p=context.getSharedPreferences("reminders",Context.MODE_PRIVATE);
        p.edit().putBoolean(type+"_enabled",enabled).putInt(type+"_hour",hour).putInt(type+"_minute",minute).putInt(type+"_weekday",weekday).apply();
        schedule(context,type);
    }
    public static void schedule(Context context, String type) {
        SharedPreferences p=context.getSharedPreferences("reminders",Context.MODE_PRIVATE);
        int request=type.equals("weight")?2101:2102;
        Intent intent=new Intent(context,ReminderReceiver.class).putExtra("type",type);
        PendingIntent pending=PendingIntent.getBroadcast(context,request,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarm=(AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        if(alarm==null)return;
        alarm.cancel(pending);
        if(!p.getBoolean(type+"_enabled",false))return;
        Calendar when=Calendar.getInstance();
        when.set(Calendar.HOUR_OF_DAY,p.getInt(type+"_hour",type.equals("weight")?9:20));
        when.set(Calendar.MINUTE,p.getInt(type+"_minute",0));
        when.set(Calendar.SECOND,0);
        when.set(Calendar.MILLISECOND,0);
        if(type.equals("weight")){
            int day=p.getInt(type+"_weekday",Calendar.SUNDAY);
            when.set(Calendar.DAY_OF_WEEK,day);
        }
        if(when.getTimeInMillis()<=System.currentTimeMillis())when.add(Calendar.DAY_OF_YEAR,type.equals("weight")?7:1);
        // A new calendar-based alarm is scheduled after each notification.
        // Unlike a fixed millisecond interval it follows DST and timezone changes.
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when.getTimeInMillis(),pending);
    }
    @Override public void onReceive(Context context, Intent intent) {
        String action=intent.getAction();
        if(Intent.ACTION_BOOT_COMPLETED.equals(action)
            ||Intent.ACTION_TIMEZONE_CHANGED.equals(action)
            ||Intent.ACTION_TIME_CHANGED.equals(action)){
            schedule(context,"weight");schedule(context,"meals");return;
        }
        String type=intent.getStringExtra("type");
        if(!"weight".equals(type)&&!"meals".equals(type))return;
        schedule(context,type);
        if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)return;
        NotificationManager manager=(NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE);
        if(manager==null)return;
        if(Build.VERSION.SDK_INT>=26){
            NotificationChannel channel=new NotificationChannel(CHANNEL,"Rappels Mon Évolution",NotificationManager.IMPORTANCE_DEFAULT);
            manager.createNotificationChannel(channel);
        }
        Intent open=new Intent(context,MainActivity.class);
        PendingIntent action=PendingIntent.getActivity(context,0,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder notification=Build.VERSION.SDK_INT>=26?new Notification.Builder(context,CHANNEL):new Notification.Builder(context);
        notification.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(type.equals("weight")?"C'est le jour de la pesée":"Ton journal alimentaire")
            .setContentText(type.equals("weight")?"Pense à enregistrer ton poids.":"As-tu noté tes repas aujourd'hui ?")
            .setAutoCancel(true).setContentIntent(action);
        manager.notify(type.equals("weight")?2101:2102,notification.build());
    }
}
