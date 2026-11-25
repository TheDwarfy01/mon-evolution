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
    assert len(orig_pos)==len(positions),'Body vertex count mismatch'
    if orig_pos!=positions:
        base=list(struct.iter_unpack('<fff',orig_pos))
        baked=list(struct.iter_unpack('<fff',positions))
        shifts=[max(abs(a-b) for a,b in zip(p,q)) for p,q in zip(base,baked)]
        assert max(shifts)<.12 and sum(shifts)/len(shifts)<.078,(
            'Unexpected gender-male base or vertex order',max(shifts))
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

def warp_global(x,y,z,lo,hi,w,change,male=False):
    h=hi-lo;t=(y-lo)/h
    torso=w.get('torso',0);clav=w.get('clavicle',0)
    # Broad, low-curvature torso transition. The original narrow Gaussian
    # hips (.525/.075) caused two isolated lateral bulges ("love handles")
    # when global fullness and local belly fullness were combined.
    # Broad curves keep the pelvis and upper thigh continuous.
    waist=gaussian(t,.61,.19)
    belly=gaussian(t,.600,.145)
    # Wide, softly-tapered posterior contour: avoid a pointed glute peak.
    # Glute/pelvis fullness extends down into the upper thighs, unlike the
    # isolated spherical rear lobe seen in previous test screenshots.
    glutes=gaussian(t,.475,.198)
    front=smooth((z-.008)/.18)
    back=1-smooth((z+.07)/.18)
    # At full positive setting the torso broadens more gently sideways than
    # it projects forward. Keep thighs/shoulders/arms proportionate.
    if male:
        # Calibrated against user-supplied frontal/side reference proportions:
        # heavy male shoulder girdle, broad rib cage, thick upper arms,
        # pronounced upper thighs and posterior gluteal volume. Avoid
        # isolated round projections on the flanks and a spherical belly.
        # Male frontal silhouette: broad shoulder girdle and trunk. Rear
        # silhouette reference: hips blend into powerful upper thighs instead
        # of two pinched lateral lobes.
        torso_x=.36+.06*waist+.075*glutes
        # Belly remains volumetric, not an isolated protruding sphere.
        torso_z=.345+.022*belly*front+.12*glutes*back
        shoulder=.41
        upperarm=.55
        forearm=.43
        thigh=.89
        calf=.45
        head_x=.21
        head_z=.20
    else:
        torso_x=.295+.105*waist
        torso_z=.365+.28*belly*front+.20*glutes*back
        shoulder=.29
        upperarm=.38
        forearm=.33
        thigh=.43
        calf=.31
        head_x=.20
        head_z=.19
    x_gain=(torso*torso_x+clav*shoulder+w.get('neck',0)*.25+
            w.get('upperarm',0)*upperarm+w.get('lowerarm',0)*forearm+
            w.get('hand',0)*.095+w.get('thigh',0)*thigh+
            w.get('calf',0)*calf+w.get('foot',0)*.055+
            w.get('head',0)*head_x)
    z_gain=(torso*torso_z+clav*shoulder+w.get('neck',0)*.25+
            w.get('upperarm',0)*upperarm+w.get('lowerarm',0)*forearm+
            w.get('hand',0)*.095+w.get('thigh',0)*thigh+
            w.get('calf',0)*calf+w.get('foot',0)*.055+
            w.get('head',0)*head_z)
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
    head=smooth((y-(hi-(.34 if not male else .279)))/.060)
    x_gain=(1-head)*x_gain+head*(.21 if male else .20)
    z_gain=(1-head)*z_gain+head*(.20 if male else .19)
    axis=(1-head)*axis
    zcenter=(1-head)*zcenter+head*.055
    # Thinning remains conservative (no collapsed limbs), but positive
    # fullness can extend to a much larger silhouette at slider maximum.
    strength=change if change>=0 else change*.55
    # Add dedicated forward abdominal projection, not a side bump.
    # The front surface alone moves in +Z; its upper/lower edges taper
    # continuously through the broad belly Gaussian.
    front_belly=torso*belly*front*(1-head)
    forward= max(0.,strength)*front_belly*(.014 if male else .084)*h
    # Backward volume at the glutes follows the pelvis / upper-thigh weights.
    butt_weight=torso+.45*w.get('thigh',0)
    # The earlier .13*h male posterior translation created a sharp protrusion.
    # Replace it with a small displacement spread over a much wider band.
    posterior= -max(0.,strength)*butt_weight*glutes*back*(.024 if male else .050)*h
    return (axis+(x-axis)*(1+strength*x_gain),y,
            zcenter+(z-zcenter)*(1+strength*z_gain)+forward+posterior)

