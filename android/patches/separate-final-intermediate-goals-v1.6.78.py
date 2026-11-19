#!/usr/bin/env python3
"""v1.6.78: independent final weight and intermediate dated objective."""
from pathlib import Path
page=Path("android/source-1.6.78/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def once(old,new):
 global s
 count=s.count(old)
 if count!=1:raise AssertionError(f"Dual-goal anchor {count}: {old[:115]!r}")
 s=s.replace(old,new,1)

# Existing p.goal remains the final objective, used by existing badges and stats.
# The intermediate goal is a separate optional field for the dated trajectory.
once(
"""const fields=document.createElement('div');fields.className='two';
oldLabel.firstChild.textContent='Poids cible (kg)';
const dateLabel=document.createElement('label');dateLabel.className='field';dateLabel.textContent='Date cible';""",
"""const fields=document.createElement('div');fields.className='two';
oldLabel.firstChild.textContent='Poids final attendu (kg)';
const intermediateLabel=document.createElement('label');intermediateLabel.className='field';
intermediateLabel.textContent='Poids intermédiaire (kg)';
const intermediateInput=document.createElement('input');intermediateInput.id='edit-intermediate-goal';
intermediateInput.type='number';intermediateInput.min='1';intermediateInput.max='400';intermediateInput.step='.1';
intermediateLabel.append(intermediateInput);
const dateLabel=document.createElement('label');dateLabel.className='field';dateLabel.textContent='Date cible';"""
)
once("fields.append(oldLabel,dateLabel);box.append(title,help,fields);",
     "fields.append(intermediateLabel,dateLabel);box.append(title,help,fields);")
once("title.textContent='🎯 Objectif de poids';",
     "title.textContent='🎯 Objectif intermédiaire daté';")
once("help.textContent='Définis un poids cible et une date pour comparer le parcours prévu aux pesées réelles.';",
     "help.textContent='Cet objectif est une étape avec sa propre date ; le poids final attendu reste indépendant.';")
once("const weight=Number(p?.goal),startWeight=Number(p?.goalStartWeight);",
     "const weight=Number(p?.intermediateGoalWeight??(p?.goalDate?p.goal:NaN)),startWeight=Number(p?.goalStartWeight);")
once("sex:p.sex||'',goalDate:p.goalDate||'',goalStartDate:p.goalStartDate||'',goalStartWeight:p.goalStartWeight,rows:unique};",
     "sex:p.sex||'',goalDate:p.goalDate||'',goalStartDate:p.goalStartDate||'',goalStartWeight:p.goalStartWeight,intermediateGoalWeight:p.intermediateGoalWeight??(p.goalDate?p.goal:null),rows:unique};")
once(
""" dateInput.value=validDate(p.goalDate)?p.goalDate:'';
 dateInput.min=dateNow();""",
""" dateInput.value=validDate(p.goalDate)?p.goalDate:'';
 intermediateInput.value=Number.isFinite(Number(p.intermediateGoalWeight))&&Number(p.intermediateGoalWeight)>0
  ?p.intermediateGoalWeight:(p.goalDate?Number(p.goal):'');
 dateInput.min=dateNow();"""
)
once(
""" const p=profile(),target=dateInput.value,weight=Number(editGoal.value);
 const last=newest(p);
 if(!last)return alert('Ajoute d’abord une pesée.');
 if(!Number.isFinite(weight)||weight<1||weight>400)return alert('Poids cible invalide.');
 if(target&&(!validDate(target)||target<=dateNow()||target<=last.date))
  return alert('Choisis une date cible future, postérieure à la dernière pesée.');
 const changed=p.goalDate!==target||Number(p.goal)!==weight||!getPlan(p);""",
""" const p=profile(),target=dateInput.value,weight=Number(intermediateInput.value);
 const finalWeight=Number(editGoal.value),last=newest(p);
 if(!last)return alert('Ajoute d’abord une pesée.');
 if(!Number.isFinite(finalWeight)||finalWeight<1||finalWeight>400)return alert('Poids final invalide.');
 if(target&&(!intermediateInput.value.trim()||!Number.isFinite(weight)||weight<1||weight>400))
  return alert('Indique un poids intermédiaire valide.');
 if(target&&(!validDate(target)||target<=dateNow()||target<=last.date))
  return alert('Choisis une date cible future, postérieure à la dernière pesée.');
 const previousWeight=Number(p.intermediateGoalWeight??(p.goalDate?p.goal:NaN));
 const changed=p.goalDate!==target||previousWeight!==weight||!getPlan(p);"""
)
once(
""" if(target){
  p.goalDate=target;
  if(changed){p.goalStartDate=last.date;p.goalStartWeight=last.weight;}
 }else{
  p.goalDate='';delete p.goalStartDate;delete p.goalStartWeight;
 }""",
""" if(target){
  p.goalDate=target;
  p.intermediateGoalWeight=weight;
  if(changed){p.goalStartDate=last.date;p.goalStartWeight=last.weight;}
 }else{
  p.goalDate='';delete p.goalStartDate;delete p.goalStartWeight;delete p.intermediateGoalWeight;
 }"""
)
once("heading.textContent='🎯 Objectif daté · poids réel';",
     "heading.textContent='🎯 Étape intermédiaire · poids réel';")
once("tile(grid,'Poids cible',number(plan.weight)+' kg');",
     "tile(grid,'Poids intermédiaire',number(plan.weight)+' kg');")
assert "Poids final attendu (kg)" in s
assert "edit-intermediate-goal" in s
assert "p.intermediateGoalWeight=weight" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.78: objectif final et objectif intermédiaire séparés")
