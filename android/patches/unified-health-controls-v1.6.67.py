#!/usr/bin/env python3
"""v1.6.67 : le panneau principal pilote seul les zones santé ; analyse distincte en bas."""
from pathlib import Path

page=Path("android/source-1.6.67/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def once(old,new):
 global s
 n=s.count(old)
 if n!=1:
  raise AssertionError(f"Ancre introuvable ou ambiguë ({n}): {old[:100]}")
 s=s.replace(old,new,1)

once(
 " let view='weight',period='all',advancedZoom='local',advancedPinch=1,reference=.5",
 " window.MonEvolutionHealthZones=window.MonEvolutionHealthZones||{enabled:true};\n"
 " let view='weight',period='all',advancedZoom='local',advancedPinch=1,reference=.5")
once(
 "metric='loss',healthReference=false,healthMetric='weight'",
 "metric='loss',healthReference=window.MonEvolutionHealthZones.enabled,healthMetric='weight'")

start=s.index(" function redraw(friendArea){")
end=s.index(" // For shared profiles, insert the same graphs", start)
assert 0<end-start<4000, "Panneau avancé a changé"
s=s[:start]+""" function redraw(friendArea){
  const p=current();
  const target=friendArea||((typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'))?$('chart').querySelector('.friend-view #advanced-friend-graphs'):panel);
  if(!target)return;
  target.replaceChildren();
  if(!p){target.append(node('p','advanced-help','Sélectionne un profil puis charge ses mesures pour afficher les graphiques.'));return;}
  healthReference=window.MonEvolutionHealthZones.enabled!==false;
  controls(target,[['Poids',view==='weight',()=>{view='weight';redraw()}],
   ['Progression',view==='progress',()=>{view='progress';redraw()}],
   ['Comparaison',view==='compare',()=>{view='compare';redraw()}],
   ['Références',view==='health',()=>{view='health';redraw()}]]);
  if(view==='weight'){
   // La courbe d’analyse avancée reste accessible avec ou sans zones.
   primaryGraph(target,p);
  }else if(view==='health'){
   if(!healthReference){
    target.append(node('p','advanced-help',
     'Les zones santé sont masquées. Active-les avec « Zones santé » dans le graphique principal pour consulter les références détaillées.'));
   }else{
    const child=p.birthDate&&Number.isFinite(utc(p.birthDate))&&days(p.birthDate,p.rows.at(-1).date)<365.25*18;
    const options=child?[['Poids','weight'],['Taille','height'],['IMC','bmi']]:[['Poids','weight'],['IMC','bmi']];
    if(!options.some(v=>v[1]===healthMetric))healthMetric='weight';
    controls(target,options.map(v=>[v[0],healthMetric===v[1],()=>{healthMetric=v[1];redraw()}]));
    healthReferenceGraph(target,p);
   }
  }else if(view==='progress')progressGraph(target,p);
  else compareTarget(target);
  if(view!=='compare')metrics(target,p);
 }
 // Un seul commutateur « Zones santé » en haut contrôle tous les graphiques.
 window.addEventListener('mon-evolution-health-zones-changed',()=>{
  healthReference=window.MonEvolutionHealthZones.enabled!==false;
  redraw();
 });
""" +s[end:]

once('<section id="chart" hidden><h2>Graphique</h2><p class="muted">Évolution du poids · ligne dorée : objectif</p>',
     '<section id="chart" hidden><h2>Analyse détaillée</h2><p class="muted">Tendances, progression, comparaisons et références.</p>')

assert "checkbox('Afficher les zones de santé" not in s
assert "['Références',view==='health'" in s
assert "window.addEventListener('mon-evolution-health-zones-changed'" in s
assert "healthReferenceGraph(target,p)" in s
assert 'availablePeriods(p)' in s
assert 'touchZoom:true' in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.67: panneau avancé indépendant et référence détaillée accessible")
