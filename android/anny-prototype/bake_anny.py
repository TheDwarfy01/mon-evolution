"""Bake official Anny phenotype samples into local Filament GLB morphs.
First diagnostic: material regions on one continuous surface, not actual garments.
No network access or optional SMPL assets permitted during generation.
"""
import sys, json, struct
from pathlib import Path
import numpy as np
import torch
import anny
import socket

# Fail rather than silently fetching external body assets.
def no_network(*a, **kw):
    raise RuntimeError("Anny asset generation must be offline")
socket.create_connection = no_network
socket.socket.connect = no_network
torch.set_num_threads(2)
model = anny.Anny(rig="anny", topology="anny", local_changes="default").to(dtype=torch.float32).eval()
faces = model.faces.detach().cpu().numpy().astype(np.int64)
assert faces.ndim == 2 and faces.shape[1] == 3
regions = [
    ["measure-neck-circ-incr"],
    ["measure-bust-circ-incr"],
    ["l-upperarm-fat-incr", "r-upperarm-fat-incr"],
    ["l-lowerarm-fat-incr", "r-lowerarm-fat-incr"],
    ["measure-waist-circ-incr"],
    ["torso-scale-depth-incr", "stomach-tone-incr"],
    ["measure-hips-circ-incr", "buttocks-volume-incr"],
    ["measure-thigh-circ-incr"],
    ["measure-calf-circ-incr"],
]
assert all(k in model.local_change_labels for region in regions for k in region)
names = [f"region_{i}_{sign}" for i in range(9) for sign in ("plus","minus")] + ["weight_plus","weight_minus"]
def sample(gender,weight=.5,changes=None):
    ph = {k:torch.tensor([.5]) for k in model.phenotype_labels}
    ph.update(gender=torch.tensor([gender]),age=torch.tensor([.67]),weight=torch.tensor([weight]),muscle=torch.tensor([.35]))
    kw = {k:torch.tensor([v]) for k,v in (changes or {}).items()}
    with torch.no_grad():
        out=model(phenotype_kwargs=ph,local_changes_kwargs=kw)
    v=out["vertices"][0].detach().cpu().numpy().astype(np.float32)
    # Anny Z-up to glTF Y-up, proper rotation.
    v=v[:,[0,2,1]].copy()
    v[:,2]*=-1
    assert np.isfinite(v).all()
    return v
def normals(v):
    n=np.zeros_like(v)
    f=np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]])
    for j in range(3): np.add.at(n,faces[:,j],f)
    n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
    return n
def export(gender,path):
    base=sample(gender)
    assert base.shape[0]>10000 and faces.max()<len(base)
    variants=[sample(gender,changes={k:sign*.65 for k in region}) for region in regions for sign in (1,-1)]
    variants += [sample(gender,1.),sample(gender,0.)]
    assert all(v.shape==base.shape for v in variants)
    assert all(np.max(np.abs(v-base))>1e-5 for v in variants)
    # One topologically continuous body; colour only, no duplicate cloth shells.
    # This lets us evaluate the shape without the prior clothing intersections.
    lo,hi=base[:,1].min(),base[:,1].max()
    h=hi-lo
    center=base[faces].mean(axis=1)
    t=(center[:,1]-lo)/h
    x=np.abs(center[:,0]-np.median(base[:,0]))/h
    shirt=(t>.50)&(t<.79)&(x<.21)
    pants=(t>.12)&(t<=.50)&(x<.25)
    # Ensure covered pelvis and torso, avoiding gaps between color regions.
    shirt |= (t>.50)&(t<.76)&(x<.27)
    group=np.where(shirt,1,np.where(pants,2,0))
    b=bytearray()
    d={"asset":{"version":"2.0","generator":"IMC Anny 0.6.2 local morph diagnostic"},
       "buffers":[{"byteLength":0}],"bufferViews":[],"accessors":[],
       "materials":[],"meshes":[],"nodes":[],"scenes":[{"nodes":[0]}],"scene":0}
    def acc(a,typ,component,target=None,bounds=False):
        a=np.ascontiguousarray(a)
        while len(b)%4:b.append(0)
        view={"buffer":0,"byteOffset":len(b),"byteLength":a.nbytes}
        if target:view["target"]=target
        d["bufferViews"].append(view); b.extend(a.tobytes())
        info={"bufferView":len(d["bufferViews"])-1,"componentType":component,"count":len(a),"type":typ}
        if bounds:info.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        d["accessors"].append(info)
        return len(d["accessors"])-1
    bn=normals(base)
    pos=acc(base.astype("<f4"),"VEC3",5126,34962,True)
    nor=acc(bn.astype("<f4"),"VEC3",5126,34962)
    targets=[]
    for v in variants:
        targets.append({"POSITION":acc((v-base).astype("<f4"),"VEC3",5126,None,True),
                        "NORMAL":acc((normals(v)-bn).astype("<f4"),"VEC3",5126)})
    primitives=[]
    for i,(name,color) in enumerate([("Skin",[.68,.46,.34,1]),("ShirtProxy",[.26,.45,.56,1]),("PantsProxy",[.15,.19,.23,1])]):
        ix=faces[group==i].reshape(-1).astype("<u2")
        assert len(ix)>0 and faces.max()<65536
        d["materials"].append({"name":name,"doubleSided":True,"pbrMetallicRoughness":{"baseColorFactor":color,"roughnessFactor":.9,"metallicFactor":0}})
        primitives.append({"attributes":{"POSITION":pos,"NORMAL":nor},"indices":acc(ix,"SCALAR",5123,34963),"material":i,"targets":targets})
    d["meshes"]=[{"name":"Anny","primitives":primitives,"weights":[0.]*20,"extras":{"targetNames":names}}]
    d["nodes"]=[{"name":"Anny","mesh":0}]
    while len(b)%4:b.append(0)
    d["buffers"][0]["byteLength"]=len(b)
    j=json.dumps(d,separators=(",",":")).encode();j+=b" "*(-len(j)%4)
    raw=struct.pack("<III",0x46546c67,2,28+len(j)+len(b))+struct.pack("<II",len(j),0x4e4f534a)+j+struct.pack("<II",len(b),0x004e4942)+b
    path.write_bytes(raw)
    print(path,len(raw),"bytes",len(base),"vertices",len(faces),"faces", "weight excursion",float(np.max(np.abs(variants[-2]-base))))
    assert len(raw)<14_000_000
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
export(0.,out/"anny-male-morph.glb")
export(1.,out/"anny-female-morph.glb")
