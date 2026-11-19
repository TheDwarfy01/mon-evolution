#!/usr/bin/env python3
"""v1.6.81: explicit medical disclaimer below pediatric charts and 18th birthday switch."""
from pathlib import Path
page=Path('android/source-1.6.81/app/src/main/assets/index.html')
s=page.read_text(encoding='utf-8')

def once(old,new):
 global s
 count=s.count(old)
 if count!=1:raise AssertionError(f'Anchor count={count}: {old[:150]!r}')
 s=s.replace(old,new,1)

notice='Les résultats affichés sur ces courbes ne constituent pas un diagnostic médical et ne remplacent pas l’interprétation d’un pédiatre ou d’un médecin.'
# Note goes AFTER the chart (including its legend and point-detail area), before
# the existing technical source attribution.
anchor="   target.append(node('p','advanced-help','Références de croissance OMS 2007 (5–19 ans, poids jusqu’à 10 ans) et seuils IMC IOTF 2012 (2–18 ans). Distinctes des courbes françaises AFPA 2018 du carnet de santé. Interprétation médicale nécessaire, notamment pendant la croissance.'));"
replacement="""   const safety=document.createElement('p');
   safety.className='pediatric-medical-warning';
   safety.setAttribute('role','note');
   safety.textContent='⚠️ Attention — Information médicale importante : Les résultats affichés sur ces courbes ne constituent pas un diagnostic médical et ne remplacent pas l’interprétation d’un pédiatre ou d’un médecin.';
   target.append(safety);
""" + anchor
once(anchor,replacement)

# Classify children exactly up to (but excluding) their 18th birthday,
# instead of using approximate month/year lengths.
once(
 "  const child=age!==null&&age>=0&&age<216;",
 "  const child=window.MonEvolutionChild?.isChildBirth?.(p.birthDate)===true;"
)
once(
 "  const adult=age===null||age>=18;",
 "  const adult=age===null||window.MonEvolutionChild?.isChildBirth?.(p.birthDate)!==true;"
)
# In the profile creation hint make the age rule explicit.
once(
 "hint.textContent='Profil enfant : aucun objectif de poids. L’application suivra la croissance et l’IMC selon l’âge et le sexe.';",
 "hint.textContent='Profil enfant (moins de 18 ans) : aucun objectif de poids. L’application suivra la croissance et l’IMC selon l’âge et le sexe.';"
)

addon=r'''
<style id="mon-evolution-pediatric-disclaimer-v181">
.pediatric-medical-warning{
 margin:14px 0 16px;padding:13px 14px;
 border:2px solid #e46d70;border-radius:12px;
 color:#fff0f0;background:#4b252e;
 font-size:13px;line-height:1.6
}
.pediatric-medical-warning strong{font-weight:750}
.pediatric-medical-warning[hidden]{display:none!important}
</style>
<script>
(function(){
 'use strict';
 // Also show the medical warning directly under the upper overview chart
 // when the selected profile is under 18.
 const topPlot=document.querySelector('#evo-v159-graph .evo-v159-chart');
 if(!topPlot)return;
 const note=document.createElement('p');
 note.className='pediatric-medical-warning';
 note.textContent='⚠️ Attention — Information médicale importante : Les résultats affichés sur ces courbes ne constituent pas un diagnostic médical et ne remplacent pas l’interprétation d’un pédiatre ou d’un médecin.';
 topPlot.after(note);
 const refresh=()=>{
  const active=typeof unifiedCurrent==='string'&&unifiedCurrent.startsWith('received:');
  note.hidden=active||!window.MonEvolutionChild?.isChildBirth?.(profile().birthDate);
 };
 const previous=render;
 render=function(){
  const result=previous();
  refresh();
  return result;
 };
 refresh();
})();
</script>
'''
once('</body></html>',addon+'\n</body></html>')
assert 'pediatric-medical-warning' in s
assert 'moins de 18 ans' in s
assert s.count(notice)==2
page.write_text(s,encoding='utf-8')
print('PASS 1.6.81: avertissement pédiatrique sous les courbes, bascule à 18 ans')
