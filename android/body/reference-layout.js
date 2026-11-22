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
  '#body-measurements .bm-stage{height:535px;max-width:440px;margin:0 auto;border-radius:13px;isolation:isolate;overflow:hidden}',
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
 const position={
  chest:{buttonY:28,originX:26,targetX:50,targetY:29},
  arm:{buttonY:33,originX:74,targetX:66,targetY:35},
  waist:{buttonY:41,originX:26,targetX:50,targetY:43},
  belly:{buttonY:49,originX:74,targetX:51,targetY:48},
  hips:{buttonY:55,originX:26,targetX:51,targetY:55},
  thigh:{buttonY:69,originX:26,targetX:46,targetY:69},
  calf:{buttonY:82,originX:74,targetX:55,targetY:82}
 };
 const NS='http://www.w3.org/2000/svg';
 function connectors(){
  const buttons=stage.querySelectorAll('.bm-point');
  if(!buttons.length)return;
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
 connectors();

 // The reference has a short row of History / Evolution / Photo actions
 // below the mannequin, not a second mannequin.
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
 const photo=document.getElementById('bm-pick-photo');
 if(photo){
  photo.classList.remove('bm-button');photo.textContent='';
  const ico=document.createElement('span');ico.className='bm-shortcut-icon';ico.textContent='▣';
  photo.append(ico,document.createTextNode('Photo'));
  nav.append(photo);
 }
 stage.insertAdjacentElement('afterend',nav);

 // Color selection is a compact, optional panel; skin/hair/eyes are
 // the ONLY available mannequin appearance controls.
 const toggle=document.createElement('button');
 toggle.type='button';toggle.className='bm-palette-header';
 toggle.textContent='🎨 Personnaliser la peau, les cheveux et les yeux';
 toggle.setAttribute('aria-expanded','false');
 toggle.onclick=()=>{
  palette.hidden=!palette.hidden;
  toggle.setAttribute('aria-expanded',String(!palette.hidden));
 };
 nav.insertAdjacentElement('afterend',toggle);
 palette.hidden=true;
 const latest=document.getElementById('bm-latest');
 if(latest)palette.insertAdjacentElement('afterend',latest);
 // Keep date, all saved measurements, chart and history intact.
 const form=right.querySelector('.bm-card');
 if(form){
  const save=form.querySelector('#bm-save');
  if(save)save.textContent='✓ Enregistrer';
  const title=form.querySelector('h3');
  if(title)title.textContent='▣ Enregistrer les mensurations';
 }
})();
