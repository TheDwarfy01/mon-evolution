#!/usr/bin/env python3
"""v1.6.78: chronological treatment lifecycle and recurring planned dose markers."""
from pathlib import Path
page=Path("android/source-1.6.78/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")

def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise AssertionError(f"Treatment recurrence anchor {n}: {old[:110]!r}")
 s=s.replace(old,new,1)

# Keep legacy event values intact in stored profiles.
once("['injection','change','stop'].includes(e.kind)",
     "['start','injection','change','stop'].includes(e.kind)")
once("const right=Math.min(v.xMax,endTime,last.t);",
     "const right=Math.min(v.xMax,endTime);")
once("if(active)paintPhase(active,last.t);",
     "if(active)paintPhase(active,v.xMax);")
once(
"""   if(active)paintPhase(active,v.xMax);
  }
 }
 svg.append(dataLayer);""",
"""   if(active)paintPhase(active,v.xMax);
  }
  // Frequency markers are a schedule, NOT proof of actual administrations.
  // Recalculate for every phase; a change or an end interrupts the old frequency.
  const intervals={daily:1,weekly:7,biweekly:14};
  for(const items of byName.values()){
   for(let i=0;i<items.length;i++){
    const evt=items[i];
    if(!['start','change'].includes(evt.kind)&&!(evt.kind==='injection'&&i===0))continue;
    const frequency=evt.frequency||'none';
    if(!['daily','weekly','biweekly','monthly'].includes(frequency))continue;
    let until=v.xMax;
    for(const later of items.slice(i+1)){
     if(['start','change','stop'].includes(later.kind)){
      until=Math.min(until,ts(later.date));break;
     }
    }
    const base=ts(evt.date);
    for(let k=1;k<=400;k++){
     let occurrence;
     if(frequency==='monthly'){
      const d=new Date(base),year=d.getFullYear(),month=d.getMonth()+k;
      const lastDay=new Date(year,month+1,0).getDate();
      occurrence=new Date(year,month,Math.min(d.getDate(),lastDay),12).getTime();
     }else occurrence=base+k*intervals[frequency]*86400000;
     if(occurrence>=until||occurrence>v.xMax)break;
     if(occurrence<v.xMin)continue;
     const x=X(occurrence);
     const marker=svgElement('line',{x1:x,x2:x,y1:T,y2:T+chartH,
       stroke:'#b9a2ff','stroke-width':1,'stroke-dasharray':'2 5','stroke-opacity':'.62'});
     dataLayer.append(marker);
     const hit=svgElement('rect',{x:x-4,y:T,width:8,height:chartH,fill:'transparent',style:'cursor:pointer'});
     const dayLabel=new Date(occurrence).toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'});
     const detail='Prise prévue (non confirmée) · '+evt.name+' · '+evt.dose+' '+(evt.unit||'mg');
     const label=svgElement('title');label.textContent=dayLabel+' · '+detail;
     hit.append(label);hit.addEventListener('click',()=>{pointInfo.textContent=dayLabel+' · '+detail;});
     dataLayer.append(hit);
    }
   }
  }
 }
 svg.append(dataLayer);"""
)
once(
"""'<label class="field">Événement<select id="treatment-kind"><option value="injection">Injection / prise</option><option value="change">Début / changement</option><option value="stop">Arrêt</option></select></label>',""",
"""'<label class="field">Événement<select id="treatment-kind"><option value="start">Début du traitement</option><option value="change">Changement de dose / rythme</option><option value="stop">Arrêt du traitement</option></select></label>',"""
)
once(
"""'</div><label class="field">Note (facultatif)<input id="treatment-note" maxlength="160" placeholder="Ex. site d’injection, information personnelle"></label>',""",
"""'</div><label class="field">Fréquence des prises / injections<select id="treatment-frequency"><option value="weekly">Chaque semaine</option><option value="biweekly">Toutes les deux semaines</option><option value="monthly">Chaque mois</option><option value="daily">Chaque jour</option><option value="none">Sans répétition planifiée</option></select></label>',
 '<label class="field">Note (facultatif)<input id="treatment-note" maxlength="160" placeholder="Ex. jour de prise, informations personnelles"></label>',"""
)
once("const list=get('treatment-list'),submit=get('treatment-submit'),cancel=get('treatment-cancel');",
     "const list=get('treatment-list'),submit=get('treatment-submit'),cancel=get('treatment-cancel'),frequency=get('treatment-frequency');")
