#!/usr/bin/env python3
"""Graphes avancés v1.6.68 : périodes selon historique, légendes, zoom et visibilité."""
from pathlib import Path
page=Path("android/source-1.6.68/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
def change(before,after):
 global s
 if s.count(before)!=1:
  raise RuntimeError("Ancre absente ou ambiguë : "+before[:100]+" (count="+str(s.count(before))+")")
 s=s.replace(before,after,1)

change("let view='weight',period='90',reference=.5",
       "let view='weight',period='all',advancedZoom='local',advancedPinch=1,reference=.5")
change("function rangeRows(p){",
       """function availablePeriods(p){
  const length=Math.max(0,days(p.rows[0].date,p.rows.at(-1).date));
  const candidates=[7,14,30,60,90,180,365,730];
  const periods=candidates.filter(n=>n<=length).map(String);
  periods.push('all');
  return periods;
 }
 function rangeRows(p){""")
change("const width=640,height=290,left=56,right=14,top=16,bottom=44;",
       "const width=430,height=330,left=52,right=13,top=23,bottom=44;")
change("const root=svg('svg',{viewBox:'0 0 640 290',class:'advanced-graph',role:'img','aria-label':opts.title||'Graphique du poids'},target);",
       "const root=svg('svg',{viewBox:'0 0 '+width+' '+height,class:'advanced-graph',role:'img','aria-label':opts.title||'Graphique du poids'},target);")
change("""  if(opts.zeroY){minY=Math.min(0,minY);maxY=Math.max(0,maxY)}
  if(maxX-minX<1){maxX=minX+1}if(maxY-minY<.1){maxY=minY+1}""",
       """  if(opts.zeroY){minY=Math.min(0,minY);maxY=Math.max(0,maxY)}
  if(maxX-minX<1){maxX=minX+1}if(maxY-minY<.1){maxY=minY+1}
  if(opts.touchZoom){
   const magnify=Math.max(1,Math.min(8,Number(advancedPinch)||1));
   if(magnify>1){
    const xWidth=(maxX-minX)/magnify;
    minX=maxX-xWidth;
    const actual=series.filter(q=>q.notes).flatMap(q=>q.points||[])
      .filter(q=>Number.isFinite(q.x)&&Number.isFinite(q.y)&&q.x>=minX&&q.x<=maxX);
    const focus=actual.length?actual.at(-1).y:(minY+maxY)/2;
    const yWidth=Math.max(.2,(maxY-minY)/magnify);
    minY=focus-yWidth/2;
    maxY=focus+yWidth/2;
   }
  }""")
change("""  const clipId='advanced-graph-clip-'+(++graphPlotSerial);""",
       """  if(opts.touchZoom){
   root.style.touchAction='pan-y';
   let initial=0,initialZoom=1,proposed=1;
   const distance=t=>Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);
   root.addEventListener('touchstart',event=>{
    if(event.touches.length!==2)return;
    initial=Math.max(10,distance(event.touches));
    initialZoom=advancedPinch;proposed=advancedPinch;
    if(event.cancelable)event.preventDefault();
   },{passive:false});
   root.addEventListener('touchmove',event=>{
    if(!initial||event.touches.length!==2)return;
    proposed=Math.max(1,Math.min(8,initialZoom*distance(event.touches)/initial));
    root.style.transform='scale('+Math.max(.65,Math.min(2.1,proposed/initialZoom))+')';
    if(event.cancelable)event.preventDefault();
   },{passive:false});
   const finish=event=>{
    if(!initial||(event.touches&&event.touches.length>=2))return;
    initial=0;
    if(Math.abs(proposed-advancedPinch)>.04){
     advancedPinch=proposed;
     redraw();
    }else root.style.transform='';
   };
   root.addEventListener('touchend',finish,{passive:true});
   root.addEventListener('touchcancel',finish,{passive:true});
  }
  const clipId='advanced-graph-clip-'+(++graphPlotSerial);""")
change("""  const periods=['30','90','365','all'],labels={'30':'30 jours','90':'90 jours','365':'1 an',all:'Tout'};
  const index=periods.indexOf(period);
  // − réduit la durée ; + l'augmente, comme pour toute valeur numérique.
  stepper(target,'Période affichée',labels[period]||'90 jours',
   ()=>{period=periods[Math.max(0,index-1)];redraw()},
   ()=>{period=periods[Math.min(periods.length-1,index+1)];redraw()},
   index<=0,index>=periods.length-1);
  const advanced=toggleChartOptions(target);""",
       """  const periods=availablePeriods(p);
  const labels={'7':'7 jours','14':'14 jours','30':'30 jours','60':'60 jours',
   '90':'90 jours','180':'6 mois','365':'1 an','730':'2 ans',all:'Tout'};
  if(!periods.includes(period))period='all';
  const index=periods.indexOf(period);
  if(periods.length>1){
   stepper(target,'Période affichée',labels[period]||'Tout',
    ()=>{period=periods[Math.max(0,index-1)];advancedPinch=1;redraw()},
    ()=>{period=periods[Math.min(periods.length-1,index+1)];advancedPinch=1;redraw()},
    index<=0,index>=periods.length-1);
  }else target.append(node('p','advanced-help','Tout l’historique est affiché : davantage de périodes seront proposées au fil des pesées.'));
  const zoomRow=controls(target,[['Zoom sur mes mesures',advancedZoom==='local',()=>{
     advancedZoom='local';advancedPinch=1;redraw();
    }],['Échelle complète',advancedZoom==='global',()=>{
     advancedZoom='global';advancedPinch=1;redraw();
    }]]);
  zoomRow.style.margin='8px 0 4px';
  const zoomInfo=node('p','advanced-help',
   'Le zoom suit les mesures réelles sans écraser la courbe sous la ligne d’objectif. Écarte deux doigts pour agrandir, rapproche-les pour réduire.');
  zoomInfo.style.margin='3px 0 10px';target.append(zoomInfo);
  if(advancedPinch>1.04){
   const reset=button('Réinitialiser le zoom · '+advancedPinch.toFixed(1).replace('.',',')+'×',false,()=>{
     advancedPinch=1;redraw();
   });
   reset.style.cssText='font-size:12px;padding:9px 12px;background:#244b5f;color:#dffdf6;border:1px solid #5e9e9b;border-radius:10px;margin-bottom:8px';
   target.append(reset);
  }
  const advanced=toggleChartOptions(target);""")
change("advanced.append(checkbox('Afficher la tendance',trend,v=>{trend=v;redraw()}));",
       "advanced.append(checkbox('Moyenne glissante des pesées (tendance)',trend,v=>{trend=v;redraw()}));")
change("advanced.append(checkbox('Afficher la projection',projection,v=>{projection=v;redraw()}));",
       "advanced.append(checkbox('Prévision indicative à partir de la tendance',projection,v=>{projection=v;redraw()}));")
change("advanced.append(checkbox('Repères types',referenceBand,v=>{referenceBand=v;redraw()}));",
       "advanced.append(checkbox('Fourchette de scénarios (0,25 à 1 kg/semaine)',referenceBand,v=>{referenceBand=v;redraw()}));")
change("graph(target,series,{title:'Poids réel, tendance, objectif, repère et projection',xMin:minWindow,xMax:maxWindow});",
       "graph(target,series,{title:'Poids réel, tendance, objectif, repère et projection',xMin:minWindow,xMax:maxWindow,yMode:advancedZoom,touchZoom:true});")
change("""   target.append(checkbox('Afficher les références santé',healthReference,checked=>{healthReference=checked;redraw()}));
   if(healthReference){""",
       """   target.append(checkbox('Afficher les zones de santé (poids / IMC)',healthReference,checked=>{healthReference=checked;redraw()}));
   const help=node('p','advanced-help',healthReference
     ?'Références activées : les bandes colorées indiquent les catégories d’IMC adultes ; pour les enfants, courbes de croissance par âge.'
     :'Option désactivée : affiche la courbe de poids et les tendances, sans les catégories d’IMC. Coche pour voir les zones de corpulence.');
   help.style.margin='1px 0 14px';target.append(help);
   if(healthReference){""")
# Make all drawn charts more legible: width less extreme, chart fills more of the phone viewport.
change("graphPlotSerial=0;","graphPlotSerial=0;")
change("document.head.append(style);",
       """document.head.append(style);
 const enhancements=document.createElement('style');
 enhancements.textContent='#advanced-weight-panel .advanced-graph,.friend-view #advanced-friend-graphs .advanced-graph{height:auto;min-height:0;max-height:none;width:100%;display:block}' +
 '#advanced-weight-panel .advanced-stepper button:disabled{opacity:.3;cursor:default}' +
 '#advanced-weight-panel .advanced-legend{gap:7px 13px;margin:7px 0 2px;line-height:1.4}' +
 '#advanced-weight-panel .advanced-point-detail{margin-top:6px!important}' +
 '#advanced-weight-panel .advanced-help{margin:8px 0;line-height:1.4}';
 document.head.append(enhancements);""")
page.write_text(s,encoding="utf-8")
assert "availablePeriods(p)" in s and "touchZoom:true" in s
assert "Afficher les zones de santé (poids / IMC)" in s
assert "Échelle complète" in s
print("OK advanced graph dynamic periods, zoom, clarity and health legend")
