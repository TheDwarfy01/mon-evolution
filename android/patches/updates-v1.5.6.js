<script>
// GitHub Pages serves metadata only. Actual APK files live on GitHub Releases.
(function () {
  const installed='1.5.6';
  const releases='https://github.com/TheDwarfy01/mon-evolution/releases';
  const versionPattern=/^\d+(?:\.\d+){1,3}$/;
  const releasePage=v=>releases+'/tag/v'+v;
  const releaseApk=v=>releases+'/download/v'+v+'/Mon_Evolution_IMC_v'+v+'.apk';
  const legacyApk=v=>'https://thedwarfy01.github.io/mon-evolution/downloads/Mon_Evolution_IMC_v'+v+'.apk';
  function openOfficial(url){
    if(window.AndroidBackup?.openOfficialUrl){
      AndroidBackup.openOfficialUrl(url);
    }else{
      window.open(url,'_blank','noopener,noreferrer');
    }
  }
  function compareVersion(a,b){
    const x=String(a).split('.').map(Number),y=String(b).split('.').map(Number);
    for(let i=0;i<Math.max(x.length,y.length);i++){
      if((x[i]||0)!==(y[i]||0))return (x[i]||0)>(y[i]||0)?1:-1;
    }
    return 0;
  }
  const check=document.getElementById('update-check');
  const pageButton=document.getElementById('update-page-open');
  const directButton=document.getElementById('update-direct-open');
  const copyButton=document.getElementById('update-copy');
  const urlInput=document.getElementById('update-url');
  let latestVersion='';
  document.getElementById('releases-home').addEventListener('click',()=>openOfficial(releases));
  pageButton.addEventListener('click',()=>{
    if(versionPattern.test(latestVersion))openOfficial(releasePage(latestVersion));
  });
  directButton.addEventListener('click',()=>{
    if(versionPattern.test(latestVersion))openOfficial(releaseApk(latestVersion));
  });
  copyButton.addEventListener('click',()=>{
    if(!versionPattern.test(latestVersion))return;
    urlInput.value=releasePage(latestVersion);
    urlInput.focus();urlInput.select();
    try{document.execCommand('copy')}catch(_){}
    document.getElementById('update-status').textContent='Lien de la page GitHub sélectionné. Ouvre-le dans Chrome.';
  });
  check.addEventListener('click',function(){
    const status=document.getElementById('update-status');
    const box=document.getElementById('update-offer');
    status.textContent='Recherche de la dernière version publiée…';
    box.style.display='none';
    latestVersion='';
    let finished=false;
    const script=document.createElement('script');
    const watchdog=setTimeout(()=>finish('Vérification indisponible. Ouvre directement la page GitHub.'),12000);
    function finish(txt){
      if(finished)return;
      finished=true;
      clearTimeout(watchdog);
      status.textContent=txt;
      script.remove();
    }
    window.__monEvolutionVersionCallback=function(info){
      const v=String(info?.version||'');
      if(!versionPattern.test(v)||!info.published||(
         info.url!==releaseApk(v) && info.url!==legacyApk(v))){
        finish('Informations de mise à jour invalides.');return;
      }
      if(compareVersion(v,installed)>0){
        latestVersion=v;
        document.getElementById('update-details').textContent='Nouvelle version disponible : '+v;
        urlInput.value=releasePage(v);
        box.style.display='block';
        finish('Version '+v+' disponible sur GitHub Releases.');
      }else{
        finish('Aucune mise à jour plus récente publiée sur GitHub.');
      }
    };
    script.onerror=()=>finish('Connexion impossible. Tu peux ouvrir la page GitHub.');
    script.src='https://thedwarfy01.github.io/mon-evolution/version.js?cache='+Date.now();
    document.head.appendChild(script);
  });
})();
</script>