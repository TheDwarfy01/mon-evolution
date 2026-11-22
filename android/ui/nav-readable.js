/* IMC v1.6.106 — readable navigation, 5 functional tabs.
   Keeps the ORIGINAL buttons and their event handlers, including private/shared. */
(()=>{
  'use strict';
  const nav=document.querySelector('header .nav');
  if(!nav)return;
  const names={
    home:'Résumé',chart:'Courbe',history:'Poids',
    'body-measurements':'Mensurations',meals:'Repas'
  };
  const icons={
    home:'<circle cx="12" cy="12" r="8.5"/><path d="M12 8v5l3 2"/>',
    chart:'<path d="M3 17l6-6 4 4 8-9"/><path d="M16 6h5v5"/>',
    history:'<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 4v16M12 12l2 2 3-4"/>',
    'body-measurements':'<path d="M5 8h14v11H5z"/><path d="M8 8V5M12 8V5M16 8V5"/><path d="M9 12h6M9 15h4"/>',
    meals:'<path d="M7 3v8M4 3v8M10 3v8M7 11v10M17 3v18M17 3c4 3 4 8 0 10"/>'
  };
  const sheet=document.createElement('style');
  sheet.textContent=[
    'header .nav{display:flex!important;flex-wrap:nowrap!important;justify-content:space-between!important;align-items:stretch!important;width:100%;max-width:100%;gap:2px!important;margin-top:8px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important}',
    'header .nav::-webkit-scrollbar{display:none}',
    'header .nav button[data-tab]:not([data-tab="profiles"]):not([data-tab="shared"]){box-sizing:border-box!important;flex:1 1 0!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:4px!important;min-width:59px!important;min-height:64px!important;max-width:none!important;padding:7px 3px 9px!important;border:0!important;border-bottom:3px solid transparent!important;border-radius:0!important;background:transparent!important;color:#c0d5e1!important;font-family:inherit!important;white-space:nowrap!important}',
    'header .nav button[data-tab][hidden]{display:none!important}',
    'header .nav button[data-tab="profiles"],header .nav button[data-tab="shared"]{display:none!important}',
    'header .nav button[data-tab] .imc-nav-icon{display:flex;align-items:center;justify-content:center;height:24px;width:24px;flex:0 0 24px}',
    'header .nav button[data-tab] .imc-nav-icon svg{display:block;width:22px;height:22px;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;fill:none}',
    'header .nav button[data-tab] .imc-nav-label{font-size:11.5px!important;line-height:1.13!important;font-weight:600!important;letter-spacing:-.03em!important;text-align:center!important;white-space:nowrap!important}',
    'header .nav button[data-tab].on{color:#83efda!important;border-bottom-color:#76e4cf!important;background:#2c526544!important}',
    'header .nav button[data-tab]:focus-visible{outline:2px solid #8dfae1!important;outline-offset:-3px!important}',
    '@media(max-width:350px){header .nav button[data-tab] .imc-nav-label{font-size:10.8px!important}header .nav button[data-tab]:not([data-tab="profiles"]):not([data-tab="shared"]){min-width:56px!important;padding-inline:2px!important}}'
  ].join('\n');
  document.head.append(sheet);
  for(const [key,label] of Object.entries(names)){
    const b=nav.querySelector('[data-tab="'+key+'"]');
    if(!b)continue;
    const ico=document.createElement('span');ico.className='imc-nav-icon';ico.setAttribute('aria-hidden','true');
    ico.innerHTML='<svg viewBox="0 0 24 24">'+icons[key]+'</svg>';
    const txt=document.createElement('span');txt.className='imc-nav-label';txt.textContent=label;
    // No clone: retain click handlers and native navigation.
    b.replaceChildren(ico,txt);
    b.setAttribute('aria-label','Ouvrir '+label);
  }
})();