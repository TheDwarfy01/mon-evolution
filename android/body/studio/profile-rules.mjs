/* Exact profile authority for MakeHuman Studio.
 * Never infer a sex from appearance settings, name, or other heuristics.
 * Age is computed from the declared birth date, not from an adult default.
 */
export function profileCategory(p,now=Date.now()){
 if(!p || (p.sex!=='male'&&p.sex!=='female'))return null;
 if(typeof p.birthDate!=='string'||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(p.birthDate))return null;
 const [year,month,day]=p.birthDate.split('-').map(Number);
 const date=new Date(p.birthDate+'T12:00:00');
 if(!Number.isFinite(date.getTime()) || date.getFullYear()!==year ||
    date.getMonth()+1!==month || date.getDate()!==day ||
    date.getTime()>now || year<1900)return null;
 const age=Math.min(105,Math.max(0,(now-date.getTime())/31556952000));
 const child=age<18;
 return {sex:p.sex,age,child,kind:(child?'child_':'adult_')+p.sex};
}
const LISTS=Object.freeze({
 adult_male:Object.freeze(['classic','summer']),
 adult_female:Object.freeze(['classic','summer','skirt']),
 child_male:Object.freeze(['classic','summer']),
 child_female:Object.freeze(['classic','summer'])
});
export function allowedOutfitsFor(kind){
 return LISTS[kind] ? [...LISTS[kind]] : [];
}
