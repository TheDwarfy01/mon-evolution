#!/usr/bin/env python3
"""Build compact unskinned GLBs from original MakeHuman meshes for Filament testing."""
from pathlib import Path
import json, struct, sys, math
FMT={'POSITION':(5126,'VEC3',12),'TEXCOORD_0':(5126,'VEC2',8)}
COLORS=[(.93,.70,.57,1),(.18,.11,.07,1),(.1,.07,.05,1),(.95,.95,.92,1),(.35,.17,.12,1),(1,1,1,.10),(.97,.95,.92,1),(.77,.36,.39,1)]

def glb_read(raw):
    assert len(raw)>300 and raw[:4]==b'glTF'
    version,size=struct.unpack_from('<II',raw,4)
    assert version==2 and size==len(raw)
    json_len,json_type=struct.unpack_from('<II',raw,12)
    assert json_type==0x4e4f534a
    gltf=json.loads(raw[20:20+json_len]); off=20+json_len
    bin_len,bin_type=struct.unpack_from('<II',raw,off)
    assert bin_type==0x004e4942
    return gltf,raw[off+8:off+8+bin_len]

def create(doc,binary,textured):
    out=bytearray();views=[];accessors=[];primitives=[];materials=[];imgs=[];tex=[]
    def append(raw,target=None):
        while len(out)%4:out.append(0)
        index=len(views)
        v={'buffer':0,'byteOffset':len(out),'byteLength':len(raw)}
        if target is not None:v['target']=target
        views.append(v);out.extend(raw)
        return index
    def copy_acc(old_index,kind):
        acc=doc['accessors'][old_index]
        view=doc['bufferViews'][acc['bufferView']]
        dtype,dims,item_bytes=FMT[kind] if kind in FMT else (5123,'SCALAR',2)
        assert acc['componentType']==dtype and acc['type']==dims
        assert not view.get('byteStride'),(kind,view.get('byteStride'))
        start=view.get('byteOffset',0)+acc.get('byteOffset',0)
        raw=binary[start:start+acc['count']*item_bytes]
        assert len(raw)==acc['count']*item_bytes
        v=append(raw,34963 if kind=='indices' else 34962)
        new={'bufferView':v,'componentType':dtype,'count':acc['count'],'type':dims}
        if kind=='POSITION':
            pos=list(struct.iter_unpack('<fff',raw))
            assert len(pos)==acc['count'] and all(math.isfinite(k) for xyz in pos for k in xyz)
            new['min']=[min(p[i] for p in pos) for i in range(3)]
            new['max']=[max(p[i] for p in pos) for i in range(3)]
        accessors.append(new)
        return len(accessors)-1
    material_ix=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            mat=doc['materials'][primitive['material']]
            position=copy_acc(primitive['attributes']['POSITION'],'POSITION')
            attrs={'POSITION':position}
            if textured:attrs['TEXCOORD_0']=copy_acc(primitive['attributes']['TEXCOORD_0'],'TEXCOORD_0')
            index=copy_acc(primitive['indices'],'indices')
            primitives.append({'attributes':attrs,'indices':index,'material':material_ix,'mode':4})
            m={'name':mat['name'],'doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'pbrMetallicRoughness':{'metallicFactor':0,'roughnessFactor':1}}
            m['pbrMetallicRoughness']['baseColorFactor']=(list(COLORS[material_ix]) if not textured else [1,1,1,1])
            if textured:
                pbr=mat.get('pbrMetallicRoughness',{})
                tx=pbr.get('baseColorTexture')
                if tx:
                    original_tx=doc['textures'][tx['index']]
                    im=doc['images'][original_tx['source']]
                    view=doc['bufferViews'][im['bufferView']]
                    raw=binary[view['byteOffset']:view['byteOffset']+view['byteLength']]
                    assert raw and len(raw)>=1000
                    images_ix=len(imgs)
                    imgs.append({'bufferView':append(raw),'mimeType':im['mimeType']})
                    tex.append({'source':images_ix})
                    m['pbrMetallicRoughness']['baseColorTexture']={'index':len(tex)-1}
                if mat.get('alphaMode')=='MASK':m.update(alphaMode='MASK',alphaCutoff=mat.get('alphaCutoff',.5))
                if mat.get('alphaMode')=='BLEND':
                    m['alphaMode']='BLEND'
                    m['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,.08]
            materials.append(m)
            material_ix+=1
    assert len(primitives)==8
    d={'asset':{'version':'2.0','generator':'IMC compact mesh converter'},'buffers':[{'byteLength':len(out)}],
       'bufferViews':views,'accessors':accessors,'materials':materials,
       'meshes':[{'name':'Corps MakeHuman sans skin ni morph','primitives':primitives}],
       'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0,'extensionsUsed':['KHR_materials_unlit']}
    if textured:d.update(images=imgs,textures=tex)
    body=json.dumps(d,separators=(',',':')).encode('utf-8')
    while len(body)%4:body+=b' '
    while len(out)%4:out.append(0)
    result=struct.pack('<III',0x46546c67,2,12+8+len(body)+8+len(out))
    result+=struct.pack('<II',len(body),0x4e4f534a)+body
    result+=struct.pack('<II',len(out),0x004e4942)+bytes(out)
    return result

def main(source,out):
    doc,binary=glb_read(Path(source).read_bytes());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for label,textured in [('filament-detail-colors.glb',False),('filament-detail-textures.glb',True)]:
        result=create(doc,binary,textured);path=out/label;path.write_bytes(result)
        d,_=glb_read(result)
        assert len(d['meshes'][0]['primitives'])==8
        assert 'skins' not in d and 'animations' not in d
        assert all(len(p['attributes']) in (1,2) and not p.get('targets') for p in d['meshes'][0]['primitives'])
        assert d['buffers'][0]['byteLength']>100_000
        print(label,path.stat().st_size,'bytes, views',len(d['bufferViews']),'accessors',len(d['accessors']))

if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
