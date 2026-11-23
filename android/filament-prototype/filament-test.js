/* Experimental native Filament viewer. Never replaces the production Three.js canvas. */
(function(){
  "use strict";
  function mount(){
    const stage=document.getElementById('bm-model');
    if(!stage||document.getElementById('filament-probe-launcher'))return false;
    const launch=document.createElement('button');
    launch.id='filament-probe-launcher';
    launch.type='button';
    launch.textContent='🔬 Tester Filament (moteur alternatif)';
    launch.title='Ouvre un diagnostic natif du GLB original, sans modifier vos mensurations.';
    launch.style.cssText='display:block;width:100%;margin:8px 0 12px;padding:12px;border-radius:12px;background:#123f54;color:#dffff9;border:1px solid #7be3d0;font-weight:700;';
    launch.addEventListener('click',()=>{
      if(window.AndroidBackup && typeof AndroidBackup.openFilamentPreview==='function'){
        AndroidBackup.openFilamentPreview();
      }else{
        alert('Visualiseur Filament non disponible dans cette version.');
      }
    });
    stage.before(launch);
    return true;
  }
  if(!mount()){
    let count=0;
    const timer=setInterval(()=>{if(mount()||++count>25)clearInterval(timer);},250);
  }
})();
