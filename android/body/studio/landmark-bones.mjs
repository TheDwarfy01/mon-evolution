/* Rig-based 3D anchors: names verified against base_body_anim.glb (53 joints). */
const JOINTS={
 neck:['neck_01','head',.34],
 chest:['spine_03','neck_01',.36],
 arm:['upperarm_l','lowerarm_l',.43],
 forearm:['lowerarm_l','hand_l',.42],
 waist:['spine_02','spine_03',.65],
 belly:['spine_01','spine_02',.60],
 hips:['pelvis','spine_01',.63],
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

/* Surface-facing offsets in meters, applied in world/camera space after
 * the exact animated bone interpolation. The spine bones lie INSIDE the body;
 * moving a marker to the skin-facing plane is essential for correct visuals.
 * This never changes the real measurement, shape, or the bone itself.
 */
const SURFACE=Object.freeze({
 neck:[0,.07],chest:[-.07,.13],
 waist:[-.145,.115],belly:[.06,.145],hips:[-.165,.115]
});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function anatomicalSurfaceOffset(key,yaw=0,heightCm=170){
 const point=SURFACE[key];if(!point)return [0,0,0];
 const c=Math.abs(Math.cos(Number.isFinite(yaw)?yaw:0));
 const scale=clamp(Number.isFinite(heightCm)?heightCm/170:1,.55,1.20);
 const screenX=point[0]*(.72+.28*c)*scale;
 return [screenX,0,point[1]*scale];
}
