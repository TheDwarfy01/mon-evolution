/* Mobile-safe, stable label lanes around the 3D body.
 * Labels are independent from the draggable model and remain visible on
 * screen at every angle; dashed leader paths track their 3D anchors.
 */
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function layoutLandmarkCallouts(items,width,height,{labelWidth=104,labelHeight=34,gap=7}={}){
 if(!(width>=120&&height>=120))return [];
 const slots=[];
 const margin=5;
 const maxTop=Math.max(margin,height-labelHeight-margin);
 for(const side of ['left','right']){
  const ordered=items.filter(item=>item.side===side&&Number.isFinite(item.x)&&Number.isFinite(item.y))
   .sort((a,b)=>a.y-b.y || String(a.key).localeCompare(String(b.key)));
  if(!ordered.length)continue;
  const spacing=Math.min(labelHeight+gap,(height-labelHeight-2*margin)/Math.max(1,ordered.length-1));
  const tops=ordered.map(item=>clamp(item.y-labelHeight/2,margin,maxTop));
  for(let i=1;i<tops.length;i++)tops[i]=Math.max(tops[i],tops[i-1]+spacing);
  if(tops.at(-1)>maxTop){
   tops[tops.length-1]=maxTop;
   for(let i=tops.length-2;i>=0;i--)tops[i]=Math.min(tops[i],tops[i+1]-spacing);
  }
  const left=side==='left'?margin:Math.max(margin,width-labelWidth-margin);
  for(let i=0;i<ordered.length;i++){
   const top=clamp(tops[i],margin,maxTop);
   const ax=side==='left'?left+labelWidth:left;
   slots.push({...ordered[i],left,top,width:labelWidth,height:labelHeight,
    connectorX:ax,connectorY:top+labelHeight/2});
  }
 }
 return slots;
}
