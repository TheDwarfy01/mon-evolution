#!/usr/bin/env python3
"""v1.6.69 : tendance observée et projection uniquement si historique suffisant."""
from pathlib import Path

page=Path("android/source-1.6.69/app/src/main/assets/index.html")
source=page.read_text(encoding="utf-8")
start=source.index(" function primaryGraph(target,p){")
end=source.index(" function progressGraph(target,p){",start)
part=source[start:end]

def once(before,after):
 global part
 n=part.count(before)
 if n!=1:
  raise AssertionError(f"Ancre du graphique manquante ou multiple ({n}): {before[:100]}")
 part=part.replace(before,after,1)

# Les indicateurs reposent uniquement sur des pesées, pas sur une perte choisie.
once("  const advanced=toggleChartOptions(target);", """  const historySpan=days(p.rows[0].date,p.rows.at(-1).date);
  const forecastReady=p.rows.length>=4&&historySpan>=21;
  const recentMeasurements=p.rows.filter(q=>utc(q.date)>=utc(p.rows.at(-1).date)-28*DAY).length;
  const forecastReliability=p.rows.length>=8&&historySpan>=42&&recentMeasurements>=4?'modérée':'limitée';
  const advanced=toggleChartOptions(target);""")
once("  advanced.append(checkbox('Prévision indicative à partir de la tendance',projection,v=>{projection=v;redraw()}));",
     """  if(forecastReady){
   advanced.append(checkbox('Prévision indicative à partir de la tendance',projection,v=>{projection=v;redraw()}));
  }else{
   advanced.append(node('p','advanced-help','Projection disponible à partir de 4 pesées réparties sur au moins 21 jours.'));
  }""")
once("  advanced.append(checkbox('Fourchette de scénarios (0,25 à 1 kg/semaine)',referenceBand,v=>{referenceBand=v;redraw()}));","")
once("  const series=[{label:'Poids réel',", """  const elapsed=days(p.rows[0].date,last.date);
  const weeklyChange=elapsed>=7?(p.rows[0].weight-last.weight)*7/elapsed:null;
  const averageText=weeklyChange===null
   ?'Variation moyenne réelle : au moins 7 jours de pesées nécessaires.'
   :weeklyChange>0.05
    ?'Perte moyenne réelle : '+fmt1(weeklyChange)+' kg/semaine'
    :weeklyChange<-.05
     ?'Prise moyenne réelle : '+fmt1(-weeklyChange)+' kg/semaine'
     :'Poids globalement stable (variation moyenne proche de 0 kg/semaine)';
  const average=node('p','advanced-help',averageText);
  average.classList.add('advanced-real-weekly');
  average.style.cssText='font-size:14px;font-weight:700;color:#e1f7f0;margin:14px 0 10px';
  average.title='Variation calculée depuis les premières jusqu’aux dernières mesures, sans hypothèse de perte future.';
  target.append(average);
  const series=[{label:'Poids réel',""")
start_b=part.index("  if(referenceBand){")
end_b=part.index("  const sl=slope(p);",start_b)
if not 0<end_b-start_b<1800:
 raise AssertionError("Section des scénarios inattendue")
part=part[:start_b]+part[end_b:]
once("if(projection&&sl!==null&&sl<-.014&&last.weight>p.goal){",
     "if(projection&&forecastReady&&sl!==null&&sl<-.014&&last.weight>p.goal){")
once("const horizon=Math.min(365,Math.max(28,(p.goal-last.weight)/sl));",
     "const horizon=Math.min(180,Math.max(28,(p.goal-last.weight)/sl));")
once("Poids réel, tendance, objectif, repère et projection",
     "Poids réel, tendance observée, objectif et projection conditionnelle")
last=part.index("  const choices=[.25,.5,.75,1],referenceIndex=choices.indexOf(reference);")
if part[last:].count("  advanced.append(node('p','advanced-help'")!=1:
 raise AssertionError("Ancienne aide des scénarios introuvable")
part=part[:last]+"""  const forecastVisible=projection&&forecastReady&&sl!==null&&sl<-.014&&last.weight>p.goal;
  const forecastText=!forecastReady
   ?'Projection masquée : historique insuffisant (4 pesées sur 21 jours minimum).'
   :!projection
    ?'Projection désactivée. Les mesures et la tendance observée restent visibles.'
    :!forecastVisible
     ?'Projection non affichée : la tendance mesurée ne montre pas actuellement de perte vers l’objectif.'
     :'Fiabilité indicative de la projection : '+forecastReliability+
      ' ('+p.rows.length+' pesées sur '+Math.round(historySpan)+' jours). Projection limitée à 6 mois, sans garantie de résultat.';
  advanced.append(node('p','advanced-help',forecastText));
 }
 """
updated=source[:start]+part+source[end:]
assert updated!=source
assert "Fourchette de scénarios (0,25 à 1 kg/semaine)" not in updated
assert "Repère (kg/semaine)" not in updated
assert "referenceIndex=choices.indexOf(reference)" not in updated
assert "advanced-real-weekly" in updated
assert "forecastReady=p.rows.length>=4&&historySpan>=21" in updated
assert "Fiabilité indicative de la projection" in updated
page.write_text(updated,encoding="utf-8")
print("OK 1.6.69 : suppression des scénarios, indicateur observé et projection conditionnelle")
