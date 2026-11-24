#!/usr/bin/env python3
"""Append bounded global body-size morphs to the validated nine-region Filament GLB.
All existing CC0 textures and nine local controls remain unchanged.
Global body fullness is a visual illustration, not a medical predictor of anatomy.
"""
from pathlib import Path
import json, struct, math, sys
from collections import defaultdict

def read(path):
    raw=Path(path).read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
    n,typ=struct.unpack_from('<II',raw,12);assert typ==0x4e4f534a
    doc=json.loads(raw[20:20+n]);off=20+n
    blen,btype=struct.unpack_from('<II',raw,off);assert btype==0x004e4942
    return doc,bytearray(raw[off+8:off+8+blen])

def access(doc,buffer,idx):
    a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    unit=({'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']])*({5126:4,5121:1,5123:2}[a['componentType']])
    return buffer[start:start+a['count']*unit],a

def skin_weights(orig,original_bytes,positions):
    prim=orig['meshes'][0]['primitives'][0]
    orig_pos,_=access(orig,original_bytes,prim['attributes']['POSITION'])
    assert orig_pos==positions, 'Original and compact body vertex order mismatch'
    raw_ji,ja=access(orig,original_bytes,prim['attributes']['JOINTS_0'])
    raw_wa,wa=access(orig,original_bytes,prim['attributes']['WEIGHTS_0'])
    assert ja['componentType']==5121 and wa['componentType']==5126
    names=[orig['nodes'][idx].get('name','') for idx in orig['skins'][0]['joints']]
    group=[]
    for n in names:
        if n in ('Root','pelvis') or n.startswith('spine_'):group.append('torso')
        elif n.startswith('neck_'):group.append('neck')
        elif n=='head':group.append('head')
        elif n.startswith('clavicle_'):group.append('clavicle')
        elif n.startswith('upperarm_'):group.append('upperarm')
        elif n.startswith('lowerarm_'):group.append('lowerarm')
        elif n.startswith(('hand_','index_','middle_','pinky_','ring_','thumb_')):group.append('hand')
        elif n.startswith('thigh_'):group.append('thigh')
        elif n.startswith('calf_'):group.append('calf')
        elif n.startswith(('foot_','ball_')):group.append('foot')
        else:raise ValueError('Unrecognized CC0 joint '+n)
    result=[]
    count=wa['count']
    assert count==ja['count'] and len(positions)==count*12
    for i in range(count):
        ids=raw_ji[4*i:4*i+4]
        weights=struct.unpack_from('<ffff',raw_wa,16*i)
        assert abs(sum(weights)-1)<.003
        agg=defaultdict(float)
        for joint,w in zip(ids,weights):agg[group[joint]]+=w
        result.append(agg)
    return result

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def gaussian(x,c,s):return math.exp(-.5*((x-c)/s)**2)

def warp_global(x,y,z,lo,hi,w,change):
    h=hi-lo;t=(y-lo)/h
    torso=w.get('torso',0);clav=w.get('clavicle',0)
    waist=gaussian(t,.60,.090)
    hips=gaussian(t,.525,.075)
    back=1-smooth((z-.02)/.16)
    # Different but coordinated anatomical fullness responses. Do not
    # stretch height or translate the complete limbs across the torso.
    torso_x=.155+.10*waist+.12*hips
    torso_z=.165+.16*waist+.17*hips*(.75+.5*back)
    x_gain=(torso*torso_x+clav*.135+w.get('neck',0)*.15+
            w.get('upperarm',0)*.21+w.get('lowerarm',0)*.16+
            w.get('hand',0)*.065+w.get('thigh',0)*.25+
            w.get('calf',0)*.16+w.get('foot',0)*.035+
            w.get('head',0)*.12)
    z_gain=(torso*torso_z+clav*.14+w.get('neck',0)*.16+
            w.get('upperarm',0)*.21+w.get('lowerarm',0)*.16+
            w.get('hand',0)*.065+w.get('thigh',0)*.25+
            w.get('calf',0)*.16+w.get('foot',0)*.035+
            w.get('head',0)*.105)
    arm_axis=min(.274,max(.1025,.1025+(.795-t)*.94))*h
    arm_axis=math.copysign(arm_axis,x)
    leg_axis=math.copysign(.125*h,x)
    arm_weight=sum(w.get(g,0) for g in ('clavicle','upperarm','lowerarm','hand'))
    leg_weight=sum(w.get(g,0) for g in ('thigh','calf','foot'))
    axis=arm_weight*arm_axis+leg_weight*leg_axis
    zcenter=(arm_weight*.065+leg_weight*.082+torso*.055+
             w.get('neck',0)*.04+w.get('head',0)*.055)
    # The face/eyes/teeth submeshes are free of the old skin. Head vertices
    # on the body and all separate face primitives use IDENTICAL transforms
    # above 1.44 m, preserving eyelid, mouth and eyeball registration.
    head=smooth((y-(hi-.279))/.060)
    x_gain=(1-head)*x_gain+head*.12
    z_gain=(1-head)*z_gain+head*.105
    axis=(1-head)*axis
    zcenter=(1-head)*zcenter+head*.055
    return (axis+(x-axis)*(1+change*x_gain),y,
            zcenter+(z-zcenter)*(1+change*z_gain))

