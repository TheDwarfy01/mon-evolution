#!/usr/bin/env python3
"""Generate a conservative clothed-body Filament test from an already validated
MakeHuman morphology GLB. T-shirt, shorts and short hair are *actual glTF
triangles* attached to the same 20 GPU morph targets as the body. This is an
experimental fitted garment, not a full cloth simulation or realistic hairstyle.
All geometry is derived from original CC0 MakeHuman data; no image-sheet
pixels are embedded as fake 3D.
"""
import json, math, struct, sys
from pathlib import Path

def read(path):
    raw=Path(path).read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
    n,tag=struct.unpack_from('<II',raw,12); assert tag==0x4e4f534a
    doc=json.loads(raw[20:20+n]);off=20+n
    nb,bt=struct.unpack_from('<II',raw,off); assert bt==0x004e4942
    return doc,bytearray(raw[off+8:off+8+nb])

def acc(doc,buf,index):
    a=doc['accessors'][index]
    view=doc['bufferViews'][a['bufferView']]
    unit=12 if a['type']=='VEC3' and a['componentType']==5126 else (
        2 if a['type']=='SCALAR' and a['componentType']==5123 else None)
    assert unit is not None and not view.get('byteStride')
    st=view.get('byteOffset',0)+a.get('byteOffset',0)
    blob=buf[st:st+a['count']*unit]
    return blob,a

def append(doc,buf,data,component,count,typename,target=None):
    while len(buf)%4:buf.append(0)
    view={'buffer':0,'byteOffset':len(buf),'byteLength':len(data)}
    if target:view['target']=target
    doc['bufferViews'].append(view)
    buf.extend(data)
    a={'bufferView':len(doc['bufferViews'])-1,'componentType':component,
       'count':count,'type':typename}
    if typename=='VEC3':
        values=list(struct.iter_unpack('<fff',data))
        a['min']=[min(v[i] for v in values) for i in range(3)]
        a['max']=[max(v[i] for v in values) for i in range(3)]
    doc['accessors'].append(a)
    return len(doc['accessors'])-1

def build(source,out,sex):
    assert sex in ('male','female')
    doc,buf=read(source)
    assert len(doc['meshes'])==2
    body=doc['meshes'][0]['primitives'][0]
    assert len(body['targets'])==20
    p,a=acc(doc,buf,body['attributes']['POSITION'])
    verts=list(struct.iter_unpack('<fff',p))
    ids,ia=acc(doc,buf,body['indices'])
    faces=list(struct.iter_unpack('<HHH',ids))
    assert a['count']>14000 and len(faces)>24000
    ymin=min(v[1] for v in verts);ymax=max(v[1] for v in verts)
    h=ymax-ymin
    # Base is a stable body. Mesh subsets use all three vertices inside the
    # garment region to avoid triangles bridging the underarm or crotch.
    def region(which,x,y,z):
        t=(y-ymin)/h
        ax=abs(x)/h
        if which=='shirt':
            torso=.485<t<.795 and ax<.185
            sleeve=.642<t<.78 and .16<ax<.32
            return torso or sleeve
        if which=='shorts':
            return .33<t<.535 and ax<.195
        if which=='hair':
            return (t>.925 or (t>.866 and z<.055)) and ax<.105
        return False
    palettes={
        'shirt':([.53,.58,.67,1] if sex=='male' else [.78,.39,.57,1]),
        'shorts':[.19,.22,.28,1],
        'hair':[.25,.18,.13,1] if sex=='male' else [.42,.29,.19,1]
    }
    garment_prims=[]
    for kind in ('shirt','shorts','hair'):
        inside=[region(kind,*p) for p in verts]
        selected=[f for f in faces if inside[f[0]] and inside[f[1]] and inside[f[2]]]
        assert len(selected)>30,(kind,len(selected))
        used=set(i for face in selected for i in face)
        # A small radial offset keeps clothing above the body at the neutral
        # size; the *same* morph deltas are applied to the garment during edits.
        epsilon=.008 if kind in ('shirt','shorts') else .010
        points=[]
        for i,(x,y,z) in enumerate(verts):
            if i in used:
                side=1 if x>=0 else -1
                x=x+side*epsilon*.45
                z=z+(epsilon if z>.065 else -epsilon)
            points.append((x,y,z))
        pos=append(doc,buf,b''.join(struct.pack('<fff',*p) for p in points),
                   5126,len(points),'VEC3',34962)
        idx=b''.join(struct.pack('<HHH',*f) for f in selected)
        index=append(doc,buf,idx,5123,len(selected)*3,'SCALAR',34963)
        material=len(doc['materials'])
        doc['materials'].append({
            'name':'IMC_'+kind,'doubleSided':True,
            'extensions':{'KHR_materials_unlit':{}},
            'pbrMetallicRoughness':{'baseColorFactor':palettes[kind],
                                    'metallicFactor':0,'roughnessFactor':1}
        })
        # Copy all original 20 morph POSITION deltas. Clothing and hair thus
        # transform with the body and do not produce rig/armature mismatches.
        garment_prims.append({
            'attributes':{'POSITION':pos},
            'indices':index,'material':material,'mode':4,
            'targets':[{'POSITION':x['POSITION']} for x in body['targets']]
        })
        print(kind,'triangles',len(selected),'materials',material)
    mesh=len(doc['meshes'])
    doc['meshes'].append({'name':'IMC_ClothingAndHair','primitives':garment_prims,
                           'weights':[0.]*20,
                           'extras':{'targetNames':doc['meshes'][0]['extras']['targetNames']}})
    doc['nodes'].append({'name':'IMC_ClothesAndHair','mesh':mesh})
    doc['scenes'][0]['nodes'].append(len(doc['nodes'])-1)
    doc['asset']['generator']='Mon Evolution IMC separate dressed '+sex+' CC0 visual prototype'
    doc['buffers'][0]['byteLength']=len(buf)
    j=json.dumps(doc,separators=(',',':')).encode('utf8');j+=b' '*(-len(j)%4)
    buf+=b'\x00'*(-len(buf)%4)
    data=(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(buf))+
          struct.pack('<II',len(j),0x4e4f534a)+j+
          struct.pack('<II',len(buf),0x004e4942)+bytes(buf))
    Path(out).write_bytes(data)
    check,_=read(out)
    assert len(check['meshes'])==3 and len(check['meshes'][2]['primitives'])==3
    assert all(len(p['targets'])==20 for p in check['meshes'][2]['primitives'])
    assert len(check['materials'])>=11 and 'skins' not in check
    print('Dressed GLB',sex, len(data),'bytes, validated 20 per-garment morph weights')

if __name__=='__main__':
    assert len(sys.argv)==4
    build(*sys.argv[1:])
