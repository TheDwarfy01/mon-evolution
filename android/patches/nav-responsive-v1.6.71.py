#!/usr/bin/env python3
"""v1.6.71 : corrige la navigation supérieure sur petits smartphones et textes agrandis."""
from pathlib import Path
p=Path("android/source-1.6.71/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
assert s.count("</head>")==1 and s.count("</body></html>")==1
css="""<style id="mon-evolution-nav-responsive-171">
/* 6 onglets toujours alignés : le style global des gros boutons ne s'applique pas au menu. */
header nav.nav{
 display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;
 width:100%;min-width:0;margin-top:8px;gap:0;align-items:stretch;
}
header nav.nav>button{
 box-sizing:border-box;display:flex!important;flex-flow:row nowrap!important;
 align-items:center;justify-content:center;gap:2px;
 width:100%;min-width:0;max-width:100%;height:43px;min-height:43px;
 padding:7px 0!important;margin:0!important;
 overflow:hidden;white-space:nowrap!important;
 text-align:center;line-height:1.1!important;
 letter-spacing:-.01em;font-size:11px!important;
}
header nav.nav .nav-tab-icon,
header nav.nav .nav-tab-label{
 flex:0 0 auto;display:inline-block;min-width:0;
 white-space:nowrap!important;line-height:1.1!important;
}
header nav.nav .nav-tab-icon{font-size:1em}
header nav.nav.nav-compact>button{
 flex-direction:column!important;gap:1px;
 height:56px;min-height:56px;padding:5px 0!important;
}
header nav.nav.nav-compact .nav-tab-icon{font-size:13px}
header nav.nav.nav-compact .nav-tab-label{font-size:inherit}
</style>
"""
script="""<script id="mon-evolution-nav-fit-171">
(function(){
 'use strict';
 const nav=document.querySelector('header nav.nav');
 if(!nav)return;
 let pending=false;
 function buttons(){return Array.from(nav.querySelectorAll(':scope > button'))}
 function prepare(){
  for(const btn of buttons()){
   if(btn.dataset.navFit171==='yes')continue;
   const label=btn.textContent.trim();
   const split=label.match(/^(\\S+)\\s+(.+)$/);
   if(!split)continue;
   const icon=document.createElement('span');
   icon.className='nav-tab-icon';icon.setAttribute('aria-hidden','true');
   icon.textContent=split[1];
   const title=document.createElement('span');
   title.className='nav-tab-label';title.textContent=split[2];
   btn.replaceChildren(icon,title);
   btn.setAttribute('aria-label',split[2]);
   btn.dataset.navFit171='yes';
  }
 }
 function readableFit(){
  pending=false;prepare();
  const items=buttons();
  if(!items.length||!nav.clientWidth)return;
  nav.style.setProperty('grid-template-columns','repeat('+items.length+',minmax(0,1fr))','important');
  nav.classList.remove('nav-compact');
  const available=items[0].clientWidth;
  let size=12;
  let fits=false;
  for(;size>=9;size-=.5){
   for(const b of items)b.style.setProperty('font-size',size+'px','important');
   fits=items.every(b=>{
    const icon=b.querySelector('.nav-tab-icon'),title=b.querySelector('.nav-tab-label');
    if(!icon||!title)return b.scrollWidth<=b.clientWidth;
    return icon.getBoundingClientRect().width+title.getBoundingClientRect().width+2<=b.clientWidth-.5;
   });
   if(fits)break;
  }
  if(!fits){
   // Secours accessibilité : icône au-dessus du titre pour TOUS les onglets, jamais un seul.
   nav.classList.add('nav-compact');
   for(let font=12;font>=9;font-=.5){
    for(const b of items)b.style.setProperty('font-size',font+'px','important');
    if(items.every(b=>{
     const title=b.querySelector('.nav-tab-label');
     return !title||title.getBoundingClientRect().width<=b.clientWidth-2;
    }))break;
   }
  }
 }
 function schedule(){
  if(pending)return;pending=true;
  window.requestAnimationFrame(readableFit);
 }
 const changes=new MutationObserver(schedule);
 changes.observe(nav,{childList:true});
 if(typeof ResizeObserver==='function'){
  new ResizeObserver(schedule).observe(nav);
 }
 window.addEventListener('resize',schedule,{passive:true});
 window.addEventListener('orientationchange',schedule,{passive:true});
 if(document.fonts&&document.fonts.ready)document.fonts.ready.then(schedule).catch(()=>{});
 schedule();
})();
</script>
"""
s=s.replace("</head>",css+"</head>")
s=s.replace("</body></html>",script+"</body></html>")
assert "mon-evolution-nav-responsive-171" in s
assert "nav.classList.add('nav-compact')" in s
assert "grid-template-columns:repeat(6,minmax(0,1fr))" in s
p.write_text(s,encoding="utf-8")
print("PASS navigation: six onglets sans retour à la ligne, ajustement dynamique et repli cohérent")
