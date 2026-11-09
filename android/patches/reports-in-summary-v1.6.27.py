#!/usr/bin/env python3
"""v1.6.27: all PDF reports grouped at bottom of Résumé, including monthly meals."""
from pathlib import Path
root=Path("android/source-1.6.27/app")
h=root/"src/main/assets/index.html"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
def R(p,a,b):
 s=p.read_text(encoding="utf-8");n=s.count(a)
 if n!=1:raise AssertionError(f"{p}: {n} occurrences for {a[:100]!r}")
 p.write_text(s.replace(a,b),encoding="utf-8")
R(g,"versionCode 42","versionCode 43")
R(g,"versionName '1.6.26'","versionName '1.6.27'")
R(m,'android:versionCode="42" android:versionName="1.6.26"','android:versionCode="43" android:versionName="1.6.27"')
R(j,"MonEvolutionIMC/1.6.26","MonEvolutionIMC/1.6.27")
R(h,'Version installée : <strong>1.6.26</strong>','Version installée : <strong>1.6.27</strong>')
R(h,'const installed="1.6.26";','const installed="1.6.27";')
script=r"""
<style>
#summary-pdf-reports{margin-top:18px}
#summary-pdf-reports>h3{font-size:15px;color:#d6eef4;margin-bottom:6px}
#summary-pdf-reports>.export-details{margin-top:8px}
#summary-report-month{font-size:14px;max-width:100%;margin:8px 0 13px}
</style>
<script>
(function(){
 const home=$('home'),meals=$('meals');
 const full=$('export-progress-pdf')?.closest('.export-details');
 const food=$('export-meals-pdf')?.closest('.export-details');
 if(!home||!meals||!full||!food)return;
 // Move existing nodes, not clones. This preserves the original PDF export
 // handlers and the meal selection made in the calendar.
 const reports=document.createElement('div');
 reports.id='summary-pdf-reports';
 const label=document.createElement('h3');label.textContent='📄 Mes bilans PDF';
 reports.append(label,full,food);
 home.append(reports);
 const content=food.querySelector('.export-content');
 const hint=content?.querySelector('.notice');
 if(hint)hint.textContent='Choisis le mois à exporter, puis télécharge le compte rendu de tes repas.';
 const monthLabel=document.createElement('label');
 monthLabel.className='field';monthLabel.textContent='Mois du compte rendu';
 const selector=document.createElement('input');
 selector.id='summary-report-month';selector.type='month';selector.setAttribute('aria-label','Mois du compte rendu des repas');
 selector.value=mealMonth;
 selector.onchange=()=>{
  if(!/^\d{4}-\d{2}$/.test(selector.value))return;
  mealMonth=selector.value;
  // Keep the meal calendar and the exported PDF on the same selected month.
  mealDate=mealMonth+'-01';
  renderMeals();
 };
 monthLabel.append(selector);
 if(content){content.insertBefore(monthLabel,$('export-meals-pdf'))}
 // Synchronize the month selector if the user browses the meal calendar.
 const previousRenderMeals=renderMeals;
 renderMeals=function(){
  previousRenderMeals();
  if(selector.value!==mealMonth)selector.value=mealMonth;
 };
})();
</script>
"""
R(h,'</body></html>',script+'</body></html>')
print("v1.6.27: all monthly and weight PDF reports grouped in Résumé")
