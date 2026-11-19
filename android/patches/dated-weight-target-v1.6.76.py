#!/usr/bin/env python3
"""v1.6.76: dated weight target and real-vs-target graphs and statistics."""
from pathlib import Path
page=Path("android/source-1.6.76/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
assert s.count("</body></html>")==1
assert "mon-evolution-goal-plan-176" not in s

def once(old,new):
 global s
 n=s.count(old)
 if n!=1:
  raise AssertionError(f"Target plan anchor count={n}: {old[:125]!r}")
 s=s.replace(old,new,1)

# Main chart: interactive, optional dated goal line over real measurements.
once(
 " panel.insertBefore(treatmentSwitch,plot);",
 """ panel.insertBefore(treatmentSwitch,plot);
 const goalSwitch=document.createElement('label');goalSwitch.className='goal-graph-switch';
 const goalCheck=document.createElement('input');goalCheck.type='checkbox';goalCheck.checked=true;
 const goalLabel=document.createElement('span');goalLabel.textContent='Afficher la trajectoire de mon objectif';
 goalSwitch.append(goalCheck,goalLabel);
 panel.insertBefore(goalSwitch,plot);
 goalCheck.onchange=()=>{pinchViewport=null;update()};"""
)
once(
 " const unit=kind==='bmi'?'IMC':'kg';",
 """ const unit=kind==='bmi'?'IMC':'kg';
 const scheduledGoal=window.MonEvolutionGoal?.get?.(p)||null;
 const goalChartVisible=!!(goalCheck.checked&&scheduledGoal);"""
)
once(
 " if(extra)values.push(extra.v);",
 """ if(extra)values.push(extra.v);
 if(goalChartVisible){
  const scale=kind==='bmi'?1/(metres*metres):1;
  values.push(scheduledGoal.weight*scale,scheduledGoal.startWeight*scale);
 }"""
)
once(
 " const b={xMin:pts[0].t,xMax:Math.max(pts[0].t+86400000,extra?.t||last.t),",
 """ const b={xMin:pts[0].t,xMax:Math.max(pts[0].t+86400000,extra?.t||last.t,goalChartVisible?ts(scheduledGoal.date):0),"""
)
once(
 " if(pts.length>1)dataLayer.append(svgElement('polyline',{",
 """ if(goalChartVisible){
  const scale=kind==='bmi'?1/(metres*metres):1;
  const begin=ts(scheduledGoal.startDate),finish=ts(scheduledGoal.date);
  const x0=X(begin),x1=X(finish);
  const y0=Y(scheduledGoal.startWeight*scale),y1=Y(scheduledGoal.weight*scale);
  const trajectory=svgElement('line',{x1:x0,y1:y0,x2:x1,y2:y1,
   stroke:'#f4d17a','stroke-width':2.7,'stroke-dasharray':'9 5'});
  const trajectoryTip=svgElement('title');
  trajectoryTip.textContent='Objectif : '+fmt(scheduledGoal.weight)+' kg le '+scheduledGoal.date;
  trajectory.append(trajectoryTip);dataLayer.append(trajectory);
  const targetPoint=svgElement('circle',{cx:x1,cy:y1,r:5.4,fill:'#f4d17a'});
  const targetTip=svgElement('title');
  targetTip.textContent='Cible '+scheduledGoal.date+' : '+fmt(scheduledGoal.weight)+' kg';
  targetPoint.append(targetTip);dataLayer.append(targetPoint);
 }
 if(pts.length>1)dataLayer.append(svgElement('polyline',{"""
)
once(
 " setLegend(kind,adult,!!extra);",
 """ setLegend(kind,adult,!!extra);
 if(goalChartVisible){
  const item=document.createElement('span');item.className='evo-v160-legend-item';
  const key=document.createElement('i');key.className='evo-v160-key';key.style.backgroundColor='#f4d17a';
  const label=document.createElement('span');label.textContent='Objectif daté · ligne dorée pointillée';
  item.append(key,label);zoneLegend.append(item);
 }"""
)
# Advanced-weight analysis p is an intentionally normalized copy of the active
# profile, so carry only the three target-plan fields into that local copy.
once(
 "sex:p.sex||'',rows:unique};",
 "sex:p.sex||'',goalDate:p.goalDate||'',goalStartDate:p.goalStartDate||'',goalStartWeight:p.goalStartWeight,rows:unique};"
)
once(
 "  const sl=slope(p);",
 """  const goalPlan=window.MonEvolutionGoal?.get?.(p)||null;
  if(goalPlan){
   series.push({label:'Trajectoire de l’objectif daté',color:'#f4d17a',dashed:true,thin:false,
    points:[{x:days(origin,goalPlan.startDate),y:goalPlan.startWeight},
            {x:days(origin,goalPlan.date),y:goalPlan.weight}]});
  }
  const sl=slope(p);"""
)
# Do not lose the goal target when advanced graph draws a short selected period.
# Its graph renderer clips to the chosen x-range when it needs to.
once(
 "  const maxWindow=windowSize===null?undefined:wEnd+Math.min(21,windowSize/4);",
 """  const maxWindow=windowSize===null?undefined:Math.max(wEnd+Math.min(21,windowSize/4),
   goalPlan?days(origin,goalPlan.date):wEnd);"""
)

addon=r'''
<style id="mon-evolution-goal-plan-176">
#goal-plan-edit{margin:14px 0 5px;padding:12px;border:1px solid #3e6778;border-radius:13px;background:#0e2839}
#goal-plan-edit h4{margin:0 0 4px;font-size:15px;color:#e0f6fa}
#goal-plan-edit .two{gap:10px}
#goal-plan-edit .field{min-width:0;margin:7px 0}
#goal-plan-edit input{min-width:0}
.goal-graph-switch{display:flex;align-items:center;gap:10px;margin:7px 0 12px;font-size:12px;color:#d5eff5}
.goal-graph-switch input{width:19px;height:19px;flex:0 0 19px;margin:0;accent-color:#f4d17a}
#goal-plan-summary{margin-top:15px;border-top:1px solid #456579;padding-top:13px}
#goal-plan-summary .goal-plan-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#goal-plan-summary .goal-plan-tile{border:1px solid #3d6278;background:#102a3e;border-radius:12px;padding:12px;min-width:0}
#goal-plan-summary .goal-plan-tile small{display:block;color:#b7ceda;font-size:11px}
#goal-plan-summary .goal-plan-tile strong{display:block;color:#f0f7fc;font-size:16px;margin-top:4px;overflow-wrap:anywhere}
#goal-plan-summary h4{font-size:15px;margin:0 0 11px}
#goal-plan-summary .goal-plan-info{font-size:12px;color:#b1d1dc;line-height:1.5;margin:11px 0 0}
</style>
<script>
(function(){
'use strict';
const editGoal=document.getElementById('edit-goal');
const reference=document.getElementById('edit-sex');
const saveButton=document.getElementById('save-profile');
const summary=document.getElementById('evo-v159-summary');
if(!editGoal||!reference||!saveButton||!summary)return;
const oldLabel=editGoal.closest('label');
const referenceRow=reference.closest('.two');
if(!oldLabel||!referenceRow)return;
const box=document.createElement('div');box.id='goal-plan-edit';
const title=document.createElement('h4');title.textContent='🎯 Objectif de poids';
const help=document.createElement('p');help.className='notice';
help.textContent='Définis un poids cible et une date pour comparer le parcours prévu aux pesées réelles.';
help.style.margin='4px 0 10px';
const fields=document.createElement('div');fields.className='two';
oldLabel.firstChild.textContent='Poids cible (kg)';
const dateLabel=document.createElement('label');dateLabel.className='field';dateLabel.textContent='Date cible';
const dateInput=document.createElement('input');dateInput.id='edit-goal-date';dateInput.type='date';
dateLabel.append(dateInput);
fields.append(oldLabel,dateLabel);box.append(title,help,fields);
referenceRow.after(box);
const summaryBlock=document.createElement('div');summaryBlock.id='goal-plan-summary';
summaryBlock.hidden=true;summary.append(summaryBlock);

const DAY=86400000;
const dayTime=d=>Date.parse(d+'T12:00:00Z');
const validDate=d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)
 &&Number.isFinite(dayTime(d))&&new Date(dayTime(d)).toISOString().slice(0,10)===d;
const localeDate=d=>new Date(dayTime(d)).toLocaleDateString('fr-FR',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
const number=v=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:1,maximumFractionDigits:1});
const newest=p=>(p.entries||[]).filter(e=>validDate(e.date)&&Number.isFinite(e.weight))
 .sort((a,b)=>a.date.localeCompare(b.date)||Number(a.id)-Number(b.id)).at(-1);
function getPlan(p){
 const weight=Number(p?.goal),startWeight=Number(p?.goalStartWeight);
 const startDate=p?.goalStartDate,finish=p?.goalDate;
 if(!validDate(startDate)||!validDate(finish)||!(dayTime(finish)>dayTime(startDate))
   ||!Number.isFinite(weight)||weight<1||weight>400
   ||!Number.isFinite(startWeight)||startWeight<1||startWeight>400)return null;
 return {weight,date:finish,startDate,startWeight};
}
window.MonEvolutionGoal={get:getPlan};
function sync(){
 const p=profile();
 dateInput.value=validDate(p.goalDate)?p.goalDate:'';
 dateInput.min=dateNow();
}
const beforeSave=saveButton.onclick;
saveButton.onclick=function(e){
 const p=profile(),target=dateInput.value,weight=Number(editGoal.value);
 const last=newest(p);
 if(!last)return alert('Ajoute d’abord une pesée.');
 if(!Number.isFinite(weight)||weight<1||weight>400)return alert('Poids cible invalide.');
 if(target&&(!validDate(target)||target<=dateNow()||target<=last.date))
  return alert('Choisis une date cible future, postérieure à la dernière pesée.');
 const changed=p.goalDate!==target||Number(p.goal)!==weight||!getPlan(p);
 // Set metadata before the original button saves the profile.
 // This retains the existing validation, local save and cloud backup.
 if(target){
  p.goalDate=target;
  if(changed){p.goalStartDate=last.date;p.goalStartWeight=last.weight;}
 }else{
  p.goalDate='';delete p.goalStartDate;delete p.goalStartWeight;
 }
 if(typeof beforeSave==='function')beforeSave.call(this,e);
};
function tile(parent,label,value){
 const cell=document.createElement('div');cell.className='goal-plan-tile';
 const small=document.createElement('small');small.textContent=label;
 const strong=document.createElement('strong');strong.textContent=value;
 cell.append(small,strong);parent.append(cell);
}
function refresh(){
 const p=profile(),plan=getPlan(p),last=newest(p);
 summaryBlock.replaceChildren();
 if(!plan||!last){summaryBlock.hidden=true;return;}
 summaryBlock.hidden=false;
 const heading=document.createElement('h4');heading.textContent='🎯 Objectif daté · poids réel';
 const grid=document.createElement('div');grid.className='goal-plan-grid';
 const span=dayTime(plan.date)-dayTime(plan.startDate);
 const completion=Math.max(0,Math.min(1,(dayTime(last.date)-dayTime(plan.startDate))/span));
 const expected=plan.startWeight+(plan.weight-plan.startWeight)*completion;
 const deviation=last.weight-expected;
 const futureDays=Math.ceil((dayTime(plan.date)-dayTime(dateNow()))/DAY);
 const remainingFromLast=(dayTime(plan.date)-dayTime(last.date))/DAY;
 let effort='Échéance dépassée';
 const diff=last.weight-plan.weight;
 if(remainingFromLast>0){
  effort=diff<=0?'Objectif atteint':number(diff*7/remainingFromLast)+' kg/semaine';
 }
 tile(grid,'Poids cible',number(plan.weight)+' kg');
 tile(grid,'Date cible',localeDate(plan.date));
 tile(grid,'Poids prévu au '+localeDate(last.date),number(expected)+' kg');
 tile(grid,'Écart réel / trajectoire',(deviation>0?'+':'')+number(deviation)+' kg');
 tile(grid,'Rythme pour atteindre la cible',effort);
 tile(grid,'Temps restant',futureDays>0?futureDays+' jour'+(futureDays>1?'s':''):futureDays===0?'Aujourd’hui':'Date dépassée');
 const note=document.createElement('p');note.className='goal-plan-info';
 note.textContent='Écart positif : poids au-dessus de la trajectoire prévue ; négatif : au-dessous. La courbe cible est une interpolation linéaire mathématique, pas une prévision médicale. Le rythme utilise la dernière pesée et le temps restant jusqu’à la date cible.';
 summaryBlock.append(heading,grid,note);
}
const priorRender=render;
render=function(){const result=priorRender();sync();refresh();return result};
sync();render();
})();
</script>
'''
s=s.replace('</body></html>',addon+'\n</body></html>')
assert "mon-evolution-goal-plan-176" in s
assert "window.MonEvolutionGoal" in s
assert "goalDate" in s and "goalStartWeight" in s
assert "goal-graph-switch" in s
page.write_text(s,encoding="utf-8")
print('PASS 1.6.76: objectif daté, courbes et statistiques')
