#!/usr/bin/env python3
"""v1.6.17: read-only friend meal calendar with day markers and meal detail."""
from pathlib import Path
root=Path("android/source-1.6.17/app")
h=root/"src/main/assets/index.html"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise AssertionError(f"{path}: {n} occurrences for {old[:110]!r}")
    path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 32","versionCode 33")
R(g,"versionName '1.6.16'","versionName '1.6.17'")
R(m,'android:versionCode="32" android:versionName="1.6.16"','android:versionCode="33" android:versionName="1.6.17"')
R(j,"MonEvolutionIMC/1.6.16","MonEvolutionIMC/1.6.17")
R(h,'Version installée : <strong>1.6.16</strong>','Version installée : <strong>1.6.17</strong>')
R(h,'const installed="1.6.16";','const installed="1.6.17";')
# The received document is cached ONLY in JS memory. The personal data tree is
# never overwritten and decrypted pictures are never put in localStorage.
R(h," let receivedTab='home';",
""" let receivedTab='home';
 const friendMealsCache=new Map();
 const friendMealNavigation=new Map();
 // Keep the validated shared document's meal data for its calendar.
 // sharedLoaded itself validates the structure and invokes onReceivedProfileLoaded.
 const originalSharedLoaded=window.sharedLoaded;
 window.sharedLoaded=function(encoded,key){
  try{
   const raw=new TextDecoder().decode(Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)));
   const doc=JSON.parse(raw);
   if(doc.format==='mon-evolution-lecture-seule' && doc.version===1 &&
      doc.profile && doc.profile.meals && typeof doc.profile.meals==='object' &&
      !Array.isArray(doc.profile.meals) && typeof key==='string'){
     friendMealsCache.set(key,doc.profile.meals);
   }else friendMealsCache.delete(key);
  }catch(e){friendMealsCache.delete(key);}
  return originalSharedLoaded(encoded,key);
 };
 function renderFriendMealCalendar(container,key){
  const meals=friendMealsCache.get(key);
  if(!meals){
   const text=document.createElement('p');
   text.className='notice';
   text.textContent='Chargement du calendrier des repas partagés…';
   container.append(text);
   return;
  }
  const available=Object.keys(meals).filter(date=>
   /^\\d{4}-\\d{2}-\\d{2}$/.test(date) && meals[date] &&
   typeof meals[date]==='object' && mealTypes.some(([k])=>
    String(meals[date][k]||'').trim() || meals[date][k+'Photo']
   )).sort();
  const now=dateNow();
  const latest=available.at(-1)||now;
  let selection=friendMealNavigation.get(key)||{month:latest.slice(0,7),day:latest};
  if(!/^\\d{4}-\\d{2}$/.test(selection.month))selection={month:latest.slice(0,7),day:latest};
  const card=document.createElement('div');card.className='card';
  const title=document.createElement('h3');title.textContent='Calendrier des repas';card.append(title);
  const explanation=document.createElement('p');explanation.className='notice';
  explanation.textContent='Un point indique qu’un repas ou une photo est disponible pour ce jour. Appuie sur une date pour le consulter.';
  card.append(explanation);
  const toolbar=document.createElement('div');
  toolbar.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:12px 0';
  const prev=document.createElement('button');prev.type='button';prev.className='secondary';prev.textContent='‹';prev.setAttribute('aria-label','Mois précédent');
  const month=document.createElement('strong');
  const next=document.createElement('button');next.type='button';next.className='secondary';next.textContent='›';next.setAttribute('aria-label','Mois suivant');
  toolbar.append(prev,month,next);card.append(toolbar);
  const grid=document.createElement('div');grid.className='friend-meal-grid';card.append(grid);
  const detail=document.createElement('div');detail.className='friend-meal-details';card.append(detail);
  function renderDetails(){
   detail.replaceChildren();
   const heading=document.createElement('h4');heading.textContent='Repas du '+day(selection.day);detail.append(heading);
   const record=meals[selection.day];
   if(!record||!mealTypes.some(([k])=>String(record[k]||'').trim()||record[k+'Photo'])){
    const empty=document.createElement('p');empty.className='notice';empty.textContent='Aucun repas partagé pour cette date.';detail.append(empty);return;
   }
   for(const [mealKey,label] of mealTypes){
    const info=String(record[mealKey]||'').trim();
    const photo=record[mealKey+'Photo'];
    if(!info&&!photo)continue;
    const block=document.createElement('div');block.className='friend-meal-item';
    const labelNode=document.createElement('strong');labelNode.textContent=label;block.append(labelNode);
    if(info){const text=document.createElement('p');text.textContent=info.slice(0,3000);block.append(text);}
    if(typeof photo==='string'&&photo.startsWith('data:image/jpeg;base64,')&&photo.length<250000){
     const image=document.createElement('img');image.src=photo;image.alt='Photo du '+label;
     image.style.cssText='display:block;width:100%;height:210px;object-fit:cover;border-radius:12px;margin-top:10px;cursor:zoom-in';
     image.onclick=()=>window.showMealPhoto?.(image.src);
     block.append(image);
    }
    detail.append(block);
   }
  }
  function renderMonth(){
   const [year,monthIndex]=selection.month.split('-').map(Number);
   if(!year||!monthIndex||monthIndex<1||monthIndex>12)return;
   month.textContent=new Date(year,monthIndex-1,1).toLocaleDateString('fr-FR',{month:'long',year:'numeric'});
   grid.replaceChildren();
   for(const label of ['L','M','M','J','V','S','D']){
    const cell=document.createElement('span');cell.className='friend-weekday';cell.textContent=label;grid.append(cell);
   }
   const offset=(new Date(year,monthIndex-1,1).getDay()+6)%7;
   for(let i=0;i<offset;i++)grid.append(document.createElement('span'));
   const count=new Date(year,monthIndex,0).getDate();
   for(let n=1;n<=count;n++){
    const date=selection.month+'-'+String(n).padStart(2,'0');
    const has=available.includes(date);
    const b=document.createElement('button');b.type='button';b.textContent=n;
    b.className='friend-meal-day'+(has?' has-friend-meals':'')+
      (date===selection.day?' friend-meal-selected':'');
    b.setAttribute('aria-label',day(date)+(has?', repas disponibles':''));
    b.onclick=()=>{
     selection.day=date;friendMealNavigation.set(key,{...selection});
     renderMonth();renderDetails();
    };
    grid.append(b);
   }
  }
  function changeMonth(delta){
   const [y,m]=selection.month.split('-').map(Number);
   const date=new Date(y,m-1+delta,1);
   selection.month=date.getFullYear()+'-'+String(date.getMonth()+1).padStart(2,'0');
   selection.day=selection.month+'-01';
   friendMealNavigation.set(key,{...selection});
   renderMonth();renderDetails();
  }
  prev.onclick=()=>changeMonth(-1);
  next.onclick=()=>changeMonth(1);
  container.append(card);
  renderMonth();renderDetails();
 }""")
