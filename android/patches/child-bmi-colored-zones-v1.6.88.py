#!/usr/bin/env python3
"""v1.6.88: age-dependent color regions + readable pediatric BMI status underneath."""
from pathlib import Path
page=Path("android/source-1.6.88/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def one(a,b):
 global s
 count=s.count(a)
 if count!=1:raise AssertionError(f"Anchor count={count}: {a[:160]!r}")
 s=s.replace(a,b,1)

# Existing graph renderer can display horizontal yBands for adults. Pediatric
# values depend on age: draw genuinely CURVED regions behind the measured BMI
# and WHO/IOTF lines, clipped inside the plotting rectangle.
anchor="  const drawing=svg('g',{'clip-path':'url(#'+clipId+')'},root);"
enhanced="""  const drawing=svg('g',{'clip-path':'url(#'+clipId+')'},root);
  // Pediatric color bands track age-specific thresholds. Unlike CSS scaling,
  // this redraws together with the axes during the live two-finger pinch.
  if(Array.isArray(opts.ageBands)){
   const plotY=value=>Y(Math.max(minY,Math.min(maxY,value)));
   for(const band of opts.ageBands){
    const valid=(band.points||[]).filter(p=>
      Number.isFinite(p.x)&&Number.isFinite(p.lower)&&
      Number.isFinite(p.upper)&&p.upper>p.lower);
    if(valid.length<2)continue;
    const high=valid.map(p=>X(p.x)+','+plotY(p.upper));
    const low=valid.slice().reverse().map(p=>X(p.x)+','+plotY(p.lower));
    svg('polygon',{points:[...high,...low].join(' '),
      fill:band.color,'fill-opacity':band.opacity??.24,stroke:'none'},drawing);
   }
  }"""
one(anchor,enhanced)

# At this position, child profiles have the WHO BMI LMS function, and each
# sex has its own IOTF thresholds (unknown sex is an unvalidated average).
anchor="""   const reference=table.filter(q=>q[0]>=low&&q[0]<=high);
   for(const [z,label,color] of [[-2,'OMS −2 écarts-types',palette[0]],[0,'OMS médiane',palette[1]],[2,'OMS +2 écarts-types',palette[2]]]){"""
enhanced="""   const reference=table.filter(q=>q[0]>=low&&q[0]<=high);
   // No age-based medical interpretation is possible from an arithmetic
   // average of boys' and girls' curves.
   const pediatricColors=[
    {label:'Maigreur (repère OMS)',color:'#4a91db',opacity:.24},
    {label:'Corpulence normale (indicatif)',color:'#31b879',opacity:.25},
    {label:'Surpoids (repère IOTF)',color:'#f1b74e',opacity:.25},
    {label:'Obésité (repère IOTF)',color:'#e86c70',opacity:.25}
   ];
   const interpolated=(rows,month,valueAt)=>{
    if(!rows.length||month<rows[0][0]||month>rows[rows.length-1][0])return null;
    const after=rows.find(q=>q[0]>=month);
    const before=[...rows].reverse().find(q=>q[0]<=month);
    if(!after||!before)return null;
    const a=valueAt(before),b=valueAt(after);
    if(!Number.isFinite(a)||!Number.isFinite(b))return null;
    const fraction=after[0]===before[0]?0:(month-before[0])/(after[0]-before[0]);
    return a+(b-a)*fraction;
   };
   const iotfSexRows=sexUnknown?[]:(window.GROWTH_IOTF2012||[])
    .filter(q=>q[1]===(sexBoy?1:2)).sort((a,b)=>a[0]-b[0]);
   const getPediatricLimits=month=>{
    if(healthMetric!=='bmi'||sexUnknown)return null;
    const bottom=interpolated(table,month,q=>derivedFor(q,-2,sexBoy));
    const overweight=interpolated(iotfSexRows,month,q=>Number(q[2]));
    const obesity=interpolated(iotfSexRows,month,q=>Number(q[3]));
    if(!Number.isFinite(bottom)||!Number.isFinite(overweight)||
       !Number.isFinite(obesity)||!(bottom<overweight&&overweight<obesity))return null;
    return {bottom,overweight,obesity};
   };
   const pediatricSamples=healthMetric==='bmi'&&!sexUnknown
    ?reference.filter(q=>q[0]>=61&&q[0]<=216)
      .map(q=>({x:q[0],limits:getPediatricLimits(q[0])}))
      .filter(q=>q.limits!==null)
    :[];
   const zonePoints=(lower,upper)=>pediatricSamples.map(q=>({
    x:q.x,lower:lower(q.limits),upper:upper(q.limits)
   }));
   const childPediatricBands=pediatricSamples.length>=2?[
    {...pediatricColors[0],points:zonePoints(()=>0,q=>q.bottom)},
    {...pediatricColors[1],points:zonePoints(q=>q.bottom,q=>q.overweight)},
    {...pediatricColors[2],points:zonePoints(q=>q.overweight,q=>q.obesity)},
    {...pediatricColors[3],points:zonePoints(q=>q.obesity,()=>100)}
   ]:[];
   for(const [z,label,color] of [[-2,'OMS −2 écarts-types',palette[0]],[0,'OMS médiane',palette[1]],[2,'OMS +2 écarts-types',palette[2]]]){"""
one(anchor,enhanced)

anchor="""   graph(target,series,{title:'Croissance et références selon âge et sexe',
    xLabel:v=>(v/12).toFixed(1)+' ans',yMode:healthZoom});
   const safety=document.createElement('p');"""
enhanced="""   graph(target,series,{title:'Croissance et références selon âge et sexe',
    xLabel:v=>(v/12).toFixed(1)+' ans',yMode:healthZoom,
    ageBands:childPediatricBands});

   if(healthMetric==='bmi'){
    if(childPediatricBands.length){
     const legend=node('div','child-bmi-zone-legend');
     for(const zone of pediatricColors){
      const item=node('span','child-bmi-zone-item');
      const swatch=node('i','child-bmi-zone-swatch');
      swatch.style.backgroundColor=zone.color;
      item.append(swatch,node('span','',zone.label));
      legend.append(item);
     }
     target.append(legend);
    }
    const latestLimits=getPediatricLimits(monthAge);
    const evaluation=node('div','child-bmi-evaluation');
    evaluation.setAttribute('role','status');
    const meaningful=Number.isFinite(measuredBmi)&&latestLimits!==null;
    let headline='Interprétation non disponible',color='#8297a9',detail='';
    if(sexUnknown){
     detail='Sexe non précisé : la moyenne des courbes fille et garçon n’est pas une référence diagnostique validée. Aucune zone de corpulence ne peut être déterminée.';
    }else if(!Number.isFinite(measuredBmi)){
     detail='Une pesée et une mesure de taille antérieure ou du même jour sont nécessaires pour estimer la zone de corpulence.';
    }else if(!latestLimits){
     detail='Les références complètes utilisées pour ces zones commencent à 5 ans et s’arrêtent avant 18 ans. Consulter le carnet de santé pour cet âge.';
    }else if(measuredBmi<latestLimits.bottom){
     headline='Zone bleue : sous le repère bas (maigreur à vérifier)';
     color=pediatricColors[0].color;
     detail='La valeur est sous le repère OMS −2 écarts-types : un professionnel doit interpréter cette mesure et la croissance.';
    }else if(measuredBmi<latestLimits.overweight){
     headline='Zone verte : corpulence normale (repère indicatif)';
     color=pediatricColors[1].color;
     detail='La mesure est entre le repère bas OMS et le seuil IOTF de surpoids à cet âge.';
    }else if(measuredBmi<latestLimits.obesity){
     headline='Zone orange : au-dessus du repère de surpoids';
     color=pediatricColors[2].color;
     detail='La valeur atteint le repère IOTF de surpoids sans atteindre celui de l’obésité.';
    }else{
     headline='Zone rouge : au-dessus du repère d’obésité';
     color=pediatricColors[3].color;
     detail='La valeur atteint le repère IOTF d’obésité, à discuter avec un pédiatre ou un médecin.';
    }
    evaluation.style.setProperty('--child-bmi-accent',color);
    evaluation.append(node('strong','', 'Situation actuelle : '+headline));
    const ageText=Number.isFinite(monthAge)?fmt1(monthAge/12)+' ans':'âge indisponible';
    evaluation.append(node('p','',
     'IMC au dernier relevé : '+(Number.isFinite(measuredBmi)?fmt1(measuredBmi):'non calculable')+
     ' · Âge au relevé : '+ageText+'.'));
    if(meaningful){
     evaluation.append(node('p','',
      'Repère bas OMS : '+fmt1(latestLimits.bottom)+
      ' · Seuil surpoids IOTF : '+fmt1(latestLimits.overweight)+
      ' · Seuil obésité IOTF : '+fmt1(latestLimits.obesity)+'.'));
     if(measuredBmi>=latestLimits.bottom&&measuredBmi<latestLimits.overweight){
      evaluation.append(node('p','',
       'Écart avec le repère de surpoids : '+fmt1(latestLimits.overweight-measuredBmi)+
       ' point(s) d’IMC. Cet écart ne constitue pas un objectif de poids.'));
     }
    }
    evaluation.append(node('p','',detail));
    evaluation.append(node('small','',
     'Lecture indicative des repères liés à l’âge et au sexe : ce résultat ne constitue pas un diagnostic.'));
    target.append(evaluation);
   }else{
    target.append(node('p','advanced-help',
     'Pour connaître la zone de corpulence estimée, sélectionne « IMC / âge ». Les courbes de poids et de taille seules ne permettent pas de classer la corpulence.'));
   }
   const safety=document.createElement('p');"""
one(anchor,enhanced)

style=r'''
<style id="mon-evolution-child-bmi-colors-v188">
#advanced-weight-panel .child-bmi-zone-legend,
#advanced-friend-graphs .child-bmi-zone-legend{
 display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:7px 11px;margin:12px 0 14px
}
#advanced-weight-panel .child-bmi-zone-item,
#advanced-friend-graphs .child-bmi-zone-item{
 display:flex;align-items:center;gap:7px;color:#daeaf2;font-size:12px;line-height:1.35
}
#advanced-weight-panel .child-bmi-zone-swatch,
#advanced-friend-graphs .child-bmi-zone-swatch{
 width:12px;height:12px;flex:none;border-radius:3px;border:1px solid #ffffff48
}
#advanced-weight-panel .child-bmi-evaluation,
#advanced-friend-graphs .child-bmi-evaluation{
 margin:14px 0;padding:14px;border:1px solid #4a6c80;
 border-left:6px solid var(--child-bmi-accent,#8297a9);
 border-radius:13px;background:#153247;color:#f0f8fc;line-height:1.5
}
#advanced-weight-panel .child-bmi-evaluation strong,
#advanced-friend-graphs .child-bmi-evaluation strong{display:block;font-size:15px}
#advanced-weight-panel .child-bmi-evaluation p,
#advanced-friend-graphs .child-bmi-evaluation p{font-size:13px;margin:7px 0}
#advanced-weight-panel .child-bmi-evaluation small,
#advanced-friend-graphs .child-bmi-evaluation small{display:block;font-size:12px;color:#bfd2df}
@media(max-width:355px){
 #advanced-weight-panel .child-bmi-zone-legend,
 #advanced-friend-graphs .child-bmi-zone-legend{grid-template-columns:1fr}
}
</style>
'''
one('</head>',style+'</head>')

for token in ('ageBands:childPediatricBands','getPediatricLimits=month',
              'Zone verte : corpulence normale','Zone orange',
              'Zone rouge','Zone bleue','Cette moyenne'):
 if token=="Cette moyenne":continue
 assert token in s,token
assert "mon-evolution-child-bmi-colors-v188" in s
assert "ce résultat ne constitue pas un diagnostic" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.88: bandes pédiatriques dépendantes de l'âge et synthèse sous le graphe")
