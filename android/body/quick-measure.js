/* Tap a measurement label on the mannequin => native-feeling quick entry dialog.
   Saves this measurement immediately instead of scrolling to the long form. */
(() => {
 'use strict';
 const stage=document.getElementById('bm-model');
 const section=document.getElementById('body-measurements');
 if(!stage||!section)return;
 const keys=['chest','arm','waist','belly','hips','thigh','calf','neck','forearm'];
 const labels=['Poitrine','Bras','Taille','Ventre','Hanches / fessier','Cuisse','Mollet','Cou','Avant-bras'];
 let selected=-1;
 const dialog=document.createElement('dialog');
 dialog.id='bm-quick-dialog';
 dialog.style.cssText='border:1px solid #598ba0;background:#102d41;color:#effaff;border-radius:20px;padding:23px;width:min(92vw,380px);max-height:85dvh;box-shadow:0 18px 66px #0009';
 const title=document.createElement('h3');title.style.cssText='margin:0 0 8px;font-size:20px';
 const help=document.createElement('p');help.textContent='Entre la mesure en centimètres. Elle sera enregistrée immédiatement pour la date sélectionnée.';
 help.style.cssText='font-size:13px;color:#b4d3dc;line-height:1.5;margin:0 0 15px';
 const date=document.createElement('div');date.style.cssText='color:#96dfd1;font-size:13px;margin-bottom:14px';
 const input=document.createElement('input');input.type='number';input.step='0.1';input.inputMode='decimal';input.placeholder='Mesure en cm';
 input.style.cssText='display:block;box-sizing:border-box;width:100%;font-size:26px;padding:13px 15px;color:#f1ffff;background:#071e2d;border:1px solid #66b5b4;border-radius:13px';
 const unit=document.createElement('p');unit.textContent='cm';unit.style.cssText='margin:3px 2px 14px;text-align:right;color:#c5dee9;font-size:12px';
 const error=document.createElement('div');error.setAttribute('role','status');error.style.cssText='color:#fac68c;font-size:13px;min-height:18px;margin-bottom:8px';
 const actions=document.createElement('div');actions.style.cssText='display:flex;gap:10px;flex-wrap:wrap';
 const cancel=document.createElement('button');cancel.type='button';cancel.className='secondary';cancel.textContent='Annuler';cancel.style.cssText='flex:1;min-height:44px';
 const saveBtn=document.createElement('button');saveBtn.type='button';saveBtn.className='primary';saveBtn.textContent='✓ Enregistrer';saveBtn.style.cssText='flex:1;min-height:44px;background:#76e7d0;color:#073538;border:0';
 actions.append(cancel,saveBtn);dialog.append(title,help,date,input,unit,error,actions);
 document.body.append(dialog);
 cancel.onclick=()=>dialog.close();
 const save=()=>{
  if(selected<0 || section.hidden)return;
  const source=document.getElementById('bm-'+keys[selected]);
  if(!source){dialog.close();return}
  const n=Number(input.value.trim().replace(',','.'));
  if(!input.value.trim()||!Number.isFinite(n)||n<Number(source.min)||n>Number(source.max)){
   error.textContent='Indique une mesure entre '+source.min+' et '+source.max+' cm.';
   input.focus();return;
  }
  const previous=source.value;
  source.value=String(Math.round(n*10)/10);
  const mainSave=document.getElementById('bm-save');
  if(!mainSave){source.value=previous;error.textContent='Enregistrement indisponible';return}
  mainSave.click();
  const status=document.getElementById('bm-status')?.textContent||'';
  if(!status.startsWith('✓')){error.textContent=status||'Enregistrement impossible';return}
  dialog.close();
  if(typeof message==='function')message(labels[selected]+' : '+n.toLocaleString('fr-FR')+' cm enregistré ✓');
 };
 saveBtn.onclick=save;
 input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();save()}});
 stage.addEventListener('click',event=>{
  const b=event.target?.closest?.('.bm-point');
  if(!b||section.hidden)return;
  const buttons=[...stage.querySelectorAll('.bm-point')];
  const index=buttons.indexOf(b);
  if(index<0||index>=keys.length)return;
  const source=document.getElementById('bm-'+keys[index]);
  if(!source)return;
  event.preventDefault();
  event.stopImmediatePropagation(); // prevents old scroll-to-form behavior
  selected=index;title.textContent='📏 '+labels[index];
  const selectedDate=document.getElementById('bm-date')?.value||'';
  date.textContent=selectedDate ? 'Mesure du '+new Date(selectedDate+'T12:00:00').toLocaleDateString('fr-FR') : '';
  input.min=source.min;input.max=source.max;
  input.value=source.value||'';error.textContent='';
  dialog.showModal();
  input.focus();
  input.select();
 },true);
})();