/* Interactive always-visible 3D landmarks with dashed connector lines.
 * Existing validated form is the only persistence path. No shape estimate is
 * ever recorded as an actual circumference without manual measurement.
 */
import * as THREE from 'three';
import { REGIONS,validMeasure } from './measurement-morph.mjs';
import { layoutLandmarkCallouts } from './landmark-layout.mjs';
import {markerLocalPosition,declutterMarkerPositions} from './landmark-projection.mjs';

export function createStudioMarkers({stage,figure,camera,getBounds,getProfile,isActive}){
 const style=document.createElement('style');
 style.id='bm-studio-landmark-style';
 style.textContent=[
  '#body-measurements #bm-model .bm-studio-leaders{position:absolute!important;inset:0!important;z-index:5!important;pointer-events:none!important;width:100%;height:100%;overflow:visible}',
  '#body-measurements #bm-model .bm-studio-landmarks{position:absolute!important;inset:0!important;z-index:6!important;pointer-events:none!important}',
  '#body-measurements #bm-model .bm-studio-landmark{position:absolute;width:23px;height:23px;border-radius:50%;transform:translate(-50%,-50%);background:#073845e8;border:2px solid #a3fbe0;box-shadow:0 0 0 2px #044057bb;color:#eafff8;pointer-events:auto!important;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;padding:0;min-width:23px;min-height:23px}',
  '#body-measurements #bm-model .bm-studio-landmark .bm-studio-dot{width:7px;height:7px;background:#fff5b3;border-radius:50%;display:block}',
  '#body-measurements #bm-model .bm-studio-callout{position:absolute;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;text-align:left;padding:3px 6px;min-height:34px;border-radius:8px;background:#092f43f5;color:#f0ffff;border:1px solid #639ba3;box-shadow:0 3px 8px #06141daa;pointer-events:auto!important;cursor:pointer;font-size:11px;line-height:1.2;overflow:hidden;white-space:nowrap;touch-action:manipulation}',
  '#body-measurements #bm-model .bm-studio-callout strong{font-size:11px;font-weight:700;overflow:hidden;text-overflow:ellipsis}',
  '#body-measurements #bm-model .bm-studio-callout small{font-size:10px;color:#9bddd0;line-height:1.1}',
  '#body-measurements #bm-model .bm-studio-landmark[data-selected="true"]{background:#1f6467;border-color:#fff5bd;box-shadow:0 0 0 4px #83efd866,0 0 16px 5px #a3fbe077;z-index:9}',
  '#body-measurements #bm-model .bm-studio-callout[data-selected="true"]{background:#1f6467;border-color:#fff5bd;z-index:9}',
  '#body-measurements #bm-model .bm-studio-landmark:focus-visible,#body-measurements #bm-model .bm-studio-callout:focus-visible{outline:3px solid #fff4bb;outline-offset:2px}',
  '#body-measurements #bm-model .bm-studio-landmark[hidden],#body-measurements #bm-model .bm-studio-callout[hidden]{display:none!important}',
  '#body-measurements .bm-studio-entry{position:absolute;z-index:12;bottom:12px;left:7px;right:7px;background:#0c3047f5;border:1px solid #83d9ce;border-radius:14px;padding:12px;box-shadow:0 12px 35px #0009;color:#e8fff9}',
  '#body-measurements .bm-studio-entry[hidden]{display:none!important}',
  '#body-measurements .bm-studio-entry-title{font-size:14px;font-weight:750;margin-bottom:7px}',
  '#body-measurements .bm-studio-entry-row{display:flex;align-items:center;gap:8px}',
  '#body-measurements .bm-studio-entry input{min-width:0;flex:1 1 auto;max-width:140px;padding:9px;border-radius:9px;border:1px solid #5dabb5;background:#123d52;color:white;font-size:16px;text-align:center}',
  '#body-measurements .bm-studio-entry button{border:1px solid #70cdb8;border-radius:9px;padding:9px 10px;background:#1d6167;color:#ecfffb;min-height:42px;font-size:12px}',
  '#body-measurements .bm-studio-entry .bm-studio-entry-help{font-size:11px;color:#a9d1df;margin-top:7px;line-height:1.4}'
 ].join('\n');
 document.head.append(style);
 const ns='http://www.w3.org/2000/svg';
 const leaders=document.createElementNS(ns,'svg');leaders.classList.add('bm-studio-leaders');
 leaders.setAttribute('aria-hidden','true');
 const layer=document.createElement('div');layer.className='bm-studio-landmarks';
 layer.setAttribute('aria-label','Repères permanents des mensurations');
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
 help.textContent='Seule une mesure saisie manuellement et enregistrée est ajoutée à l’historique.';
 row.append(input,unit,save,cancel);editor.append(heading,row,help);
 stage.append(leaders,layer,editor);
 const buttons=new Map(),tags=new Map(),paths=new Map();
 let selected='',pendingFocus=false;
 function select(key){
  selected=key;
  for(const [other,button] of buttons)button.dataset.selected=String(other===key);
  for(const [other,button] of tags)button.dataset.selected=String(other===key);
 }
 function openEditor(r,event){
  event?.preventDefault();event?.stopPropagation();
  if(!isActive())return;
  const p=getProfile(),target=document.getElementById('bm-'+r.key);
  const editDate=document.getElementById('bm-date');
  if(!target||!editDate||target.disabled){
   help.textContent='Pour modifier ce profil, ouvre sa fiche de mensurations.';
   return;
  }
  select(r.key);
  heading.textContent=r.label+' · '+editDate.value;
  const value=target.value||p?.measurements?.[r.key];
  input.value=value!==undefined&&value!==null?String(value):'';
  input.min=String(r.min);input.max=String(r.max);
  input.setAttribute('aria-label',r.label+' en centimètres');
  help.textContent='Seule une mesure saisie et enregistrée est ajoutée à l’historique.';
  editor.hidden=false;pendingFocus=true;
  requestAnimationFrame(()=>{if(pendingFocus){pendingFocus=false;input.focus({preventScroll:true});input.select();}});
 }
 for(const r of REGIONS){
  const dot=document.createElement('button');dot.type='button';dot.className='bm-studio-landmark';
  dot.title='Saisir '+r.label;dot.hidden=true;
  const middle=document.createElement('span');middle.className='bm-studio-dot';dot.append(middle);
  const tag=document.createElement('button');tag.type='button';tag.className='bm-studio-callout';tag.hidden=true;
  const strong=document.createElement('strong');strong.textContent=r.label;
  const small=document.createElement('small');small.textContent='— cm';
  tag.append(strong,small);
  dot.addEventListener('click',event=>openEditor(r,event));
  tag.addEventListener('click',event=>openEditor(r,event));
  const polyline=document.createElementNS(ns,'polyline');
  polyline.setAttribute('stroke','#a4f2db');polyline.setAttribute('stroke-width','1.5');
  polyline.setAttribute('stroke-dasharray','4 4');polyline.setAttribute('stroke-linecap','round');
  polyline.setAttribute('fill','none');
  leaders.append(polyline);
  layer.append(dot,tag);buttons.set(r.key,dot);tags.set(r.key,tag);paths.set(r.key,polyline);
 }
 function close(){
  editor.hidden=true;selected='';pendingFocus=false;
  for(const button of buttons.values())button.dataset.selected='false';
  for(const tag of tags.values())tag.dataset.selected='false';
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
  const target=document.getElementById('bm-'+selected),submit=document.getElementById('bm-save');
  if(!target||!submit||target.disabled||submit.disabled){
   help.textContent='Saisie indisponible pour ce profil en lecture seule.';return;
  }
  target.value=String(Math.round(number*10)/10);
  target.dispatchEvent(new Event('input',{bubbles:true}));
  submit.click();
  const status=document.getElementById('bm-status')?.textContent||'';
  if(status.startsWith('✓'))close();
  else help.textContent=status||'Vérifie les valeurs et la date de la mesure.';
 };
 const keepMounted=()=>{
  if(!leaders.isConnected)stage.append(leaders);
  if(!layer.isConnected)stage.append(layer);
  if(!editor.isConnected)stage.append(editor);
 };
 new MutationObserver(keepMounted).observe(stage,{childList:true});
 function update(){
  const p=getProfile();
  if(!isActive()||!p||!camera||!figure){
   for(const btn of buttons.values())btn.hidden=true;
   for(const tag of tags.values())tag.hidden=true;
   leaders.style.display='none';close();return;
  }
  keepMounted();leaders.style.display='';
  const bounds=getBounds(),width=stage.clientWidth,height=stage.clientHeight;
  if(width<120||height<120)return;
  leaders.setAttribute('viewBox','0 0 '+width+' '+height);
  camera.updateMatrixWorld(true);figure.updateMatrixWorld(true);
  const items=[];
  for(const r of REGIONS){
   const local=markerLocalPosition(r,bounds,p.visualRatios||{},figure.rotation.y);
   const pos=new THREE.Vector3(...local);
   pos.applyMatrix4(figure.matrixWorld).project(camera);
   const x=(pos.x*.5+.5)*width,y=(-pos.y*.5+.5)*height;
   const dot=buttons.get(r.key),tag=tags.get(r.key);
   if(!Number.isFinite(x)||!Number.isFinite(y)||pos.z<=-1||pos.z>=1){
    dot.hidden=true;tag.hidden=true;paths.get(r.key).setAttribute('points','');continue;
   }
   const px=Math.max(13,Math.min(width-13,x));
   const py=Math.max(13,Math.min(height-13,y));
   dot.hidden=false;
   const value=p.visualMeasurements?.[r.key];
   const fmt=Number.isFinite(value)?(p.measurementMode==='estimated'?'≈ ':'')+
    value.toLocaleString('fr-FR',{maximumFractionDigits:1})+' cm':'— cm';
   tag.querySelector('small').textContent=fmt;
   const note=p.measurementMode==='estimated'?' estimation visuelle, non mesurée':'';
   const title=r.label+' : '+fmt+note+' ; toucher pour modifier';
   dot.setAttribute('aria-label',title);tag.setAttribute('aria-label',title);
   selectMarkerState(r.key,dot,tag);
   // Alternate label lanes left/right; markers stay at their projected points.
   items.push({key:r.key,side:r.x<0?'left':'right',x:px,y:py});
  }
  const clean=declutterMarkerPositions(items,width,height);
  for(const item of clean){
   const dot=buttons.get(item.key);
   dot.style.left=item.x+'px';dot.style.top=item.y+'px';
  }
  const placements=layoutLandmarkCallouts(clean,width,height,{
   labelWidth:width<330?91:103,labelHeight:34,gap:6
  });
  for(const place of placements){
   const tag=tags.get(place.key);tag.hidden=false;
   tag.style.left=place.left+'px';tag.style.top=place.top+'px';
   tag.style.width=place.width+'px';tag.style.height=place.height+'px';
   const bend=place.side==='left'?place.connectorX+8:place.connectorX-8;
   const gap=Math.hypot(place.x-place.anchorX,place.y-place.anchorY);
   paths.get(place.key).setAttribute('points',
    place.connectorX+','+place.connectorY+' '+bend+','+place.connectorY+
    ' '+place.x+','+place.y+
    (gap>3?' '+place.anchorX+','+place.anchorY:''));
  }
 }
 function selectMarkerState(key,dot,tag){
  const selectedState=String(selected===key);
  dot.dataset.selected=selectedState;tag.dataset.selected=selectedState;
 }
 return {update,close};
}
