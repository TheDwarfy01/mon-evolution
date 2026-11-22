/* MakeHuman body-morph adapter: parameters for a future exported 3D mesh.
 * This module never infers actual appearance from BMI alone.
 * A compatible MakeHuman GLB with named morph targets is required to render.
 */
(function(global){
  'use strict';
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  function parameters(profile){
    const p=profile||{};
    const heightCm=Number(p.height), weightKg=Number(p.weight);
    if(!(heightCm>=40&&heightCm<=230&&weightKg>=2&&weightKg<=350))
      return {valid:false,reason:'height_weight_missing'};
    const age=(p.age===undefined||p.age===null||p.age==='')?NaN:Number(p.age);
    const birth=p.birthDate||p.birth||p.dob||p.dateNaissance;
    let ageYears=age;
    if(!Number.isFinite(ageYears)&&typeof birth==='string'){
      const parsed=new Date(birth),today=new Date();
      if(!Number.isNaN(parsed.getTime()))
        ageYears=(today-parsed)/(365.2425*24*60*60*1000);
    }
    const child=(p.isChild===true||p.child===true)||(Number.isFinite(ageYears)&&ageYears>=0&&ageYears<18);
    const bmi=weightKg/Math.pow(heightCm/100,2);
    if(child){
      // Never derive a child's body shape from adult BMI cutoffs.
      // An age-appropriate MakeHuman child model with validated morphs
      // is required; only height scaling is exposed until then.
      return {valid:true,child:true,ageYears,
        heightScale:clamp(heightCm/140,.25,1.65),
        weightShape:null,waistShape:null,
        bmi:Number(bmi.toFixed(2)),
        indicativeOnly:true,weightLossGoalAllowed:false,
        needsAgeAppropriateMorph:true};
    }
    // This is a visual proxy, NOT an anatomical prediction.
    const weightShape=clamp((bmi-21)/23,-.65,1);
    const waist=Number(p.waist),hip=Number(p.hips),chest=Number(p.chest);
    const ratio=(finite(waist)&&waist>0&&finite(hip)&&hip>0)?waist/hip:null;
    return {valid:true,bmi:Number(bmi.toFixed(2)),
      heightScale:clamp(heightCm/170,.47,1.36),
      weightShape,waistHipRatio:ratio,
      waistShape:ratio===null?null:clamp((ratio-.82)*2,-.35,.5),
      chestCm:chest>0&&chest<220?chest:null,
      indicativeOnly:true};
  }
  function apply(mesh,params){
    if(!mesh||!params?.valid||!mesh.morphTargetDictionary||!mesh.morphTargetInfluences)return false;
    const dict=mesh.morphTargetDictionary, influences=mesh.morphTargetInfluences;
    // Supported exporter must supply these shape keys with matching topology.
    if(params.child)return false; // no adult shape morph on children
    const index=dict.body_weight;
    if(!Number.isInteger(index))return false;
    influences[index]=clamp(params.weightShape,0,1);
    if(Number.isInteger(dict.body_slim))influences[dict.body_slim]=clamp(-params.weightShape,0,1);
    if(Number.isInteger(dict.body_waist)&&params.waistShape!==null)
      influences[dict.body_waist]=clamp(params.waistShape,0,1);
    return true;
  }
  global.MonEvolutionBodyMorph={parameters,apply};
})(typeof window!=='undefined'?window:globalThis);
