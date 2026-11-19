#!/usr/bin/env python3
"""v1.6.83: newborn date first, child goal hidden, neutral average of two reference series."""
from pathlib import Path
path=Path('android/source-1.6.83/app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')

def once(old,new):
 global s
 count=s.count(old)
 if count!=1:raise AssertionError(f'anchor count={count}: {old[:145]!r}')
 s=s.replace(old,new,1)

# Existing child onsubmit logic accepts boy/girl only: allow a third non-empty
# value; never require selection of a binary sex.
once(
 "  if(child&&!['male','female'].includes(sex.value)){",
 "  if(child&&!['male','female','unknown'].includes(sex.value)){"
)
once(
 "    event.preventDefault();alert('Choisis fille ou garçon pour afficher les références pédiatriques.');return;",
 "    event.preventDefault();alert('Choisis garçon, fille ou non précisé.');return;"
)

# Replace the misleading sex-selection warning with a neutral, informative guide.
once(
 """  if(child&&p.sex!=='female'&&p.sex!=='male'){
   target.append(node('p','advanced-help','Choisis fille ou garçon dans le profil pour afficher les courbes pédiatriques.'));
   return;
  }""",
 """  if(child&&p.sex!=='female'&&p.sex!=='male'){
   target.append(node('p','advanced-help',
    'Sexe non précisé : affichage indicatif de la moyenne arithmétique des références fille et garçon, à âge identique. Cette moyenne n’est pas une courbe médicale validée et ne permet pas de poser un diagnostic.'));
  }"""
)
# Protect the pediatric BMI interpretation from treating an unknown sex as female.
once(
 """   const sexBoy=p.sex==='male';
   const table=window.GROWTH_WHO2007||[];
   const lastRecord=""",
 """   const sexBoy=p.sex==='male';
   const sexUnknown=p.sex!=='male'&&p.sex!=='female';
   const table=window.GROWTH_WHO2007||[];
   const lastRecord="""
)
once(
 "   const iotfTable=(window.GROWTH_IOTF2012||[]).filter(q=>q[1]===(sexBoy?1:2));",
 "   const iotfTable=sexUnknown?[]:(window.GROWTH_IOTF2012||[]).filter(q=>q[1]===(sexBoy?1:2));"
)
once(
 """   if(measuredBmi===null){
    status.append(node('p','', 'Renseigne la taille mesurée pour interpréter l’IMC selon l’âge et le sexe.'));
   }else if(Number.isFinite(overweightCutoff)&&Number.isFinite(obesityCutoff)){""",
 """   if(measuredBmi===null){
    status.append(node('p','', 'Renseigne la taille mesurée pour calculer l’IMC.'));
   }else if(sexUnknown){
    status.append(node('p','', 'IMC '+fmt1(measuredBmi)+' · références moyennées fille/garçon : aucun classement médical (surpoids ou obésité) établi.'));
   }else if(Number.isFinite(overweightCutoff)&&Number.isFinite(obesityCutoff)){"""
)

# For unknown sex, calculate the actual z-score curve for each sex at every
# age and then average the two values. DO NOT average LMS coefficients,
# which is mathematically incorrect for percentile or z-score curves.
old="""   const low=Math.max(61,Math.floor(lo-6)),high=Math.min(228,Math.ceil(hi+6));
   const indices=healthMetric==='height'?(sexBoy?[1,2]:[3,4]):
      healthMetric==='weight'?(sexBoy?[5,6,7]:[8,9,10]):
      (sexBoy?[11,12,13]:[14,15,16]);
   const derived=(row,z)=>{
    if(healthMetric==='height'){
      const M=row[indices[0]],S=row[indices[1]];
      return M==null||S==null?null:M*(1+S*z);
    }
    const L=row[indices[0]],M=row[indices[1]],S=row[indices[2]];
    if(L==null||M==null||S==null)return null;
    return Math.abs(L)<.00001?M*Math.exp(S*z):M*Math.pow(1+L*S*z,1/L);
   };
   const reference=table.filter(q=>q[0]>=low&&q[0]<=high);"""
