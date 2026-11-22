/* Mon Évolution IMC — modèles haute définition, cadrés de face.
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
      eyeY:.075,eyeXs:[.470,.534],
      hair:[.345,.666,.006,.092],face:[.397,.605,.081,.176],
      neck:[.445,.554,.157,.218],
      arms:[[.18,.386,.230,.605],[.616,.82,.230,.605]],
      legs:[[.345,.492,.615,.942],[.513,.666,.615,.942]]
    },
    female:{
      eyeY:.072,eyeXs:[.471,.535],
      hair:[.344,.657,.006,.119],face:[.398,.601,.086,.174],
      neck:[.444,.555,.157,.220],
      arms:[[.174,.397,.218,.601],[.602,.83,.218,.601]],
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
      image.src=FILE;
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
  function recolor(pixels,state){
    const d=pixels.data,w=pixels.width,h=pixels.height;
    const f=figures[state.model];
    const wantSkin=state.skin.toUpperCase()!==BASE.skin.toUpperCase();
    const wantHair=state.hair.toUpperCase()!==BASE.hair.toUpperCase();
    const wantEyes=state.eyes.toUpperCase()!==BASE.eyes.toUpperCase();
    if(!wantSkin&&!wantHair&&!wantEyes)return;
    const skin=rgb(state.skin),hair=rgb(state.hair),eyes=rgb(state.eyes);
    const faceHole=f.face;
    for(let y=0;y<h;y++){
      const py=y/h;
      for(let x=0;x<w;x++){
        const px=x/w,i=(y*w+x)*4;
        const r=d[i],g=d[i+1],b=d[i+2];
        let dst=null,alpha=0;
        const isSkin=(inRect(px,py,f.face)||inRect(px,py,f.neck)||
          f.arms.some(a=>inRect(px,py,a))||f.legs.some(a=>inRect(px,py,a)));
        // The original photos have warm skin, while clothing and
        // background are charcoal/neutral. Retain natural photographic shadows.
        const warm=r>70&&g>35&&b>24&&r>g*1.055&&r>b*1.15&&g>b*.91;
        if(wantSkin&&isSkin&&warm){
          const luminosity=clamp((r*.30+g*.56+b*.14)/170,.37,1.60);
          dst=skin.map(v=>clamp(v*luminosity,0,255));
          alpha=.90;
        }
        if(wantHair&&inRect(px,py,f.hair)&&!inRect(px,py,faceHole)){
          const bright=(r+g+b)/3;
          const darkHair=bright<155&&r<g*1.75;
          if(darkHair){
            const light=clamp(bright/96,.24,1.65);
            dst=hair.map(v=>clamp(v*light,0,255));
            alpha=.94;
          }
        }
        if(wantEyes){
          const distances=f.eyeXs.map(cx=>((px-cx)/.010)**2+((py-f.eyeY)/.0048)**2);
          if(Math.min(...distances)<1.0&&r<172&&g<168){
            const light=clamp((r+g+b)/210,.65,1.25);
            dst=eyes.map(v=>clamp(v*light,0,255));
            alpha=.93;
          }
        }
        if(dst){
          d[i]=Math.round(r*(1-alpha)+dst[0]*alpha);
          d[i+1]=Math.round(g*(1-alpha)+dst[1]*alpha);
          d[i+2]=Math.round(b*(1-alpha)+dst[2]*alpha);
        }
      }
    }
  }
  async function paint(){
    scheduled=false;
    if(root.hidden)return;
    const state=appearance();
    const key=[state.id,state.model,state.skin,state.hair,state.eyes].join('|');
    const canvas=makeCanvas();
    if(lastKey===key&&canvas.dataset.renderedKey===key)return;
    const stamp=++serial;
    try{
      const img=await source();
      if(stamp!==serial)return;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      if(!ctx)throw Error('Canvas indisponible');
      canvas.width=WIDTH;canvas.height=HEIGHT;
      const sx=state.model==='female'?WIDTH:0;
      ctx.drawImage(img,sx,0,WIDTH,HEIGHT,0,0,WIDTH,HEIGHT);
      const pixels=ctx.getImageData(0,0,WIDTH,HEIGHT);
      recolor(pixels,state);
      ctx.putImageData(pixels,0,0);
      canvas.dataset.renderedKey=key;
      lastKey=key;
      stage.querySelector('.bm-photo-error')?.remove();
    }catch(e){
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
  window.addEventListener('pageshow',schedule);
  schedule();
})();
