/* Rig-based 3D anchors: names verified against base_body_anim.glb (53 joints). */
const JOINTS={
 neck:['neck_01','head',.34],
 chest:['spine_03','neck_01',.36],
 arm:['upperarm_l','lowerarm_l',.43],
 forearm:['lowerarm_l','hand_l',.42],
 waist:['spine_01','spine_02',.56],
 belly:['pelvis','spine_01',.57],
 hips:['pelvis','thigh_r',.18],
 thigh:['thigh_r','calf_r',.43],
 calf:['calf_r','foot_r',.48]
};
export function requiredAnatomicalBones(){
 return [...new Set(Object.values(JOINTS).flatMap(([a,b])=>[a,b]))];
}
export function anatomicalAnchor(key,joints){
 const rule=JOINTS[key];if(!rule||!joints)return null;
 const [nameA,nameB,t]=rule,a=joints[nameA],b=joints[nameB];
 if(!Array.isArray(a)||!Array.isArray(b)||a.length!==3||b.length!==3||
   !a.every(Number.isFinite)||!b.every(Number.isFinite))return null;
 return a.map((n,i)=>n*(1-t)+b[i]*t);
}
