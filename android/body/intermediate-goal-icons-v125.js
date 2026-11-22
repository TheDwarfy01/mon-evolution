/* Mon Évolution IMC — independent intermediate goal actions and pediatric hints.
 * Only the intermediate four-field plan is saved/cleared by these icons.
 * No weight-loss objective is exposed or created for under-18 profiles.
 */
(()=>{
'use strict';
const goalBox=document.getElementById('goal-plan-edit');
const height=document.getElementById('edit-birth');
const profiles=document.getElementById('profiles');
const childBirth=b=>window.MonEvolutionChild?.isChildBirth?.(b)===true;
const hints=profiles?[...profiles.querySelectorAll('.notice')].filter(p=>
 /^(?:Pour un enfant\s*:|Profil enfant\s*:)/i.test(p.textContent.trim())):[];
const css=document.createElement('style');css.id='intermediate-goal-icons-child-hints-v125';
css.textContent=[
 '#goal-plan-edit .intermediate-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:10px}',
 '#goal-plan-edit .intermediate-heading h4{flex:1;min-width:0;margin:3px 0 0!important}',
 '#goal-plan-edit .intermediate-actions{display:flex;align-items:center;gap:7px;flex:0 0 auto}',
 '#goal-plan-edit .intermediate-icon{display:inline-flex!important;align-items:center;justify-content:center;width:39px!important;height:39px!important;min-width:39px!important;padding:7px!important;border-radius:11px!important;border:1px solid #47798e!important;background:#174b60!important;color:#e3fff7!important;cursor:pointer}',
 '#goal-plan-edit .intermediate-icon:hover{background:#215e70!important}',
 '#goal-plan-edit .intermediate-icon:focus-visible{outline:2px solid #81edcd!important;outline-offset:2px}',
 '#goal-plan-edit .intermediate-icon.delete{border-color:#855966!important;color:#ffdce1!important}',
 '#goal-plan-edit .intermediate-icon svg{display:block;width:19px;height:19px;stroke:currentColor;stroke-width:2;fill:none;stroke-linejoin:round;stroke-linecap:round}',
 '#goal-plan-edit .intermediate-icon:disabled{opacity:.5;cursor:not-allowed}',
 '#profiles .child-profile-only:not([data-child-visible="yes"]){display:none!important}'
].join('\n');document.head.append(css);
hints.forEach(node=>node.classList.add('child-profile-only'));
function currentBirth(){
 const value=height?.value||'';
 const saved=typeof profile==='function'?profile()?.birthDate||'':'';
 return value||saved;
}
function refreshChildHints(){
 const child=childBirth(currentBirth());
 for(const p of hints)p.dataset.childVisible=child?'yes':'no';
 if(goalBox&&goalBox.querySelector('.intermediate-actions'))
   goalBox.querySelectorAll('.intermediate-icon').forEach(b=>{b.disabled=child;});
}
height?.addEventListener('input',refreshChildHints);
height?.addEventListener('change',refreshChildHints);
document.getElementById('profile-picker')?.addEventListener('change',()=>requestAnimationFrame(refreshChildHints));
if(typeof render==='function'){
 const oldRender=render;
 render=function(){const result=oldRender();refreshChildHints();return result;};
}
refreshChildHints();
if(!goalBox)return;
const title=goalBox.querySelector('h4');
const startDate=document.getElementById('edit-goal-start-date');
const startWeight=document.getElementById('edit-goal-start-weight');
const endDate=document.getElementById('edit-goal-date');
const endWeight=document.getElementById('edit-intermediate-goal');
if(!title||!startDate||!startWeight||!endDate||!endWeight)return;
const heading=document.createElement('div');heading.className='intermediate-heading';
const actions=document.createElement('div');actions.className='intermediate-actions';
function iconButton(label,type,svg){
 const b=document.createElement('button');
 b.type='button';b.className='intermediate-icon'+(type==='delete'?' delete':'');
 b.title=label;b.setAttribute('aria-label',label);
 b.innerHTML=svg;
 return b;
}
const saveIcon=iconButton('Enregistrer l’objectif intermédiaire','save',
 '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 3h14l3 3v15H3V3h1Z"/><path d="M7 3v7h10V3M7 21v-8h10v8"/><path d="M10 16h4"/></svg>');
const eraseIcon=iconButton('Effacer l’objectif intermédiaire','delete',
 '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v7M14 11v7"/></svg>');
actions.append(saveIcon,eraseIcon);
title.before(heading);heading.append(title,actions);
function dateValid(raw){
 if(typeof raw!=='string'||! /^\d{4}-\d{2}-\d{2}$/.test(raw))return false;
 const parsed=Date.parse(raw+'T12:00:00Z');
 return Number.isFinite(parsed)&&new Date(parsed).toISOString().slice(0,10)===raw;
}
function positive(input){
 const text=input.value.trim().replace(',','.');
 const value=Number(text);
 return text&&Number.isFinite(value)&&value>=1&&value<=400?value:null;
}
function refreshGoalViews(){
 if(typeof render==='function')render();
 // Existing goal-plan rendering and graphs are refreshed by the render wrappers.
 refreshChildHints();
}
saveIcon.addEventListener('click',()=>{
 const p=typeof profile==='function'?profile():null;
 if(!p||childBirth(p.birthDate)){alert('Les profils enfants ne disposent pas d’objectifs de poids.');return;}
 const a=startDate.value,b=endDate.value,w0=positive(startWeight),w1=positive(endWeight);
 if(!dateValid(a)||!dateValid(b)||Date.parse(b+'T12:00:00Z')<=Date.parse(a+'T12:00:00Z')){
  alert('Choisis une date de départ et une date d’arrivée ultérieure.');return;
 }
 if(w0===null||w1===null){
  alert('Indique deux poids valides entre 1 et 400 kg.');return;
 }
 p.goalStartDate=a;
 p.goalStartWeight=w0;
 p.goalDate=b;
 p.intermediateGoalWeight=w1;
 save();refreshGoalViews();
 if(typeof message==='function')message('Objectif intermédiaire enregistré ✓');
});
eraseIcon.addEventListener('click',()=>{
 const p=typeof profile==='function'?profile():null;
 if(!p||childBirth(p.birthDate))return;
 if(!confirm('Effacer uniquement l’objectif intermédiaire ? Le poids final et les pesées seront conservés.'))return;
 delete p.goalDate;delete p.goalStartDate;delete p.goalStartWeight;
 delete p.intermediateGoalWeight;
 save();refreshGoalViews();
 // After the profile's legacy refresh (which pre-fills the first recorded
 // measurement), clear the intermediate form to match the delete action.
 startDate.value='';startWeight.value='';endDate.value='';endWeight.value='';
 if(typeof message==='function')message('Objectif intermédiaire effacé ✓');
});
refreshChildHints();
})();