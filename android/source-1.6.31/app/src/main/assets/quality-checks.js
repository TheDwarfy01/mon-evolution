// Règles testables, hors stockage : ne transmettent aucune donnée personnelle.
// Utilisées pour valider les documents avant restauration/affichage.
(function(root){
 'use strict';
 const DATE=/^\d{4}-\d{2}-\d{2}$/;
 const number=(v,min,max)=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
 const validEntry=e=>!!e&&typeof e==='object'&&number(e.weight,1,400)&&
   typeof e.date==='string'&&DATE.test(e.date);
 const validProfile=p=>!!p&&typeof p==='object'&&
   typeof p.id==='string'&&p.id.length>0&&
   typeof p.name==='string'&&p.name.trim().length>0&&p.name.length<=100&&
   number(p.height,45,250)&&number(p.goal,1,400)&&
   Array.isArray(p.entries)&&p.entries.length>=1&&p.entries.length<=20000&&
   p.entries.every(validEntry);
 const isBackupDocument=doc=>!!doc&&doc.format==='mon-evolution'&&doc.version===1&&
   !!doc.data&&Array.isArray(doc.data.profiles)&&
   doc.data.profiles.length>=1&&doc.data.profiles.length<=50&&
   doc.data.profiles.every(validProfile);
 const isSharedDocument=doc=>{
   if(!doc||doc.format!=='mon-evolution-lecture-seule'||doc.version!==1||
     !doc.profile)return false;
   const p=doc.profile;
   return typeof p.name==='string'&&p.name.trim().length>0&&p.name.length<=100&&
     number(p.height,45,250)&&number(p.goal,1,400)&&
     Array.isArray(p.entries)&&p.entries.length>=1&&p.entries.length<=20000&&
     p.entries.every(validEntry);
 };
 const normalWeightRange=heightCm=>{
   if(!number(heightCm,45,250))return null;
   const factor=(heightCm/100)**2;
   return {low:18.5*factor,high:25*factor};
 };
 const bmiCategory=bmi=>{
   if(!Number.isFinite(bmi)||bmi<0)return null;
   if(bmi<18.5)return 'Insuffisance pondérale';
   if(bmi<25)return 'Corpulence normale';
   if(bmi<30)return 'Surpoids';
   if(bmi<35)return 'Obésité I';
   if(bmi<40)return 'Obésité II';
   return 'Obésité III';
 };
 const friendState=v=>['ok','pending','password','access','missing','network','preview','format','error'].includes(v)?v:'unknown';
 const invitationState=(linked,invitation,hasPassword)=>{
   if(!linked)return 'setup';
   if(typeof invitation!=='string'||!/^https:\/\/thedwarfy01\.github\.io\/mon-evolution\/share\.html\?/.test(invitation))return 'link';
   if(!hasPassword)return 'password';
   return 'ready';
 };
 root.MonEvolutionQuality=Object.freeze({
  validEntry,validProfile,isBackupDocument,isSharedDocument,
  normalWeightRange,bmiCategory,friendState,invitationState
 });
})(window);
