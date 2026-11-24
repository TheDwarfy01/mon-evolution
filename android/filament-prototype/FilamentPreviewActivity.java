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
import com.google.android.filament.Skybox;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.utils.ModelViewer;
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
    private Skybox background;
    private Choreographer.FrameCallback frameCallback;
    private boolean running;
    private float lastX;
    private double yaw;
    private TextView status;
    private String currentModel="filament-test-cube.glb";
    private String currentLabel="Cube test";
    private int renderedFrames=0;
    private String lastRenderError="";
    private int frameCount=0;
    private SurfaceView stage;

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
        status.setText("Test Filament : cube orange au démarrage, puis mannequin simplifié.");
        root.addView(status);
        LinearLayout modes=new LinearLayout(this);
        modes.setPadding(dp(this,6),0,dp(this,6),dp(this,4));
        String[] names={"Corps simple","Cube test","Corps complet"};
        String[] files={"filament-simple-body.glb","filament-test-cube.glb","filament-base-body.glb"};
        for(int i=0;i<names.length;i++){
            final String filename=files[i],label=names[i];
            Button button=new Button(this);
            button.setText(label);
            button.setTextSize(11);
            button.setAllCaps(false);
            modes.addView(button,new LinearLayout.LayoutParams(0,dp(this,44),1f));
            button.setOnClickListener(v->switchModel(filename,label));
        }
        root.addView(modes);
        SurfaceView surface=new SurfaceView(this);
        stage=surface;
        root.addView(surface,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f));
        TextView help=new TextView(this);
        help.setText("Corps simple = maillage fixe CC0. Cube = vérification moteur. Corps complet = squelette et morphing. Faites glisser pour tourner. Aucun profil requis.");
        help.setTextSize(12);
        help.setTextColor(Color.WHITE);
        help.setPadding(dp(this,14),dp(this,10),dp(this,14),dp(this,12));
        root.addView(help);
        Button back=new Button(this);
        back.setText("Quitter le test");
        back.setOnClickListener(v->finish());
        root.addView(back);
        root.setOnApplyWindowInsetsListener((v,insets)->{
            v.setPadding(insets.getSystemWindowInsetLeft(),
                insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(),
                insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(root);
        // The diagnostic GLB is packaged inside the experimental APK so that
        // the viewer is available even when the app has no saved profile.
        // Production profile storage is intentionally not accessed here.
        try {
            initializeFilament();
            // Use no camera manipulator: orbit is explicitly controlled below
            // to keep the test viewpoint reproducible between screenshots.
            viewer=new ModelViewer(surface, Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK), null);
            // A visible gray-blue backdrop helps distinguish missing geometry
            // from a genuinely black surface.
            background=new Skybox.Builder().color(0.13f,0.17f,0.22f,1f)
                .build(viewer.getEngine());
            viewer.getScene().setSkybox(background);
            // Use the documented default Filament camera convention: the
            // normalized model is centered at z=-4, viewed from origin.
            surface.post(()->{
                if(viewer!=null && surface.getWidth()>0 && surface.getHeight()>0){
                    double aspect=(double)surface.getWidth()/surface.getHeight();
                    viewer.getCamera().setLensProjection(28.0,aspect,0.05,100.0);
                    cameraAtYaw();
                }
            });
            switchModel("filament-test-cube.glb","Cube test");
            surface.setOnTouchListener((view,event)->{
                if(event.getActionMasked()==MotionEvent.ACTION_DOWN){
                    lastX=event.getX();
                    return true;
                }
                if(event.getActionMasked()==MotionEvent.ACTION_MOVE){
                    float now=event.getX();
                    yaw+=(now-lastX)*0.008;
                    lastX=now;
                    cameraAtYaw();
                    return true;
                }
                return true;
            });
            frameCallback=new Choreographer.FrameCallback(){
                @Override public void doFrame(long time){
                    if(!running||viewer==null)return;
                    try {
                        if(viewer.render(time))renderedFrames++;
                        if(++frameCount%45==0) refreshDiagnostic();
                    }catch(Throwable error){
                        lastRenderError=error.getClass().getSimpleName()+
                            (error.getMessage()==null?"":(" : "+error.getMessage()));
                        status.setText("ERREUR RENDU : "+lastRenderError);
                    }finally{
                        if(running)Choreographer.getInstance().postFrameCallback(this);
                    }
                }
            };
        }catch(Exception ex){
            status.setText("Filament non initialisé : "+ex.getClass().getSimpleName()+
                (ex.getMessage()==null?"":(" · "+ex.getMessage())));
        }
    }
    private void refreshDiagnostic(){
        if(viewer==null)return;
        try {
            int sceneCount=viewer.getScene().getEntityCount();
            int total=viewer.getAsset()==null?0:viewer.getAsset().getEntityCount();
            int renderable=viewer.getAsset()==null?0:viewer.getAsset().getRenderableEntityCount();
            int progress=Math.round(100f*viewer.getProgress());
            String message=currentLabel+" | GPU "+progress+"% | objet "+renderable+
                " | scène "+sceneCount+" | frames "+renderedFrames+
                " | surface "+stage.getWidth()+"x"+stage.getHeight();
            if(!lastRenderError.isEmpty())message+=" | "+lastRenderError;
            status.setText(message);
            android.util.Log.i("IMC_Filament_Diagnostic",message+" total="+total);
        }catch(Exception ex){
            status.setText("Erreur diagnostic : "+ex.toString());
        }
    }

    private void cameraAtYaw(){
        if(viewer==null)return;
        double distance=4.0;
        viewer.getCamera().lookAt(
            Math.sin(yaw)*distance,0.15,-4+Math.cos(yaw)*distance,
            0,0,-4,0,1,0);
    }

    private void switchModel(String file,String label){
        if(viewer==null)return;
        try{
            byte[] bytes;
            try(java.io.InputStream input=getAssets().open(file)){
                java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream(400_000);
                byte[] chunk=new byte[65536];
                int count;
                while((count=input.read(chunk))!=-1){
                    if(output.size()+count>14_000_000)
                        throw new java.io.IOException("GLB trop volumineux");
                    output.write(chunk,0,count);
                }
                bytes=output.toByteArray();
            }
            if(bytes.length<500)throw new java.io.IOException("GLB incomplet");
            ByteBuffer buffer=ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
            buffer.put(bytes).flip();
            viewer.loadModelGlb(buffer);
            if(viewer.getAsset()==null)throw new IllegalStateException("AssetLoader refuse le GLB");
            if(viewer.getAnimator()!=null && viewer.getAnimator().getAnimationCount()>0){
                viewer.getAnimator().applyAnimation(0,0f);
                viewer.getAnimator().updateBoneMatrices();
                viewer.setAutoPlayAnimations(true);
            }else{
                viewer.setAutoPlayAnimations(false);
            }
            viewer.transformToUnitCube(new com.google.android.filament.utils.Float3(0f,0f,-4f));
            yaw=0;
            cameraAtYaw();
            currentModel=file;
            currentLabel=label;
            frameCount=0;
            renderedFrames=0;
            lastRenderError="";
            status.setText(label+" · "+bytes.length+" octets · GPU en cours");
        }catch(Exception ex){
            status.setText(label+" : ECHEC "+ex.getClass().getSimpleName()+
                (ex.getMessage()==null?"":" · "+ex.getMessage()));
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
        // ModelViewer destroys its engine on SurfaceView detach.
        // Release our own skybox only while the engine is still valid.
        if(viewer!=null && background!=null) {
            try {
                if(viewer.getSwapChain()!=null) {
                    viewer.getScene().setSkybox(null);
                    viewer.getEngine().destroySkybox(background);
                }
            } catch(IllegalStateException ignored) {}
        }
        background=null;
        viewer=null;
        super.onDestroy();
    }
}
