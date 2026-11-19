#!/usr/bin/env python3
"""v1.6.82: independent dated intermediate-goal segment with editable start values."""
from pathlib import Path
page=Path('android/source-1.6.82/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

def once(old,new):
 global s
 count=s.count(old)
 if count!=1: raise AssertionError(f'Anchor count={count}: {old[:135]!r}')
 s=s.replace(old,new,1)

# The intermediate goal has four independently editable values.
once(
 """const dateLabel=document.createElement('label');dateLabel.className='field';dateLabel.textContent='Date cible';
const dateInput=document.createElement('input');dateInput.id='edit-goal-date';dateInput.type='date';""",
 """const startDateLabel=document.createElement('label');startDateLabel.className='field';
startDateLabel.textContent='Date de départ';
const startDateInput=document.createElement('input');startDateInput.id='edit-goal-start-date';startDateInput.type='date';
startDateLabel.append(startDateInput);
const startWeightLabel=document.createElement('label');startWeightLabel.className='field';
startWeightLabel.textContent='Poids de départ (kg)';
const startWeightInput=document.createElement('input');startWeightInput.id='edit-goal-start-weight';
startWeightInput.type='number';startWeightInput.min='1';startWeightInput.max='400';startWeightInput.step='.1';
startWeightLabel.append(startWeightInput);
const dateLabel=document.createElement('label');dateLabel.className='field';dateLabel.textContent='Date d’arrivée';
const dateInput=document.createElement('input');dateInput.id='edit-goal-date';dateInput.type='date';"""
)
once(
 "fields.append(intermediateLabel,dateLabel);box.append(title,help,fields);",
 "fields.append(startDateLabel,startWeightLabel,intermediateLabel,dateLabel);box.append(title,help,fields);"
)
once(
 "help.textContent='Cet objectif est une étape avec sa propre date ; le poids final attendu reste indépendant.';",
 "help.textContent='Trajectoire indépendante : départ (date et poids), arrivée (date et poids cible). Le départ utilise par défaut la première pesée, que tu peux modifier.';"
)

# Refresh defaults: first available entry, never most recent.
once(
 """ dateInput.value=validDate(p.goalDate)?p.goalDate:'';
 intermediateInput.value=Number.isFinite(Number(p.intermediateGoalWeight))&&Number(p.intermediateGoalWeight)>0
  ?p.intermediateGoalWeight:(p.goalDate?Number(p.goal):'');
 dateInput.min=dateNow();""",
 """ const first=(p.entries||[]).filter(e=>validDate(e.date)&&Number.isFinite(e.weight))
  .sort((a,b)=>a.date.localeCompare(b.date)||Number(a.id)-Number(b.id))[0];
 startDateInput.value=validDate(p.goalStartDate)?p.goalStartDate:(first?.date||dateNow());
 startWeightInput.value=Number.isFinite(Number(p.goalStartWeight))&&Number(p.goalStartWeight)>0
  ?p.goalStartWeight:(first?.weight??'');
 dateInput.value=validDate(p.goalDate)?p.goalDate:'';
 intermediateInput.value=Number.isFinite(Number(p.intermediateGoalWeight))&&Number(p.intermediateGoalWeight)>0
  ?p.intermediateGoalWeight:(p.goalDate?Number(p.goal):'');
 dateInput.min='';"""
)
# Explicitly validate the full trajectory before touching the saved profile.
once(
 """const beforeSave=saveButton.onclick;
saveButton.onclick=function(e){
 const p=profile(),target=dateInput.value,weight=Number(intermediateInput.value);
 const finalWeight=Number(editGoal.value),last=newest(p);
 if(!last)return alert('Ajoute d’abord une pesée.');
 if(!Number.isFinite(finalWeight)||finalWeight<1||finalWeight>400)return alert('Poids final invalide.');
 if(target&&(!intermediateInput.value.trim()||!Number.isFinite(weight)||weight<1||weight>400))
  return alert('Indique un poids intermédiaire valide.');
 if(target&&(!validDate(target)||target<=dateNow()||target<=last.date))
  return alert('Choisis une date cible future, postérieure à la dernière pesée.');
 const previousWeight=Number(p.intermediateGoalWeight??(p.goalDate?p.goal:NaN));
 const changed=p.goalDate!==target||previousWeight!==weight||!getPlan(p);
 // Set metadata before the original button saves the profile.
 // This retains the existing validation, local save and cloud backup.
 if(target){
  p.goalDate=target;
  p.intermediateGoalWeight=weight;
  if(changed){p.goalStartDate=last.date;p.goalStartWeight=last.weight;}
 }else{
  p.goalDate='';delete p.goalStartDate;delete p.goalStartWeight;delete p.intermediateGoalWeight;
 }
 if(typeof beforeSave==='function')beforeSave.call(this,e);
};""",
 """const beforeSave=saveButton.onclick;
saveButton.onclick=function(e){
 const p=profile();
 const child=window.MonEvolutionChild?.isChildBirth?.(p.birthDate)===true;
 const finalWeight=Number(editGoal.value);
 if(!child&&(!Number.isFinite(finalWeight)||finalWeight<1||finalWeight>400))
  return alert('Poids final invalide.');
 if(child){if(typeof beforeSave==='function')beforeSave.call(this,e);return;}
 const endDate=dateInput.value,startDate=startDateInput.value;
 const endValue=intermediateInput.value.trim(),startValue=startWeightInput.value.trim();
 const target=Number(endValue),startWeight=Number(startValue);
 if(endDate||endValue){
  if(!validDate(startDate)||!validDate(endDate)||dayTime(endDate)<=dayTime(startDate))
   return alert('La date d’arrivée doit être postérieure à la date de départ.');
  if(!startValue||!Number.isFinite(startWeight)||startWeight<1||startWeight>400)
   return alert('Indique un poids de départ valide.');
  if(!endValue||!Number.isFinite(target)||target<1||target>400)
   return alert('Indique un poids cible intermédiaire valide.');
  // These four fields belong only to this intermediate goal, not the final target.
  p.goalStartDate=startDate;
  p.goalStartWeight=startWeight;
  p.goalDate=endDate;
  p.intermediateGoalWeight=target;
 }else{
  p.goalDate='';delete p.goalStartDate;
  delete p.goalStartWeight;delete p.intermediateGoalWeight;
 }
 if(typeof beforeSave==='function')beforeSave.call(this,e);
};"""
)

# Remove the redundant horizontal interim-weight line. Only the segment remains.
a=s.index(' function primaryGraph(target,p){')
b=s.index(' function progressGraph(target,p){',a)
part=s[a:b]
start=part.index('  // Final target stays gold;')
stop=part.index('  if(trend){',start)
assert 'const intermediateWeight=Number(p.intermediateGoalWeight)' in part[start:stop]
part=part[:start]+part[stop:]
assert "label:'Trajectoire vers l’objectif intermédiaire daté'" in part
assert "  const goalPlan=window.MonEvolutionGoal?.get?.(p)||null;" in part
part=part.replace(
 """  if(goalPlan){
   series.push({label:'Trajectoire vers l’objectif intermédiaire daté',color:'#f3a4cc',dashed:true,thin:false,""",
 """  if(goalPlan){
   advanced.append(checkbox('Afficher l’objectif intermédiaire',window.MonEvolutionGoal?.advancedVisible!==false,
    v=>{window.MonEvolutionGoal.advancedVisible=v;redraw()}));
  }
  if(goalPlan&&window.MonEvolutionGoal?.advancedVisible!==false){
   series.push({label:'Trajectoire de l’objectif intermédiaire',color:'#f3a4cc',dashed:true,thin:false,""",
 1
)
assert part.count("if(goalPlan&&window.MonEvolutionGoal?.advancedVisible!==false)")==1
s=s[:a]+part+s[b:]

# Make the whole intermediate segment visible in the "Tout" period, when enabled.
once(
 """    ?wEnd+Math.max(3,Math.min(7,wEnd/4))
    :wEnd+Math.min(21,windowSize/4);""",
 """    ?Math.max(wEnd+Math.max(3,Math.min(7,wEnd/4)),
      goalPlan&&window.MonEvolutionGoal?.advancedVisible!==false?days(origin,goalPlan.date):0)
    :wEnd+Math.min(21,windowSize/4);"""
)

# The upper graph already has a checkbox and a dated segment; share the new label/color
# and allow a starting date before the first logged measurement.
once(
 "goalLabel.textContent='Afficher la trajectoire de mon objectif';",
 "goalLabel.textContent='Afficher l’objectif intermédiaire';"
)
once(
 """ const b={xMin:pts[0].t,xMax:Math.max(pts[0].t+86400000,extra?.t||last.t,goalChartVisible?ts(scheduledGoal.date):0),""",
 """ const b={xMin:Math.min(pts[0].t,goalChartVisible?ts(scheduledGoal.startDate):Infinity),
  xMax:Math.max(pts[0].t+86400000,extra?.t||last.t,goalChartVisible?ts(scheduledGoal.date):0),"""
)
once(
 "stroke:'#f4d17a','stroke-width':2.7,'stroke-dasharray':'9 5'",
 "stroke:'#f3a4cc','stroke-width':2.7,'stroke-dasharray':'9 5'"
)
once(
 "cx:x1,cy:y1,r:5.4,fill:'#f4d17a'",
 "cx:x1,cy:y1,r:5.4,fill:'#f3a4cc'"
)
once(
 "key.style.backgroundColor='#f4d17a';",
 "key.style.backgroundColor='#f3a4cc';"
)
once(
 "label.textContent='Objectif daté · ligne dorée pointillée';",
 "label.textContent='Objectif intermédiaire · trajectoire rose pointillée';"
)
once(
 "window.MonEvolutionGoal={get:getPlan};",
 "window.MonEvolutionGoal={get:getPlan,advancedVisible:true};"
)

assert "const intermediateWeight=Number(p.intermediateGoalWeight)" not in s
assert "edit-goal-start-date" in s and "edit-goal-start-weight" in s
assert "p.goalStartDate=startDate" in s and "p.goalStartWeight=startWeight" in s
assert "first?.weight??''" in s
assert "Trajectoire de l’objectif intermédiaire" in s
assert "Objectif intermédiaire · trajectoire rose pointillée" in s
assert "Afficher l’objectif intermédiaire" in s
assert "dayTime(endDate)<=dayTime(startDate)" in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.82: 4 goal fields, first weigh-in defaults, single diagonal segment')
