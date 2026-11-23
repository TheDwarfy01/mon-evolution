/* Mon Évolution IMC — independent, non-medical circumference-to-shape guide.
 * This does NOT reconstruct body anatomy from a circumference or estimate
 * clinical body composition. It gives bounded, smoothly distributed visual
 * changes around the selected anatomical regions of a MakeHuman mesh.
 */
export const REGIONS=Object.freeze([
 {key:'neck',label:'Cou',min:10,max:110,y:.845,x:.07,z:.095,r:.055,kind:'center',base:.215},
 {key:'chest',label:'Poitrine',min:20,max:260,y:.705,x:-.13,z:.105,r:.082,kind:'center',base:.525},
 {key:'arm',label:'Bras',min:10,max:110,y:.665,x:.295,z:.065,r:.080,kind:'arm',base:.185},
 {key:'forearm',label:'Avant-bras',min:10,max:110,y:.535,x:.415,z:.09,r:.075,kind:'arm',base:.155},
 {key:'waist',label:'Taille',min:20,max:260,y:.643,x:-.115,z:.14,r:.057,kind:'center',base:.445},
 {key:'belly',label:'Ventre',min:20,max:300,y:.600,x:.12,z:.155,r:.059,kind:'center',base:.465},
 {key:'hips',label:'Hanches',min:20,max:300,y:.557,x:-.17,z:.125,r:.071,kind:'center',base:.525},
 {key:'thigh',label:'Cuisse',min:15,max:200,y:.340,x:-.175,z:.075,r:.102,kind:'leg',base:.315},
 {key:'calf',label:'Mollet',min:10,max:130,y:.165,x:.175,z:.08,r:.082,kind:'leg',base:.215}
]);
const MAP=Object.fromEntries(REGIONS.map(r=>[r.key,r]));
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const gauss=(x,c,r)=>Math.exp(-.5*((x-c)/r)**2);
export const validMeasure=(key,value)=>MAP[key] && Number.isFinite(value) &&
 value>=MAP[key].min && value<=MAP[key].max;
export function latestMeasurements(profile){
 const rows=(Array.isArray(profile?.bodyMeasurements)?profile.bodyMeasurements:[])
  .filter(r=>r&&typeof r.date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(r.date))
  .slice().sort((a,b)=>a.date.localeCompare(b.date)||(a.updatedAt||'').localeCompare(b.updatedAt||''));
 const result={};
 for(const row of rows){
  for(const item of REGIONS)if(validMeasure(item.key,row[item.key]))
   result[item.key]=row[item.key];
 }
 return result;
}
export function visualRatios(measures,heightCm,weightKg,child=false,estimated=false){
 const result={};
 if(!(heightCm>=40&&heightCm<=240&&weightKg>1))return result;
 // Expected circumferences are visual heuristics only, not clinical norms.
 const bmi=weightKg/((heightCm/100)**2);
 // Keep the historic measurement-based deformation unchanged.
 // Estimated mode must not normalize away high-BMI shape changes.
 const bulk=child||estimated?1:clamp(1+(bmi-23)*.009,.85,1.18);
 for(const r of REGIONS){
  const v=measures[r.key];
  if(!validMeasure(r.key,v))continue;
  const baseline=heightCm*r.base*bulk;
  // Explicitly cap deformation to reduce garment collisions or distortions.
  const raw=clamp(v/baseline,.70,estimated&&!child?2.35:1.30);
  result[r.key]=1+(raw-1)*.78;
 }
 return result;
}
// Return body-centric coordinates from a base vertex without changing bone
// indices, weights, normals, target names or immutable source geometry.
export function deformPosition(x,y,z,minY,height,ratios,estimated=false){
 if(!(height>.1))return [x,y,z];
 const yn=clamp((y-minY)/height,-.2,1.2);
 const midX=height*.125;
 let center=0,centerWeight=0,arm=0,leg=0;
 for(const r of REGIONS){
  const ratio=ratios[r.key];
  if(!Number.isFinite(ratio))continue;
  // In estimated adult mode the arms hang from shoulder to elbow and wrist:
  // the old arm/forearm peaks (.665/.535) sat too low, beside the torso.
  // Preserve measured and child deformations exactly as before.
  const centerY=estimated?(r.key==='arm'?.735:r.key==='forearm'?.635:r.y):r.y;
  const radius=estimated&&(r.key==='arm'||r.key==='forearm')?.075:r.r;
  let alpha=gauss(yn,centerY,radius)*(ratio-1);
  if(r.kind==='center'){center+=alpha;centerWeight+=gauss(yn,r.y,r.r);}
  else if(r.kind==='arm')arm+=alpha;
  else leg+=alpha;
 }
 const ax=Math.abs(x);
 const mid=clamp((ax-height*.16)/(height*.08),0,1);
 const legs=clamp((ax-height*.05)/(height*.08),0,1);
 // At high weight, the old torso/arm split assigned most upper-arm
 // vertices to the chest and inflated sleeves while leaving forearms thin.
 // Locate the limb smoothly from the side of the chest towards elbow/wrist.
 // Measured silhouettes preserve the existing split.
 const smoothstep=t=>{const v=clamp(t,0,1);return v*v*(3-2*v);};
 const armProximity=estimated?
  smoothstep((ax/height-.118)/.078)*
  smoothstep((yn-.57)/.085)*
  (1-smoothstep((yn-.83)/.065)):0;
 const armFactor=estimated?Math.max(mid,armProximity):mid;
 const shoulderDamping=estimated?
  1-.58*smoothstep((yn-.70)/.10)*
      smoothstep((ax/height-.082)/.095):1;
 const torsoFactor=(1-armFactor)*shoulderDamping;
 const legFactor=legs;
 // Average overlapping torso zones so that individual edited circumferences
 // remain responsive at higher weights rather than clipping immediately.
 // Measured mode retains the exact earlier deformation.
 const effectiveCenter=estimated&&centerWeight>0?
  (center/Math.max(1,centerWeight))*.70:center;
 const cap=estimated?.35:.23;
 const armResponse=estimated?1.16:1;
 const amount=clamp(effectiveCenter*torsoFactor+arm*armFactor*armResponse+leg*legFactor,-cap,cap);
 // Extremities: dilate about each limb axis, never push the limb sideways
 // as a whole. Torso and hips expand symmetrically about the mid-line.
 // Never snap the deformation axis at an arbitrary limb threshold:
 // that creates visible cracks at elbows and thigh seams as points pass .7.
 const upper=smoothstep((yn-.43)/.14);
 const lower=1-smoothstep((yn-.40)/.14);
 const armBlend=smoothstep((armFactor-.25)/.65)*upper;
 const legBlend=smoothstep((legFactor-.25)/.65)*lower;
 // A bent arm's approximate medial axis varies from shoulder to wrist.
 // A fixed x=.22H axis was inappropriate near the female shoulder/upper arm.
 const armAxis=estimated?height*clamp(.100+(.795-yn)*.91,.100,.274):height*.22;
 const axis=Math.sign(x)*(
  armAxis*armBlend + midX*legBlend*(1-armBlend)
 );
 return [axis+(x-axis)*(1+amount),y,z*(1+amount)];
}
