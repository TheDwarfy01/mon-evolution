#!/usr/bin/env python3
"""v1.6.75: private per-profile treatment log and annotated weight curves."""
from pathlib import Path

path=Path("android/source-1.6.75/app/src/main/assets/index.html")
src=path.read_text(encoding="utf-8")
assert src.count("</body></html>")==1
assert 'mon-evolution-treatments-175' not in src

def once(old,new):
 global src
 count=src.count(old)
 if count!=1:
  raise AssertionError(f"Treatments patch: expected one anchor, got {count}: {old[:100]!r}")
 src=src.replace(old,new,1)

# Keep existing graph, zoom and pinch; extend its SVG draw in place.
once(
 " const p=profile(),metres=Math.max(.5,Number(p.height)/100||1.7);",
 """ const p=profile(),metres=Math.max(.5,Number(p.height)/100||1.7);
 const treatmentEvents=treatmentCheck.checked&&Array.isArray(p.treatments)
  ?p.treatments.filter(e=>e&&typeof e.name==='string'&&/^\\d{4}-\\d{2}-\\d{2}$/.test(e.date)&&['injection','change','stop'].includes(e.kind)).slice(0,1000)
   .sort((a,b)=>a.date.localeCompare(b.date)||String(a.id).localeCompare(String(b.id)))
  :[];"""
)
once(
 "panel.append(heading,tabs,toolbar,plot,pointInfo,zoneLegend,zoomHelp,leg,info);",
 """ panel.append(heading,tabs,toolbar,plot,pointInfo,zoneLegend,zoomHelp,leg,info);
 const treatmentSwitch=document.createElement('label');treatmentSwitch.className='treatment-graph-switch';
 const treatmentCheck=document.createElement('input');treatmentCheck.type='checkbox';treatmentCheck.checked=true;
 const treatmentLabel=document.createElement('span');treatmentLabel.textContent='Afficher traitements et injections';
 treatmentSwitch.append(treatmentCheck,treatmentLabel);
 panel.insertBefore(treatmentSwitch,plot);
 treatmentCheck.onchange=()=>{pinchViewport=null;update()};"""
)
once(
 " svg.append(dataLayer);\n for(let i=0;i<5;i++){",
 """ // Zones chronologiques : première administration, changement de dose, arrêt.
 if(treatmentEvents.length){
  const byName=new Map();
  for(const item of treatmentEvents){
   const key=item.name.trim().toLocaleLowerCase('fr-FR');
   if(!byName.has(key))byName.set(key,[]);
   byName.get(key).push(item);
  }
  let phaseNumber=0;
  for(const items of byName.values()){
   let active=null;
   const paintPhase=(entry,endTime)=>{
    const left=Math.max(v.xMin,ts(entry.date));
    const right=Math.min(v.xMax,endTime,last.t);
    if(right<=left)return;
    const colors=['#b39bff','#88bbe7','#d4a4e6','#bfa4ff'];
    const area=svgElement('rect',{x:X(left),y:T,width:Math.max(0,X(right)-X(left)),
       height:chartH,fill:colors[phaseNumber++%colors.length],'fill-opacity':'.17'});
    const title=svgElement('title');title.textContent='Période '+entry.name+' · '+entry.dose+' '+(entry.unit||'mg');
    area.append(title);dataLayer.append(area);
    if(X(right)-X(left)>78){
     const label=svgElement('text',{x:X(left)+5,y:T+14,fill:'#f5eaff','font-size':9});
     label.textContent=(entry.name+' '+entry.dose+' '+(entry.unit||'mg')).slice(0,23);
     dataLayer.append(label);
    }
   };
   for(const item of items){
    if(item.kind==='stop'){
     if(active)paintPhase(active,ts(item.date));
     active=null;continue;
    }
    if(!active){active=item;continue;}
    if(item.kind==='change'||Number(item.dose)!==Number(active.dose)||String(item.unit)!==String(active.unit)){
     paintPhase(active,ts(item.date));active=item;
    }
   }
   if(active)paintPhase(active,last.t);
  }
 }
 svg.append(dataLayer);
 for(let i=0;i<5;i++){"""
)
once(
 " if(pts.length>1)dataLayer.append(svgElement('polyline',{",
 """ // Lignes verticales interactives : injection, changement ou arrêt.
 for(const event of treatmentEvents){
  const t=ts(event.date);
  if(t<v.xMin||t>v.xMax)continue;
  const x=X(t);
  const color=event.kind==='stop'?'#ff9e99':event.kind==='change'?'#ffd18d':'#ddaaff';
  dataLayer.append(svgElement('line',{x1:x,x2:x,y1:T,y2:T+chartH,
   stroke:color,'stroke-width':event.kind==='change'?2:1.6,
   'stroke-dasharray':event.kind==='injection'?'4 5':'6 3','stroke-opacity':'.9'}));
  const detail=event.name+(event.kind==='stop'?' · Arrêt':
    ' · '+event.dose+' '+(event.unit||'mg')+(event.kind==='change'?' · Changement':' · Injection'));
  const dateLabel=new Date(t).toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'});
  const hit=svgElement('rect',{x:x-7,y:T,width:14,height:chartH,fill:'transparent',style:'cursor:pointer'});
  hit.addEventListener('click',()=>{pointInfo.textContent=dateLabel+' · '+detail+(event.note?' · '+event.note:'')});
  const tip=svgElement('title');tip.textContent=dateLabel+' · '+detail+(event.note?' · '+event.note:'');
  hit.append(tip);dataLayer.append(hit);
 }
 if(pts.length>1)dataLayer.append(svgElement('polyline',{"""
)
once(
 " setLegend(kind,adult,!!extra);\n}",
 """ setLegend(kind,adult,!!extra);
 if(treatmentEvents.length){
  const item=document.createElement('span');item.className='evo-v160-legend-item';
  const key=document.createElement('i');key.className='evo-v160-key';key.style.backgroundColor='#b39bff';
  const name=document.createElement('span');name.textContent='Traitements : zones = doses, traits verticaux = événements';
  item.append(key,name);zoneLegend.append(item);
 }
}"""
)
addon=r'''
<style id="mon-evolution-treatments-175">
#treatment-card{margin-top:18px}
#treatment-card .treatment-intro{line-height:1.5}
#treatment-card .treatment-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#treatment-card .treatment-fields .field{min-width:0;margin:7px 0}
#treatment-card input,#treatment-card select{min-width:0}
#treatment-card .treatment-list{margin-top:14px}
#treatment-card .treatment-event{border:1px solid #3b5e72;background:#10283c;border-radius:12px;padding:12px;margin:9px 0}
#treatment-card .treatment-event strong{display:block;color:#eafaff;font-size:14px;overflow-wrap:anywhere}
#treatment-card .treatment-event small{display:block;color:#acd1df;font-size:12px;line-height:1.5;margin-top:5px}
#treatment-card .treatment-event .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
#treatment-card .treatment-event .actions button{flex:1;min-width:110px;padding:9px;font-size:12px}
#treatment-card .treatment-buttons{display:flex;gap:9px;margin:13px 0}
#treatment-card .treatment-buttons button{flex:1;min-width:0;padding:12px}
.treatment-graph-switch{display:flex;align-items:center;gap:10px;margin:6px 0 12px;font-size:12px;color:#d5eff5}
.treatment-graph-switch input{width:19px;height:19px;flex:0 0 19px;margin:0;accent-color:#bd9dff}
@media(max-width:360px){#treatment-card .treatment-fields{gap:7px}}
</style>
<script>
(function(){
'use strict';
const section=document.getElementById('profiles');
const backup=document.getElementById('drive-state')?.closest('.card');
if(!section||!backup||typeof profile!=='function'||typeof save!=='function')return;
const card=document.createElement('section');card.className='card';card.id='treatment-card';
card.innerHTML=[
 '<h3>💊 Traitements</h3>',
 '<p class="notice treatment-intro">Historique privé du profil. Enregistre les injections, changements de dose ou arrêts. Les événements s’affichent sur la courbe du poids.</p>',
 '<form id="treatment-form">',
 '<label class="field">Nom du traitement<input id="treatment-name" maxlength="80" required placeholder="Nom du traitement" autocomplete="off"></label>',
 '<div class="treatment-fields">',
 '<label class="field">Événement<select id="treatment-kind"><option value="injection">Injection / prise</option><option value="change">Début / changement</option><option value="stop">Arrêt</option></select></label>',
 '<label class="field">Date<input id="treatment-date" type="date" required></label>',
 '</div><div class="treatment-fields">',
 '<label class="field">Dose<input id="treatment-dose" type="number" min="0.001" step="any" required placeholder="Ex. 2,5"></label>',
 '<label class="field">Unité<select id="treatment-unit"><option value="mg">mg</option><option value="µg">µg</option><option value="mL">mL</option><option value="UI">UI</option><option value="comprimé(s)">comprimé(s)</option><option value="autre">autre</option></select></label>',
 '</div><label class="field">Note (facultatif)<input id="treatment-note" maxlength="160" placeholder="Ex. site d’injection, information personnelle"></label>',
 '<div class="treatment-buttons">',
 '<button type="submit" class="primary" id="treatment-submit">＋ Enregistrer</button>',
 '<button type="button" class="secondary" id="treatment-cancel" hidden>Annuler</button>',
 '</div></form><div class="treatment-list" id="treatment-list" aria-live="polite"></div>',
 '<p class="notice">Données incluses dans la sauvegarde privée du profil, non transmises dans les profils partagés. Cette chronologie n’indique pas l’effet médical d’un traitement.</p>'
].join('');
section.insertBefore(card,backup);
const get=id=>document.getElementById(id);
const form=get('treatment-form'),kind=get('treatment-kind'),dose=get('treatment-dose'),unit=get('treatment-unit');
const list=get('treatment-list'),submit=get('treatment-submit'),cancel=get('treatment-cancel');
let editId=null,editingProfileId=null;
const kindName={injection:'Injection / prise',change:'Début / changement',stop:'Arrêt'};
function treatments(){
 const p=profile();
 if(!Array.isArray(p.treatments))p.treatments=[];
 return p.treatments;
}
function reset(){
 form.reset();editId=null;editingProfileId=null;
 get('treatment-date').max=dateNow();
 get('treatment-date').value=dateNow();
 submit.textContent='＋ Enregistrer';cancel.hidden=true;
 updateKind();
}
function updateKind(){
 const stopped=kind.value==='stop';
 dose.disabled=stopped;unit.disabled=stopped;dose.required=!stopped;
 dose.closest('label').style.opacity=stopped?'.45':'1';
 unit.closest('label').style.opacity=stopped?'.45':'1';
}
kind.addEventListener('change',updateKind);
cancel.onclick=reset;
function display(){
 const p=profile();const events=Array.isArray(p.treatments)?p.treatments:[];
 list.replaceChildren();
 if(editingProfileId&&editingProfileId!==p.id)reset();
 if(!events.length){
  const empty=document.createElement('p');empty.className='notice';
  empty.textContent='Aucun traitement enregistré pour ce profil.';
  list.append(empty);return;
 }
 const heading=document.createElement('strong');
 heading.textContent='Historique · '+events.length+' événement'+(events.length>1?'s':'');
 list.append(heading);
 for(const e of [...events].sort((a,b)=>b.date.localeCompare(a.date)||String(b.id).localeCompare(String(a.id)))){
  const item=document.createElement('div');item.className='treatment-event';
  const title=document.createElement('strong');
  title.textContent=e.name+' · '+(kindName[e.kind]||'Événement');
  const sub=document.createElement('small');
  const dayLabel=new Date(e.date+'T12:00:00').toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'});
  sub.textContent=dayLabel+(e.kind==='stop'?'':' · '+e.dose+' '+e.unit)+(e.note?' · '+e.note:'');
  const actions=document.createElement('div');actions.className='actions';
  const edit=document.createElement('button');edit.type='button';edit.className='secondary';edit.textContent='✎ Modifier';
  edit.onclick=()=>{
   editId=String(e.id);editingProfileId=p.id;
   get('treatment-name').value=e.name;kind.value=e.kind;
   get('treatment-date').value=e.date;dose.value=e.dose||'';unit.value=e.unit||'mg';
   get('treatment-note').value=e.note||'';
   updateKind();submit.textContent='✓ Enregistrer la modification';cancel.hidden=false;
   card.scrollIntoView({behavior:'smooth',block:'start'});
  };
  const remove=document.createElement('button');remove.type='button';remove.className='secondary';remove.textContent='🗑 Supprimer';
  remove.onclick=()=>{
   if(!confirm('Supprimer cet événement de traitement ?'))return;
   p.treatments=treatments().filter(row=>String(row.id)!==String(e.id));
   if(editId===String(e.id))reset();
   save();render();
  };
  actions.append(edit,remove);item.append(title,sub,actions);list.append(item);
 }
}
form.onsubmit=e=>{
 e.preventDefault();
 const p=profile(),name=get('treatment-name').value.trim();
 const date=get('treatment-date').value,action=kind.value;
 const value=Number(dose.value);
 if(!name||name.length>80||!/^\d{4}-\d{2}-\d{2}$/.test(date)||date>dateNow()){
  alert('Vérifie le nom et la date (pas dans le futur).');return;
 }
 if(action!=='stop'&&(!Number.isFinite(value)||value<=0||value>100000)){
  alert('Entre une dose positive valide.');return;
 }
 if(editId&&p.id!==editingProfileId){alert('Le profil a changé. Recommence la saisie.');reset();return;}
 const event={id:editId||('t'+Date.now()+'_'+Math.random().toString(36).slice(2,7)),
  name,date,kind:action,dose:action==='stop'?null:value,
  unit:action==='stop'?'':unit.value,
  note:get('treatment-note').value.trim()};
 if(treatments().length>=1000&&!editId){alert('Limite de 1000 événements par profil.');return;}
 if(editId){
  const index=p.treatments.findIndex(row=>String(row.id)===editId);
  if(index<0){alert('Événement introuvable.');reset();return;}
  p.treatments[index]=event;
 }else p.treatments.push(event);
 reset();save();render();message('Traitement enregistré ✓');
};
const priorRender=render;
render=function(){const result=priorRender();display();return result};
reset();display();
})();
</script>
'''
src=src.replace("</body></html>",addon+"\n</body></html>")
assert "mon-evolution-treatments-175" in src
assert "treatmentEvents" in src and "treatment-graph-switch" in src
assert "p.treatments" in src and "treatment-list" in src
path.write_text(src,encoding="utf-8")
print('OK v1.6.75: traitements, doses, périodes et injections sur la courbe')
