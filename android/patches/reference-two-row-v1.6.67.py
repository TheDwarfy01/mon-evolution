#!/usr/bin/env python3
"""v1.6.67: références sur deux lignes, contrôles adaptés à la largeur Android."""
from pathlib import Path
page=Path("android/source-1.6.67/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
def change(a,b):
 global s
 n=s.count(a)
 if n!=1:
  raise AssertionError(f"Expected exactly one anchor ({n}): {a[:110]}")
 s=s.replace(a,b,1)

# Inline important grid to bypass inherited flex styling on all four navigation buttons.
change(
 "  advancedTabs.classList.add('advanced-view-tabs');",
 """  advancedTabs.classList.add('advanced-view-tabs');
  advancedTabs.style.setProperty('display','grid','important');
  advancedTabs.style.setProperty('grid-template-columns','repeat(4,minmax(0,1fr))','important');
  advancedTabs.style.setProperty('gap','5px','important');
  advancedTabs.style.setProperty('flex-wrap','nowrap','important');
  advancedTabs.style.setProperty('width','100%','important');
  for(const b of advancedTabs.querySelectorAll('button')){
   b.style.setProperty('width','100%','important');
   b.style.setProperty('min-width','0','important');
   b.style.setProperty('font-size','clamp(11px,3.3vw,15px)','important');
   b.style.setProperty('padding','8px 2px','important');
   b.style.setProperty('min-height','50px','important');
  }"""
)

change(
 "    healthReferenceGraph(target,p);\n   }\n  }else if(view==='progress')",
 """    healthReferenceGraph(target,p);
    // Regrouper Poids / IMC / Vue globale / Zoom mesures sous les 4 onglets.
    // Les courbes enfants ont aussi « Taille » : leur barre s'adapte sans masquer d'option.
    const strips=[...target.querySelectorAll(':scope > .advanced-controls')].filter(el=>el!==advancedTabs);
    if(strips.length===2){
     const [measures,zoomModes]=strips;
     const combined=node('div','advanced-reference-toolbar');
     const buttons=[...measures.querySelectorAll('button'),...zoomModes.querySelectorAll('button')];
     combined.classList.toggle('advanced-reference-child',buttons.length===5);
     for(const b of buttons){
      if(b.textContent==='Zoom sur mes mesures')b.textContent='Zoom mesures';
      b.style.setProperty('font-size','clamp(11px,3.3vw,14px)','important');
      b.style.setProperty('min-width','0','important');
      combined.append(b);
     }
     measures.remove();zoomModes.remove();
     target.insertBefore(combined,advancedTabs.nextSibling);
    }
   }
  }else if(view==='progress')"""
)

style="""<style id="mon-evolution-ref-compact-167">
#advanced-weight-panel .advanced-reference-toolbar,
#advanced-friend-graphs .advanced-reference-toolbar{
 display:grid!important;
 grid-template-columns:repeat(4,minmax(0,1fr))!important;
 gap:6px!important;
 margin:10px 0 14px!important;
 align-items:stretch;
 width:100%;
}
#advanced-weight-panel .advanced-reference-toolbar button,
#advanced-friend-graphs .advanced-reference-toolbar button{
 box-sizing:border-box;
 width:100%!important;
 min-width:0!important;
 min-height:51px;
 margin:0!important;
 padding:8px 2px!important;
 white-space:normal;
 overflow-wrap:break-word;
 line-height:1.2;
 text-align:center;
 color:#edfaff;
 background:#213e54;
 border:1px solid #4a6f82;
 border-radius:11px;
}
#advanced-weight-panel .advanced-reference-toolbar button.chosen,
#advanced-friend-graphs .advanced-reference-toolbar button.chosen{
 background:#2c706d;border-color:#8be8d4;
}
#advanced-weight-panel .advanced-reference-toolbar.advanced-reference-child,
#advanced-friend-graphs .advanced-reference-toolbar.advanced-reference-child{
 grid-template-columns:repeat(3,minmax(0,1fr))!important;
}
</style>
"""
change("</head>",style+"</head>")
assert "advancedTabs.style.setProperty('display','grid','important')" in s
assert "advanced-reference-toolbar" in s
assert "target.insertBefore(combined,advancedTabs.nextSibling)" in s
page.write_text(s,encoding="utf-8")
print("PASS 1.6.67 layout references adult 4+4, pediatric flexible, selectors preserved")