once("const kindName={injection:'Injection / prise',change:'Début / changement',stop:'Arrêt'};",
     """const kindName={start:'Début',injection:'Prise ponctuelle enregistrée',change:'Changement',stop:'Arrêt'};
const freqName={daily:'chaque jour',weekly:'chaque semaine',biweekly:'toutes les deux semaines',monthly:'chaque mois',none:'sans répétition'};""")
once(
""" dose.disabled=stopped;unit.disabled=stopped;dose.required=!stopped;
 dose.closest('label').style.opacity=stopped?'.45':'1';
 unit.closest('label').style.opacity=stopped?'.45':'1';""",
""" dose.disabled=stopped;unit.disabled=stopped;dose.required=!stopped;
 frequency.disabled=stopped;
 dose.closest('label').style.opacity=stopped?'.45':'1';
 unit.closest('label').style.opacity=stopped?'.45':'1';
 frequency.closest('label').style.opacity=stopped?'.45':'1';"""
)
once(
"""title.textContent=e.name+' · '+(kindName[e.kind]||'Événement');""",
"""const prior=events.some(row=>row!==e&&row.name.trim().toLowerCase()===e.name.trim().toLowerCase()
   &&row.date<e.date&&row.kind!=='stop');
  const displayKind=e.kind==='change'&&!prior?'Début':(kindName[e.kind]||'Événement');
  title.textContent=e.name+' · '+displayKind;"""
)
once(
"""sub.textContent=dayLabel+(e.kind==='stop'?'':' · '+e.dose+' '+e.unit)+(e.note?' · '+e.note:'');""",
"""sub.textContent=dayLabel+(e.kind==='stop'?'':' · '+e.dose+' '+e.unit+
   (e.frequency?' · '+(freqName[e.frequency]||e.frequency):' · fréquence à préciser'))+
   (e.note?' · '+e.note:'');"""
)
once(
"""get('treatment-name').value=e.name;kind.value=e.kind;
   get('treatment-date').value=e.date;dose.value=e.dose||'';unit.value=e.unit||'mg';""",
"""get('treatment-name').value=e.name;kind.value=e.kind==='injection'?'start':e.kind;
   if(e.kind==='change'&&!prior)kind.value='start';
   get('treatment-date').value=e.date;dose.value=e.dose||'';unit.value=e.unit||'mg';
   frequency.value=e.frequency||'none';"""
)
once(
"""unit:action==='stop'?'':unit.value,
  note:get('treatment-note').value.trim()};""",
"""unit:action==='stop'?'':unit.value,
  frequency:action==='stop'?'none':frequency.value,
  note:get('treatment-note').value.trim()};"""
)
once(
"""'<p class="notice treatment-intro">Historique privé du profil. Enregistre les injections, changements de dose ou arrêts. Les événements s’affichent sur la courbe du poids.</p>',""",
"""'<p class="notice treatment-intro">Enregistre le début, les changements et l’arrêt de chaque traitement. La fréquence programme des repères sur la courbe : une prise prévue n’est jamais considérée comme confirmée.</p>',"""
)
once(
"""'<p class="notice">Données incluses dans la sauvegarde privée du profil, non transmises dans les profils partagés. Cette chronologie n’indique pas l’effet médical d’un traitement.</p>'""",
"""'<p class="notice">Les repères automatiques indiquent uniquement les dates théoriques, sans confirmer les injections. Données incluses dans la sauvegarde privée, non transmises aux profils partagés.</p>'"""
)
once("name.textContent='Traitements : zones = doses, traits verticaux = événements';",
     "name.textContent='Traitements : zones = périodes, traits fins pointillés = prises prévues (non confirmées)';")
assert "treatment-frequency" in s
assert "frequency:action==='stop'?'none':frequency.value" in s
assert "Prise prévue (non confirmée)" in s
assert "Début du traitement" in s
page.write_text(s,encoding="utf-8")
print("PASS v1.6.78: début / changement / arrêt et récurrence planifiée")
