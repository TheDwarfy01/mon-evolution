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
    private int touchMoves=0;
    private String loadError="";
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
        modes.setOrientation(LinearLayout.VERTICAL);
        modes.setPadding(dp(this,6),0,dp(this,6),dp(this,4));
        String[] names={"Corps simple","Corps détaillé","Cube test","Rig original"};
        String[] files={"filament-simple-body.glb","filament-detailed-static.glb",
                        "filament-test-cube.glb","filament-base-body.glb"};
        for(int rowIndex=0;rowIndex<2;rowIndex++){
            LinearLayout buttonRow=new LinearLayout(this);
            for(int column=0;column<2;column++){
                int i=rowIndex*2+column;
                final String filename=files[i],label=names[i];
                Button button=new Button(this);
                button.setText(label);
                button.setTextSize(12);
                button.setAllCaps(false);
                buttonRow.addView(button,new LinearLayout.LayoutParams(0,dp(this,42),1f));
                button.setOnClickListener(v->switchModel(filename,label));
            }
            modes.addView(buttonRow);
        }
        root.addView(modes);
        SurfaceView surface=new SurfaceView(this);
        stage=surface;
        root.addView(surface,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f));
        TextView help=new TextView(this);
        help.setText("Glissez un doigt pour tourner, pincez pour zoomer. Corps détaillé : peau et visage d'origine, sans animation. Rig original : diagnostic du GLB articulé. Aucun profil requis.");
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
            // Use Filament's native camera manipulator with its own touch events.
            // Never apply Camera.lookAt directly: ModelViewer.render overwrites it
            // from the manipulator on every frame.
            viewer=new ModelViewer(surface, Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK), new com.google.android.filament.utils.Manipulator.Builder().targetPosition(0f,0f,-4f).orbitHomePosition(0f,0f,0f).build(com.google.android.filament.utils.Manipulator.Mode.ORBIT));
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
                    // ModelViewer.render retrieves the camera pose from the manipulator.
                }
            });
            switchModel("filament-simple-body.glb","Corps simple");
            surface.setOnTouchListener((view,event)->{
                // Forward raw touches to ModelViewer's GestureDetector; it updates
                // the orbit camera, pan and pinch-to-zoom on the next frame.
                viewer.onTouchEvent(event);
                if(event.getActionMasked()==MotionEvent.ACTION_MOVE)touchMoves++;
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
            int total=viewer.getAsset()==null?0:viewer.getAsset().getEntities().length;
            int renderable=viewer.getAsset()==null?0:viewer.getAsset().getRenderableEntities().length;
            int progress=Math.round(100f*viewer.getProgress());
            String message=currentLabel+" | GPU "+progress+"% | objets "+renderable+
                " | scène "+sceneCount+" | frames "+renderedFrames+
                " | gestes "+touchMoves+" | surface "+stage.getWidth()+"x"+stage.getHeight();
            if(!loadError.isEmpty())message+=" | CHARGEMENT : "+loadError;
            if(!lastRenderError.isEmpty())message+=" | "+lastRenderError;
            status.setText(message);
            android.util.Log.i("IMC_Filament_Diagnostic",message+" total="+total);
        }catch(Exception ex){
            status.setText("Erreur diagnostic : "+ex.toString());
        }
    }

    private void switchModel(String file,String label){
        if(viewer==null)return;
        currentModel=file;
        currentLabel=label;
        loadError="";
        touchMoves=0;
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
            // Keep the touch-controlled camera instead of resetting it via lookAt.
            frameCount=0;
            renderedFrames=0;
            lastRenderError="";
            status.setText(label+" · "+bytes.length+" octets · GPU en cours");
        }catch(Exception ex){
            loadError=ex.getClass().getSimpleName()+
                (ex.getMessage()==null?"":" · "+ex.getMessage());
            status.setText(label+" : ECHEC "+loadError);
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
