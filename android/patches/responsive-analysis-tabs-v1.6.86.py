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
# Keep four equally sized columns and fit each label with measured text size.
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
  // Keep four tabs on ONE row; shrink the typography only when needed.
  // Layout measurement is based on the actual button width, not the screen
  // width, so font scaling works on Android with different display densities.
  const measure=document.createElement('canvas').getContext('2d');
  const fitAdvancedTabs=()=>{
   advancedTabs.style.setProperty('grid-template-columns','repeat(4,minmax(0,1fr))','important');
   for(const b of advancedTabs.querySelectorAll('button')){
    const width=b.getBoundingClientRect().width;
    if(width<=0)continue;
    const style=getComputedStyle(b);
    const family=style.fontFamily||'sans-serif';
    const weight=style.fontWeight||'600';
    const space=Math.max(12,width-8);
    let size=15;
    if(measure){
     while(size>8 && (()=>{
      measure.font=weight+' '+size+'px '+family;
      return measure.measureText(b.textContent.trim()).width>space;
     })())size-=.5;
    }else size=Math.max(8,Math.min(15,space/Math.max(5,b.textContent.length*.62)));
    b.style.setProperty('font-size',size+'px','important');
   }
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
assert "grid-template-columns','repeat(4,minmax(0,1fr))'" in s
assert "b.style.setProperty('white-space','nowrap','important')" in s
assert 'mon-evolution-responsive-advanced-tabs-v186' in s
assert 'adaptiveObserver.observe(advancedTabs)' in s
page.write_text(s,encoding='utf-8')
print('PASS v1.6.86: 4 onglets sur une ligne, police ajustée à leur largeur')
