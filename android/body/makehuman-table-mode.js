/* Mon Évolution IMC — sans moteur 3D : tableau de mensurations.
 * Le rendu 3D n'apparaît que si le module MakeHuman a été activé.
 */
(()=>{
'use strict';
const root=document.getElementById('body-measurements');
const layout=document.getElementById('bm-main');
const stage=document.getElementById('bm-model');
const fields=document.getElementById('bm-fields');
if(!root||!layout||!stage||!fields)return;
const left=layout.querySelector(':scope > .bm-card');
const right=layout.querySelector(':scope > .bm-ref-side');
if(!left||!right)return;
const css=document.createElement('style');css.id='bm-table-only-mode';
css.textContent=[
 '#body-measurements #bm-models,',
 '#body-measurements #bm-model svg.bm-man,',
 '#body-measurements #bm-model canvas.bm-photo-canvas,',
 '#body-measurements #bm-model .bm-photo-error,',
 '#body-measurements #bm-model .bm-point,',
 '#body-measurements #bm-model .bm-measure-lines {display:none!important;}',
 '#body-measurements #bm-model{display:none!important;}',
 '#body-measurements #bm-model.bm-makehuman-active{display:block!important;height:min(70vh,540px)!important;background:linear-gradient(150deg,#0b3046,#123b49)!important;}',
 '#body-measurements #bm-main.bm-table-only{display:grid!important;grid-template-columns:minmax(0,1fr)!important;gap:12px!important;}',
 '#body-measurements #bm-main.bm-table-only > .bm-card{display:none!important;}',
 '#body-measurements #bm-main.bm-table-only .bm-ref-side{width:100%;min-width:0;}',
 '#body-measurements #bm-main.bm-table-only .bm-ref-side > .bm-card{width:100%;min-width:0;}',
 '#body-measurements #bm-main:not(.bm-table-only){display:grid!important;grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr)!important;}',
 '#body-measurements .bm-table-heading{display:grid;grid-template-columns:minmax(0,1fr) minmax(96px,36%);gap:12px;padding:9px 11px;background:#16455a;border:1px solid #39657a;border-radius:10px 10px 0 0;font-size:12px;font-weight:750;color:#dffdfa;}',
 '#body-measurements #bm-fields{display:grid!important;grid-template-columns:minmax(0,1fr)!important;gap:0!important;border:1px solid #39657a;border-top:0;border-radius:0 0 10px 10px;overflow:hidden;}',
 '#body-measurements #bm-fields label{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(96px,36%);align-items:center;gap:12px;margin:0;padding:8px 11px;border-bottom:1px solid #284c61;font-size:13px;line-height:1.3;}',
 '#body-measurements #bm-fields label:nth-child(even){background:#18384b66;}',
 '#body-measurements #bm-fields label:last-child{border-bottom:0;}',
 '#body-measurements #bm-fields label input{margin:0!important;max-width:100%;min-height:40px;text-align:right;}',
 '#body-measurements .bm-mh-panel{margin:9px 0 15px;padding:10px 8px;min-height:46px;border-radius:12px;background:#14354a;border:1px solid #36667a;}',
 '#body-measurements .bm-mh-panel button{min-height:38px;}',
 '#body-measurements #bm-main.bm-table-only .bm-palette-header,',
 '#body-measurements #bm-main.bm-table-only #bm-colors,',
 '#body-measurements #bm-main.bm-table-only .bm-silhouette-shortcuts{display:none!important;}',
 '@media(max-width:780px){#body-measurements #bm-main:not(.bm-table-only){grid-template-columns:1fr!important;}#body-measurements #bm-model.bm-makehuman-active{height:min(66vh,515px)!important;}}'
].join('\n');
document.head.append(css);
const title=root.querySelector('.bm-title');
if(title&&title.parentElement===left)root.insertBefore(title,layout);
const tableHead=document.createElement('div');
tableHead.className='bm-table-heading';tableHead.setAttribute('aria-hidden','true');
const c1=document.createElement('span');c1.textContent='Partie du corps';
const c2=document.createElement('span');c2.textContent='Valeur (cm)';
tableHead.append(c1,c2);fields.before(tableHead);
const panel=root.querySelector('.bm-mh-panel');
const formCard=fields.closest('.bm-card');
if(panel&&formCard){const h=formCard.querySelector('h3');if(h)h.after(panel);else formCard.prepend(panel);}
const heading=left.querySelector('h3');
if(heading)heading.textContent='Silhouette morphologique 3D';
const caption=left.querySelector('.bm-hint');
if(caption)caption.textContent='Silhouette indicative liée aux mesures du profil. Fais-la pivoter avec le doigt.';
function sync(){
 const active=stage.classList.contains('bm-makehuman-active')
     &&!!stage.querySelector('canvas.bm-makehuman-canvas');
 layout.classList.toggle('bm-table-only',!active);
 if(panel&&formCard&&!formCard.contains(panel)){
  const h=formCard.querySelector('h3');if(h)h.after(panel);else formCard.prepend(panel);
 }
}
new MutationObserver(sync).observe(stage,{attributes:true,attributeFilter:['class'],childList:true});
window.addEventListener('mon-evolution-makehuman-ready',()=>requestAnimationFrame(sync));
window.addEventListener('mon-evolution-appearance-changed',()=>requestAnimationFrame(sync));
sync();
})();