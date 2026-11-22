/* Mon Évolution IMC — photoreal adult models, frontal studio view.
   Single source sprite: left male, right female. Both are standing upright,
   full body visible, arms relaxed. No external images, no secondary mannequin.
   Skin / hair / iris are recolored directly on the photograph; user metrics
   are never changed by visual personalization. */
(() => {
  'use strict';
  const stage=document.getElementById('bm-model');
  const root=document.getElementById('body-measurements');
  const models=document.getElementById('bm-models');
  const colorsPanel=document.getElementById('bm-colors');
  if(!stage||!root||!models||!colorsPanel)return;

  const SOURCE='models-front-facing.webp';
  const ORIGINAL_SKIN='#D99E78',ORIGINAL_HAIR='#4A2D22',ORIGINAL_EYES='#593826';
  const male={face:{x:.5,y:.093},head:[.36,.65,.012,.145],arms:[[.12,.41,.17,.64],[.59,.88,.17,.64]],legs:[.28,.72,.60,.985],eyes:[.468,.532,.104]};
  const female={face:{x:.5,y:.093},head:[.36,.65,.010,.150],arms:[[.13,.40,.17,.65],[.60,.87,.17,.65]],legs:[.27,.73,.59,.99],eyes:[.466,.534,.103]};
  const bounds=(v,a,b)=>Math.max(a,Math.min(b,v));
  const inBox=(x,y,v)=>x>=v[0]&&x<=v[1]&&y>=v[2]&&y<=v[3];
  const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
  let image=null,pending=false,lastKey='',requestNumber=0;
  const style=document.createElement('style');
  style.textContent=[
    '#bm-model{position:relative;background:#092435!important;isolation:isolate}',
    '#bm-model svg.bm-man{display:none!important}',
    '#bm-model .bm-photo-canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center;z-index:0;pointer-events:none;border-radius:13px}',
    '#bm-model .bm-point{z-index:3}',
    '#bm-model .bm-photo-error{position:absolute;top:35%;left:18%;right:18%;z-index:1;color:#cdece8;font-size:12px;line-height:1.5;text-align:center;background:#123548;padding:14px;border-radius:12px}',
  ].join('\n');
  document.head.append(style);

  const current=()=>{
    const p=typeof profile==='function'?profile():{};
    const a=p?.bodyAppearance||{};
    return {
      id:p?.id||'',
      model:a.model==='female'?'female':a.model==='male'?'male':p?.sex==='female'?'female':'male',
      skin:/^#[a-f0-9]{6}$/i.test(a.skin||'')?a.skin:ORIGINAL_SKIN,
      hair:/^#[a-f0-9]{6}$/i.test(a.hair||'')?a.hair:ORIGINAL_HAIR,
      eyes:/^#[a-f0-9]{6}$/i.test(a.eyes||'')?a.eyes:ORIGINAL_EYES
    };
  };
  function ensureCanvas(){
    let c=stage.querySelector('canvas.bm-photo-canvas');
    if(!c){
      c=document.createElement('canvas');
      c.className='bm-photo-canvas';
      c.setAttribute('role','img');
      c.setAttribute('aria-label','Silhouette photoréaliste de face pour les mensurations');
      stage.insertBefore(c,stage.firstChild);
    }
    return c;
  }
  function loadImage(){
    if(image)return Promise.resolve(image);
    if(loadImage.pending)return loadImage.pending;
    loadImage.pending=new Promise((resolve,reject)=>{
      const im=new Image();
      im.onload=()=>{
        if(im.naturalWidth!==560||im.naturalHeight!==560){
          reject(Error('Le modèle photographique ne correspond pas au format attendu.'));return;
        }
        image=im;resolve(image);
      };
      im.onerror=()=>reject(Error('Photographies non disponibles dans cette version.'));
      im.src=SOURCE;
    }).catch(e=>{loadImage.pending=null;throw e});
    return loadImage.pending;
  }
  function recolor(pixels,a){
    const d=pixels.data,geo=a.model==='female'?female:male,w=pixels.width,h=pixels.height;
    const [sr,sg,sb]=rgb(a.skin),[hr,hg,hb]=rgb(a.hair),[er,eg,eb]=rgb(a.eyes);
    const needsSkin=a.skin.toUpperCase()!==ORIGINAL_SKIN.toUpperCase();
    const needsHair=a.hair.toUpperCase()!==ORIGINAL_HAIR.toUpperCase();
    const needsEyes=a.eyes.toUpperCase()!==ORIGINAL_EYES.toUpperCase();
    if(!needsSkin&&!needsHair&&!needsEyes)return;
    for(let y=0;y<h;y++){
      const yy=y/h;
      for(let x=0;x<w;x++){
        const xx=x/w,idx=(y*w+x)*4;
        const r=d[idx],g=d[idx+1],b=d[idx+2];
        const face=inBox(xx,yy,[.38,.62,.041,.16]);
        const neck=inBox(xx,yy,[.43,.57,.15,.22]);
        const arms=geo.arms.some(rect=>inBox(xx,yy,rect));
        const legs=inBox(xx,yy,geo.legs);
        const hairRegion=inBox(xx,yy,geo.head)&&!inBox(xx,yy,[.39,.61,.075,.175]);
        let alpha=0,target=null;
        const skinLike=r>53&&g>27&&b>15&&r>g*1.08&&g>b*.90&&r>b*1.14;
        if(needsSkin&&(face||neck||arms||legs)&&skinLike){
          const light=bounds((r*.34+g*.49+b*.17)/155,.52,1.52);
          target=[sr*light,sg*light,sb*light];alpha=.76;
        }
        if(needsHair&&hairRegion&&(r+g+b)/3<172){
          const light=bounds((r+g+b)/240,.34,1.42);
          target=[hr*light,hg*light,hb*light];alpha=.80;
        }
        if(needsEyes){
          const l=((xx-geo.eyes[0])/.012)**2+((yy-geo.eyes[2])/.0055)**2;
          const t=((xx-geo.eyes[1])/.012)**2+((yy-geo.eyes[2])/.0055)**2;
          if(Math.min(l,t)<1.0&&r<185&&g<185){
            target=[er,eg,eb];alpha=.82;
          }
        }
        if(target){
          d[idx]=Math.round(r*(1-alpha)+bounds(target[0],0,255)*alpha);
          d[idx+1]=Math.round(g*(1-alpha)+bounds(target[1],0,255)*alpha);
          d[idx+2]=Math.round(b*(1-alpha)+bounds(target[2],0,255)*alpha);
        }
      }
    }
  }
  async function paint(){
    pending=false;
    if(root.hidden)return;
    const a=current(),key=[a.id,a.model,a.skin,a.hair,a.eyes].join('|');
    const c=ensureCanvas();
    if(lastKey===key&&c.dataset.renderedKey===key)return;
    const number=++requestNumber;
    try{
      const sprite=await loadImage();
      if(number!==requestNumber)return;
      const ctx=c.getContext('2d',{willReadFrequently:true});
      if(!ctx)throw Error('Affichage photo non disponible');
      // Split the composite image in two at x=280. Never show both people.
      const x=a.model==='female'?280:0;
      c.width=280;c.height=560;
      ctx.clearRect(0,0,280,560);
      ctx.drawImage(sprite,x,0,280,560,0,0,280,560);
      const pixels=ctx.getImageData(0,0,280,560);
      recolor(pixels,a);
      ctx.putImageData(pixels,0,0);
      c.dataset.renderedKey=key;lastKey=key;
      stage.querySelector('.bm-photo-error')?.remove();
    }catch(error){
      if(!stage.querySelector('.bm-photo-error')){
        const box=document.createElement('div');box.className='bm-photo-error';
        box.textContent='Impossible de charger le mannequin photo. Aucune mesure n’a été modifiée.';
        stage.append(box);
      }
    }
  }
  const schedule=()=>{
    if(pending)return;
    pending=true;
    requestAnimationFrame(paint);
  };
  const stageWatch=new MutationObserver(m=>{
    // Rendering removes/reinserts the photo canvas; restore it after a base re-render.
    if(m.some(x=>[...x.addedNodes].some(n=>
      n.nodeType===1&&(n.matches?.('.bm-point,.bm-man')))))schedule();
  });
  stageWatch.observe(stage,{childList:true,subtree:false});
  const modelWatch=new MutationObserver(schedule);
  modelWatch.observe(models,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed']});
  // Existing palettes change in-place; listen without suppressing existing callbacks.
  colorsPanel.addEventListener('click',()=>queueMicrotask(schedule));
  document.addEventListener('click',e=>{
    if(e.target?.closest?.('#visual-profile-picker,.profile-portrait-choice'))queueMicrotask(schedule);
  });
  schedule();
})();