R(h,"  const source=cards[index[tab]];\n  if(source){",
"""  const source=cards[index[tab]];
  if(tab==='meals'){
   renderFriendMealCalendar(section,unifiedCurrent.slice(9));
  }else if(source){""")
R(h," sheet.textContent='.friend-view-active > :not(.friend-view){display:none!important}.friend-view-active > .friend-view{display:block}.friend-view .card{margin-top:12px}';",
""" sheet.textContent='.friend-view-active > :not(.friend-view){display:none!important}.friend-view-active > .friend-view{display:block}.friend-view .card{margin-top:12px}'+
 '.friend-meal-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}'+
 '.friend-weekday{text-align:center;color:#9ab5c7;font-size:12px;padding:8px 0}'+
 '.friend-meal-day{position:relative;min-height:45px;padding:7px 2px 15px!important;border-radius:10px}'+
 '.friend-meal-day.has-friend-meals::after{content:\"\";position:absolute;bottom:5px;left:50%;transform:translateX(-50%);width:6px;height:6px;border-radius:50%;background:#76e4d0}'+
 '.friend-meal-day.friend-meal-selected{outline:2px solid #76e4d0}'+
 '.friend-meal-details{margin-top:20px}.friend-meal-item{padding:14px 0;border-top:1px solid #365269}';""")
print("v1.6.17 read-only shared meal calendar with day dots prepared")
