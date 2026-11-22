/* Mon Évolution IMC 1.6.108
   Amis / Version / À propos sur la ligne « TON PARCOURS, À TON RYTHME ».
   Conserve les éléments existants : leurs callbacks, ARIA, synchronisations,
   contrôle de la dernière version et lien de téléchargement restent actifs. */
(()=>{
 'use strict';
 const header=document.querySelector('header');
 const upper=header?.querySelector(':scope > .upper');
 const sync=document.getElementById('friends-auto-sync-status');
 const version=document.getElementById('release-auto-check-status');
 const info=document.getElementById('about-info-trigger');
 if(!header||!upper||!sync||!version||document.getElementById('imc-header-status-row'))return;

 const css=document.createElement('style');
 css.textContent=[
  '#imc-header-status-row{display:flex;align-items:center;justify-content:space-between;gap:4px;width:100%;min-width:0;min-height:28px;margin:0 0 4px}',
  '#imc-header-status-row>.upper{flex:1 1 auto;min-width:0;margin:0!important;font-size:clamp(7px,2.25vw,9px)!important;letter-spacing:.105em!important;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#a8c8d9}',
  '#imc-header-meta{display:flex;align-items:center;justify-content:flex-end;gap:4px;flex:0 0 auto;min-width:0}',
  '#imc-header-meta #friends-auto-sync-status,#imc-header-meta #release-auto-check-status{display:inline-flex!important;align-items:center;justify-content:center;flex:0 0 auto!important;min-width:0;max-width:none!important;min-height:25px;padding:5px 6px!important;margin:0!important;border-radius:8px;border:1px solid #416b81;background:#24506977;color:#d4f2f0;font-size:0!important;line-height:1.1!important;text-align:center!important;white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;cursor:default}',
  '#imc-header-meta #friends-auto-sync-status::after,#imc-header-meta #release-auto-check-status::after{content:attr(data-compact);font-size:10px!important;line-height:1.15;font-weight:650;white-space:nowrap}',
  '#imc-header-meta #release-auto-check-status.available{cursor:pointer!important;border-color:#76e5ca;background:#285e60;color:#b5ffe6}',
  '#imc-header-meta #about-info-trigger{flex:0 0 24px!important;width:24px!important;height:24px!important;min-height:24px!important;padding:0!important;margin:0!important;display:grid!important;place-items:center!important;font-size:14px!important;line-height:1!important}',
  '#friends-release-status-row:empty{display:none!important}',
  '@media(max-width:360px){#imc-header-status-row{gap:2px}#imc-header-meta{gap:2px}#imc-header-meta #friends-auto-sync-status,#imc-header-meta #release-auto-check-status{padding:5px 4px!important}#imc-header-meta #friends-auto-sync-status::after,#imc-header-meta #release-auto-check-status::after{font-size:9px!important}#imc-header-meta #about-info-trigger{flex-basis:21px!important;width:21px!important;height:21px!important}}'
 ].join('\n');
 document.head.append(css);

 const container=document.createElement('div');
 container.id='imc-header-status-row';
 const right=document.createElement('div');right.id='imc-header-meta';
 upper.insertAdjacentElement('beforebegin',container);
 container.append(upper,right);
 // Move EXISTING elements — do not replace text or their event listeners.
 right.append(sync,version);
 if(info)right.append(info);
 const previous=document.getElementById('friends-release-status-row');
 if(previous && !previous.children.length)previous.remove();

 const decorate=(p,type)=>{
   const raw=p.textContent||'';
   const bits=raw.split(' · ');
   const main=bits.length>1?bits.slice(1,-1).join(' · '):raw;
   let short='';
   if(type==='friends'){
     if(/✓/.test(main))short='Amis ✓'+(main.match(/\d+\s*\/\s*\d+/)?.[0]||'');
     else if(/⚠/.test(main))short='Amis ⚠'+(main.match(/\d+\s*\/\s*\d+/)?.[0]||'');
     else if(/erreur|échec/i.test(main))short='Amis !';
     else if(/synchron|cours/i.test(main))short='Amis …';
     else if(/aucun/i.test(main))short='Amis —';
     else short='Amis ·';
   }else{
     if(p.classList.contains('available')||/disponible/i.test(main))short='Version ↑';
     else if(/✓|à jour/i.test(main))short='Version ✓';
     else if(/erreur|échec|indisponible/i.test(main))short='Version !';
     else if(/vérification|cours/i.test(main))short='Version …';
     else short='Version ·';
   }
   p.dataset.compact=short;
   const detail=raw.trim()|| (type==='friends'?'État des amis indisponible':'État de la version indisponible');
   p.title=detail;
   p.setAttribute('aria-label',detail);
 };
 for(const [p,type] of [[sync,'friends'],[version,'version']]){
   decorate(p,type);
   // Existing app changes textContent on sync/update; the status badge follows live.
   const observer=new MutationObserver(()=>decorate(p,type));
   observer.observe(p,{childList:true,characterData:true,subtree:true,attributes:true,attributeFilter:['class']});
 }
})();
