/* Mon Évolution IMC — en-tête simplifié, version 1.6.104.
   Déplace les deux VRAIS boutons Profil/Partagés sans réinitialiser les listeners.
   Leur gestion Drive, le partage, les rappels et les profils restent intacts. */
(function(){
  'use strict';
  const brand=document.querySelector('header .brand-hello');
  const nav=document.querySelector('header .nav');
  const profileTab=document.querySelector('header .nav [data-tab="profiles"]');
  const sharedTab=document.querySelector('header .nav [data-tab="shared"]');
  if(!brand||!nav||!profileTab||!sharedTab||document.getElementById('header-quick-actions'))return;

  const style=document.createElement('style');
  style.textContent=[
   '.brand-hello{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:6px!important;min-width:0}',
   '.brand-hello h1{font-size:clamp(19px,5.1vw,23px)!important;line-height:1.12;min-width:0;white-space:nowrap;margin:0}',
   '.header-greeting{display:none!important}',
   '#header-quick-actions{display:flex;align-items:center;justify-content:flex-end;gap:4px;flex:0 0 auto;margin-left:auto}',
   '#header-quick-actions button{box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:2px;width:51px;min-width:45px;min-height:49px;padding:3px 3px 5px!important;background:transparent!important;color:#cfebf4!important;border:0!important;border-bottom:2px solid transparent!important;border-radius:9px!important;font-family:inherit;cursor:pointer;touch-action:manipulation}',
   '#header-quick-actions button svg{width:21px;height:21px;display:block;stroke:currentColor;stroke-width:1.85;fill:none;stroke-linejoin:round;stroke-linecap:round}',
   '#header-quick-actions button .quick-label{font-size:10px;line-height:1.05;font-weight:600;white-space:nowrap}',
   '#header-quick-actions button.on,#header-quick-actions button:focus-visible{color:#86f4df!important;background:#255567!important;border-bottom-color:#82e8d8!important;outline:none}',
   '#header-quick-actions button:active{background:#2b6377!important}',
   'header .nav{justify-content:space-around;max-width:100%;overflow-x:auto;scrollbar-width:thin}',
   'header .nav [data-tab="profiles"],header .nav [data-tab="shared"]{display:none!important}',
   '@media(max-width:360px){#header-quick-actions{gap:1px}#header-quick-actions button{width:44px;min-width:40px;padding:2px!important}#header-quick-actions button .quick-label{font-size:9px}.brand-hello h1{font-size:19px!important}}'
  ].join('\n');
  document.head.append(style);

  const shortcuts=document.createElement('div');
  shortcuts.id='header-quick-actions';
  shortcuts.setAttribute('role','group');
  shortcuts.setAttribute('aria-label','Accès rapide aux profils et aux partages');
  function decorate(button,label,title,iconMarkup){
    button.textContent='';
    const icon=document.createElement('span');
    icon.className='quick-icon';icon.setAttribute('aria-hidden','true');
    icon.innerHTML=iconMarkup;
    const text=document.createElement('span');text.className='quick-label';text.textContent=label;
    button.append(icon,text);
    button.type='button';
    button.setAttribute('aria-label',title);
    button.title=title;
    // Move the original button itself; all existing listeners stay attached.
    shortcuts.append(button);
  }
  decorate(profileTab,'Profil','Ouvrir mes profils, réglages et sauvegardes',
    '<svg viewBox="0 0 24 24"><circle cx="12" cy="7.5" r="3.7"/><path d="M4.7 20v-1.8c0-3.3 3-5.8 7.3-5.8s7.3 2.5 7.3 5.8V20z"/></svg>');
  decorate(sharedTab,'Partagés','Ouvrir les profils partagés',
    '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.1"/><path d="M2.5 19v-1.4c0-2.8 2.8-4.7 6.5-4.7s6.5 1.9 6.5 4.7V19z"/><path d="M16 5.1a3 3 0 0 1 0 5.9M17.7 13.4c2.7.7 3.8 2.3 3.8 4.4V19"/></svg>');
  const greeting=brand.querySelector('.header-greeting');
  if(greeting)greeting.remove();
  brand.append(shortcuts);

  // La page d'accueil n'a pas besoin d'un deuxième « Bonjour » :
  // son titre est déjà masqué par la présentation compacte actuelle.
  const homeHello=document.querySelector('#home > h2');
  if(homeHello && homeHello.textContent.includes('Bonjour,')){
    // Conserver le nœud #name : render() en dépend.
    const nameNode=homeHello.querySelector('#name');
    if(nameNode){homeHello.replaceChildren(document.createTextNode('Suivi de '),nameNode);}
  }
})();
