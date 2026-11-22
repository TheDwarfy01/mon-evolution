/* Mon Évolution IMC — v1.6.120, recoloration photo réaliste sans aplats.
   Modèles haute définition, cadrés de face.
   Deux personnages issus de la même ressource WebP 1620x1440,
   découpée en deux vues indépendantes de 810x1440.
   Les couleurs s'appliquent aux pixels du personnage ACTIF sans changer
   la silhouette, le profil ni les mensurations enregistrées. */
(() => {
  'use strict';
  const root=document.getElementById('body-measurements');
  const stage=document.getElementById('bm-model');
  const models=document.getElementById('bm-models');
  const palette=document.getElementById('bm-colors');
  if(!root||!stage||!models||!palette)return;

  const FILE='models-hq-v2.webp',WIDTH=810,HEIGHT=1440;
  const BASE={skin:'#D99E78',hair:'#4A2D22',eyes:'#593826'};
  const figures={
    male:{
      eyeY:.088,eyeXs:[.470,.534],
      hair:[.345,.666,.006,.092],face:[.397,.605,.047,.176],
      neck:[.445,.554,.157,.218],
      arms:[[.18,.386,.230,.605],[.616,.82,.230,.605]],
      legs:[[.345,.492,.615,.942],[.513,.666,.615,.942]]
    },
    female:{
      eyeY:.094,eyeXs:[.466,.529],
      hair:[.344,.657,.006,.119],face:[.398,.601,.052,.174],
      neck:[.444,.555,.157,.220],
      arms:[[.174,.397,.178,.601],[.602,.83,.178,.601]],
      legs:[[.342,.494,.554,.935],[.512,.666,.554,.935]]
    }
  };
  const inRect=(x,y,r)=>x>=r[0]&&x<=r[1]&&y>=r[2]&&y<=r[3];
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const rgb=c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));
  const isColor=c=>typeof c==='string'&&/^#[0-9a-fA-F]{6}$/.test(c);
  let spritePromise=null;
  let scheduled=false;
  let lastKey='';
  let serial=0;
  const style=document.createElement('style');
  style.textContent=[
    '#bm-model{position:relative;isolation:isolate;background:linear-gradient(135deg,#283b4a,#172e40)!important}',
    '#bm-model svg.bm-man{display:none!important}',
    '#bm-model canvas.bm-photo-canvas{position:absolute!important;inset:0;width:100%;height:100%;object-fit:contain;object-position:center;display:block!important;z-index:0;pointer-events:none;border-radius:12px}',
    '#bm-model .bm-point{position:absolute;z-index:3}',
    '#bm-model .bm-photo-error{position:absolute;z-index:1;top:38%;left:12%;right:12%;background:#102e41;padding:14px;border-radius:10px;color:#d5efed;font-size:12px;text-align:center}'
  ].join('\n');
  document.head.append(style);

  function appearance(){
    const p=typeof profile==='function'?profile():null;
    const a=p?.bodyAppearance||{};
    return {
      id:p?.id||'',
      model:a.model==='female'?'female':a.model==='male'?'male':p?.sex==='female'?'female':'male',
      skin:isColor(a.skin)?a.skin:BASE.skin,
      hair:isColor(a.hair)?a.hair:BASE.hair,
      eyes:isColor(a.eyes)?a.eyes:BASE.eyes
    };
  }
  function source(){
    if(spritePromise)return spritePromise;
    spritePromise=new Promise((resolve,reject)=>{
      const image=new Image();
      image.onload=()=>image.naturalWidth===WIDTH*2&&image.naturalHeight===HEIGHT?
        resolve(image):reject(Error('Format du modèle invalide'));
      image.onerror=()=>reject(Error('Images haute définition introuvables'));
      // A data URL is origin-clean in Android WebView, unlike a file:// image
      // when file-to-file access is restricted (the secure Android default).
      image.src=window.MonEvolutionStudioSpriteData||FILE;
    }).catch(e=>{spritePromise=null;throw e;});
    return spritePromise;
  }
  function makeCanvas(){
    let c=stage.querySelector('canvas.bm-photo-canvas');
    if(!c){
      c=document.createElement('canvas');
      c.className='bm-photo-canvas';
      c.setAttribute('role','img');
      c.setAttribute('aria-label','Silhouette photoréaliste personnalisable');
      stage.insertBefore(c,stage.firstChild);
    }
    return c;
  }
  // Accurate segment masks are generated from the original transparent
  // portraits at build time. Drawing alpha masks never requires reading pixels
  // from Android WebView canvases, which previously caused rectangular patches.
  const featureNames=['skin','hair','eyes'];
  let maskPromise=null;
  function maskSources(){
    if(maskPromise)return maskPromise;
    const urls=window.MonEvolutionStudioMasks||{};
    maskPromise=Promise.all(featureNames.map(key=>new Promise((resolve,reject)=>{
      const url=urls[key];
      if(typeof url!=='string'||!url.startsWith('data:image/png;base64,')){
        reject(Error('Masque de couleur absent: '+key));return;
      }
      const img=new Image();
      img.onload=()=>img.naturalWidth===WIDTH*2&&img.naturalHeight===HEIGHT?
        resolve([key,img]):reject(Error('Dimension du masque invalide: '+key));
      img.onerror=()=>reject(Error('Masque illisible: '+key));
      img.src=url;
    }))).then(entries=>Object.fromEntries(entries))
      .catch(error=>{maskPromise=null;throw error;});
    return maskPromise;
  }
  const layers=document.createElement('canvas');
  layers.width=WIDTH;layers.height=HEIGHT;
  const layerCtx=layers.getContext('2d');
  function tintMaskedPart(ctx,mask,model,color,kind){
    if(!layerCtx)return;
    layerCtx.clearRect(0,0,WIDTH,HEIGHT);
    layerCtx.globalCompositeOperation='source-over';
    layerCtx.globalAlpha=1;
    const sx=model==='female'?WIDTH:0;
    layerCtx.drawImage(mask,sx,0,WIDTH,HEIGHT,0,0,WIDTH,HEIGHT);
    // Apply chosen color inside only the alpha of the semantic mask.
    // This replaces rectangular source-atop fills with accurate edges.
    layerCtx.globalCompositeOperation='source-in';
    layerCtx.fillStyle=color;
    layerCtx.fillRect(0,0,WIDTH,HEIGHT);
    layerCtx.globalCompositeOperation='source-over';
    // Preserve original photographic lighting instead of painting a flat
    // 82-90%-opaque colour on top of the skin or the hair. The soft-light
    // compositing keeps the details of eyelids, face, hair and legs visible.
    ctx.save();
    if(kind==='eyes'){
      ctx.globalCompositeOperation='source-over';
      ctx.globalAlpha=.47;
      ctx.drawImage(layers,0,0);
    }else{
      ctx.globalCompositeOperation='soft-light';
      ctx.globalAlpha=kind==='hair'?.76:.72;
      ctx.drawImage(layers,0,0);
      ctx.globalCompositeOperation='source-over';
      ctx.globalAlpha=kind==='hair'?.23:.28;
      ctx.drawImage(layers,0,0);
      // White / blonde hair needs a gentle lift without a white opaque cap.
      const chosen=rgb(color);
      const brightness=(chosen[0]*.2126+chosen[1]*.7152+chosen[2]*.0722)/255;
      if(kind==='hair'&&brightness>.76){
        ctx.globalCompositeOperation='screen';
        ctx.globalAlpha=.19;
        ctx.drawImage(layers,0,0);
      }
    }
    ctx.restore();
  }
  async function paint(){
    scheduled=false;
    if(root.hidden)return;
    const state=appearance();
    const key=[state.id,state.model,state.skin,state.hair,state.eyes].join('|');
    const canvas=makeCanvas();
    // A completed draw is authoritative: an older async error must never
    // cover an already visible portrait (male or female).
    if(lastKey===key&&canvas.dataset.renderedKey===key){
      stage.querySelector('.bm-photo-error')?.remove();
      return;
    }
    const stamp=++serial;
    try{
      const img=await source();
      // Switching model/profile can replace the canvas while the WebP loads.
      // Never let a response for an old canvas overwrite the current view.
      if(stamp!==serial||!stage.contains(canvas)){schedule();return;}
      const ctx=canvas.getContext('2d',{willReadFrequently:true})||canvas.getContext('2d');
      if(!ctx)throw Error('Canvas indisponible');
      canvas.width=WIDTH;canvas.height=HEIGHT;
      const sx=state.model==='female'?WIDTH:0;
      ctx.drawImage(img,sx,0,WIDTH,HEIGHT,0,0,WIDTH,HEIGHT);
      // The source photo stays untouched; color changes are drawn as
      // precisely segmented overlays. No getImageData or block-shaped fill.
      try{
        const masks=await maskSources();
        if(stamp!==serial||!stage.contains(canvas)){schedule();return;}
        for(const kind of featureNames){
          if(state[kind].toUpperCase()!==BASE[kind].toUpperCase()){
            tintMaskedPart(ctx,masks[kind],state.model,state[kind],kind);
          }
        }
      }catch(maskError){
        // Never hide or corrupt the original portrait if optional colors fail.
        console.warn('Masques de couleurs non disponibles',maskError);
      }
      if(stamp!==serial||!stage.contains(canvas)){schedule();return;}
      canvas.dataset.renderedKey=key;
      lastKey=key;
      stage.querySelector('.bm-photo-error')?.remove();
    }catch(e){
      if(stamp!==serial||!stage.contains(canvas)){schedule();return;}
      // Transient failures must not cover a portrait successfully drawn before.
      if(canvas.dataset.renderedKey){
        stage.querySelector('.bm-photo-error')?.remove();
        return;
      }
      if(!stage.querySelector('.bm-photo-error')){
        const box=document.createElement('div');box.className='bm-photo-error';
        box.textContent='Image indisponible. Vos mensurations restent enregistrées.';
        stage.append(box);
      }
    }
  }
  function schedule(){
    if(scheduled)return;
    scheduled=true;
    requestAnimationFrame(paint);
  }
  // The original palette re-renders its DOM on every choice, so observing
  // it (not only the click) is essential. This also covers profile changes.
  const watcher=new MutationObserver(mutations=>{
    if(mutations.some(m=>m.target===stage&&
       [...m.addedNodes].some(n=>n.nodeType===1&&
       n.matches?.('canvas.bm-photo-canvas,.bm-photo-error'))))return;
    schedule();
  });
  watcher.observe(stage,{childList:true});
  watcher.observe(models,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed']});
  watcher.observe(palette,{childList:true,subtree:true});
  palette.addEventListener('click',()=>requestAnimationFrame(schedule));
  models.addEventListener('click',()=>requestAnimationFrame(schedule));
  document.addEventListener('click',e=>{
    if(e.target?.closest?.('#visual-profile-picker,.profile-portrait-choice'))requestAnimationFrame(schedule);
  });
  window.addEventListener('mon-evolution-appearance-changed',()=>{
    // Force repaint even when the same profile is selected again.
    lastKey='';
    schedule();
  });
  window.addEventListener('pageshow',schedule);
  schedule();
})();
