/* Mild nonmedical visual-only smoothing for weight-estimated adult inner thighs.
 * No saved measurement, biometric estimate or mode preference is altered.
 */
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const smooth=t=>{const n=clamp(t,0,1);return n*n*(3-2*n);};
export function estimatedThighIntensity(cm,kg,child=false){
 if(child||!Number.isFinite(cm)||!Number.isFinite(kg)||cm<100||kg<=0)return 0;
 return clamp((kg/((cm/100)**2)-18)/12,0,1);
}
export function softenInnerThigh(x,y,z,minY,height,intensity=0){
 if(!(height>.1)||!(intensity>0)||![x,y,z].every(Number.isFinite))return [x,y,z];
 const yn=(y-minY)/height;
 const vertical=smooth((yn-.205)/.095)*(1-smooth((yn-.405)/.085));
 const medial=1-smooth((Math.abs(x)/height-.020)/.080);
 if(vertical<=0||medial<=0||Math.abs(x)<height*.009)return [x,y,z];
 const dx=height*(.004+.013*clamp(intensity,0,1))*vertical*medial;
 return [Math.sign(x)*Math.max(height*.010,Math.abs(x)-dx),y,z];
}
