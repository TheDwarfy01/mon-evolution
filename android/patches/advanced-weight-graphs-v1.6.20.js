/* Advanced Mon Évolution weight visualization — no third-party services. */
(function(){
 'use strict';
 const DAY=86400000, NS='http://www.w3.org/2000/svg';
 const fmt1=v=>Number(v).toLocaleString('fr-FR',{maximumFractionDigits:1,minimumFractionDigits:1});
 const DATE=/^\d{4}-\d{2}-\d{2}$/;
 const utc=date=>Date.parse(date+'T12:00:00Z');
 const days=(a,b)=>(utc(b)-utc(a))/DAY;
 const dateAt=(a,d)=>new Date(utc(a)+d*DAY).toISOString().slice(0,10);
 const colors=['#78e4cf','#f7d77c','#8caeff','#f5a5c4','#ffb47d','#b5e68b','#c9a8ff'];
 let view='weight',period='all',reference=.5,trend=true,projection=true,referenceBand=false,metric='loss';
 let sharedMap=new Map(), sharedWanted=new Set(), sharedState='';
 let activeData=null;
 const personalChart=$('chart').querySelector(':scope > .card');
 const panel=document.createElement('div');panel.className='card';panel.id='advanced-weight-panel';
 if(personalChart)personalChart.hidden=true;
 $('chart').append(panel);
 const style=document.createElement('style');
 style.textContent='.advanced-controls{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.advanced-controls button,.advanced-controls select{width:auto;margin:0;padding:9px 11px;border:1px solid #4a6f82;border-radius:10px;background:#213e54;color:#edfaff;font-size:12px}.advanced-controls button.chosen{background:#2c706d;border-color:#8be8d4}.advanced-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}.advanced-stat{border:1px solid #345a70;background:#10293d;border-radius:12px;padding:12px}.advanced-stat b{display:block;font-size:18px;margin-top:5px}.advanced-stat small{color:#b3cede}.advanced-graph{display:block;width:100%;height:auto;min-height:240px}.advanced-legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:12px;color:#bcd2df;font-size:12px}.advanced-legend span:before{content:"● ";color:var(--legend-color)}.advanced-check{display:flex;gap:8px;align-items:center;margin:10px 0;color:#d6e7f0;font-size:13px}.advanced-check input{width:17px;height:17px;margin:0;accent-color:#7de3cf}.advanced-help{color:#a9c3d2;font-size:12px;line-height:1.5}.friend-view-active #advanced-weight-panel{display:none}';
 document.head.append(style);
 function node(tag,cls,text){
  const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;
 }
 function button(label,active,fn){
  const b=node('button',active?'chosen':'',label);b.type='button';b.onclick=fn;return b;
 }
 function sectionTitle(text){return node('h3','',text);}
 function controls(target,items){
  const box=node('div','advanced-controls');
  for(const item of items)box.append(button(item[0],item[1],item[2]));
  target.append(box);return box;
 }
 function checkbox(label,checked,fn){
  const row=node('label','advanced-check');const input=document.createElement('input');
  input.type='checkbox';input.checked=checked;input.onchange=()=>fn(input.checked);
  row.append(input,node('span','',label));return row;
 }
 function clean(p){
  if(!p||!Array.isArray(p.entries))return null;
  const entries=p.entries.filter(e=>e && DATE.test(e.date) && Number.isFinite(e.weight) && e.weight>=25 && e.weight<=400)
   .slice(0,20000).sort((a,b)=>a.date.localeCompare(b.date)||(Number(a.id)||0)-(Number(b.id)||0));
  if(!entries.length)return null;
  const unique=[];for(const e of entries){
   if(unique.length&&unique[unique.length-1].date===e.date)unique[unique.length-1]=e;
   else unique.push(e);
  }
  return {name:String(p.name||'Profil').slice(0,100),goal:Number(p.goal),height:Number(p.height)||0,rows:unique};
 }
 function current(){
  if(typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'))return clean(sharedMap.get(unifiedCurrent.slice(9))) ;
  return clean(profile());
 }
 function rangeRows(p){
  if(period==='all')return p.rows;
  const end=p.rows.at(-1).date;
  const cutoff=utc(end)-Number(period)*DAY;
  const subset=p.rows.filter(r=>utc(r.date)>=cutoff);
  const before=p.rows.filter(r=>utc(r.date)<cutoff).at(-1);
  return before?[before,...subset]:subset;
 }
 function interpolateAt(rows,target){
  const ordered=rows.filter(r=>utc(r.date)<=target);
  return ordered.length?ordered.at(-1):null;
 }
 function slope(p){
  const rows=p.rows,last=rows.at(-1),cutoff=utc(last.date)-28*DAY;
  let recent=rows.filter(r=>utc(r.date)>=cutoff);
  if(recent.length<3 || days(recent[0].date,last.date)<14)recent=rows;
  if(recent.length<3 || days(recent[0].date,recent.at(-1).date)<14)return null;
  const x0=utc(recent[0].date),xs=recent.map(r=>(utc(r.date)-x0)/DAY);
  const ys=recent.map(r=>r.weight),avgX=xs.reduce((a,b)=>a+b,0)/xs.length,avgY=ys.reduce((a,b)=>a+b,0)/ys.length;
  let num=0,den=0;xs.forEach((x,i)=>{num+=(x-avgX)*(ys[i]-avgY);den+=(x-avgX)**2});
  return den>0?num/den:null;
 }
 function stats(p){
  const rows=p.rows,first=rows[0],last=rows.at(-1),daySpan=days(first.date,last.date);
  const weekly=daySpan>=7?(first.weight-last.weight)*7/daySpan:null;
  const cutoff7=interpolateAt(rows,utc(last.date)-7*DAY);
  const cutoff30=interpolateAt(rows,utc(last.date)-30*DAY);
  const change7=cutoff7&&days(cutoff7.date,last.date)>=7?last.weight-cutoff7.weight:null;
  const change30=cutoff30&&days(cutoff30.date,last.date)>=30?last.weight-cutoff30.weight:null;
  const recentSlope=slope(p);
  const rate=recentSlope!==null?-recentSlope*7:null;
  const remaining=last.weight-p.goal;
  const eta=rate>0.1&&remaining>0?remaining/rate:null;
  const etaDate=eta!==null&&eta<=104?dateAt(last.date,Math.ceil(eta*7)):null;
  const month=rows.filter(r=>r.date.slice(0,7)===last.date.slice(0,7));
  const avgMonth=month.reduce((s,r)=>s+r.weight,0)/(month.length||1);
  const first14=interpolateAt(rows,utc(last.date)-14*DAY);
  const plateau=first14&&days(first14.date,last.date)>=14&&Math.abs(last.weight-first14.weight)<.2;
  return {first,last,weekly,change7,change30,rate,etaDate,avgMonth,plateau};
 }
 function shortNum(x,unit=' kg'){
  return Number.isFinite(x)?(x>0?'+':'')+fmt1(x)+unit:'Données insuffisantes';
 }
 function svg(tag,attrs,parent,textValue){
  const el=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs||{}))el.setAttribute(k,String(v));
  if(textValue!==undefined)el.textContent=textValue;
  if(parent)parent.append(el);
  return el;
 }
 function graph(target,series,opts={}){
  const width=640,height=290,left=56,right=14,top=16,bottom=44;
  const pts=series.flatMap(s=>s.points||[]).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
  if(!pts.length){target.append(node('p','advanced-help','Pas assez de mesures pour dessiner cette courbe.'));return;}
  let minX=Math.min(...pts.map(p=>p.x)),maxX=Math.max(...pts.map(p=>p.x));
  let minY=Math.min(...pts.map(p=>p.y)),maxY=Math.max(...pts.map(p=>p.y));
  if(opts.zeroY){minY=Math.min(0,minY);maxY=Math.max(0,maxY)}
  if(maxX-minX<1){maxX=minX+1}if(maxY-minY<.1){maxY=minY+1}
  const padY=(maxY-minY)*.09;minY-=padY;maxY+=padY;
  const X=v=>left+(v-minX)/(maxX-minX)*(width-left-right);
  const Y=v=>height-bottom-(v-minY)/(maxY-minY)*(height-top-bottom);
  const root=svg('svg',{viewBox:'0 0 640 290',class:'advanced-graph',role:'img','aria-label':opts.title||'Graphique du poids'},target);
  for(let i=0;i<=4;i++){
   const v=minY+(maxY-minY)*i/4,y=Y(v);
   svg('line',{x1:left,x2:width-right,y1:y,y2:y,stroke:'#36576c','stroke-width':1},root);
   svg('text',{x:left-8,y:y+5,'font-size':13,fill:'#b7cddb','text-anchor':'end'},root,fmt1(v));
  }
  for(let i=0;i<=4;i++){
   const v=minX+(maxX-minX)*i/4,x=X(v);
   svg('text',{x,y:height-16,'font-size':12,fill:'#b7cddb','text-anchor':'middle'},root,String(Math.round(v))+' j');
  }
  for(const s of series){
   const pp=(s.points||[]).filter(v=>Number.isFinite(v.x)&&Number.isFinite(v.y)).sort((a,b)=>a.x-b.x);
   if(!pp.length)continue;
   if(s.band){
    const polygon=pp.map(p=>X(p.x)+','+Y(p.y)).join(' ')+' '+pp.slice().reverse().map(p=>X(p.x)+','+Y(p.y2)).join(' ');
    svg('polygon',{points:polygon,fill:s.color,'fill-opacity':.14,stroke:'none'},root);continue;
   }
   if(pp.length>1)svg('polyline',{points:pp.map(p=>X(p.x)+','+Y(p.y)).join(' '),fill:'none',stroke:s.color||colors[0],'stroke-width':s.thin?2:3,'stroke-dasharray':s.dashed?'8 6':'none','stroke-linecap':'round','stroke-linejoin':'round'},root);
   if(pp.length===1)svg('circle',{cx:X(pp[0].x),cy:Y(pp[0].y),r:5,fill:s.color||colors[0]},root);
   if(s.notes){
    for(const p of pp.filter(p=>p.note)){
     const c=svg('circle',{cx:X(p.x),cy:Y(p.y),r:4,fill:'#fff0ac',stroke:'#142f43','stroke-width':1},root);
     svg('title',{},c,String(p.note).slice(0,120));
    }
   }
  }
  const leg=node('div','advanced-legend');for(const s of series.filter(s=>!s.band)){
   const span=node('span','',s.label);span.style.setProperty('--legend-color',s.color||colors[0]);leg.append(span);
  }target.append(leg);
 }
 function weeklyRecords(p){
  const byWeek=new Map();
  for(const row of p.rows){
   const d=new Date(utc(row.date)),dow=(d.getUTCDay()+6)%7;
   const monday=new Date(d.getTime()-dow*DAY).toISOString().slice(0,10);
   byWeek.set(monday,row);
  }
  const weeks=[...byWeek.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
  return weeks.slice(1).map(([key,row],i)=>({date:key,change:row.weight-weeks[i][1].weight})).slice(-16);
 }
 function metrics(target,p){
  const s=stats(p),items=[
   ['7 jours',shortNum(s.change7)],
   ['30 jours',shortNum(s.change30)],
   ['Moyenne depuis le départ',s.weekly===null?'Données insuffisantes':fmt1(s.weekly)+' kg/sem.'],
   ['Tendance récente',s.rate===null?'Données insuffisantes':fmt1(s.rate)+' kg/sem.'],
   ['Poids moyen du mois',fmt1(s.avgMonth)+' kg'],
   ['Objectif estimé',s.etaDate?day(s.etaDate):'Projection indisponible']
  ];
  const box=node('div','advanced-stats');
  for(const [label,value] of items){const cell=node('div','advanced-stat');cell.append(node('small','',label),node('b','',value));box.append(cell);}
  target.append(box);
  const info=node('p','advanced-help',s.plateau?'Poids stable sur 14 jours environ (variation inférieure à 0,2 kg).':'Les variations quotidiennes et les plateaux sont fréquents : privilégie la tendance de plusieurs semaines.');
  target.append(info);
 }
 function primaryGraph(target,p){
  target.append(sectionTitle('Évolution du poids'));
  controls(target,[['30 j',period==='30',()=>{period='30';redraw()}],['90 j',period==='90',()=>{period='90';redraw()}],['1 an',period==='365',()=>{period='365';redraw()}],['Tout',period==='all',()=>{period='all';redraw()}]]);
  controls(target,[['Réel + tendance',trend,()=>{trend=!trend;redraw()}],['Projection',projection,()=>{projection=!projection;redraw()}],['Repères types',referenceBand,()=>{referenceBand=!referenceBand;redraw()}]]);
  const rows=rangeRows(p),origin=p.rows[0].date,last=p.rows.at(-1),wEnd=days(origin,last.date);
  const series=[{label:'Poids réel',color:colors[0],notes:true,points:rows.map(r=>({x:days(origin,r.date),y:r.weight,note:r.note}))},
   {label:'Objectif',color:'#f7d77c',dashed:true,thin:true,points:[{x:0,y:p.goal},{x:wEnd,y:p.goal}]}];
  if(trend){
   const trendPoints=rows.map(r=>{
    let recent=p.rows.filter(q=>utc(q.date)<=utc(r.date)&&utc(q.date)>=utc(r.date)-7*DAY);
    if(recent.length<3)recent=p.rows.filter(q=>utc(q.date)<=utc(r.date)).slice(-3);
    return {x:days(origin,r.date),y:recent.reduce((s,q)=>s+q.weight,0)/recent.length};
   });
   series.push({label:'Tendance (7 jours / 3 pesées)',color:colors[2],points:trendPoints});
  }
  if(referenceBand){
   const horizon=Math.max(28,wEnd);
   series.unshift({band:true,color:'#7ee3cf',points:[{x:0,y:p.rows[0].weight,y2:p.rows[0].weight},{x:horizon,y:p.rows[0].weight-horizon/7*.25,y2:p.rows[0].weight-horizon/7*1}]});
  }
  const ref=Math.max(28,wEnd);
  series.push({label:'Repère '+fmt1(reference)+' kg/sem.',color:'#ffb47d',dashed:true,points:[{x:0,y:p.rows[0].weight},{x:ref,y:p.rows[0].weight-ref/7*reference}]});
  const sl=slope(p);
  if(projection&&sl!==null&&sl<-.014&&last.weight>p.goal){
   const horizon=Math.min(365,Math.max(28,(p.goal-last.weight)/sl));
   series.push({label:'Projection (indicative)',color:'#c9a8ff',dashed:true,points:[{x:wEnd,y:last.weight},{x:wEnd+horizon,y:last.weight+sl*horizon}]});
  }
  graph(target,series,{title:'Poids réel, tendance, objectif, repère et projection'});
  target.append(node('p','advanced-help','Repères 0,25 à 1 kg/semaine : simples scénarios, pas une norme médicale. Les projections prolongent la tendance passée et ne prédisent pas les résultats futurs.'));
  controls(target,[...([.25,.5,.75,1].map(value=>['Repère '+fmt1(value),reference===value,()=>{reference=value;redraw()}]))]);
 }
 function progressGraph(target,p){
  target.append(sectionTitle('Progression et évolution hebdomadaire'));
  const start=p.rows[0].weight,goal=p.goal;
  const loss=p.rows.map(r=>({x:days(p.rows[0].date,r.date),y:start-r.weight}));
  const objective=Math.max(.001,start-goal);
  graph(target,[{label:'Kg perdus cumulés',color:colors[0],points:loss},{label:'Objectif en kg',color:colors[1],dashed:true,points:[{x:0,y:objective},{x:Math.max(1,loss.at(-1).x),y:objective}]}],{title:'Perte cumulée depuis le départ',zeroY:true});
  const bars=weeklyRecords(p),area=node('div','',undefined);target.append(sectionTitle('Variation par semaine'));
  if(!bars.length){target.append(node('p','advanced-help','Au moins deux semaines de mesures sont nécessaires.'));return}
  const max=Math.max(.1,...bars.map(b=>Math.abs(b.change)));
  for(const b of bars){
   const line=node('div','',undefined);line.style.cssText='display:flex;align-items:center;gap:10px;margin:8px 0;font-size:12px';
   const name=node('span','',b.date.slice(5));name.style.width='42px';
   const track=node('div');track.style.cssText='height:15px;background:#1c4055;border-radius:8px;flex:1;overflow:hidden';
   const fill=node('div');fill.style.cssText='height:100%;width:'+Math.round(Math.abs(b.change)/max*100)+'%;background:'+(b.change<=0?'#78e4cf':'#f2a3a3')+';border-radius:8px';
   track.append(fill);const val=node('span','',shortNum(b.change));val.style.minWidth='70px';
   line.append(name,track,val);area.append(line);
  }
  target.append(area);
  target.append(node('p','advanced-help','Une barre compare les dernières pesées de deux semaines consécutives contenant des mesures. Vert : baisse de poids ; rose : hausse.'));
 }
 function validComparison(p){
  return p&&p.rows.length>0&&Number.isFinite(p.goal);
 }
 function compareTarget(target){
  target.append(sectionTitle('Comparer les profils'));
  target.append(node('p','advanced-help','Pour comparer équitablement des personnes qui démarrent à des dates ou poids différents, chaque courbe commence à son premier jour de suivi (jour 0).'));
  const people=[...(data.profiles||[]).map(p=>({id:'local:'+p.id,name:p.name,local:true})),
    ...getReceivedList().map(p=>({id:'received:'+p.key,name:p.name,local:false}))];
  const opts=node('div');
  for(const item of people){
   if(item.id===unifiedCurrent)continue;
   opts.append(checkbox(item.name+(item.local?' · Personnel':' · Partagé'),sharedWanted.has(item.id),checked=>{
    if(checked){sharedWanted.add(item.id);if(!item.local&&!sharedMap.has(item.id.slice(9)))window.AndroidBackup?.loadComparisonProfile?.(item.id.slice(9))}
    else sharedWanted.delete(item.id);
    redraw();
   }));
  }target.append(opts);
  const refresh=button('↻ Actualiser les profils partagés',false,()=>{
   const selected=[...sharedWanted].filter(id=>id.startsWith('received:'));
   if(!selected.length){sharedState='Choisis au moins un ami à comparer.';redraw();return}
   sharedState='Actualisation des profils choisis…';
   for(const id of selected)window.AndroidBackup?.loadComparisonProfile?.(id.slice(9));
   redraw();
  });
  target.append(refresh);
  if(sharedState)target.append(node('p','advanced-help',sharedState));
  controls(target,[['Poids réel',metric==='weight',()=>{metric='weight';redraw()}],['Kg perdus',metric==='loss',()=>{metric='loss';redraw()}],['% du poids initial',metric==='initial',()=>{metric='initial';redraw()}],['% de l’objectif',metric==='goal',()=>{metric='goal';redraw()}]]);
  const selected=[{id:unifiedCurrent,p:current()}];
  for(const id of sharedWanted){
   if(id.startsWith('local:'))selected.push({id,p:clean((data.profiles||[]).find(p=>'local:'+p.id===id))});
   else selected.push({id,p:clean(sharedMap.get(id.slice(9)))});
  }
  const series=[];let idx=0;
  for(const {p} of selected){
   if(!validComparison(p))continue;
   const first=p.rows[0],goalRange=first.weight-p.goal;
   if(metric==='goal'&&goalRange<=0)continue;
   const points=p.rows.map(r=>{
    let y=r.weight;if(metric==='loss')y=first.weight-r.weight;
    else if(metric==='initial')y=100*(first.weight-r.weight)/first.weight;
    else if(metric==='goal')y=100*(first.weight-r.weight)/goalRange;
    return {x:days(first.date,r.date),y};
   });
   series.push({label:p.name,color:colors[idx++%colors.length],points});
  }
  if(series.length)graph(target,series,{title:'Comparaison des profils : '+metric,zeroY:metric!=='weight'});
  else target.append(node('p','advanced-help','Aucune courbe comparable disponible. Vérifie les mesures et actualise les profils partagés.'));
  target.append(node('p','advanced-help','Les profils reçus restent en lecture seule. Leurs mesures servent uniquement à l’affichage de ce graphique et ne sont pas enregistrées dans ton profil personnel.'));
 }
 function redraw(friendArea){
  const p=current();
  const target=friendArea||((typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:'))?$('chart').querySelector('.friend-view #advanced-friend-graphs'):panel);
  if(!target)return;
  target.replaceChildren();
  if(!p){target.append(node('p','advanced-help','Sélectionne un profil puis charge ses mesures pour afficher les graphiques.'));return;}
  controls(target,[['Poids',view==='weight',()=>{view='weight';redraw()}],['Progression',view==='progress',()=>{view='progress';redraw()}],['Comparaison',view==='compare',()=>{view='compare';redraw()}]]);
  if(view==='weight')primaryGraph(target,p);
  else if(view==='progress')progressGraph(target,p);
  else compareTarget(target);
  if(view!=='compare')metrics(target,p);
 }
 // For shared profiles, insert the same graphs in the read-only friend view
 // instead of the old static SVG copied into the friend panel.
 window.onFriendChartView=section=>{
  section.querySelectorAll('.card').forEach(e=>e.remove());
  const area=node('div','');area.id='advanced-friend-graphs';section.append(area);
  redraw(area);
 };
 const oldLoaded=window.sharedLoaded;
 window.sharedLoaded=function(encoded,key){
  try{
   const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
   const doc=JSON.parse(new TextDecoder().decode(bytes));
   if(doc.format==='mon-evolution-lecture-seule'&&doc.version===1&&doc.profile&&typeof key==='string')sharedMap.set(key,{name:doc.profile.name,height:doc.profile.height,goal:doc.profile.goal,entries:doc.profile.entries});
  }catch(e){/* Only validated data is displayed by oldLoaded. */}
  const result=oldLoaded(encoded,key);
  if(!$('chart').hidden)redraw();
  return result;
 };
 // Background reading of other authorized shared profiles, without changing
 // the selected profile. The backend returns only permitted weight measurements.
 window.comparisonProfileLoaded=function(key,base64){
  try{
   const text=new TextDecoder().decode(Uint8Array.from(atob(base64),c=>c.charCodeAt(0)));
   const p=JSON.parse(text);
   if(!/^[a-f0-9-]{36}$/.test(key)||!clean(p))throw Error('invalid');
   sharedMap.set(key,p);sharedState='Profils partagés actualisés.';
  }catch(e){sharedState='Données de comparaison indisponibles.'}
  if(!$('chart').hidden)redraw();
 };
 window.comparisonProfileFailed=function(key){
  sharedState='Impossible de lire un profil partagé. Vérifie son lien Drive et son code.';
  if(!$('chart').hidden)redraw();
 };
 const originalRender=render;
 render=function(){originalRender();if(!$('chart').hidden&&!(unifiedCurrent||'').startsWith('received:'))redraw()};
 const chartButton=document.querySelector('[data-tab="chart"]');
 if(chartButton)chartButton.addEventListener('click',()=>{
  if(!(unifiedCurrent||'').startsWith('received:'))redraw();
 });
 // The visual profile switcher calls selectUnified and nav updates; leave the
 // underlying profile selection mechanisms intact.
 redraw();
})();
