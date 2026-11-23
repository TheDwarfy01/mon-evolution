package fr.monevolution.app;

import android.app.Activity;
import android.os.Bundle;
import android.view.Choreographer;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.SurfaceView;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.graphics.Color;
import com.google.android.filament.Engine;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.utils.ModelViewer;
import java.io.File;
import java.io.FileInputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Isolated diagnostic: same CC0 GLB as Studio v2, rendered natively with Filament.
 * Does not read, change, or persist patient measurements or profile data.
 * The base body is deliberately tested WITHOUT the old Three.js deformation,
 * clothing triangle masking, or normal rebuilding code.
 */
public final class FilamentPreviewActivity extends Activity {
    private ModelViewer viewer;
    private Choreographer.FrameCallback frameCallback;
    private boolean running;
    private float lastX;
    private double yaw;
    private TextView status;
    private static final String BODY="base_body_anim.glb";

    private static void initializeFilament() throws Exception {
        // Utils is a Kotlin object; its init method can have a Java static wrapper
        // depending on the published artifact. Support both without requiring the
        // Kotlin Gradle plugin in the legacy Java-only Android application.
        Class<?> utils = Class.forName("com.google.android.filament.utils.Utils");
        Method init=utils.getMethod("init");
        Object receiver=Modifier.isStatic(init.getModifiers())?null:utils.getField("INSTANCE").get(null);
        init.invoke(receiver);
    }
    private static int dp(Activity a,float value) {
        return (int)(value*a.getResources().getDisplayMetrics().density+0.5f);
    }
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(13,33,46));
        TextView title=new TextView(this);
        title.setText("FILAMENT · ESSAI 3D");
        title.setTextColor(Color.WHITE);
        title.setTextSize(19);
        title.setGravity(Gravity.CENTER);
        title.setPadding(12,dp(this,16),12,dp(this,10));
        root.addView(title);
        status=new TextView(this);
        status.setTextColor(Color.rgb(189,232,224));
        status.setTextSize(13);
        status.setPadding(dp(this,15),0,dp(this,15),dp(this,12));
        status.setText("Diagnostic du maillage GLB original : sans corrections Three.js.");
        root.addView(status);
        SurfaceView surface=new SurfaceView(this);
        root.addView(surface,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f));
        TextView help=new TextView(this);
        help.setText("Faire glisser horizontalement pour examiner les épaules et les aisselles. Le test affiche uniquement le modèle de base, sans vêtements ni mensurations.");
        help.setTextSize(12);
        help.setTextColor(Color.WHITE);
        help.setPadding(dp(this,14),dp(this,10),dp(this,14),dp(this,12));
        root.addView(help);
        Button back=new Button(this);
        back.setText("Fermer le diagnostic");
        back.setOnClickListener(v->finish());
        root.addView(back);
        setContentView(root);
        File model=new File(new File(new File(getFilesDir(),"makehuman"),"studio-v2"),BODY);
        if(!model.isFile()||model.length()<1_000_000||model.length()>14_000_000){
            status.setText("Module 3D absent. Dans cette application de test, ouvrir d’abord le mannequin 3D et installer le module Studio. Revenir ensuite ici.");
            return;
        }
        try {
            initializeFilament();
            // Use no camera manipulator: orbit is explicitly controlled below
            // to keep the test viewpoint reproducible between screenshots.
            viewer=new ModelViewer(surface, Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK), null);
            byte[] bytes=new byte[(int)model.length()];
            try(FileInputStream input=new FileInputStream(model)){
                int offset=0;
                while(offset<bytes.length){
                    int n=input.read(bytes,offset,bytes.length-offset);
                    if(n<0)throw new java.io.EOFException("GLB incomplet");
                    offset+=n;
                }
            }
            ByteBuffer buffer=ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
            buffer.put(bytes);
            buffer.flip();
            viewer.loadModelGlb(buffer);
            if(viewer.getAsset()==null)throw new IllegalStateException("Chargement GLB impossible");
            viewer.resetToDefaultState();
            viewer.setAutoPlayAnimations(false);
            viewer.getCamera().lookAt(0,0,0,0,0,-4,0,1,0);
            status.setText("GLB chargé · Filament natif · rotation tactile · corps original sans morphing.");
            surface.setOnTouchListener((view,event)->{
                if(event.getActionMasked()==MotionEvent.ACTION_DOWN){
                    lastX=event.getX();
                    return true;
                }
                if(event.getActionMasked()==MotionEvent.ACTION_MOVE){
                    float now=event.getX();
                    yaw+=(now-lastX)*0.008;
                    lastX=now;
                    double radius=4.0;
                    viewer.getCamera().lookAt(radius*Math.sin(yaw),0.25,-4+radius*Math.cos(yaw),
                        0,0,-4,0,1,0);
                    return true;
                }
                return true;
            });
            frameCallback=new Choreographer.FrameCallback(){
                @Override public void doFrame(long time){
                    if(!running||viewer==null)return;
                    viewer.render(time);
                    Choreographer.getInstance().postFrameCallback(this);
                }
            };
        }catch(Exception ex){
            status.setText("Filament non initialisé : "+ex.getClass().getSimpleName()+
                (ex.getMessage()==null?"":(" · "+ex.getMessage())));
        }
    }
    @Override protected void onResume(){
        super.onResume();
        running=true;
        if(frameCallback!=null)Choreographer.getInstance().postFrameCallback(frameCallback);
    }
    @Override protected void onPause(){
        running=false;
        if(frameCallback!=null)Choreographer.getInstance().removeFrameCallback(frameCallback);
        super.onPause();
    }
    @Override protected void onDestroy(){
        running=false;
        if(viewer!=null){viewer.destroy();viewer=null;}
        super.onDestroy();
    }
}
