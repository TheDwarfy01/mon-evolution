// Mon Évolution IMC — dernière version sur GitHub Releases.
window.__monEvolutionVersionCallback?.({
  version: "1.5.6",
  published: true,
  url: "https://github.com/TheDwarfy01/mon-evolution/releases/download/v1.5.6/Mon_Evolution_IMC_v1.5.6.apk"
});
// Les anciennes versions utilisent un champ de lien unique : prioriser la
// page GitHub (Assets), qui fonctionne sur Samsung.
(function(){
  var input=document.getElementById('update-url');
  var offer=document.getElementById('update-offer');
  if(input && offer && offer.style.display==='block'){
    input.value="https://github.com/TheDwarfy01/mon-evolution/releases/tag/v1.5.6";
    var status=document.getElementById('update-status');
    if(status)status.textContent="Version 1.5.6 disponible : ouvre la page GitHub puis Assets.";
  }
})();
