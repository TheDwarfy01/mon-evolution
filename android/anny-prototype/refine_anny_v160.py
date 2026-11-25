"""Upgrade native Anny baked GLBs: coherent material regions, native weight
extrapolation, fitted garment surfaces, scalp cap, iris geometry. Experimental.
One continuous surface, no coincident duplicate garment triangles.
"""
import json,struct,sys
from pathlib import Path
import numpy as np
from collections import defaultdict
from garment_surface import fabric_solver,male_pec_finish

def read(path):
    raw=path.read_bytes()
    n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),raw[28+n:]
def load(d,b,i):
    a=d['accessors'][i]; v=d['bufferViews'][a['bufferView']]
    k=3 if a['type']=='VEC3' else 1
    return np.frombuffer(b,dtype={5126:'<f4',5123:'<u2'}[a['componentType']],count=a['count']*k,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy().reshape(-1,k) if k==3 else np.frombuffer(b,dtype='<u2',count=a['count'],offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
def normals(v,f):
    n=np.zeros_like(v)
    cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    for j in range(3):np.add.at(n,f[:,j],cross)
    return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
def smooth(a):
    a=np.clip(a,0,1);return a*a*(3-2*a)
def build(src,dest,style,female):
    old,raw=read(src);ps=old['meshes'][0]['primitives'];p=ps[0]
    v=load(old,raw,p['attributes']['POSITION'])
    f=np.concatenate([load(old,raw,q['indices']).reshape(-1,3) for q in ps]).astype(np.int64)
    delta=np.array([load(old,raw,q['POSITION']) for q in p['targets']])
    assert len(delta)==20 and len(v)==13718
    # Endpoint amplitude is prepared from native Anny weight directions in bake_anny.
    # Find the four anatomical connected components, rather than treating the eyes as skin.
    parent=np.arange(len(v))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]];a=parent[a]
        return a
    for a,b,c in f:
        aa,bb,cc=find(a),find(b),find(c)
        parent[bb]=aa;parent[cc]=aa
    lab=np.array([find(i) for i in range(len(v))])
    ids,counts=np.unique(lab,return_counts=True)
    main=ids[np.argmax(counts)]
    eyes=[i for i,c in zip(ids,counts) if 50<=c<=110]
    assert len(eyes)==2,counts
    cf=v[f].mean(axis=1); t=(v[:,1]-v[:,1].min())/np.ptp(v[:,1])
    h=float(np.ptp(v[:,1]));ft=t[f].mean(axis=1);x=np.abs(cf[:,0])/h
    body=lab[f[:,0]]==main
    # Rounded neckline and shoulder coverage based on a continuous profile.
    u=np.clip((x-.035)/.055,0,1)
    collar=.815+.043*u*u*(3-2*u)
    sleeve=(ft>.57)&(ft<collar)&(x<(.335 if style=='long' else .22))
    shirt=body&(((ft>.50)&(ft<collar)&(x<.18))|sleeve)
    pants=body&(ft<=.515)&(ft>(.047 if style=='long' else .31))&(~shirt)
    group=np.zeros(len(f),dtype=np.int32)
    group[shirt]=1;group[pants]=2
    # Scalp cap: high forehead, lower at back, no material over the eyes.
    head=body&(ft>.88)
    hz=(cf[:,2]-v[:,2].min())/h
    # Face points toward +Z; keep front hairline above brow.
    head &= (ft>(.93+.035*smooth((hz-.045)/.08)))
    group[head]=3
    for eye in eyes:
        q=v[lab==eye];mask=lab[f[:,0]]==eye
        center=(q.max(axis=0)+q.min(axis=0))/2
        radius=(q[:,2].max()-q[:,2].min())/2
        front=(cf[:,2]-center[2])/max(radius,1e-6)
        group[mask]=4
        group[mask&(front>.57)]=5
        group[mask&(front>.91)]=6
    group[(~body)&(~np.isin(lab[f[:,0]],eyes))]=7
    assert all(np.any(group==i) for i in range(8)),np.bincount(group)
    # Displace only vertices completely inside garment/scalp regions. The boundary
    # shares exactly the same position with skin, preventing gaps and z-fighting.
    incident=np.zeros((len(v),8),dtype=np.int32)
    for k in range(3):np.add.at(incident,(f[:,k],group),1)
    totals=incident.sum(1)
    inset=np.zeros(len(v),dtype=np.float32)
    for g,amount in [(1,.010),(2,.009),(3,.009 if not female else .014)]:
        inside=(incident[:,g]==totals)&(totals>0)
        inset[inside]=amount
    # Smooth the fitted shell relief over its interior, preserving the shared edges.
    edge=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    a=np.concatenate([edge[:,0],edge[:,1]]);b=np.concatenate([edge[:,1],edge[:,0]])
    degree=np.bincount(a,minlength=len(v))
    for _ in range(2):
        s=np.bincount(a,weights=inset[b],minlength=len(v))/np.maximum(degree,1)
        inset=np.where(inset>0,.55*inset+.45*s,0).astype(np.float32)
    # Recompute relief at every morph endpoint so garment and hair follow body.
    solve,cloth_inside,seams=fabric_solver(f,group,len(v),h)
    assert np.any(cloth_inside) and np.any(seams)
    shirt_inside=(incident[:,1]==totals)&(totals>0)&(~seams)
    pec_finish=(lambda q:q) if female else male_pec_finish(v,shirt_inside,f,h)
    offsets=np.load(src.with_suffix('.pose.npy'))
    assert offsets.shape==(21,len(v),3) and np.isfinite(offsets).all()
    def surface(q):
        # Only a bounded surface finish for clothing, no custom anatomical patch.
        fabric=solve(q)
        displacement=fabric-q
        length=np.linalg.norm(displacement,axis=1,keepdims=True)
        fabric=q+displacement*np.minimum(1.,(.006*h)/np.maximum(length,1e-9))
        dressed=fabric+normals(fabric,f)*inset[:,None]
        assert np.max(np.linalg.norm(fabric-q,axis=1))<=.00601*h
        assert np.array_equal(fabric[(~cloth_inside)&(~seams)],q[(~cloth_inside)&(~seams)])
        finished=pec_finish(dressed)
        assert np.array_equal(finished[:,:2],dressed[:,:2])
        assert np.array_equal(finished[~shirt_inside],dressed[~shirt_inside])
        assert np.max(np.abs(finished[:,2]-dressed[:,2]))<=.00301*h
        return finished
    base=surface(v)+offsets[0]
    variants=[surface(v+d)+offsets[i+1] for i,d in enumerate(delta)]
    # Arm motion is conservative on the native heavy endpoint.
    assert np.ptp(base[:,0])<np.ptp(v[:,0]),'Posed arms did not narrow the base'
    print('Posed base width',float(np.ptp(base[:,0])),'heavy width',float(np.ptp(variants[18][:,0])))
    # Validate numerical integrity and deformation amplitude, not clinical accuracy.
    assert all(np.isfinite(q).all() for q in [base]+variants)
    assert np.abs(delta[18]).max()>.001
    assert np.abs(delta[18]).max()<.45
    # Test the extreme combined shape as well as each isolated morph.
    combined=base+(variants[18]-base)+.2925*(variants[10]-base)+.65*(variants[12]-base)+.65*(variants[14]-base)
    half=base+.5*(variants[18]-base)
    assert np.isfinite(half).all()
    assert np.isfinite(combined).all()
    for q in [base]+variants+[half,combined]:
        lengths=np.linalg.norm(q[edge[:,0]]-q[edge[:,1]],axis=1)
        assert np.isfinite(lengths).all() and lengths.max()<h*.25
    # Normals updated for all morph targets. Shared vertex arrays and indices.
    buf=bytearray()
    doc={'asset':{'version':'2.0','generator':'IMC Anny v171 extended native weight and local male fabric finish'},
         'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[],'materials':[],
         'meshes':[],'nodes':[{'name':'Anny','mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
    def acc(arr,typ,ctype,target=None,bounds=False):
        arr=np.ascontiguousarray(arr)
        while len(buf)%4:buf.append(0)
        view={'buffer':0,'byteOffset':len(buf),'byteLength':arr.nbytes}
        if target:view['target']=target
        doc['bufferViews'].append(view);buf.extend(arr.tobytes())
        info={'bufferView':len(doc['bufferViews'])-1,'componentType':ctype,'count':len(arr),'type':typ}
        if bounds:info.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
        doc['accessors'].append(info);return len(doc['accessors'])-1
    n=normals(base,f)
    pos=acc(base.astype('<f4'),'VEC3',5126,34962,True)
    nor=acc(n.astype('<f4'),'VEC3',5126,34962)
    targets=[{'POSITION':acc((q-base).astype('<f4'),'VEC3',5126,None,True),
              'NORMAL':acc((normals(q,f)-n).astype('<f4'),'VEC3',5126)} for q in variants]
    mats=[('Skin',[.62,.39,.27,1]),('Shirt',[.20,.39,.58,1]),('Pants',[.10,.16,.25,1]),('Hair',[.12,.07,.035,1]),('Sclera',[.85,.85,.82,1]),('Iris',[.18,.30,.20,1]),('Pupil',[.012,.012,.012,1]),('Mouth',[.34,.16,.13,1])]
    prims=[]
    for i,(name,color) in enumerate(mats):
        doc['materials'].append({'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color,'roughnessFactor':.9,'metallicFactor':0}})
        ix=f[group==i].reshape(-1).astype('<u2')
        prims.append({'attributes':{'POSITION':pos,'NORMAL':nor},'indices':acc(ix,'SCALAR',5123,34963),'material':i,'targets':targets})
    doc['meshes']=[{'name':'Anny','primitives':prims,'weights':[0.]*20,'extras':old['meshes'][0]['extras']}]
    while len(buf)%4:buf.append(0)
    doc['buffers'][0]['byteLength']=len(buf)
    j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*(-len(j)%4)
    data=struct.pack('<III',0x46546c67,2,28+len(j)+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf
    dest.write_bytes(data)
    assert len(data)<14_000_000
    print(dest, len(data), 'material faces',np.bincount(group).tolist(),'max heavy excursion',float(np.abs(delta[18]).max()))
if __name__=='__main__':
    assets=Path(sys.argv[1])
    for sex in ['male','female']:
        for style in ['long','sport']:
            build(assets/f'anny-{sex}-morph.glb',assets/f'anny-{sex}-{style}-morph.glb',style,sex=='female')
