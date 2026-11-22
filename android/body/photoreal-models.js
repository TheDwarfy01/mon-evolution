/* Mon Évolution IMC — modèle photographique UNIQUE, Homme/Femme.
   Les couleurs sont appliquées aux pixels de la photographie hors ligne;
   il n'existe plus de bascule vers un second mannequin.
   Source photo toujours conservée; bodyAppearance ne contient que 3 couleurs.
*/
(() => {
 'use strict';
 const root=document.getElementById('body-measurements');
 const stage=document.getElementById('bm-model');
 const models=document.getElementById('bm-models');
 if(!root||!stage||!models)return;

 const male='body-male.jpg',female='body-female.jpg';
 const originals=new Map();
 let photoCanvas=null, rendering=false, queued=false, activeSource='', currentKey='';
 const css=document.createElement('style');
 css.textContent=[
  '#bm-model{position:relative;background:radial-gradient(ellipse at 50% 38%,#22475a 0%,#0b2b3f 65%,#0b2638 100%)}',
  '#bm-model svg.bm-man{display:none!important}',
  '#bm-model .bm-photo-canvas,#bm-model .bm-photo-fallback{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center;pointer-events:none;z-index:0;display:block}',
  '#bm-model .bm-photo-canvas{border-radius:13px}',
  '#bm-model .bm-point{z-index:3}',
  '#bm-models{display:flex;align-items:center;justify-content:center;gap:8px}',
  '#bm-models .bm-button{min-width:103px;padding:8px 12px}',
  '.bm-photo-tip{font-size:11px;color:#aedbdc;text-align:center;margin:5px 0 10px}',
  '#bm-colors .bm-palette-description{font-size:11px;color:#99c7d5}',
 ].join('\n');
 document.head.append(css);

 // App sends these exact model values into bodyAppearance; do not modify the
 // users' measurements, photos, or Drive-backed data.
 const current=()=>{
  const p=typeof profile==='function'?profile():null;
  const a=p?.bodyAppearance||{};
  return {
   model:a.model==='female'?'female':a.model==='male'?'male':p?.sex==='female'?'female':'male',
   skin:a.skin||'#D99E78',hair:a.hair||'#4A2D22',eyes:a.eyes||'#593826'
  };
 };
 const rgb=h=>[1,3,5].map(i=>parseInt((h||'#888888').slice(i,i+2),16)||0);
 const bound=(v,min,max)=>Math.max(min,Math.min(max,v));
 const skinRegion=(x,y)=>{
  // The center of an upright, forward-facing adult is selected. The
  // photograph outside these regions is NEVER colorized.
  const face=(y>=.07&&y<=.25&&x>=.40&&x<=.60);
  const neck=(y>=.23&&y<=.32&&x>=.45&&x<=.55);
  const arms=(y>=.26&&y<=.68&&((x>=.19&&x<=.40)||(x>=.61&&x<=.81)));
  const legs=(y>=.52&&y<=.96&&x>=.29&&x<=.72);
  return face||neck||arms||legs;
 };
 const hairRegion=(x,y)=>y>=.035&&y<=.185&&x>=.37&&x<=.63;
 const eyeRegion=(x,y)=>{
  const left=((x-.472)/.010)**2+((y-.177)/.006)**2;
  const right=((x-.527)/.010)**2+((y-.177)/.006)**2;
  return left<=1||right<=1;
 };
 function recolor(src,colors){
  // Preserve actual photographic highlights, facial features and clothing.
  // Recoloring uses softly blended, approximate anatomical masks. Hair and
  // iris positioning is approximate (the photos are illustrative).
  const [sr,sg,sb]=rgb(colors.skin),[hr,hg,hb]=rgb(colors.hair),
        [er,eg,eb]=rgb(colors.eyes);
  const image=new ImageData(new Uint8ClampedArray(src.data),src.width,src.height);
  const d=image.data,w=src.width,h=src.height;
  const skinDefault='#D99E78',hairDefault='#4A2D22',eyesDefault='#593826';
  const skinChange=colors.skin!==skinDefault,hairChange=colors.hair!==hairDefault,
        eyeChange=colors.eyes!==eyesDefault;
  if(!skinChange&&!hairChange&&!eyeChange)return image;
  for(let y=0;y<h;y++){
   const yy=y/h;
   for(let x=0;x<w;x++){
    const xx=x/w,i=(y*w+x)*4;
    let r=d[i],g=d[i+1],b=d[i+2],alpha=0,R=0,G=0,B=0;
    if(skinChange&&skinRegion(xx,yy)){
      // Basic skin chroma gate: dark clothing and saturated scenery are avoided.
      if(r>65&&g>32&&b>16&&r>g*1.06&&g>b*.86&&r>b*1.16){
        const strength=bound((r-g)/70,.25,.78);
        const lum=(r*.31+g*.54+b*.15)/170;
        R=bound(sr*lum,0,255);G=bound(sg*lum,0,255);B=bound(sb*lum,0,255);
        alpha=strength;
      }
    }
    if(hairChange&&hairRegion(xx,yy)){
      const brightness=(r+g+b)/3;
      if(brightness<205){
        const lum=bound(brightness/105,.22,1.75);
        R=bound(hr*lum,0,255);G=bound(hg*lum,0,255);B=bound(hb*lum,0,255);
        alpha=.72;
      }
    }
    if(eyeChange&&eyeRegion(xx,yy)){
      const brightness=(r+g+b)/3;
      if(brightness<155){
        const lum=bound(brightness/72,.5,1.2);
        R=bound(er*lum,0,255);G=bound(eg*lum,0,255);B=bound(eb*lum,0,255);
        alpha=.82;
      }
    }
    if(alpha){
      d[i]=Math.round(r*(1-alpha)+R*alpha);
      d[i+1]=Math.round(g*(1-alpha)+G*alpha);
      d[i+2]=Math.round(b*(1-alpha)+B*alpha);
    }
   }
  }
  return image;
 }
 function ensureCanvas(){
  let canvas=stage.querySelector('canvas.bm-photo-canvas');
  if(!canvas){
   canvas=document.createElement('canvas');canvas.className='bm-photo-canvas';
   canvas.setAttribute('aria-label','Mannequin adulte photoréaliste personnalisable');
   canvas.setAttribute('role','img');
   stage.insertBefore(canvas,stage.firstChild);
  }
  photoCanvas=canvas;
  return canvas;
 }
 function fallbackPhoto(file){
  let img=stage.querySelector('img.bm-photo-fallback');
  if(!img){
   img=document.createElement('img');img.className='bm-photo-fallback';
   stage.insertBefore(img,stage.firstChild);
  }
  if(!img.src.endsWith(file))img.src=file;
 }
 function load(file,complete){
  if(originals.has(file)){complete(originals.get(file));return;}
  const img=new Image();
  img.onload=()=>{
   try{
    const canvas=document.createElement('canvas');
    const scale=Math.min(1,720/Math.max(img.naturalWidth,img.naturalHeight));
    canvas.width=Math.max(1,Math.round(img.naturalWidth*scale));
    canvas.height=Math.max(1,Math.round(img.naturalHeight*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(!ctx)throw Error('Canvas indisponible');
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
    originals.set(file,pixels);
    complete(pixels);
   }catch(e){fallbackPhoto(file)}
  };
  img.onerror=()=>fallbackPhoto(file);
  img.src=file;
 }
 function paint(){
  queued=false;
  if(root.hidden)return;
  const colors=current(),file=colors.model==='female'?female:male;
  const key=[file,colors.skin,colors.hair,colors.eyes].join('|');
  const canvas=ensureCanvas();
  // Vector and photographic representations never appear together.
  if(currentKey===key&&stage.querySelector('canvas.bm-photo-canvas')?.width>0)return;
  const request=key;
  load(file,pixels=>{
    if([current().model==='female'?female:male,current().skin,current().hair,current().eyes].join('|')!==request)return;
    try{
      const c=ensureCanvas();
      c.width=pixels.width;c.height=pixels.height;
      const ctx=c.getContext('2d',{willReadFrequently:true});
      if(!ctx)throw Error('Canvas indisponible');
      ctx.putImageData(recolor(pixels,current()),0,0);
      stage.querySelector('img.bm-photo-fallback')?.remove();
      currentKey=request;
    }catch(e){fallbackPhoto(file)}
  });
 }
 function schedule(){
  if(queued)return;
  queued=true;requestAnimationFrame(paint);
 }
 // Re-render after gender, skin/hair/eye palette or active profile changes.
 const watch=new MutationObserver(mutations=>{
  if(mutations.some(m=>m.target===stage&&
     [...m.addedNodes].some(n=>n.nodeType===1&&n.matches?.('canvas.bm-photo-canvas,img.bm-photo-fallback'))))return;
  schedule();
 });
 watch.observe(stage,{childList:true});
 watch.observe(models,{childList:true,attributes:true,subtree:true,attributeFilter:['aria-pressed']});
 const palettes=document.getElementById('bm-colors');
 if(palettes)watch.observe(palettes,{childList:true});
 const quick=document.createElement('p');quick.className='bm-photo-tip';
 quick.textContent='Touchez un repère pour enregistrer une mesure. Personnalisez les couleurs ci-dessous.';
 stage.insertAdjacentElement('afterend',quick);
 schedule();
})();