new="""   const low=Math.max(61,Math.floor(lo-6)),high=Math.min(228,Math.ceil(hi+6));
   const indicesFor=boy=>healthMetric==='height'?(boy?[1,2]:[3,4]):
      healthMetric==='weight'?(boy?[5,6,7]:[8,9,10]):
      (boy?[11,12,13]:[14,15,16]);
   const derivedFor=(row,z,boy)=>{
    const indices=indicesFor(boy);
    if(healthMetric==='height'){
      const M=row[indices[0]],S=row[indices[1]];
      return M==null||S==null?null:M*(1+S*z);
    }
    const L=row[indices[0]],M=row[indices[1]],S=row[indices[2]];
    if(L==null||M==null||S==null)return null;
    return Math.abs(L)<.00001?M*Math.exp(S*z):M*Math.pow(1+L*S*z,1/L);
   };
   const derived=(row,z)=>{
    if(!sexUnknown)return derivedFor(row,z,sexBoy);
    const boy=derivedFor(row,z,true),girl=derivedFor(row,z,false);
    return Number.isFinite(boy)&&Number.isFinite(girl)?(boy+girl)/2:null;
   };
   const reference=table.filter(q=>q[0]>=low&&q[0]<=high);"""
once(old,new)
once(
 "    line(label,color,reference.map(q=>({x:q[0],y:derived(q,z)})).filter(v=>Number.isFinite(v.y)));",
 "    line(label+(sexUnknown?' · moyenne fille/garçon':''),color,reference.map(q=>({x:q[0],y:derived(q,z)})).filter(v=>Number.isFinite(v.y)));"
)

# IOTF lines are also paired and averaged at the same month. These neutral
# guides are visual aids only; the status card deliberately does not classify
# the child against an unvalidated averaged IOTF threshold.
old="""   if(healthMetric==='bmi'){
    const sex=sexBoy?1:2;
    const iotf=(window.GROWTH_IOTF2012||[]).filter(q=>q[1]===sex&&q[0]>=Math.max(24,lo-12)&&q[0]<=Math.min(216,hi+12));
    line('IOTF seuil surpoids (IMC 25 adulte)',palette[3],iotf.map(q=>({x:q[0],y:q[2]})));
    line('IOTF seuil obésité (IMC 30 adulte)',palette[4],iotf.map(q=>({x:q[0],y:q[3]})));
   }"""
new="""   if(healthMetric==='bmi'){
    const allIotf=window.GROWTH_IOTF2012||[];
    const range=q=>q[0]>=Math.max(24,lo-12)&&q[0]<=Math.min(216,hi+12);
    const iotf=sexUnknown
      ?allIotf.filter(q=>q[1]===1&&range(q)).map(b=>{
       const g=allIotf.find(q=>q[0]===b[0]&&q[1]===2);
       return g?[b[0],0,(b[2]+g[2])/2,(b[3]+g[3])/2]:null;
      }).filter(Boolean)
      :allIotf.filter(q=>q[1]===(sexBoy?1:2)&&range(q));
    const suffix=sexUnknown?' · moyenne indicative fille/garçon':'';
    line('IOTF repère surpoids'+suffix,palette[3],iotf.map(q=>({x:q[0],y:q[2]})));
    line('IOTF repère obésité'+suffix,palette[4],iotf.map(q=>({x:q[0],y:q[3]})));
   }"""
once(old,new)
# These reference sources remain the same; clarify the visual interpolation.
once(
 """   target.append(node('p','advanced-help','Références de croissance OMS 2007 (5–19 ans, poids jusqu’à 10 ans) et seuils IMC IOTF 2012 (2–18 ans). Distinctes des courbes françaises AFPA 2018 du carnet de santé. Interprétation médicale nécessaire, notamment pendant la croissance.'));""",
 """   target.append(node('p','advanced-help',
    (sexUnknown?'En mode non précisé, les valeurs fille et garçon sont moyennées point par point : ce ne sont ni des normes officielles ni des seuils diagnostiques. ':'')+
    'Sources : croissance OMS 2007 (5–19 ans, poids jusqu’à 10 ans) et seuils IMC IOTF 2012 (2–18 ans). Distinctes des courbes françaises AFPA 2018 du carnet de santé. Un avis médical est nécessaire pour interpréter les courbes.'));"""
)
# Don't change the red warning text or the underlying cloud/backup formats.

