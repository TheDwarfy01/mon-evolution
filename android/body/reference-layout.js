/* IMC — reference layout from the two supplied Mensurations mockups.
   One photo body + dotted callouts, 3 adjacent cards, 3 compact color controls.
   Existing save/history/chart functions and their listeners are NOT replaced.
*/
(() => {
 'use strict';
 const section=document.getElementById('body-measurements');
 const layout=document.getElementById('bm-main');
 const stage=document.getElementById('bm-model');
 const toggles=document.getElementById('bm-models');
 const palette=document.getElementById('bm-colors');
 if(!section||!layout||!stage||!toggles||!palette)return;
 const cards=[...layout.children];
 const left=cards[0],right=cards[1];
 if(!left||!right||document.getElementById('bm-reference-styles'))return;
 const css=document.createElement('style');css.id='bm-reference-styles';
 css.textContent=[
  '#body-measurements{--bm-teal:#77efd4;--bm-border:#285a72}',
  '#body-measurements .bm-layout{display:grid;grid-template-columns:minmax(0,0.94fr) minmax(0,1.06fr);gap:12px;margin:4px 0 14px;align-items:start}',
  '#body-measurements .bm-card{min-width:0;overflow:hidden;border-radius:14px;border:1px solid #2a607b;background:linear-gradient(155deg,#0b2d43 10%,#072739 80%);box-shadow:inset 0 1px 0 #326d8955;padding:13px}',
  '#body-measurements .bm-card h3{margin:0 0 7px;color:#eafaf8;font-size:15px;line-height:1.3}',
  '#body-measurements .bm-title{display:flex!important;align-items:center;gap:7px;margin:0 0 0}',
  '#body-measurements .bm-title h2{font-size:19px!important;line-height:1.2}',
  '#body-measurements .bm-ref-subtitle{font-size:11px;color:#a6cddd;margin:3px 0 9px;line-height:1.4}',
  '#body-measurements .bm-original-lead{display:none!important}',
  '#body-measurements #bm-models{display:flex;justify-content:center;gap:5px;margin:5px auto 10px}',
  '#body-measurements #bm-models .bm-button{border-radius:999px;font-size:12px;min-width:92px;padding:5px 10px;min-height:32px}',
  '#body-measurements .bm-stage{height:535px;max-width:440px;margin:0 auto;border-radius:13px;isolation:isolate;overflow:hidden;background:transparent!important}',
  '#body-measurements #bm-model{background:transparent!important}',
  '#body-measurements .bm-stage .bm-photo-canvas,#body-measurements .bm-stage .bm-photo-fallback{object-fit:contain;object-position:center}',
  '#body-measurements .bm-measure-lines{position:absolute;inset:0;width:100%;height:100%;z-index:2;pointer-events:none;overflow:visible}',
  '#body-measurements .bm-point{z-index:3;min-width:83px;max-width:27%;padding:6px 6px;min-height:39px;border-radius:9px;border:1px solid #397d95;background:#062537e8;box-shadow:0 4px 12px #00132080;text-align:left}',
  '#body-measurements .bm-point strong{font-size:11px;font-weight:650;color:#f2ffff}',
  '#body-measurements .bm-point small{font-size:11px;color:#97e8e2}',
  '#body-measurements .bm-point[data-side="left"]{left:1%}',
  '#body-measurements .bm-point[data-side="right"]{right:1%}',
  '#body-measurements .bm-point[data-metric="neck"],#body-measurements .bm-point[data-metric="forearm"]{display:none!important}',
  '#body-measurements .bm-point[data-active="true"]{border-color:var(--bm-teal);background:#1b6669}',
  '#body-measurements .bm-silhouette-shortcuts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;margin:8px 0}',
  '#body-measurements .bm-silhouette-shortcuts button{display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;min-height:52px;padding:6px 3px;border:1px solid #315f77;border-radius:9px;color:#cef4f5;background:#1a3d50;font-size:11px}',
  '#body-measurements .bm-silhouette-shortcuts button .bm-shortcut-icon{font-size:21px;line-height:1.2;color:var(--bm-teal)}',
  '#body-measurements .bm-palette-header{display:block;width:100%;text-align:left;color:#abeee3;background:#19394d;border:1px solid #335f76;border-radius:9px;padding:10px;margin:6px 0 4px;font-size:12px}',
  '#body-measurements #bm-colors[hidden]{display:none!important}',
  '#body-measurements #bm-colors{margin:7px 0 4px;padding:8px;border-radius:10px;background:#0c283d;border:1px solid #355c72;gap:7px}',
  '#body-measurements #bm-colors .bm-swatch{width:26px;height:26px}',
  '#body-measurements #bm-model > #bm-colors{position:absolute!important;right:7px;top:57px;width:44%;max-width:188px;box-sizing:border-box;z-index:13;display:grid;gap:10px;margin:0;padding:9px;background:#0b2c40eF;border:1px solid #568a9c;border-radius:10px;touch-action:pan-y}',
  '#body-measurements #bm-model > #bm-colors[hidden]{display:none!important}',
  '#body-measurements #bm-model > #bm-colors .bm-color-slider-row{display:block}',
  '#body-measurements #bm-model > #bm-colors .bm-color-preview{display:none}',
  '#body-measurements #bm-model > #bm-colors .bm-color-range{width:100%;box-sizing:border-box;padding:0;border:0;outline-offset:2px;touch-action:none}',
  '#body-measurements #bm-model > #bm-colors .bm-color-range::-webkit-slider-thumb{width:23px;height:23px;margin-top:-4px}',
  '#body-measurements #bm-model > #bm-colors .bm-color-value{font-size:10px;line-height:1.15;overflow-wrap:anywhere}',
  '#body-measurements #bm-model .bm-colors-toggle{position:absolute;right:8px;top:8px;z-index:14;min-height:34px;min-width:38px;padding:5px 8px;border:1px solid #639ba3;border-radius:8px;background:#103e52ef;color:#e3fffb;font-size:17px;touch-action:manipulation}',
  '#body-measurements #bm-model .bm-colors-toggle[aria-expanded="true"]{background:#226e70;border-color:#91efdc}',
  '#body-measurements #bm-model.bm-color-mode .bm-point,#body-measurements #bm-model.bm-color-mode .bm-measure-lines,#body-measurements #bm-model.bm-color-mode .bm-studio-landmarks,#body-measurements #bm-model.bm-color-mode .bm-studio-leaders,#body-measurements #bm-model.bm-color-mode .bm-studio-entry,#body-measurements #bm-model.bm-color-mode .bm-studio-density{display:none!important}',
  '#body-measurements #bm-model .bm-studio-density{top:auto!important;bottom:8px!important}',
  '#body-measurements #bm-main.bm-table-only .bm-colors-toggle,#body-measurements #bm-main.bm-table-only #bm-colors{display:none!important}',
  '#body-measurements .bm-hint{font-size:11px}',
  '#body-measurements .bm-ref-side{display:grid;gap:8px;align-content:start}',
  '#body-measurements .bm-ref-side>.bm-card{margin:0}',
  '#body-measurements .bm-form-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}',
  '#body-measurements .bm-form-grid label{font-size:11px}',
  '#body-measurements .bm-form-grid input,#body-measurements .bm-date{padding:7px 7px;font-size:13px;border-radius:8px}',
  '#body-measurements .bm-save{min-height:37px;padding:9px;margin-top:11px;border-radius:8px;font-size:12px}',
  '#body-measurements .bm-history{max-height:140px}',
  '#body-measurements .bm-history-row{font-size:11px;padding:6px 0}',
  '#body-measurements .bm-progress{min-height:140px}',
  '#body-measurements .bm-key{gap:5px 8px}',
  '#body-measurements .bm-key label{font-size:11px}',
  '#body-measurements .bm-last{min-height:20px;margin:4px 0;font-size:11px;color:#9abfcb}',
  '@media(max-width:760px){#body-measurements .bm-layout{grid-template-columns:1fr}#body-measurements .bm-stage{height:540px}#body-measurements .bm-ref-side{gap:10px}}',
  '@media(max-width:365px){#body-measurements .bm-stage{height:515px}#body-measurements .bm-point{min-width:75px;padding:5px;max-width:28%}#body-measurements .bm-point strong{font-size:10px}#body-measurements .bm-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}',
 ].join('\n');document.head.append(css);
 const originalTitle=section.querySelector(':scope > .bm-title');
 const lead=section.querySelector(':scope > p.muted');
 if(originalTitle){
  left.prepend(originalTitle);
  originalTitle.querySelector('h2')?.replaceChildren(document.createTextNode('Mensurations'));
 }
 left.querySelector(':scope > h3')?.remove();
 if(lead){
  lead.classList.add('bm-original-lead');
  const subtitle=document.createElement('p');subtitle.className='bm-ref-subtitle';
  subtitle.textContent='Suivi des tours et mensurations corporelles';
  originalTitle?.insertAdjacentElement('afterend',subtitle);
 }
 if(left.querySelector(':scope > .bm-hint'))left.querySelector(':scope > .bm-hint').remove();
 right.classList.add('bm-ref-side');

 // Dotted lines from each measurement label to the precise intended body zone.
 const metrics=['chest','arm','waist','belly','hips','thigh','calf','neck','forearm'];
 // The height coordinates refer to the photographed figure, not the tag.
 // Separate calibrations ensure that the dotted lines reach real anatomical
 // landmarks on each portrait. Waist = narrow natural waist; belly = abdomen
 // below it, never the shorts/crotch; hip = lateral pelvis, not the groin.
 // Every coordinate is a percent of the 810x1440 studio portrait
 // (drawn with object-fit:contain). Targets refer to anatomy, not label height.
 const malePositions={
  chest:{buttonY:27,originX:26,targetX:50,targetY:28.7},
  arm:{buttonY:33,originX:74,targetX:69,targetY:33.8},
  waist:{buttonY:42,originX:26,targetX:49,targetY:39.7},
  belly:{buttonY:51,originX:74,targetX:50,targetY:42.5},
  hips:{buttonY:57,originX:26,targetX:39,targetY:49.2},
  thigh:{buttonY:70,originX:26,targetX:43,targetY:62.5},
  calf:{buttonY:85,originX:74,targetX:58,targetY:78.6}
 };
 const femalePositions={
  chest:{buttonY:27,originX:26,targetX:50,targetY:28.7},
  arm:{buttonY:33,originX:74,targetX:69,targetY:33.8},
  waist:{buttonY:42,originX:26,targetX:49,targetY:39.5},
  belly:{buttonY:51,originX:74,targetX:50,targetY:42.7},
  hips:{buttonY:57,originX:26,targetX:39,targetY:49.3},
  thigh:{buttonY:70,originX:26,targetX:42,targetY:60.7},
  calf:{buttonY:85,originX:74,targetX:57,targetY:78.5}
 };
 function activeFigure(){
  const selected=[...toggles.querySelectorAll('button')].find(b=>b.getAttribute('aria-pressed')==='true');
  if(selected)return /femme/i.test(selected.textContent||'')?'female':'male';
  const p=typeof profile==='function'?profile():null;
  return p?.bodyAppearance?.model==='female'||(!p?.bodyAppearance?.model&&p?.sex==='female')?'female':'male';
 }
 const NS='http://www.w3.org/2000/svg';
 function connectors(){
  const buttons=stage.querySelectorAll('.bm-point');
  if(!buttons.length)return;
  const position=activeFigure()==='female'?femalePositions:malePositions;
  for(let i=0;i<buttons.length;i++){
   const button=buttons[i];
   const key=metrics[i];
   button.dataset.metric=key;
   if(position[key])button.style.top=position[key].buttonY+'%';
  }
  const previous=stage.querySelector('.bm-measure-lines');
  if(previous)previous.remove();
  const overlay=document.createElementNS(NS,'svg');
  overlay.classList.add('bm-measure-lines');
  overlay.setAttribute('viewBox','0 0 100 100');
  overlay.setAttribute('preserveAspectRatio','none');
  overlay.setAttribute('aria-hidden','true');
  for(const [key,pos] of Object.entries(position)){
   const line=document.createElementNS(NS,'line');
   for(const [k,v] of Object.entries({
    x1:pos.originX,y1:pos.buttonY+3,x2:pos.targetX,y2:pos.targetY,
    stroke:'#72e9df','stroke-width':'.32','stroke-dasharray':'1.1 1.3','stroke-linecap':'round',opacity:'.9'
   }))line.setAttribute(k,v);
   overlay.append(line);
   const dot=document.createElementNS(NS,'circle');
   dot.setAttribute('cx',pos.targetX);dot.setAttribute('cy',pos.targetY);
   dot.setAttribute('r','.72');dot.setAttribute('fill','#84fff1');
   dot.setAttribute('stroke','#1b747b');dot.setAttribute('stroke-width','.2');
   overlay.append(dot);
  }
  stage.append(overlay);
 }
 // Only refresh connectors after the base mannequin genuinely rerenders.
 // Avoid an observer loop when the overlay itself is inserted.
 const observer=new MutationObserver(mutations=>{
  if(mutations.some(m=>[...m.addedNodes].some(n=>
     n.nodeType===1&&n.classList?.contains('bm-point'))))connectors();
 });
 observer.observe(stage,{childList:true});
 // A sex switch can update button attributes before the stage is rerendered.
 const sexObserver=new MutationObserver(()=>connectors());
 sexObserver.observe(toggles,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed']});
 connectors();

 // Three shortcuts below the mannequin. Photo stays available inside
 // the measurements form, where its original click listener remains intact.
 const nav=document.createElement('div');nav.className='bm-silhouette-shortcuts';
 function jump(label,symbol,target){
  const b=document.createElement('button');b.type='button';
  const ico=document.createElement('span');ico.className='bm-shortcut-icon';ico.textContent=symbol;
  b.append(ico,document.createTextNode(label));
  b.onclick=()=>document.getElementById(target)?.scrollIntoView({behavior:'smooth',block:'center'});
  nav.append(b);
 }
 jump('Historique','▤','bm-history');
 jump('Évolution','▥','bm-graph');
 const customize=document.createElement('button');
 customize.type='button';
 customize.setAttribute('aria-controls','bm-colors');
 customize.setAttribute('aria-expanded','false');
 const paletteIcon=document.createElement('span');
 paletteIcon.className='bm-shortcut-icon';
 paletteIcon.textContent='🎨';
 customize.append(paletteIcon,document.createTextNode('Personnalisation'));
 const colorToggle=document.createElement('button');
 colorToggle.type='button';colorToggle.className='bm-colors-toggle';
 colorToggle.textContent='🎨';colorToggle.title='Afficher les couleurs';
 colorToggle.setAttribute('aria-label','Afficher les couleurs');
 colorToggle.setAttribute('aria-controls','bm-colors');
 colorToggle.setAttribute('aria-expanded','false');
 function syncColorMode(){
  const open=!palette.hidden;
  stage.classList.toggle('bm-color-mode',open);
  for(const button of [customize,colorToggle])button.setAttribute('aria-expanded',String(open));
  colorToggle.textContent=open?'✕':'🎨';
  colorToggle.title=open?'Masquer les couleurs et retrouver les mesures':'Afficher les couleurs';
  colorToggle.setAttribute('aria-label',colorToggle.title);
  window.dispatchEvent(new Event('mon-evolution-color-mode-changed'));
 }
 customize.onclick=colorToggle.onclick=()=>{
  palette.hidden=!palette.hidden;
  syncColorMode();
  if(!palette.hidden){
   const r=stage.getBoundingClientRect();
   if(r.top<0||r.bottom>window.innerHeight)stage.scrollIntoView({behavior:'smooth',block:'start'});
  }
 };
 nav.append(customize);
 stage.insertAdjacentElement('afterend',nav);
 palette.hidden=true;
 stage.append(palette,colorToggle);
 // Stage may be rebuilt after profile changes, so reattach the existing controls.
 new MutationObserver(()=>{
  if(!stage.contains(palette))stage.append(palette);
  if(!stage.contains(colorToggle))stage.append(colorToggle);
 }).observe(stage,{childList:true});
 syncColorMode();
 // Keep date, all saved measurements, chart and history intact.
 const form=right.querySelector('.bm-card');
 if(form){
  const save=form.querySelector('#bm-save');
  if(save)save.textContent='✓ Enregistrer';
  const title=form.querySelector('h3');
  if(title)title.textContent='▣ Enregistrer les mensurations';
 }
})();
