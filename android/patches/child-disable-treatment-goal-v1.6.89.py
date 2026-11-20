#!/usr/bin/env python3
"""v1.6.89 — enfant: cases traitements et objectif désactivées, aucune courbe d'objectif."""
from pathlib import Path
page=Path("android/source-1.6.89/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise AssertionError(f"Ancre unique requise ({n}): {old[:160]!r}")
 s=s.replace(old,new,1)

# The two controls are global UI preferences: never overwrite saved adult
# preferences when a child profile is temporarily selected.
once(
 " const goalCheck=document.createElement('input');goalCheck.type='checkbox';goalCheck.checked=true;",
 """ const goalCheck=document.createElement('input');goalCheck.type='checkbox';goalCheck.checked=true;
 let adultTreatmentChecked=treatmentCheck.checked;
 let adultGoalChecked=goalCheck.checked;"""
)

# Before chart drawing, align the switches with the *currently viewed* profile.
# Keep the two boxes visible but unchecked/disabled, as explicitly requested.
once(
 "function update(){\n const p=profile(),r=rows();",
 """function update(){
 const p=profile(),r=rows();
 const isMinor=window.MonEvolutionChild?.isChildBirth?.(p.birthDate)===true;
 if(isMinor){
  if(!treatmentCheck.disabled)adultTreatmentChecked=treatmentCheck.checked;
  if(!goalCheck.disabled)adultGoalChecked=goalCheck.checked;
  treatmentCheck.checked=false;
  goalCheck.checked=false;
 }else{
  if(treatmentCheck.disabled)treatmentCheck.checked=adultTreatmentChecked;
  if(goalCheck.disabled)goalCheck.checked=adultGoalChecked;
  adultTreatmentChecked=treatmentCheck.checked;
  adultGoalChecked=goalCheck.checked;
 }
 treatmentCheck.disabled=isMinor;
 goalCheck.disabled=isMinor;
 treatmentSwitch.classList.toggle('child-option-disabled',isMinor);
 goalSwitch.classList.toggle('child-option-disabled',isMinor);
 const childHelp=panel.querySelector('.child-graph-options-help');
 if(childHelp)childHelp.hidden=!isMinor;"""
)

# No accidental rendering if the underlying values exist in old data:
# the gender/age checked gate is part of the chart computation itself.
once(
 " const treatmentEvents=treatmentCheck.checked&&Array.isArray(p.treatments)",
 " const treatmentEvents=!window.MonEvolutionChild?.isChildBirth?.(p.birthDate)&&treatmentCheck.checked&&Array.isArray(p.treatments)"
)
once(
 " const goalChartVisible=!!(goalCheck.checked&&scheduledGoal);",
 " const goalChartVisible=!!(!window.MonEvolutionChild?.isChildBirth?.(p.birthDate)&&goalCheck.checked&&scheduledGoal);"
)

# The old yellow flat goal shown in the user's screenshot comes from the
# adult-only goal (numeric placeholder for child profile compatibility).
# Hide it in pediatric charts rather than deleting the placeholder data.
once(
 "  if(kind==='weight'&&Number.isFinite(Number(p.goal)))values.push(Number(p.goal));",
 "  if(kind==='weight'&&!window.MonEvolutionChild?.isChildBirth?.(p.birthDate)&&Number.isFinite(Number(p.goal)))values.push(Number(p.goal));"
)
once(
 " if(kind==='weight'&&Number(p.goal)>v.yMin&&Number(p.goal)<v.yMax){",
 " if(kind==='weight'&&!window.MonEvolutionChild?.isChildBirth?.(p.birthDate)&&Number(p.goal)>v.yMin&&Number(p.goal)<v.yMax){"
)
once(
 " const rate=speed(r),forecast=predict(r,p);",
 " const rate=speed(r),forecast=isMinor?null:predict(r,p);"
)

# Explain why the controls are disabled. Preserve treatment entries, and do not
# infer that prescribed medical care is inappropriate in childhood.
once(
 " panel.insertBefore(goalSwitch,plot);\n goalCheck.onchange=()=>{pinchViewport=null;update()};",
 """ panel.insertBefore(goalSwitch,plot);
 const childGraphHelp=document.createElement('p');
 childGraphHelp.className='child-graph-options-help';
 childGraphHelp.textContent='Profil enfant : les options de traitement et d’objectif de poids sont désactivées sur cette courbe.';
 childGraphHelp.hidden=true;
 panel.insertBefore(childGraphHelp,plot);
 goalCheck.onchange=()=>{pinchViewport=null;update()};"""
)

style=r'''
<style id="mon-evolution-child-no-target-options-v189">
#evo-v159-graph .child-option-disabled{opacity:.55;cursor:not-allowed}
#evo-v159-graph .child-option-disabled input{cursor:not-allowed;accent-color:#849aab}
#evo-v159-graph .child-graph-options-help{font-size:12px;color:#b8d6de;margin:6px 0 12px;line-height:1.5}
#evo-v159-graph .child-graph-options-help[hidden]{display:none!important}
</style>
'''
once('</head>',style+'</head>')

for expected in [
 "treatmentCheck.checked=false","goalCheck.checked=false",
 "treatmentCheck.disabled=isMinor","goalCheck.disabled=isMinor",
 "treatmentSwitch.classList.toggle('child-option-disabled',isMinor)",
 "goalSwitch.classList.toggle('child-option-disabled',isMinor)",
 "forecast=isMinor?null:predict(r,p)",
 "const goalChartVisible=!!(!window.MonEvolutionChild",
 "const treatmentEvents=!window.MonEvolutionChild",
 "kind==='weight'&&!window.MonEvolutionChild",
 "mon-evolution-child-no-target-options-v189"
]: assert expected in s,expected
page.write_text(s,encoding="utf-8")
print("PASS v1.6.89: options enfant désactivées, objectifs et injections masqués seulement du graphique, adultes préservés")
