// Mon Évolution IMC — dernière version téléchargeable.
window.__monEvolutionVersionCallback?.({
  version: "1.5.4",
  published: true,
  url: "https://thedwarfy01.github.io/mon-evolution/downloads/Mon_Evolution_IMC_v1.5.4.apk"
});
(function(){
  var input=document.getElementById('update-url');
  var offer=document.getElementById('update-offer');
  if(input && offer && offer.style.display==='block'){
    input.value="https://github.com/TheDwarfy01/mon-evolution/releases/download/v1.5.4/Mon_Evolution_IMC_v1.5.4.apk";
    var status=document.getElementById('update-status');
    if(status) status.textContent="Version 1.5.4 disponible. Copiez le lien GitHub Releases et ouvrez-le dans Chrome.";
  }
})();
