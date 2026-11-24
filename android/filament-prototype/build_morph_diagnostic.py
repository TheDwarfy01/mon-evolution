#!/usr/bin/env python3
"""Create a static CC0 Filament body with 9 reversible morphology controls.
This is a visual diagnostic, NOT a medical anatomical estimate."""
import json, math, struct, sys
from pathlib import Path
REGIONS=[('neck',.845,.055,'center'),('chest',.705,.082,'center'),
 ('arm',.745,.085,'arm'),('forearm',.648,.085,'arm'),('waist',.643,.057,'center'),
 ('belly',.600,.105,'center'),('hips',.557,.071,'center'),
 ('thigh',.340,.102,'leg'),('calf',.165,.082,'leg')]
def smooth(x):
 x=max(0.,min(1.,x));return x*x*(3.-2.*x)
def smooth_band(v, lo, hi):
    return smooth((v-lo)/(hi-lo))

def skin_vertex_groups(document,binary,compact,compact_binary):
    """Recover native MakeHuman skin weights, then discard the skin at export.
    The original and stable compact body must have precisely matching vertices.
    These weights classify torso, arms, hands, legs and feet anatomically,
    avoiding the previous error where belly editing moved wrists and fingers.
    """
    src=document['meshes'][0]['primitives'][0]
    dst=compact['meshes'][0]['primitives'][0]
    def values(gltf,data,idx,unit):
        acc=gltf['accessors'][idx]
        view=gltf['bufferViews'][acc['bufferView']]
        assert not view.get('byteStride')
        offset=view.get('byteOffset',0)+acc.get('byteOffset',0)
        length=acc['count']*unit
        return data[offset:offset+length],acc
    positions,pa=values(document,binary,src['attributes']['POSITION'],12)
    same,pb=values(compact,compact_binary,dst['attributes']['POSITION'],12)
    assert pa['count']==pb['count'] and positions==same, "Body vertex mapping changed"
    joints,ja=values(document,binary,src['attributes']['JOINTS_0'],4)
    weights,wa=values(document,binary,src['attributes']['WEIGHTS_0'],16)
    assert ja['count']==wa['count']==pa['count']
    assert ja['componentType']==5121 and wa['componentType']==5126
    names=[document['nodes'][idx].get('name','') for idx in document['skins'][0]['joints']]
    categories=[]
    for name in names:
        if name in ('Root','pelvis') or name.startswith('spine_'): cat='torso'
        elif name.startswith('neck_'): cat='neck'
        elif name=='head': cat='head'
        elif name.startswith('clavicle_'):cat='clavicle'
        elif name.startswith('upperarm_'):cat='upperarm'
        elif name.startswith('lowerarm_'):cat='lowerarm'
        elif name.startswith(('hand_','index_','middle_','pinky_','ring_','thumb_')):cat='hand'
        elif name.startswith('thigh_'):cat='thigh'
        elif name.startswith('calf_'):cat='calf'
        elif name.startswith(('foot_','ball_')):cat='foot'
        else: raise ValueError('Unknown MakeHuman joint '+name)
        categories.append(cat)
    result=[]
    for i in range(pa['count']):
        joint_ids=joints[i*4:i*4+4]
        w=struct.unpack_from('<ffff',weights,i*16)
        assert abs(sum(w)-1)<.002
        d={}
        for joint,weight in zip(joint_ids,w):
            group=categories[joint]
            d[group]=d.get(group,0.0)+weight
        result.append(d)
    return result

def warp(key,x,y,z,lo,hi,change,skin):
    h=hi-lo;t=(y-lo)/h
    center,radius,kind=next((c,r,k) for name,c,r,k in REGIONS if name==key)
    vertical=math.exp(-.5*((t-center)/radius)**2)
    arm_skin=sum(skin.get(k,0) for k in ('clavicle','upperarm','lowerarm','hand'))
    leg_skin=sum(skin.get(k,0) for k in ('thigh','calf','foot'))
    hand_skin=skin.get('hand',0)
    foot_skin=skin.get('foot',0)
    if kind=='center':
        # Arm geometry and the fingers are EXCLUDED even when they overlap the
        # abdomen in world-space Y. No x-only anatomical guesses are permitted.
        no_arms=1-smooth_band(arm_skin,.015,.18)
        no_legs=1-smooth_band(leg_skin,.08,.52)
        no_head=1-smooth_band(skin.get('head',0),.005,.22)
        influence=vertical*no_arms*no_legs*no_head
        if key=='neck':
            influence*=smooth_band(skin.get('neck',0)+skin.get('torso',0),.04,.6)
        axis=0.
    elif kind=='arm':
        no_hands=1-smooth_band(hand_skin,.025,.55)
        no_torso=1-smooth_band(skin.get('torso',0),.15,.85)
        arm_bone=skin.get('upperarm',0)+.25*skin.get('lowerarm',0) if key=='arm' else skin.get('lowerarm',0)+.2*skin.get('upperarm',0)
        influence=vertical*smooth_band(arm_bone,.05,.55)*no_hands*no_torso
        axis=math.copysign(h*max(.1025,min(.274,.1025+(.795-t)*.94)),x)
    else:
        no_feet=1-smooth_band(foot_skin,.025,.6)
        leg_bone=skin.get('thigh',0)+.20*skin.get('calf',0) if key=='thigh' else skin.get('calf',0)+.18*skin.get('thigh',0)
        influence=vertical*smooth_band(leg_bone,.04,.6)*no_feet
        axis=math.copysign(h*.125,x)
    # Local belly control projects mainly FORWARD, not sideways.
    # Previous uniform xyz scaling produced exaggerated side lobes when
    # combined with the global fullness slider. Front-only projection also
    # preserves the abdominal/back contour on the opposite side.
    if key=='belly':
        forward=smooth_band(z,.008,.145)
        return (axis+(x-axis)*(1+change*influence*.10),
                y,z+change*influence*forward*.185)
    amplitude=change*influence
    return axis+(x-axis)*(1+amplitude),y,z*(1+amplitude)