def append_target(doc,buf,positions,lo,hi,skin,sign,male=False):
    block=bytearray()
    for i,(x,y,z) in enumerate(positions):
        nx,ny,nz=warp_global(x,y,z,lo,hi,skin[i],sign,male)
        block.extend(struct.pack('<fff',nx-x,ny-y,nz-z))
    while len(buf)%4:buf.append(0)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(block)})
    buf.extend(block)
    doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,
          'componentType':5126,'count':len(positions),'type':'VEC3'})
    return len(doc['accessors'])-1

def build(morph,original,destination,male=False):
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
        body['targets'].append({'POSITION':append_target(doc,buf,body_points,lo,hi,skin,sign,male)})
        doc['meshes'][0]['extras']['targetNames'].append(name)
        doc['meshes'][0]['weights'].append(0.)
        for prim in doc['meshes'][1]['primitives']:
            data,ac=access(doc,buf,prim['attributes']['POSITION'])
            assert ac['componentType']==5126
            points=list(struct.iter_unpack('<fff',data))
            assert points and min(p[1] for p in points)>1.30
            neutral=[{'head':1.} for _ in points]
            prim.setdefault('targets',[]).append(
                {'POSITION':append_target(doc,buf,points,lo,hi,neutral,sign,male)})
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
    # Bounds/continuity checks: a much larger abdomen, smooth flanks,
    # proportional arms, shoulders, head, glutes and legs at maximum.
    # Unlike the old mirror targets, slimming is deliberately less aggressive.
    changed_axes={'head':0,'torso':0,'upperarm':0,'thigh':0,'calf':0}
    max_dx=max_dz=0.
    for i,(x,y,z) in enumerate(body_points):
        up=warp_global(x,y,z,lo,hi,skin[i],1.,male)
        down=warp_global(x,y,z,lo,hi,skin[i],-1.,male)
        assert up[1]==y and down[1]==y
        assert all(math.isfinite(v) for v in up+down)
        max_dx=max(max_dx,abs(up[0]-x))
        max_dz=max(max_dz,abs(up[2]-z))
        assert abs(up[0]-x)<.26 and abs(up[2]-z)<.45
        assert abs(down[0]-x)<.15 and abs(down[2]-z)<.18
        for region in changed_axes:
            if skin[i].get(region,0)>.75 and abs(up[0]-x)+abs(up[2]-z)>.00025:
                changed_axes[region]+=1
    assert all(v>30 for v in changed_axes.values()),changed_axes
    # Visage and eyes use identical transform function at all extreme settings.
    for primitive in check['meshes'][1]['primitives']:
        assert len(primitive['targets'])==2
    if male:
        # Upper buttock and upper thigh must blend smoothly, rather than
        # creating the triangular projection visible in the screenshot.
        upper=[(p,skin[i]) for i,p in enumerate(body_points)
               if .46<(p[1]-lo)/(hi-lo)<.59 and p[2]<.11]
        assert len(upper)>25
        extremes=[abs(warp_global(*p,lo,hi,s,1.,True)[2]-p[2]) for p,s in upper]
        assert max(extremes)<.29,('posterior peak too large',max(extremes))
        # In obese male morphology a sizeable share of the change is carried
        # by the upper thighs, not just the front abdominal profile.
        thigh_vertices=[i for i,s in enumerate(skin) if s.get('thigh',0)>.75]
        assert len(thigh_vertices)>60
        nonzero=sum(abs(warp_global(*body_points[i],lo,hi,skin[i],1.,True)[0]-
                        body_points[i][0])>.012 for i in thigh_vertices)
        assert nonzero>100,('insufficient upper-thigh volume',nonzero)
    print('Visual global mass targets OK:',len(binary),'bytes; body 20, face 2, max deviation',max_dx,max_dz,'regions',changed_axes)

if __name__=='__main__':
    assert len(sys.argv) in (4,5)
    build(*sys.argv[1:4],male=(len(sys.argv)==5 and sys.argv[4]=='--male'))