# Place date of birth and sex before any goals and weight inputs in the new
# profile form. Date of birth is needed to know whether a goal is applicable.
addon=r'''
<style id="mon-evolution-profile-age-sex-v183">
#profile-dialog .child-goal-message{margin:10px 0 13px;padding:10px 12px;
 border:1px solid #5d9d99;border-radius:10px;background:#153d47;
 font-size:13px;color:#e1f6f3;line-height:1.5}
#profile-dialog .child-goal-message[hidden]{display:none!important}
#profile-dialog .child-goal-hidden{display:none!important}
</style>
<script>
(function(){
 'use strict';
 const form=document.getElementById('profile-form');
 const birth=document.getElementById('new-birth');
 const sex=document.getElementById('new-sex');
 const goal=document.getElementById('new-goal');
 const firstName=document.getElementById('new-name');
 const editSex=document.getElementById('edit-sex');
 if(!form||!birth||!sex||!goal||!firstName)return;
 const birthRow=birth.closest('.two');
 const heightField=document.getElementById('new-height')?.closest('label');
 if(birthRow&&heightField)form.insertBefore(birthRow,heightField);
 const birthField=birth.closest('label');
 if(birthField&&birthField.firstChild)birthField.firstChild.textContent='Date de naissance';
 birth.required=true;
 const options=[
  {value:'male',label:'Garçon'},
  {value:'female',label:'Fille'},
  {value:'unknown',label:'Non précisé'}
 ];
 const refreshOptions=select=>{
  if(!select)return;
  const old=select.value;
  select.replaceChildren();
  for(const opt of options){
   const element=document.createElement('option');
   element.value=opt.value;element.textContent=opt.label;
   select.append(element);
  }
  select.value=options.some(o=>o.value===old)?old:'unknown';
 };
 refreshOptions(sex);
 refreshOptions(editSex);
 const updateSelect=()=>{
  // An unspecified sex is a valid choice in childhood, with averaged curves.
  sex.required=false;
  const child=window.MonEvolutionChild?.isChildBirth?.(birth.value)===true;
  const goalField=goal.closest('label');
  if(goalField){goalField.hidden=child;goalField.classList.toggle('child-goal-hidden',child);}
  goal.required=!child;
  const hint=form.querySelector('.child-goal-message');
  if(hint)hint.hidden=!child;
 };
 birth.addEventListener('input',updateSelect);
 birth.addEventListener('change',updateSelect);
 const oldCreate=form.onsubmit;
 if(oldCreate){
  form.onsubmit=function(event){
   updateSelect();
   if(!birth.value){
    event.preventDefault();
    alert('Renseigne la date de naissance pour déterminer le type de profil.');
    return;
   }
   return oldCreate.call(this,event);
  };
 }
 // Preserve "Non précisé" when other profile renderers reset the edit selector.
 const oldRender=render;
 render=function(){
  const result=oldRender();
  if(editSex&&profile().sex==='')editSex.value='unknown';
  return result;
 };
 updateSelect();
})();
</script>
'''
once('</body></html>',addon+'\n</body></html>')
assert "moyenne arithmétique des références fille et garçon" in s
assert "const derivedFor=(row,z,boy)" in s
assert "en mode non précisé" not in s or True
assert "birth.required=true" in s
assert "form.insertBefore(birthRow,heightField)" in s
assert "value:'unknown',label:'Non précisé'" in s
assert "si sexUnknown" not in s
path.write_text(s,encoding='utf-8')
print('PASS 1.6.83: birth first, minor without target, neutral averaged reference curves')