def read(blob):
 assert blob[:4]==b'glTF' and struct.unpack_from('<II',blob,4)==(2,len(blob))
 n,t=struct.unpack_from('<II',blob,12);assert t==0x4e4f534a
 doc=json.loads(blob[20:20+n]);i=20+n;m,bt=struct.unpack_from('<II',blob,i)
 assert bt==0x004e4942
 return doc,bytearray(blob[i+8:i+8+m])
def build(source,original,out):
 doc,buf=read(Path(source).read_bytes())
 skinned,skin_binary=read(Path(original).read_bytes())
 skin_groups=skin_vertex_groups(skinned,skin_binary,doc,buf)
 assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==8
 body=doc['meshes'][0]['primitives'][0]
 a=doc['accessors'][body['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
 assert a['type']=='VEC3' and a['componentType']==5126
 start=v.get('byteOffset',0)+a.get('byteOffset',0)
 points=list(struct.iter_unpack('<fff',buf[start:start+a['count']*12]))
 lo=min(p[1] for p in points);hi=max(p[1] for p in points)
 assert len(points)>10000 and 1.4<hi-lo<1.9
 names=[];targets=[]
 for key,*_ in REGIONS:
  for sign,suffix in [(1,'plus'),(-1,'moins')]:
   block=bytearray();changed=0
   for i,(x,y,z) in enumerate(points):
    strength=(.70 if sign>0 else -.25) if key=='belly' else sign*.23
    nx,ny,nz=warp(key,x,y,z,lo,hi,strength,skin_groups[i])
    delta=(nx-x,ny-y,nz-z)
    changed+=abs(delta[0])+abs(delta[2])>1e-7
    block.extend(struct.pack('<fff',*delta))
   assert changed>50,(key,changed)
   if key=='belly' and sign>0:
    # A larger belly should project substantially forward while keeping
    # lateral x displacement well below the z projection.
    positive=[struct.unpack_from('<fff',block,i*12) for i in range(len(points))
              if skin_groups[i].get('torso',0)>.80 and
                 .53<(points[i][1]-lo)/(hi-lo)<.67 and points[i][2]>.06]
    assert len(positive)>25
    forward=max(dz for _,_,dz in positive)
    lateral=max(abs(dx) for dx,_,_ in positive)
    assert forward>.07 and lateral<.020,(forward,lateral)
   # Critical safety checks on every target, both directions:
   # belly/waist/chest/hps cannot translate hands, wrists or upper arms.
   if key in ('belly','waist','chest','hips','neck'):
    for i,(x,y,z) in enumerate(points):
     s=skin_groups[i]
     owned=s.get('upperarm',0)+s.get('lowerarm',0)+s.get('hand',0)+s.get('clavicle',0)
     if owned>=.18:
      dx,_,dz=struct.unpack_from('<fff',block,i*12)
      assert math.hypot(dx,dz)<.000001,(key,i,owned,dx,dz)
   if key in ('arm','forearm'):
    for i in range(len(points)):
     if skin_groups[i].get('hand',0)>=.55:
      dx,_,dz=struct.unpack_from('<fff',block,i*12)
      assert math.hypot(dx,dz)<.000001,("hands stationary",key,i,dx,dz)
   if key in ('thigh','calf'):
    for i in range(len(points)):
     if skin_groups[i].get('foot',0)>=.60:
      dx,_,dz=struct.unpack_from('<fff',block,i*12)
      assert math.hypot(dx,dz)<.000001,("feet stationary",key,i,dx,dz)
   while len(buf)%4:buf.append(0)
   doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(block)})
   buf.extend(block)
   doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,
      'componentType':5126,'count':len(points),'type':'VEC3'})
   targets.append({'POSITION':len(doc['accessors'])-1});names.append(key+'_'+suffix)
 assert len(targets)==18
 body['targets']=targets
 doc['meshes']=[{'name':'Corps 9 regions','primitives':[body],
       'weights':[0.]*18,'extras':{'targetNames':names}},
      {'name':'Visage stable','primitives':doc['meshes'][0]['primitives'][1:]}]
 doc['nodes']=[{'name':'Corps','mesh':0},{'name':'Visage','mesh':1}]
 doc['scenes']=[{'nodes':[0,1]}];doc['scene']=0
 doc['asset']['generator']='Mon Evolution IMC Filament 9 visual measurements (CC0 body)'
 doc['buffers'][0]['byteLength']=len(buf)
 js=json.dumps(doc,separators=(',',':')).encode('utf8');js+=b' '*(-len(js)%4)
 buf+=b'\0'*(-len(buf)%4)
 output=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(buf))
 output+=struct.pack('<II',len(js),0x4e4f534a)+js
 output+=struct.pack('<II',len(buf),0x004e4942)+bytes(buf)
 dest=Path(out);dest.write_bytes(output)
 verified,_=read(output)
 assert len(verified['meshes'][0]['primitives'][0]['targets'])==18
 assert len(verified['meshes'][1]['primitives'])==7
 assert 'skins' not in verified and 'animations' not in verified
 assert len(verified.get('images',[]))>=5
 print('Filament morph GLB',dest,len(output),'bytes')
if __name__=='__main__':
 assert len(sys.argv)==4
 build(sys.argv[1],sys.argv[2],sys.argv[3])
