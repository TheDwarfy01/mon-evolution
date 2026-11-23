/* Anatomical marker placement and collision avoidance for the 3D studio.
 * The screen positions are visual only: measurement values and persistence
 * remain entirely managed by the existing form.
 */
import {deformPosition} from './measurement-morph.mjs';

const HEIGHTS=Object.freeze({
 neck:.895,chest:.720,arm:.670,forearm:.535,
 waist:.570,belly:.520,hips:.445,thigh:.340,calf:.165
});
const SURFACE=Object.freeze({
 neck:.070,chest:.155,arm:.070,forearm:.065,
 waist:.140,belly:.155,hips:.175,thigh:.105,calf:.080
});
const LIMBS=new Set(['arm','forearm','thigh','calf']);
const clamp=(v,low,high)=>Math.max(low,Math.min(high,v));

/* Smoothly follow the nearest visible surface as the model turns. A flip at
 * exactly 90 degrees made the old landmarks jump across the silhouette.
 * The same deformPosition used by body meshes follows recorded morph ratios.
 */
export function markerLocalPosition(region,bounds,ratios={},yaw=0){
 const h=bounds?.height,base=bounds?.minY;
 if(!(h>0)||!Number.isFinite(base))return [0,0,0];
 const size=h/1.75,turn=Number.isFinite(yaw)?yaw:0;
 const facingX=-Math.sin(turn),facingZ=Math.cos(turn);
 const x=LIMBS.has(region.key)
  ? size*(region.x*(1-Math.abs(facingX))+Math.abs(region.x)*facingX*Math.abs(facingX))
  : size*(region.x+(SURFACE[region.key]||.10)*facingX);
 const z=size*region.z*facingZ;
 const y=base+h*(HEIGHTS[region.key]??region.y);
 return deformPosition(x,y,z,base,h,ratios);
}

/* Keep markers very near their real anchors. A small offset, when needed,
 * prevents touch targets from covering one another in side/profile views.
 * Connectors can then end at the precise original anatomical anchor.
 */
export function declutterMarkerPositions(items,width,height,{
 minDistance=27,maxOffset=30,padding=14
}={}){
 const nodes=items.map(item=>({...item,anchorX:item.x,anchorY:item.y}));
 if(nodes.length<2)return nodes;
 function limit(n){
  const dx=n.x-n.anchorX,dy=n.y-n.anchorY;
  const dist=Math.hypot(dx,dy);
  if(dist>maxOffset){n.x=n.anchorX+dx*maxOffset/dist;n.y=n.anchorY+dy*maxOffset/dist;}
  n.x=clamp(n.x,padding,Math.max(padding,width-padding));
  n.y=clamp(n.y,padding,Math.max(padding,height-padding));
 }
 for(let pass=0;pass<32;pass++){
  let collisions=0;
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
   const a=nodes[i],b=nodes[j],dx=b.x-a.x,dy=b.y-a.y;
   const distance=Math.hypot(dx,dy);
   if(distance>=minDistance-.2)continue;
   collisions++;
   // With coincident anchors use a stable angle, not a random direction.
   const angle=(i*3+j*5)*2.399963229728653;
   const ux=distance>.001?dx/distance:Math.cos(angle);
   const uy=distance>.001?dy/distance:Math.sin(angle);
   const shift=(minDistance-distance)/2+.03;
   a.x-=ux*shift;a.y-=uy*shift;
   b.x+=ux*shift;b.y+=uy*shift;
   limit(a);limit(b);
  }
  if(!collisions)break;
 }
 return nodes;
}
