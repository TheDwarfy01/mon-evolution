#!/usr/bin/env python3
"""v1.6.90: WHO age-dependent shaded ranges for pediatric weight and height."""
from pathlib import Path

page=Path("android/source-1.6.90/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def once(before,after):
 global s
 n=s.count(before)
 if n!=1:
  raise AssertionError("Expected one anchor, found %s: %r"%(n,before[:145]))
 s=s.replace(before,after,1)

# BMI has four distinct clinical-reference bands. Weight-for-age and
# height-for-age instead use WHO -2/+2 SD as visually informative ranges:
# BLUE below -2 SD, GREEN between -2 and +2, AMBER above +2.
# These ranges must never be called "overweight" or "obesity" for height/weight.
once(
 """   const childPediatricBands=pediatricSamples.length>=2?[
    {...pediatricColors[0],points:zonePoints(()=>0,q=>q.bottom)},
    {...pediatricColors[1],points:zonePoints(q=>q.bottom,q=>q.overweight)},
    {...pediatricColors[2],points:zonePoints(q=>q.overweight,q=>q.obesity)},
    {...pediatricColors[3],points:zonePoints(q=>q.obesity,()=>100)}
   ]:[];
   for(const [z,label,color]""",
 """   const bmiBands=pediatricSamples.length>=2?[
    {...pediatricColors[0],points:zonePoints(()=>0,q=>q.bottom)},
    {...pediatricColors[1],points:zonePoints(q=>q.bottom,q=>q.overweight)},
    {...pediatricColors[2],points:zonePoints(q=>q.overweight,q=>q.obesity)},
    {...pediatricColors[3],points:zonePoints(q=>q.obesity,()=>100)}
   ]:[];
   // WHO 2007 supports age/height 5-19 and age/weight 5-10 only.
   // Each point is derived for its precise age, with no extrapolation.
   const growthMetricSamples=healthMetric==='weight'||healthMetric==='height'
    ?reference.map(q=>{
      const bottom=derived(q,-2),upper=derived(q,2);
      if(!Number.isFinite(bottom)||!Number.isFinite(upper)||bottom>=upper)return null;
      return {x:q[0],bottom,upper};
     }).filter(Boolean)
    :[];
   const growthColors=[
    {label:'Sous le repère OMS −2',color:'#4a91db',opacity:.22},
    {label:'Entre OMS −2 et +2',color:'#31b879',opacity:.24},
    {label:'Au-dessus du repère OMS +2',color:'#f1b74e',opacity:.23}
   ];
   const growthZone=(low,high)=>growthMetricSamples.map(q=>({
    x:q.x,lower:low(q),upper:high(q)
   }));
   const growthBands=growthMetricSamples.length>=2?[
    {...growthColors[0],points:growthZone(()=>0,q=>q.bottom)},
    {...growthColors[1],points:growthZone(q=>q.bottom,q=>q.upper)},
    {...growthColors[2],points:growthZone(q=>q.upper,()=>healthMetric==='height'?250:400)}
   ]:[];
   const childPediatricBands=healthMetric==='bmi'?bmiBands:growthBands;
   for(const [z,label,color]"""
)

once(
 """   }else{
    target.append(node('p','advanced-help',
     'Pour connaître la zone de corpulence estimée, sélectionne « IMC / âge ». Les courbes de poids et de taille seules ne permettent pas de classer la corpulence.'));
   }
   const safety=document.createElement('p');""",
 """   }else{
    const metricName=healthMetric==='weight'?'poids':'taille';
    const unit=healthMetric==='weight'?'kg':'cm';
    const ageRecorded=points.at(-1)?.x??null;
    const valueRecorded=points.at(-1)?.y??null;
    const refBottom=Number.isFinite(ageRecorded)
      ?interpolated(table,ageRecorded,q=>derived(q,-2)):null;
    const refUpper=Number.isFinite(ageRecorded)
      ?interpolated(table,ageRecorded,q=>derived(q,2)):null;
    const validReference=Number.isFinite(refBottom)&&Number.isFinite(refUpper)&&
      refBottom<refUpper;
    if(growthBands.length){
     const legend=node('div','child-bmi-zone-legend');
     for(const zone of growthColors){
      const item=node('span','child-bmi-zone-item');
      const swatch=node('i','child-bmi-zone-swatch');
      swatch.style.backgroundColor=zone.color;
      item.append(swatch,node('span','',zone.label));
      legend.append(item);
     }
     target.append(legend);
    }
    const evaluation=node('div','child-bmi-evaluation');
    evaluation.setAttribute('role','status');
    let headline='Référence indisponible',accent='#8297a9',message='';
    if(!validReference){
     message=healthMetric==='weight'
      ?'La référence OMS de poids pour l’âge disponible dans l’application couvre 5 à 10 ans. Ne pas extrapoler au-delà.'
      :'La référence OMS de taille pour l’âge disponible dans l’application couvre 5 à 19 ans. Ne pas extrapoler hors de cette plage.';
    }else if(valueRecorded<refBottom){
     headline='Zone bleue : sous le repère OMS −2';
     accent=growthColors[0].color;
     message='Mesure sous le repère bas pour cet âge. Un médecin peut l’interpréter avec la croissance dans la durée.';
    }else if(valueRecorded<=refUpper){
     headline='Zone verte : dans la plage des repères OMS';
     accent=growthColors[1].color;
     message='Mesure située entre les repères OMS −2 et +2 pour cet âge. Cela ne suffit pas à évaluer la corpulence.';
    }else{
     headline='Zone orange : au-dessus du repère OMS +2';
     accent=growthColors[2].color;
     message='Mesure au-dessus du repère haut pour cet âge, sans conclusion de surpoids ou d’obésité.';
    }
    if(sexUnknown)message+=' Sexe non précisé : il s’agit de la moyenne indicative fille/garçon, pas d’une norme médicale validée.';
    evaluation.style.setProperty('--child-bmi-accent',accent);
    evaluation.append(node('strong','',
     'Lecture '+metricName+' / âge : '+headline));
    evaluation.append(node('p','',
     'Dernière mesure : '+(Number.isFinite(valueRecorded)?fmt1(valueRecorded)+' '+unit:'indisponible')+
     ' · Âge au relevé : '+(Number.isFinite(ageRecorded)?fmt1(ageRecorded/12)+' ans':'indisponible')+'.'));
    if(validReference){
     evaluation.append(node('p','',
      'Repères OMS pour cet âge : '+fmt1(refBottom)+' à '+fmt1(refUpper)+' '+unit+'.'));
    }
    evaluation.append(node('p','',message));
    evaluation.append(node('small','',
     'Ces couleurs servent à lire les courbes de croissance. La taille et le poids par âge ne suffisent pas pour déterminer une corpulence normale, un surpoids ou une obésité. Consulte « IMC / âge » pour les repères de corpulence.'));
    target.append(evaluation);
   }
   const safety=document.createElement('p');"""
)

assert "const childPediatricBands=healthMetric==='bmi'?bmiBands:growthBands;" in s
assert "La référence OMS de poids pour l’âge" in s
assert "La référence OMS de taille pour l’âge" in s
assert "Lecture '+metricName+' / âge" in s
assert "pas d’une norme médicale validée" in s
assert "La taille et le poids par âge ne suffisent pas" in s
assert s.count("ageBands:childPediatricBands")==1
assert "const growthMetricSamples" in s
assert "interpolated(table,ageRecorded,q=>derived(q,-2))" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.90: zones OMS dynamiques poids/taille + lecture explicative sans diagnostic")
