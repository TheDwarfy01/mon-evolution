/* Subtle facial presets using REAL MakeHuman Studio CC0 morph target names.
 * Designed to preserve expressions, eye/hair colours, age and all body measures.
 * No direct vertex surgery: the same targets exist on face, eyes, eyelashes and brows.
 */
const SOFT=Object.freeze({
 adult_female:Object.freeze({
  face_nose_width_decr:.16,face_nose_length_decr:.06,
  face_jaw_width_decr:.14,face_cheekbones_incr:.12,
  face_eye_size_incr:.095,face_lips_incr:.09,face_chin_decr:.045
 }),
 adult_male:Object.freeze({
  face_nose_width_decr:.10,face_jaw_width_decr:.065,
  face_cheekbones_incr:.085,face_eye_size_incr:.06,
  face_lips_incr:.045
 }),
 child_female:Object.freeze({
  face_nose_width_decr:.06,face_jaw_width_decr:.065,
  face_cheekbones_incr:.075,face_eye_size_incr:.055,
  face_lips_incr:.035
 }),
 child_male:Object.freeze({
  face_nose_width_decr:.055,face_jaw_width_decr:.04,
  face_cheekbones_incr:.06,face_eye_size_incr:.055
 })
});
export const FACE_CHOICES=Object.freeze([
 Object.freeze({id:'natural',label:'Naturel'}),
 Object.freeze({id:'soft',label:'Traits doux'})
]);
export function faceMorphsFor(kind,preset){
 if(preset!=='soft')return {};
 return {...(SOFT[kind]||{})};
}
