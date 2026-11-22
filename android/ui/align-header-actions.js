/* Mon Évolution IMC v1.6.111 — align the two action icons precisely.
   Profil is centered below Amis; Partagés below Version.
   The original buttons (and all click handlers) remain unchanged.
   No effect on data, sync, info button or update actions. */
(()=>{
  'use strict';
  const amis=document.getElementById('friends-auto-sync-status');
  const version=document.getElementById('release-auto-check-status');
  const profile=document.querySelector('#header-quick-actions [data-tab="profiles"]');
  const shared=document.querySelector('#header-quick-actions [data-tab="shared"]');
  if(!amis||!version||!profile||!shared)return;

  const center=node=>{
    const r=node.getBoundingClientRect();
    return r.left+r.width/2;
  };
  let request=0;
  const align=()=>{
    request=0;
    // Measure original, unshifted icon locations so repeated calls do not drift.
    profile.style.transform='none';
    shared.style.transform='none';
    const deltaProfile=center(amis)-center(profile);
    const deltaShared=center(version)-center(shared);
    const reasonable=v=>Math.max(-65,Math.min(65,Math.round(v*10)/10));
    profile.style.transform='translateX('+reasonable(deltaProfile)+'px)';
    shared.style.transform='translateX('+reasonable(deltaShared)+'px)';
  };
  const schedule=()=>{
    if(!request)request=requestAnimationFrame(align);
  };
  const style=document.createElement('style');
  style.textContent=[
    '#header-quick-actions [data-tab="profiles"],#header-quick-actions [data-tab="shared"]{position:relative;will-change:transform;transition:transform .12s ease;touch-action:manipulation}',
    '@media(prefers-reduced-motion:reduce){#header-quick-actions [data-tab]{transition:none!important}}'
  ].join('\n');
  document.head.append(style);
  const observer=new MutationObserver(schedule);
  observer.observe(amis,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['data-compact','class']});
  observer.observe(version,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['data-compact','class']});
  if(typeof ResizeObserver==='function'){
    const resize=new ResizeObserver(schedule);
    resize.observe(amis);
    resize.observe(version);
    resize.observe(document.querySelector('#header-quick-actions'));
  }
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
  schedule();
})();