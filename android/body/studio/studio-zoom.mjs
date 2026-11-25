// Camera-only zoom: never alter the mesh, morph values or recorded measurements.
export const initialView=()=>({zoom:1,x:0,y:0});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function boundedView(zoom,x,y,aspect=1){
 const z=clamp(Number.isFinite(zoom)?zoom:1,1,3);
 const travel=1.2*(1-1/z);
 return {zoom:z,x:clamp(Number.isFinite(x)?x:0,-travel*aspect,travel*aspect),
  y:clamp(Number.isFinite(y)?y:0,-travel,travel)};
}
export function pinchView(view,oldPair,newPair,width,height){
 if(!(height>0&&width>0))return view;
 const dist=p=>Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);
 const center=p=>({x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2});
 const d=dist(oldPair),next=dist(newPair);
 if(d<4||next<4)return view;
 const zoom=clamp(view.zoom*next/d,1,3),a=center(oldPair),b=center(newPair);
 const oldScale=2.4/(height*view.zoom),newScale=2.4/(height*zoom);
 return boundedView(zoom,view.x+(a.x-width/2)*oldScale-(b.x-width/2)*newScale,
  view.y-(a.y-height/2)*oldScale+(b.y-height/2)*newScale,width/height);
}
