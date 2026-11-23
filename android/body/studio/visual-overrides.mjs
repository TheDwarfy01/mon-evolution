/* Explicitly edited circumference values take priority over visual weight
 * estimates. The saved observations remain in bodyMeasurements, never here.
 * Per-profile storage records only which existing dated measurement to display.
 */
import {REGIONS,validMeasure} from './measurement-morph.mjs';
import {estimateVisualMeasurements} from './visual-defaults.mjs';
const known=new Set(REGIONS.map(r=>r.key));
const prefix='mon-evolution-studio-visual-overrides-v1:';
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s);
export function visualOverrideKey(id){
 const key=String(id??'');
 return key&&key.length<=128?prefix+key:null;
}
export function readVisualOverrides(id,store){
 const key=visualOverrideKey(id);if(!key)return {};
 try{
  const doc=JSON.parse(store?.getItem(key)||'{}');
  if(!doc||typeof doc!=='object'||Array.isArray(doc))return {};
  return Object.fromEntries(Object.entries(doc).filter(([k,v])=>known.has(k)&&validDate(v)));
 }catch{return {};}
}
export function recordVisualOverrides(id,date,keys,store){
 const storageKey=visualOverrideKey(id);
 if(!storageKey||!validDate(date)||!Array.isArray(keys))return false;
 const changed=keys.filter(k=>known.has(k));
 if(!changed.length)return false;
 const current=readVisualOverrides(id,store);
 for(const k of changed)current[k]=date;
 try{store?.setItem(storageKey,JSON.stringify(current));return true;}catch{return false;}
}
export function resolveVisualMeasurements(profile,mode,overrideDates={}){
 if(mode==='neutral')return {values:{},estimatedKeys:[]};
 if(mode!=='estimated')return {values:profile?.measurements||{},estimatedKeys:[]};
 const values=estimateVisualMeasurements(profile)||{};
 const estimated=new Set(Object.keys(values));
 const rows=Array.isArray(profile?.records)?profile.records:[];
 for(const [key,date] of Object.entries(overrideDates)){
  if(!known.has(key)||!validDate(date))continue;
  const row=rows.find(r=>r&&r.date===date);
  if(!row||!validMeasure(key,row[key]))continue;
  values[key]=row[key];estimated.delete(key);
 }
 return {values,estimatedKeys:[...estimated]};
}
