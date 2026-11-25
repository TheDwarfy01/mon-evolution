#!/usr/bin/env python3
"""Bake native MakeHuman gender_male morph into the compact CC0 Filament body.
Keeps all eight textured primitives, removes the source rig and other morphs.
This creates a genuinely male base before local/global fullness is applied.
"""
import json,struct,sys
from pathlib import Path

def unpack(path):
    blob=Path(path).read_bytes()
    assert blob[:4]==b'glTF' and struct.unpack_from('<II',blob,4)==(2,len(blob))
    n,tag=struct.unpack_from('<II',blob,12);assert tag==0x4e4f534a
    gltf=json.loads(blob[20:20+n]);offset=20+n
    count,typ=struct.unpack_from('<II',blob,offset)
    assert typ==0x004e4942
    return gltf,bytearray(blob[offset+8:offset+8+count])

def read_morph(doc,binary,accessor_index):
    a=doc['accessors'][accessor_index]
    v=doc['bufferViews'][a['bufferView']]
    assert a['type']=='VEC3' and a['componentType']==5122 and a.get('normalized')
    stride=v.get('byteStride',6)
    assert stride in (6,8)
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [tuple(max(-1.,k/32767.) for k in struct.unpack_from('<hhh',binary,start+i*stride))
            for i in range(a['count'])]

def bake(original,compact,out):
    source,raw=unpack(original);doc,buf=unpack(compact)
    assert len(source['meshes'])==6
    assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==8
    source_prims=[(m,p) for m in source['meshes'] for p in m['primitives']]
    target_prims=doc['meshes'][0]['primitives']
    assert len(source_prims)==len(target_prims)
    body_shift=0
    face_shift=0
    for i,((mesh,source_prim),dest_prim) in enumerate(zip(source_prims,target_prims)):
        assert 'gender_male' in mesh['extras']['targetNames']
        gender=mesh['extras']['targetNames'].index('gender_male')
        target=source_prim['targets'][gender]
        displacement=read_morph(source,raw,target['POSITION'])
        a=doc['accessors'][dest_prim['attributes']['POSITION']]
        original_a=source['accessors'][source_prim['attributes']['POSITION']]
        assert a['count']==original_a['count']==len(displacement)
        assert a['componentType']==5126 and a['type']=='VEC3'
        v=doc['bufferViews'][a['bufferView']]
        assert v.get('byteStride') in (None,12)
        at=v.get('byteOffset',0)+a.get('byteOffset',0)
        coords=[]
        for j,(dx,dy,dz) in enumerate(displacement):
            x,y,z=struct.unpack_from('<fff',buf,at+j*12)
            xyz=(x+dx,y+dy,z+dz)
            assert all(-2.<u<3. for u in xyz) and max(abs(dx),abs(dy),abs(dz))<.12
            struct.pack_into('<fff',buf,at+j*12,*xyz)
            coords.append(xyz)
        a['min']=[min(pt[k] for pt in coords) for k in range(3)]
        a['max']=[max(pt[k] for pt in coords) for k in range(3)]
        if i==0:body_shift=sum(abs(t[0])+abs(t[1])+abs(t[2]) for t in displacement)
        else:face_shift+=sum(abs(t[0])+abs(t[1])+abs(t[2]) for t in displacement)
    assert body_shift>30 and face_shift>.5,(body_shift,face_shift)
    doc['asset']['generator']='Mon Evolution IMC CC0 male morph baked from MakeHuman'
    js=json.dumps(doc,separators=(',',':')).encode('utf8');js+=b' '*(-len(js)%4)
    buf+=b'\0'*(-len(buf)%4)
    blob=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(buf))
    blob+=struct.pack('<II',len(js),0x4e4f534a)+js
    blob+=struct.pack('<II',len(buf),0x004e4942)+bytes(buf)
    Path(out).write_bytes(blob)
    verify,_=unpack(out)
    assert len(verify['meshes'][0]['primitives'])==8
    assert 'skins' not in verify and 'animations' not in verify
    assert len(verify.get('images',[]))>=6
    print('Bake male CC0 OK:',len(blob),'bytes',round(body_shift,2),round(face_shift,2))

if __name__=='__main__':
    assert len(sys.argv)==4
    bake(*sys.argv[1:])
