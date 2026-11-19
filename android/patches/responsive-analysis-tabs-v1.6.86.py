#!/usr/bin/env python3
"""v1.6.86: prevent wrapped 'Comparaison' and adapt advanced tabs to narrow screens."""
from pathlib import Path
page=Path('android/source-1.6.86/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

def once(old,new):
 global s
 n=s.count(old)
 if n!=1: raise AssertionError(f'Responsive tabs anchor count={n}: {old[:110]!r}')
 s=s.replace(old,new,1)

# Inline !important grid width introduced in v1.6.67 overrides media queries.
# Make its column count depend on the actual available width in the panel.
old="""  for(const b of advancedTabs.querySelectorAll('button')){
   b.style.setProperty('width','100%','important');
   b.style.setProperty('min-width','0','important');
   b.style.setProperty('font-size','clamp(11px,3.3vw,15px)','important');
   b.style.setProperty('padding','8px 2px','important');
   b.style.setProperty('min-height','50px','important');
  }"""
new="""  for(const b of advancedTabs.querySelectorAll('button')){
   b.style.setProperty('width','100%','important');
   b.style.setProperty('min-width','0','important');
   b.style.setProperty('font-size','clamp(12px,3.3vw,15px)','important');
   b.style.setProperty('padding','8px 4px','important');
   b.style.setProperty('min-height','50px','important');
   b.style.setProperty('white-space','nowrap','important');
   b.style.setProperty('overflow-wrap','normal','important');
   b.style.setProperty('word-break','normal','important');
   b.style.setProperty('hyphens','none','important');
  }
  // On normal-sized displays the four tabs stay on one row. When the inner
  // panel is narrow (< 410 CSS px), use 2 x 2 readable tabs rather than
  // cutting "Comparaison" into two lines or shrinking the text too much.
  const fitAdvancedTabs=()=>{
   const available=advancedTabs.clientWidth||target.clientWidth||document.documentElement.clientWidth;
   const columns=available<410?'repeat(2,minmax(0,1fr))':'repeat(4,minmax(0,1fr))';
   advancedTabs.style.setProperty('grid-template-columns',columns,'important');
  };
  fitAdvancedTabs();
  if(typeof ResizeObserver==='function'){
   const adaptiveObserver=new ResizeObserver(()=>{
    if(!advancedTabs.isConnected){adaptiveObserver.disconnect();return;}
    fitAdvancedTabs();
   });
   adaptiveObserver.observe(advancedTabs);
  }"""
once(old,new)

style="""<style id="mon-evolution-responsive-advanced-tabs-v186">
#advanced-weight-panel .advanced-view-tabs button,
#advanced-friend-graphs .advanced-view-tabs button{
 white-space:nowrap!important;overflow-wrap:normal!important;
 word-break:normal!important;hyphens:none!important;
 text-align:center;min-height:48px!important;line-height:1.25
}
</style>
"""
once('</head>',style+'</head>')
assert "available<410?'repeat(2,minmax(0,1fr))'" in s
assert "b.style.setProperty('white-space','nowrap','important')" in s
assert 'mon-evolution-responsive-advanced-tabs-v186' in s
assert 'adaptiveObserver.observe(advancedTabs)' in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.86: onglets largeur adaptative et intitulés sur une ligne')
