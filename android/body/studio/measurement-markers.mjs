/* Localised, interactive measurement handles on the MakeHuman 3D figure.
 * The existing validated measurements form remains the ONLY persistence path.
 * The 3D view never writes the profile or backup by itself.
 */
import * as THREE from 'three';
import { REGIONS,validMeasure } from './measurement-morph.mjs';

export function createStudioMarkers({stage,figure,camera,getBounds,getProfile,isActive}){
 const style=document.createElement('style');
 style.id='bm-studio-landmark-style';
 style.textContent=[
 '#body-measurements #bm-model .bm-studio-landmarks{position:absolute!important;inset:0!important;z-index:6!important;pointer-events:none!important}',
 '#body-measurements #bm-model .bm-studio-landmark{position:absolute;min-width:28px;min-height:28px;border-radius:999px;transform:translate(-50%,-50%);background:#073845dd;border:2px solid #a3fbe0;box-shadow:0 0 0 4px #04405766,0 3px 8px #071e2c9c;color:#eafff8;pointer-events:auto!important;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;padding:0}',
 '#body-measurements #bm-model .bm-studio-landmark:focus-visible{outline:3px solid #fff4bb;outline-offset:3px}',
 '#body-measurements #bm-model .bm-studio-landmark[data-selected="true"]{background:#d5f9ed;color:#062f3a;border-color:#fff5bd;z-index:9}',
 '#body-measurements #bm-model .bm-studio-landmark .bm-studio-dot{width:7px;height:7px;background:#fff5b3;border-radius:50%;display:block}',
 '#body-measurements #bm-model .bm-studio-landmark .bm-studio-label{position:absolute;left:32px;background:#092f43ee;color:#f0ffff;border:1px solid #63929c;border-radius:8px;padding:3px 7px;white-space:nowrap;font-size:11px;pointer-events:none;line-height:1.15}',
 '#body-measurements #bm-model .bm-studio-landmark[data-side="left"] .bm-studio-label{left:auto;right:32px}',
 '#body-measurements #bm-model .bm-studio-landmark[hidden]{display:none!important}',
 '#body-measurements .bm-studio-entry{position:absolute;z-index:12;bottom:12px;left:7px;right:7px;background:#0c3047f5;border:1px solid #83d9ce;border-radius:14px;padding:12px;box-shadow:0 12px 35px #0009;color:#e8fff9}',
 '#body-measurements .bm-studio-entry[hidden]{display:none!important}',
 '#body-measurements .bm-studio-entry-title{font-size:14px;font-weight:750;margin-bottom:7px}',
 '#body-measurements .bm-studio-entry-row{display:flex;align-items:center;gap:8px}',
 '#body-measurements .bm-studio-entry input{min-width:0;flex:1 1 auto;max-width:140px;padding:9px;border-radius:9px;border:1px solid #5dabb5;background:#123d52;color:white;font-size:16px;text-align:center}',
 '#body-measurements .bm-studio-entry button{border:1px solid #70cdb8;border-radius:9px;padding:9px 10px;background:#1d6167;color:#ecfffb;min-height:42px;font-size:12px}',
 '#body-measurements .bm-studio-entry .bm-studio-entry-help{font-size:11px;color:#a9d1df;margin-top:7px;line-height:1.4}',
 '@media(max-width:450px){#body-measurements #bm-model .bm-studio-landmark .bm-studio-label{display:none}#body-measurements #bm-model .bm-studio-landmark[data-selected="true"] .bm-studio-label{display:block}}'
 ].join('\n');
 document.head.append(style);

 const layer=document.createElement('div');layer.className='bm-studio-landmarks';
 layer.setAttribute('aria-label','Repères de saisie des mensurations');
 const editor=document.createElement('div');editor.className='bm-studio-entry';editor.hidden=true;
 const heading=document.createElement('div');heading.className='bm-studio-entry-title';
 const row=document.createElement('div');row.className='bm-studio-entry-row';
 const input=document.createElement('input');input.type='number';input.step='.1';input.inputMode='decimal';
 input.setAttribute('aria-label','Mensuration en centimètres');
 const unit=document.createElement('span');unit.textContent='cm';
 const save=document.createElement('button');save.type='button';save.textContent='✓ Enregistrer';
 const cancel=document.createElement('button');cancel.type='button';cancel.textContent='✕';
 cancel.setAttribute('aria-label','Fermer la saisie');
 const help=document.createElement('div');help.className='bm-studio-entry-help';
 help.textContent='Enregistrement dans le tableau et l’historique, pour la date sélectionnée. Le rendu 3D est indicatif.';
 row.append(input,unit,save,cancel);editor.append(heading,row,help);
 stage.append(layer,editor);
 const buttons=new Map();
 let selected='',pendingFocus=false;
 for(const r of REGIONS){
  const button=document.createElement('button');
  button.type='button';button.className='bm-studio-landmark';
  button.setAttribute('aria-label','Renseigner '+r.label);
  button.title='Saisir '+r.label;
  button.dataset.side=r.x<0?'left':'right';
  const dot=document.createElement('span');dot.className='bm-studio-dot';
  const label=document.createElement('span');label.className='bm-studio-label';label.textContent=r.label;
  button.append(dot,label);button.hidden=true;
  button.addEventListener('click',event=>{
   event.preventDefault();event.stopPropagation();
   if(!isActive())return;
   selected=r.key;
   const p=getProfile();
   const target=document.getElementById('bm-'+r.key);
   const editDate=document.getElementById('bm-date');
   if(!target||!editDate||target.disabled){
    help.textContent='Pour modifier ce profil, ouvre sa fiche de mensurations.';
    return;
   }
   heading.textContent=r.label+' · '+editDate.value;
   const value=target.value||p?.measurements?.[r.key];
   input.value=value!==undefined&&value!==null?String(value):'';
   input.min=String(r.min);input.max=String(r.max);
   input.setAttribute('aria-label',r.label+' en centimètres');
   editor.hidden=false;
   for(const [key,el] of buttons)el.dataset.selected=String(key===selected);
   pendingFocus=true;
   requestAnimationFrame(()=>{if(pendingFocus){pendingFocus=false;input.focus({preventScroll:true});input.select();}});
  });
  buttons.set(r.key,button);layer.append(button);
 }
 function close(){
  editor.hidden=true;selected='';
  pendingFocus=false;
  for(const button of buttons.values())button.dataset.selected='false';
 }
 cancel.onclick=close;
 input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();save.click()}else if(e.key==='Escape')close();});
 save.onclick=()=>{
  if(!selected)return;
  const number=Number(input.value.trim().replace(',','.'));
  const r=REGIONS.find(x=>x.key===selected);
  if(!input.value.trim()||!validMeasure(selected,number)){
   help.textContent='Entre une valeur entre '+r.min+' et '+r.max+' cm.';
   input.focus();return;
  }
  const target=document.getElementById('bm-'+selected);
  const submit=document.getElementById('bm-save');
  if(!target||!submit||target.disabled||submit.disabled){
   help.textContent='Saisie indisponible pour ce profil en lecture seule.';return;
  }
  target.value=String(Math.round(number*10)/10);
  target.dispatchEvent(new Event('input',{bubbles:true}));
  submit.click(); // Apply the same date limits, range validation, history & backup.
  const status=document.getElementById('bm-status')?.textContent||'';
  if(status.startsWith('✓')){
   close();
  }else{
   help.textContent=status||'Vérifie les valeurs et la date de la mesure.';
  }
 };
 const keepMounted=()=>{
  if(!layer.isConnected)stage.append(layer);
  if(!editor.isConnected)stage.append(editor);
 };
 new MutationObserver(keepMounted).observe(stage,{childList:true});
 function update(){
  const p=getProfile();
  if(!isActive()||!p||!camera||!figure){
   for(const btn of buttons.values())btn.hidden=true;
   close();return;
  }
  keepMounted();
  const bounds=getBounds();
  const width=stage.clientWidth,height=stage.clientHeight;
  if(width<120||height<120)return;
  camera.updateMatrixWorld(true);
  figure.updateMatrixWorld(true);
  // The marks are anterior. When viewing the back, hide them rather than
  // drawing false anatomical labels over the back of the model.
  const front=Math.cos(figure.rotation.y)>-.18;
  for(const r of REGIONS){
   const button=buttons.get(r.key);
   if(!front){button.hidden=true;continue;}
   const factor=bounds.height/1.75;
   const pos=new THREE.Vector3(r.x*factor,bounds.minY+bounds.height*r.y,r.z*factor);
   pos.applyMatrix4(figure.matrixWorld).project(camera);
   const left=(pos.x*.5+.5)*width,top=(-pos.y*.5+.5)*height;
   const visible=pos.z>-1&&pos.z<1&&left>=15&&left<=width-15&&top>=15&&top<=height-15;
   button.hidden=!visible;
   if(!visible)continue;
   button.style.left=left+'px';button.style.top=top+'px';
   const value=p.measurements?.[r.key];
   button.setAttribute('aria-label',r.label+' : '+(Number.isFinite(value)?value+' centimètres':'non mesurée')+' ; toucher pour modifier');
   button.dataset.selected=String(selected===r.key);
  }
 }
 return {update,close};
}
