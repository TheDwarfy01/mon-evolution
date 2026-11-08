#!/usr/bin/env python3
"""v1.6.22: move outgoing encrypted sharing controls into the Shared tab, collapsed."""
from pathlib import Path
root=Path("android/source-1.6.22/app")
h=root/"src/main/assets/index.html"
j=root/"src/main/java/fr/monevolution/app/MainActivity.java"
g=root/"build.gradle"
m=root/"src/main/AndroidManifest.xml"
def R(path,old,new):
 s=path.read_text(encoding="utf-8")
 count=s.count(old)
 if count!=1:raise AssertionError(f"{path}: expected 1, found {count}: {old[:100]!r}")
 path.write_text(s.replace(old,new),encoding="utf-8")
R(g,"versionCode 37","versionCode 38")
R(g,"versionName '1.6.21'","versionName '1.6.22'")
R(m,'android:versionCode="37" android:versionName="1.6.21"','android:versionCode="38" android:versionName="1.6.22"')
R(j,"MonEvolutionIMC/1.6.21","MonEvolutionIMC/1.6.22")
R(h,'Version installée : <strong>1.6.21</strong>','Version installée : <strong>1.6.22</strong>')
R(h,'const installed="1.6.21";','const installed="1.6.22";')
script=r"""
<style>
#outgoing-share-wrapper{margin:18px 0}
#outgoing-share-wrapper>summary{list-style:none;cursor:pointer;padding:18px 20px;border-radius:16px;background:#1d465d;border:1px solid #3d667c;font-weight:750}
#outgoing-share-wrapper>summary::-webkit-details-marker{display:none}
#outgoing-share-wrapper>summary:after{content:"⌄";float:right}
#outgoing-share-wrapper[open]>summary:after{content:"⌃"}
#outgoing-share-wrapper .card{margin-top:12px}
#outgoing-advanced{margin-top:14px;border-top:1px solid #365c70;padding-top:14px}
#outgoing-advanced summary{cursor:pointer;color:#bddce7;padding:12px 0}
</style>
<script>
(function(){
 const sharing=document.querySelector('#create-share')?.closest('.card');
 const shared=$('shared');
 if(!sharing||!shared)return;
 // Move the existing DOM controls, never clone them: native JavaScript listeners,
 // the stored Drive URI and all confirmation dialogs remain unchanged.
 const outer=document.createElement('details');outer.id='outgoing-share-wrapper';
 const summary=document.createElement('summary');
 summary.textContent='🔗 Partager mon profil personnel';
 const info=document.createElement('p');info.className='notice';
 info.textContent='Créer, mettre à jour ou envoyer le profil personnel choisi. Les profils reçus restent en lecture seule.';
 sharing.prepend(info);
 const current=document.createElement('p');current.className='notice';current.id='outgoing-personal-name';
 sharing.prepend(current);
 function refreshName(){
  const p=profile();
  current.textContent='Profil que tu partages : '+(p?.name||'aucun');
 }
 sharing.addEventListener('click',refreshName);
 outer.append(summary,sharing);
 // Friend cards are inserted at the start of Shared; place this section after
 // them, before the URL/manual import card.
 const cards=Array.from(shared.children).filter(x=>x.classList?.contains('card'));
 const lookup=cards.find(x=>x.querySelector('#shared-public-url'));
 shared.insertBefore(outer,lookup||null);
 const advanced=document.createElement('details');advanced.id='outgoing-advanced';
 const advancedTitle=document.createElement('summary');advancedTitle.textContent='⚙ Gestion avancée du partage';
 advanced.append(advancedTitle);
 for(const id of ['stop-share','delete-active-share','manage-drive-share']){
  const control=$(id);if(control)advanced.append(control);
 }
 const notices=Array.from(sharing.children).filter(el=>el.matches('p.notice') &&
  el.textContent.includes('Pour lui retirer'));
 for(const notice of notices)advanced.append(notice);
 const unused=$('open-share');
 if(unused){unused.hidden=true;unused.style.display='none'}
 sharing.append(advanced);
 summary.addEventListener('click',()=>{refreshName();if(typeof shareStatus==='function')shareStatus()});
 const profileSelect=$('profile-picker');
 if(profileSelect)profileSelect.addEventListener('change',refreshName);
 refreshName();
})();
</script>
"""
R(h,'</body></html>',script+'</body></html>')
print("v1.6.22: outgoing sharing relocated and advanced controls collapsed")
