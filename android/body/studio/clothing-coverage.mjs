/* Explicit coverage zones for original CC0 MakeHuman clothing models.
 * This is a rendering-only mask; the source assets are never modified.
 */
export const BODY_ZONE=Object.freeze({
 feet:1,legs:2,hips:4,torso:8,coat:16,underwear_m:32,
 underwear_f:64,bra:128,shorts:256,shirt:512,hoodie:1024,
 dress:2048,jacket:4096,boots:8192
});
export const GARMENT_ZONE=Object.freeze({
 'clothing_tshirt.glb':['torso','shirt'],
 'clothing_shirt.glb':['shirt','torso'],
 'clothing_hoodie.glb':['hoodie','torso','shirt'],
 // Jeans also cover the hips/pelvis: omitting these leaves brown patches
 // protruding through the waistband and pockets.
 'clothing_jeans.glb':['legs','hips','shorts'],
 'clothing_shorts.glb':['shorts','hips'],
 'clothing_skirt.glb':['hips','shorts'],
 'clothing_shoes.glb':['feet']
});
export function hideMaskFor(files){
 let mask=0;
 for(const name of files||[])for(const zone of GARMENT_ZONE[name]||[])
  mask|=BODY_ZONE[zone]||0;
 return mask;
}
export function coveredTriangle(zones,mask){
 if(!mask||!Array.isArray(zones)||zones.length!==3)return false;
 // A body triangle at the seam often has one vertex in an adjacent region.
 // Requiring 3/3 (the old code) exposed a jagged strip of skin. Hide 2/3.
 let match=0;
 for(const z of zones)if((Math.round(z)&mask)!==0)match++;
 return match>=2;
}
export function behindOpaqueGarment(yNorm,xNorm,files){
 if(!Array.isArray(files)||files.length===0)return false;
 const has=name=>files.includes(name);
 const trousers=has('clothing_jeans.glb');
 const shorts=has('clothing_shorts.glb');
 const skirt=has('clothing_skirt.glb');
 const top=has('clothing_tshirt.glb')||has('clothing_shirt.glb')||has('clothing_hoodie.glb');
 const shoes=has('clothing_shoes.glb');
 // Conservative backup for GLBs where custom _CCZONE is absent on a few
 // boundary triangles. Do not hide arms, hands, face or neck.
 if(trousers && yNorm>=.075 && yNorm<=.51 && xNorm<.24)return true;
 if((shorts||skirt)&&yNorm>=.33&&yNorm<=.51&&xNorm<.23)return true;
 if(top&&yNorm>=.56&&yNorm<=.735&&xNorm<.175)return true;
 if(shoes&&yNorm<=.062&&xNorm<.26)return true;
 return false;
}