def append_target(doc,buf,positions,lo,hi,skin,sign):
    block=bytearray()
    for i,(x,y,z) in enumerate(positions):
        nx,ny,nz=warp_global(x,y,z,lo,hi,skin[i],sign)
        block.extend(struct.pack('<fff',nx-x,ny-y,nz-z))
    while len(buf)%4:buf.append(0)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(block)})
    buf.extend(block)
    doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,
          'componentType':5126,'count':len(positions),'type':'VEC3'})
    return len(doc['accessors'])-1

def build(morph,original,destination):
    doc,buf=read(morph);orig,ob=read(original)
    assert len(doc['meshes'])==2 and len(doc['meshes'][0]['primitives'])==1
    assert len(doc['meshes'][1]['primitives'])==7
    body=doc['meshes'][0]['primitives'][0]
    assert len(body['targets'])==18 and len(doc['meshes'][0]['weights'])==18
    body_bytes,ba=access(doc,buf,body['attributes']['POSITION'])
    assert ba['componentType']==5126
    body_points=list(struct.iter_unpack('<fff',body_bytes))
    lo=min(y for x,y,z in body_points);hi=max(y for x,y,z in body_points)
    skin=skin_weights(orig,ob,body_bytes)
    for sign,name in [(1,'corpulence_plus'),(-1,'corpulence_moins')]:
        body['targets'].append({'POSITION':append_target(doc,buf,body_points,lo,hi,skin,sign)})
        doc['meshes'][0]['extras']['targetNames'].append(name)
        doc['meshes'][0]['weights'].append(0.)
        for prim in doc['meshes'][1]['primitives']:
            data,ac=access(doc,buf,prim['attributes']['POSITION'])
            assert ac['componentType']==5126
            points=list(struct.iter_unpack('<fff',data))
            assert points and min(p[1] for p in points)>1.44
            neutral=[{'head':1.} for _ in points]
            prim.setdefault('targets',[]).append(
                {'POSITION':append_target(doc,buf,points,lo,hi,neutral,sign)})
    doc['meshes'][1]['weights']=[0.,0.]
    doc['meshes'][1]['extras']={'targetNames':['corpulence_plus','corpulence_moins']}
    doc['asset']['generator']='Mon Evolution IMC global fullness + nine regions · CC0'
    doc['buffers'][0]['byteLength']=len(buf)
    data=json.dumps(doc,separators=(',',':')).encode('utf8')
    data+=b' '*(-len(data)%4)
    buf+=b'\0'*(-len(buf)%4)
    binary=(struct.pack('<III',0x46546c67,2,12+8+len(data)+8+len(buf))+
          struct.pack('<II',len(data),0x4e4f534a)+data+
          struct.pack('<II',len(buf),0x004e4942)+bytes(buf))
    Path(destination).write_bytes(binary)
    check,_=read(destination)
    assert len(check['meshes'][0]['primitives'][0]['targets'])==20
    assert all(len(p['targets'])==2 for p in check['meshes'][1]['primitives'])
    assert len(check['meshes'][0]['weights'])==20
    assert len(check['meshes'][1]['weights'])==2
    # Both directions are centered on the unchanged neutral mesh.
    for i,(x,y,z) in enumerate(body_points):
        up=warp_global(x,y,z,lo,hi,skin[i],1.)
        down=warp_global(x,y,z,lo,hi,skin[i],-1.)
        for a,b,neutral in zip(up,down,(x,y,z)):
            assert math.isfinite(a) and math.isfinite(b)
            assert abs((a+b)/2-neutral)<2e-6
        assert abs(up[0]-x)<.10 and abs(up[2]-z)<.15
    print('Visual global mass targets OK:',len(binary),'bytes; body 20, face 2, unmodified neutral positions')

if __name__=='__main__':
    assert len(sys.argv)==4
    build(*sys.argv[1:])
