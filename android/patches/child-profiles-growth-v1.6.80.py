#!/usr/bin/env python3
"""v1.6.80: child profiles without weight-loss targets and pediatric reference charts."""
from pathlib import Path
page=Path('android/source-1.6.80/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise AssertionError(f'child-profile anchor count={n}: {old[:130]!r}')
 s=s.replace(old,new,1)

# Keep legacy numeric 'goal' for compatibility with backup / chart functions, but
# don't treat it as a goal for children: start weight is used only as a neutral
# internal placeholder, with an explicit noWeightGoal flag.
once(
 "goal:Number($('new-goal').value),birthDate:$('new-birth').value,",
 """goal:($('new-goal').value.trim()?Number($('new-goal').value):Number($('new-weight').value)),
 noWeightGoal:window.MonEvolutionChild?.isChildBirth?.($('new-birth').value)===true,
 birthDate:$('new-birth').value,"""
)
# The create input has HTML required: switch it off for an under-18 birthdate.
# Do not remove required validation for adults.

# Use last known measured height (never a future height) for the BMI trend,
# and warn the user when the measurement is older than the weight record.
once(
 """  const tall=r=>Number(r.heightCm)>=45&&Number(r.heightCm)<=250?Number(r.heightCm):null;
  const actualMetric=r=>{""",
 """  const tall=r=>Number(r.heightCm)>=45&&Number(r.heightCm)<=250?Number(r.heightCm):null;
  const latestKnownHeight=r=>p.rows.filter(q=>q.date<=r.date&&tall(q)!==null).at(-1)?.heightCm||null;
  const actualMetric=r=>{"""
)
once(
 """   const h=tall(r)||(child?null:p.height);
   return h? r.weight/Math.pow(h/100,2):null;""",
 """   const h=tall(r)||(child?latestKnownHeight(r):p.height);
   return h? r.weight/Math.pow(h/100,2):null;"""
)
once(
 """   const measuredHeight=tall(r)||(child?null:p.height);""",
 """   const measuredHeight=tall(r)||(child?latestKnownHeight(r):p.height);"""
)
# Create a pediatric status just before the established IOTF/WHO reference series.
once(
 """  if(child){
   const sexBoy=p.sex==='male';
   const table=window.GROWTH_WHO2007||[];""",
 """  if(child){
   const sexBoy=p.sex==='male';
   const table=window.GROWTH_WHO2007||[];
   const lastRecord=p.rows.at(-1);
   const heightRecord=p.rows.filter(q=>q.date<=lastRecord.date&&tall(q)!==null).at(-1);
   const height=heightRecord?Number(heightRecord.heightCm):null;
   const monthAge=ageOn(lastRecord.date);
   const measuredBmi=height?lastRecord.weight/Math.pow(height/100,2):null;
   const iotfTable=(window.GROWTH_IOTF2012||[]).filter(q=>q[1]===(sexBoy?1:2));
   const firstThreshold=iotfTable.find(q=>q[0]>=monthAge);
   const previousThreshold=[...iotfTable].reverse().find(q=>q[0]<=monthAge);
   const interpolate=(index)=>{
    if(!firstThreshold||!previousThreshold)return null;
    const span=firstThreshold[0]-previousThreshold[0];
    const portion=span>0?(monthAge-previousThreshold[0])/span:0;
    return Number(previousThreshold[index])+(Number(firstThreshold[index])-Number(previousThreshold[index]))*portion;
   };
   const overweightCutoff=interpolate(2),obesityCutoff=interpolate(3);
   const status=node('div','child-reference-summary');
   const caption=node('strong','','Repères de corpulence pédiatrique');
   status.append(caption);
   if(measuredBmi===null){
    status.append(node('p','', 'Renseigne la taille mesurée pour interpréter l’IMC selon l’âge et le sexe.'));
   }else if(Number.isFinite(overweightCutoff)&&Number.isFinite(obesityCutoff)){
    const interpretation=measuredBmi>=obesityCutoff
     ?'Au-dessus du seuil IOTF-30 (repère obésité)'
     :measuredBmi>=overweightCutoff
      ?'Au-dessus du seuil IOTF-25 (repère surpoids)'
      :'Sous les seuils IOTF du surpoids';
    status.append(node('p','', 'IMC '+fmt1(measuredBmi)+' · '+interpretation+'.'));
   }else{
    status.append(node('p','', 'Références IOTF indisponibles pour cet âge : aucune catégorie ne peut être estimée.'));
   }
   status.append(node('small','', 'Taille de référence : '+(height===null?'non renseignée':fmt1(height)+' cm, mesurée le '+heightRecord.date)+'. '+
    'Ces repères de dépistage ne constituent pas un diagnostic ; comparer les courbes successives avec le médecin.'));
   target.append(status);"""
)
# Suppress the generic text that incorrectly describes the age coverage.
once(
 """  if(child&&age<24&&healthMetric!=='bmi'){
   target.append(node('p','advanced-help','Pour cet âge, les tables OMS 2007 de 5 à 19 ans ne couvrent pas encore la croissance. Consulter le carnet de santé et son médecin.'));
  }""",
 """  if(child&&age<61&&healthMetric!=='bmi'){
   target.append(node('p','advanced-help','Les courbes OMS de poids et taille embarquées commencent à 5 ans ; seul le suivi des mesures est présenté avant cet âge. Consulter les courbes du carnet de santé.'));
  }"""
)
# Use the established reference renderer for all child graph panels.
a=s.index(" function primaryGraph(target,p){")
b=s.index(" function progressGraph(target,p){",a)
part=s[a:b]
head=" function primaryGraph(target,p){"
assert part.startswith(head)
part=part.replace(head,head+"""
  if(window.MonEvolutionChild?.isChildBirth?.(p.birthDate)){
   target.append(sectionTitle('Suivi de croissance'));
   const explanation=node('p','advanced-help',
    'Suivi de croissance : les courbes d’IMC dépendent de l’âge, du sexe et de la taille. Aucun objectif de perte de poids.');
   target.append(explanation);
   if(!window.MonEvolutionChild.metric)window.MonEvolutionChild.metric='bmi';
   healthMetric=window.MonEvolutionChild.metric;
   controls(target,[['IMC / âge', 'bmi'],['Poids / âge','weight'],['Taille / âge','height']]
    .map(([label,kind])=>[label,healthMetric===kind,()=>{
      window.MonEvolutionChild.metric=kind;redraw();
    }]));
   healthReferenceGraph(target,p);
   return;
  }
""",1)
s=s[:a]+part+s[b:]

# Hide all adult weight-loss performance panels for under-18 profiles. This
# preserves internal DOM fields and all existing storage/backup compatibility.
addon=r'''
<style id="mon-evolution-children-v180">
body.child-profile #home #evolution-rank,
body.child-profile #home .bar,
body.child-profile #home .summary-balance,
body.child-profile #home #goal-value,
body.child-profile #home #goal-value + *,
body.child-profile #home #evo-v159-summary,
body.child-profile #home .legacy-advanced-stats{display:none!important}
body.child-profile #home #pct{display:none!important}
body.child-profile #home #goal-value{display:none!important}
body.child-profile #home .goal-label{display:none!important}
body.child-profile #goal-plan-edit{display:none!important}
body.child-profile #edit-goal{display:none!important}
body.child-profile .adult-only-goal{display:none!important}
.child-reference-summary{margin:12px 0 14px;padding:13px;border:1px solid #4f8493;
 border-radius:13px;background:#153b4d;color:#ecf8fb;line-height:1.45}
.child-reference-summary strong{display:block;font-size:14px}
.child-reference-summary p{margin:7px 0;font-size:14px}
.child-reference-summary small{color:#bdd9e2;font-size:12px;line-height:1.5}
#profile-dialog .child-goal-hidden{display:none!important}
#profile-dialog .child-goal-message[hidden]{display:none!important}
#profile-dialog .child-goal-message{color:#bddedb;font-size:12px;line-height:1.45;margin:8px 0}
</style>
<script>
(function(){
 'use strict';
 function isChildBirth(birth){
  if(typeof birth!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(birth))return false;
  const born=new Date(birth+'T12:00:00Z');
  const today=new Date(dateNow()+'T12:00:00Z');
  if(!Number.isFinite(born.getTime())||born>today)return false;
  const years=today.getUTCFullYear()-born.getUTCFullYear()-
   (today.getUTCMonth()*32+today.getUTCDate()<born.getUTCMonth()*32+born.getUTCDate()?1:0);
  return years>=0&&years<18;
 }
 window.MonEvolutionChild={isChildBirth,metric:'bmi'};
 const birth=document.getElementById('new-birth');
 const goal=document.getElementById('new-goal');
 const sex=document.getElementById('new-sex');
 const weight=document.getElementById('new-weight');
 const form=document.getElementById('profile-form');
 const goalLabel=goal?.closest('label');
 const hint=document.createElement('p');hint.className='child-goal-message';
 hint.textContent='Profil enfant : aucun objectif de poids. L’application suivra la croissance et l’IMC selon l’âge et le sexe.';
 if(goalLabel)goalLabel.after(hint);
 function updateCreate(){
  const child=isChildBirth(birth.value);
  if(goalLabel){goalLabel.hidden=child;goalLabel.classList.toggle('child-goal-hidden',child);}
  if(goal)goal.required=!child;
  if(sex)sex.required=child;
  hint.hidden=!child;
 }
 birth?.addEventListener('input',updateCreate);
 birth?.addEventListener('change',updateCreate);
 updateCreate();
 const oldCreate=form?.onsubmit;
 if(form&&oldCreate){
  form.onsubmit=function(event){
   const child=isChildBirth(birth.value);
   if(birth.value&&birth.value>dateNow()){
    event.preventDefault();alert('La date de naissance ne peut pas être dans le futur.');return;
   }
   if(child&&!['male','female'].includes(sex.value)){
    event.preventDefault();alert('Choisis fille ou garçon pour afficher les références pédiatriques.');return;
   }
   const previous=goal.value;
   if(child)goal.value=weight.value; // neutral legacy placeholder, not a weight target
   const result=oldCreate.call(this,event);
   if(child){goal.value='';}
   else goal.value=previous;
   return result;
  };
 }
 const editGoal=document.getElementById('edit-goal');
 const goalEditLabel=editGoal?.closest('label');
 if(goalEditLabel)goalEditLabel.classList.add('adult-only-goal');
 const oldRender=render;
 function updateProfile(){
  const child=isChildBirth(profile().birthDate);
  document.body.classList.toggle('child-profile',child);
  if(goalEditLabel)goalEditLabel.hidden=child;
  // Hide the parent tile, not its data. This is a read-only display change.
  const goalTile=document.getElementById('goal-value')?.closest('.tile');
  if(goalTile)goalTile.hidden=child;
  const percent=document.getElementById('pct');
  if(percent?.parentElement)percent.parentElement.hidden=child;
  const summary=document.querySelector('#home .hero .summary-balance');
  if(summary)summary.hidden=child;
  const badge=document.getElementById('evolution-rank');
  if(badge)badge.hidden=child;
  const goalCard=document.getElementById('goal-plan-edit');
  if(goalCard)goalCard.hidden=child;
  // For adult profiles, the old inputs retain their existing validation.
 }
 render=function(){
  const result=oldRender();
  updateProfile();
  return result;
 };
 updateProfile();
})();
</script>
'''
once('</body></html>',addon+'\n</body></html>')
assert 'noWeightGoal:window.MonEvolutionChild' in s
assert 'Suivi de croissance' in s
assert 'child-reference-summary' in s
assert 'body.child-profile' in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.80: child creation, neutral goal, BMI/IOTF growth chart')
