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
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import com.google.android.filament.RenderableManager;
import com.google.android.filament.MaterialInstance;
import com.google.android.filament.Colors;
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
    private LinearLayout morphPanel;
    private SeekBar morphSlider;
    private SeekBar massSlider;
    private TextView massLabel;
    private float globalMass=0f;
    private int faceTargetCount=0;
    private Spinner morphSelector;
    private TextView morphValueLabel;
    private final float[] morphValues=new float[9];
    private int morphTargetCount=0;
    private int morphUpdates=0;
    private int activeRegion=5;
    private Spinner skinSpinner,eyeSpinner,hairSpinner;
    private int skinChoice=0,eyeChoice=0,hairChoice=0;
    private final float[][] skinPalette={
        {1f,1f,1f,1f},{.83f,.68f,.58f,1f},{.63f,.47f,.36f,1f},
        {.49f,.34f,.25f,1f},{.33f,.21f,.16f,1f}
    };
    private final float[][] eyePalette={
        {1f,1f,1f,1f},{.40f,.55f,.95f,1f},{.30f,.75f,.38f,1f},
        {.48f,.30f,.17f,1f}
    };
    private final float[][] hairPalette={
        {.22f,.15f,.10f,1f},{.06f,.055f,.05f,1f},{.47f,.31f,.16f,1f},
        {.75f,.63f,.42f,1f},{.53f,.22f,.12f,1f},{.60f,.58f,.53f,1f}
    };
    private static final String[] MORPH_LABELS={
        "Cou","Poitrine","Bras","Avant-bras","Taille",
        "Ventre","Hanches","Cuisse","Mollet"
    };

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
        String[] names={"Homme habillé","Femme habillée","Homme sans vêtements",
                        "Femme sans vêtements","Cube test","Ancien mannequin"};
        String[] files={"filament-male-dressed.glb","filament-female-dressed.glb",
                        "filament-male-morph.glb","filament-female-morph.glb",
                        "filament-test-cube.glb","filament-morph-global.glb"};
        for(int rowIndex=0;rowIndex<3;rowIndex++){
            LinearLayout buttonRow=new LinearLayout(this);
            int end=Math.min(names.length,rowIndex*2+2);
            for(int i=rowIndex*2;i<end;i++){
                final String filename=files[i],label=names[i];
                Button button=new Button(this);
                button.setText(label);
                button.setTextSize(12);
                button.setAllCaps(false);
                buttonRow.addView(button,new LinearLayout.LayoutParams(0,dp(this,40),1f));
                button.setOnClickListener(v->switchModel(filename,label));
            }
            modes.addView(buttonRow);
        }
        root.addView(modes);
        SurfaceView surface=new SurfaceView(this);
        stage=surface;
        root.addView(surface,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f));

        morphPanel=new LinearLayout(this);
        morphPanel.setOrientation(LinearLayout.VERTICAL);
        morphPanel.setPadding(dp(this,10),dp(this,2),dp(this,10),dp(this,2));

        massLabel=new TextView(this);
        massLabel.setTextColor(Color.WHITE);
        massLabel.setTextSize(14);
        massLabel.setPadding(dp(this,6),dp(this,2),0,0);
        morphPanel.addView(massLabel);
        massSlider=new SeekBar(this);
        massSlider.setMax(100);
        // Neutral is 40: the upper 60% of travel offers a wider obesity range.
        massSlider.setProgress(40);
        morphPanel.addView(massSlider,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,dp(this,35)));
        massSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override public void onProgressChanged(SeekBar seek,int progress,boolean fromUser){
                if(!fromUser)return;
                globalMass=progress<=40 ?
                    (progress-40)/40f : (progress-40)/60f;
                refreshMorphLabel();
                applyMorphWeights();
            }
            @Override public void onStartTrackingTouch(SeekBar seek){}
            @Override public void onStopTrackingTouch(SeekBar seek){}
        });
        LinearLayout selectRow=new LinearLayout(this);
        morphSelector=new Spinner(this);
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_dropdown_item,MORPH_LABELS);
        morphSelector.setAdapter(adapter);
        selectRow.addView(morphSelector,new LinearLayout.LayoutParams(0,dp(this,44),1));
        morphValueLabel=new TextView(this);
        morphValueLabel.setTextColor(Color.WHITE);
        morphValueLabel.setTextSize(12);
        morphValueLabel.setGravity(Gravity.CENTER_VERTICAL);
        selectRow.addView(morphValueLabel,new LinearLayout.LayoutParams(0,dp(this,44),1));
        Button reset=new Button(this);
        reset.setText("Réinitialiser");
        reset.setAllCaps(false);
        selectRow.addView(reset,new LinearLayout.LayoutParams(0,dp(this,44),1));
        morphPanel.addView(selectRow);
        morphSlider=new SeekBar(this);
        morphSlider.setMax(100);
        morphSlider.setProgress(50);
        morphPanel.addView(morphSlider,new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,dp(this,40)));
        root.addView(morphPanel);
        LinearLayout colorsRow=new LinearLayout(this);
        colorsRow.setPadding(dp(this,8),dp(this,2),dp(this,8),dp(this,2));
        skinSpinner=addColorSpinner(colorsRow,new String[]{"Peau naturelle","Peau claire","Peau mate","Peau brune","Peau foncée"},0);
        eyeSpinner=addColorSpinner(colorsRow,new String[]{"Yeux naturels","Yeux bleus","Yeux verts","Yeux marron"},1);
        hairSpinner=addColorSpinner(colorsRow,new String[]{"Cheveux bruns","Cheveux noirs","Châtains","Blonds","Roux","Gris"},2);
        root.addView(colorsRow);
        morphSelector.setSelection(activeRegion);
        morphSelector.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> parent,
                android.view.View view,int position,long id){
                activeRegion=position;
                morphSlider.setProgress(Math.round(50+50*morphValues[position]));
                refreshMorphLabel();
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> parent){}
        });
        morphSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override public void onProgressChanged(SeekBar seek,int progress,boolean fromUser){
                if(!fromUser)return;
                morphValues[activeRegion]=(progress-50)/50f;
                refreshMorphLabel();
                applyMorphWeights();
            }
            @Override public void onStartTrackingTouch(SeekBar seek){}
            @Override public void onStopTrackingTouch(SeekBar seek){}
        });
        reset.setOnClickListener(v->{
            java.util.Arrays.fill(morphValues,0f);
            morphSlider.setProgress(50);
            globalMass=0f;
            massSlider.setProgress(40);
            refreshMorphLabel();
            applyMorphWeights();
        });
        refreshMorphLabel();
        TextView help=new TextView(this);
        help.setText("Essai homme/femme : t-shirt, short et cheveux courts en maillage 3D déformable. Trois couleurs au choix : peau, yeux et cheveux. Visage MakeHuman texturé d'origine ; les portraits précédents sont des références, pas des maillages 3D. Aucune donnée personnelle enregistrée.");
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
            switchModel("filament-male-dressed.glb","Homme habillé");
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
    private Spinner addColorSpinner(LinearLayout row,String[] options,int type){
        Spinner spinner=new Spinner(this);
        spinner.setBackgroundColor(Color.rgb(36,60,71));
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_dropdown_item,options);
        spinner.setAdapter(adapter);
        row.addView(spinner,new LinearLayout.LayoutParams(0,dp(this,42),1f));
        spinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> a,
                android.view.View v,int pos,long id){
                if(type==0)skinChoice=pos;
                else if(type==1)eyeChoice=pos;
                else hairChoice=pos;
                applyColors();
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> a){}
        });
        return spinner;
    }

    private void colorMaterial(MaterialInstance instance,float[] rgba){
        if(instance==null)return;
        instance.setParameter("baseColorFactor",Colors.RgbaType.SRGB,
            rgba[0],rgba[1],rgba[2],rgba[3]);
    }

    private void applyColors(){
        if(viewer==null||viewer.getAsset()==null)return;
        if(!currentModel.contains("dressed")&&!currentModel.contains("morph"))return;
        try{
            RenderableManager manager=viewer.getEngine().getRenderableManager();
            for(int entity:viewer.getAsset().getRenderableEntities()){
                int instance=manager.getInstance(entity);
                if(instance==0)continue;
                String name=viewer.getAsset().getName(entity);
                if(name==null)continue;
                if(name.equals("Corps")){
                    colorMaterial(manager.getMaterialInstanceAt(instance,0),
                        skinPalette[skinChoice]);
                }else if(name.equals("Visage")){
                    // Index 3 corresponds to the iris in the validated
                    // MakeHuman compact facial mesh, not the sclera.
                    colorMaterial(manager.getMaterialInstanceAt(instance,3),
                        eyePalette[eyeChoice]);
                }else if(name.equals("IMC_ClothesAndHair")){
                    colorMaterial(manager.getMaterialInstanceAt(instance,2),
                        hairPalette[hairChoice]);
                }
            }
        }catch(Throwable error){
            loadError="Couleurs : "+error.getClass().getSimpleName()+
                " "+error.getMessage();
        }
    }

    private void refreshMorphLabel(){
        if(massLabel!=null){
            int progress=massSlider==null?40:massSlider.getProgress();
            int index=progress<=40?Math.round(65+35f*progress/40):
                Math.round(100+100f*(progress-40)/60);
            massLabel.setText("Corpulence globale · "+index+
                " (indice visuel 65–200, pas le poids en %)");
        }
        if(morphValueLabel==null)return;
        int percentage=activeRegion==5?
            Math.round(100+(morphValues[activeRegion]>=0?70:25)*morphValues[activeRegion]):
            Math.round(100+23*morphValues[activeRegion]);
        morphValueLabel.setText(MORPH_LABELS[activeRegion]+" "+percentage+" %");
    }

    private void applyMorphWeights(){
        if(viewer==null||viewer.getAsset()==null||
            !(currentModel.equals("filament-morph-global.glb")||
              currentModel.equals("filament-male-morph.glb")||
              currentModel.equals("filament-female-morph.glb")||
              currentModel.equals("filament-male-dressed.glb")||
              currentModel.equals("filament-female-dressed.glb")))return;
        try {
            // Body: first 18 weights preserve the proven independent 9-zone controls,
            // the last pair drives global body fullness.
            float[] weights=new float[20];
            for(int i=0;i<9;i++){
                weights[i*2]=Math.max(0,morphValues[i]);
                weights[i*2+1]=Math.max(0,-morphValues[i]);
            }
            // At severe global fullness, the abdomen is already enlarged.
            // Reduce additional LOCAL positive belly projection so both
            // sliders at maximum do not create an unnatural balloon.
            if((currentModel.equals("filament-male-morph.glb")||
                currentModel.equals("filament-male-dressed.glb"))&&globalMass>0f){
                float complement=1f-0.60f*globalMass;
                weights[10]*=complement; // region index 5: belly PLUS
            }
            weights[18]=Math.max(0,globalMass);
            weights[19]=Math.max(0,-globalMass);
            // Face: exactly matching global head targets on all facial submeshes.
            float[] faceWeights={weights[18],weights[19]};
            RenderableManager manager=viewer.getEngine().getRenderableManager();
            int bodyFound=0,faceFound=0;
            for(int entity:viewer.getAsset().getRenderableEntities()){
                int instance=manager.getInstance(entity);
                if(instance==0)continue;
                int count=manager.getMorphTargetCount(instance);
                if(count>=20){
                    manager.setMorphWeights(instance,weights,0);
                    bodyFound++;
                }else if(count==2){
                    manager.setMorphWeights(instance,faceWeights,0);
                    faceFound++;
                }
            }
            morphTargetCount=bodyFound;
            faceTargetCount=faceFound;
            if(bodyFound>0&&faceFound>0){
                morphUpdates++;
                loadError="";
            }else{
                loadError="Contrôle de corpulence incomplet : corps "+bodyFound+
                    ", visage "+faceFound;
            }
        }catch(Throwable ex){
            loadError="Morph : "+ex.getClass().getSimpleName()+" "+ex.getMessage();
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
            if(currentModel.contains("morph")||currentModel.contains("dressed"))
                message+=" | corps "+morphTargetCount+" visage "+faceTargetCount+
                    " | réglages "+morphUpdates;
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
        morphTargetCount=0;
        faceTargetCount=0;
        if(morphPanel!=null)
            morphPanel.setVisibility(
                (file.contains("morph")||file.contains("dressed"))?
                android.view.View.VISIBLE:android.view.View.GONE);
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
            applyMorphWeights();
            applyColors();
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
