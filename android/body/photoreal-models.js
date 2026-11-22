/* Two bundled photographic fitness models; vector mode remains for palette edits.
   Photographs are downloaded only during the signed APK build, never at runtime. */
(() => {
 'use strict';
 const root=document.getElementById('body-measurements');
 const stage=document.getElementById('bm-model');
 const models=document.getElementById('bm-models');
 const palettes=document.getElementById('bm-colors');
 if(!root||!stage||!models||!palettes)return;
 const selectedProfile=()=>typeof profile==='function'?profile().id:'unknown';
 const key=()=> 'imc-body-photo-mode-v1-'+selectedProfile();
 let view='photo';
 const modeBar=document.createElement('div');modeBar.className='bm-mode-selector';
 const photoBtn=document.createElement('button');photoBtn.type='button';photoBtn.className='bm-button';photoBtn.textContent='📷 Photo réaliste';
 const vectorBtn=document.createElement('button');vectorBtn.type='button';vectorBtn.className='bm-button';vectorBtn.textContent='🎨 Mannequin personnalisable';
 modeBar.append(photoBtn,vectorBtn);models.insertAdjacentElement('afterend',modeBar);
 const note=document.createElement('p');note.className='bm-hint';
 note.textContent='Les couleurs de peau, cheveux et yeux personnalisent le mannequin illustré. Les deux photos sont incluses hors ligne.';
 modeBar.insertAdjacentElement('afterend',note);
 const css=document.createElement('style');
 css.textContent=[
  '.bm-mode-selector{display:flex;gap:7px;flex-wrap:wrap;justify-content:center;margin:7px 0}',
  '.bm-mode-selector .bm-button{font-size:12px;padding:8px 9px;flex:1;min-width:110px}',
  '.bm-mode-selector .bm-button[aria-pressed="true"]{background:#6cdec7;color:#073533;border-color:#8bf7da;font-weight:800}',
  '#bm-model .bm-photo-model{position:absolute!important;inset:0;width:100%;height:100%;object-fit:contain;object-position:center center;display:block;z-index:0;pointer-events:none;border-radius:12px;-webkit-mask-image:linear-gradient(to bottom,transparent 0%,#000 8%,#000 90%,transparent 100%);mask-image:linear-gradient(to bottom,transparent 0%,#000 8%,#000 90%,transparent 100%)}',
  '#bm-model.bm-photo-view svg.bm-man{display:none!important}',
  '#bm-model .bm-point{z-index:2}',
  '#bm-model.bm-photo-view{background:radial-gradient(ellipse at 50% 45%,#2a4b5d,transparent 77%)}'
 ].join('\n');document.head.append(css);
 const mode=(force)=>{
  view=force || localStorage.getItem(key())||'photo';
  if(!['photo','vector'].includes(view))view='photo';
  photoBtn.setAttribute('aria-pressed',String(view==='photo'));
  vectorBtn.setAttribute('aria-pressed',String(view==='vector'));
  stage.classList.toggle('bm-photo-view',view==='photo');
  const svg=stage.querySelector('svg.bm-man');
  const previous=stage.querySelector('img.bm-photo-model');
  if(view==='vector'){
   if(previous)previous.remove();
   return;
  }
  const female=!!models.querySelector('.bm-button[aria-pressed="true"]')?.textContent?.includes('Femme');
  const expected=female?'body-female.jpg':'body-male.jpg';
  if(!previous){
   const img=document.createElement('img');img.className='bm-photo-model';
   img.src=expected;img.alt='Silhouette photographique '+(female?'féminine':'masculine');
   img.onerror=()=>{
    // Network/build or APK asset errors must leave the functional vector mannequin.
    stage.classList.remove('bm-photo-view');
    photoBtn.setAttribute('aria-pressed','false');
    vectorBtn.setAttribute('aria-pressed','true');
    img.remove();
   };
   stage.insertBefore(img,svg||stage.firstChild);
  }else if(!previous.src.endsWith(expected))previous.src=expected;
 };
 const change=next=>{
  view=next;try{localStorage.setItem(key(),next)}catch(e){}
  mode(next);
 };
 photoBtn.onclick=()=>change('photo');
 vectorBtn.onclick=()=>change('vector');
 palettes.addEventListener('click',e=>{
  if(!e.target?.closest?.('.bm-swatch'))return;
  // Swatches remain fully functional via the existing SVG, not a misleading
  // global photo filter that would also recolor clothing and backgrounds.
  if(view==='photo')change('vector');
 },true);
 const observer=new MutationObserver(()=>{
  if(root.hidden)return;
  mode();
 });
 observer.observe(stage,{childList:true});
 observer.observe(models,{childList:true});
 // Observe profile changes without polling or rewriting profile data.
 const oldProfilePicker=document.getElementById('profile-picker');
 oldProfilePicker?.addEventListener('change',()=>queueMicrotask(mode));
 mode();
})();