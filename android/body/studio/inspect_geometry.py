#!/usr/bin/env python3
"""Read only the public CC0 3D model; diagnostic text, no binary committed."""
import json,struct,urllib.request
url="https://raw.githubusercontent.com/kblood/CharacterCreator/852e48f316b90a0937234886630e4fb4cdfd1f78/output/base_body_anim.glb"
raw=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"IMC-geometry-inspection"}),timeout=60).read()
assert raw[:4]==b'glTF'
size,kind=struct.unpack_from("<II",raw,12)
data=json.loads(raw[20:20+size])
print("SIZE",len(raw),"NODES",len(data.get("nodes",[])),"MESHES",len(data.get("meshes",[])),"SKINS",len(data.get("skins",[])))
for i,skin in enumerate(data.get("skins",[])):
 print("SKIN",i,"joints",len(skin.get("joints",[])),"names")
 for joint in skin.get("joints",[]):
  n=data["nodes"][joint];print(" J",joint,repr(n.get("name")),"t",n.get("translation"),"r",n.get("rotation"))
for i,n in enumerate(data.get("nodes",[])):
 if n.get("mesh") is not None: print("MESH_NODE",i,"name",n.get("name"),"mesh",n["mesh"],"skin",n.get("skin"),"translation",n.get("translation"),"scale",n.get("scale"))
for i,mesh in enumerate(data.get("meshes",[])):
 for j,prim in enumerate(mesh.get("primitives",[])):
  pos=data["accessors"][prim["attributes"]["POSITION"]]
  print("MESH_BOUNDS",i,j,"name",mesh.get("name"),"count",pos.get("count"),"min",pos.get("min"),"max",pos.get("max"))

# Facial options must be verified against actual exported GLB targets; never invent one.
for i,mesh in enumerate(data.get("meshes",[])):
 target_names=mesh.get("extras",{}).get("targetNames",[])
 print("MESH_MORPH_NAMES",i,repr(mesh.get("name")),len(target_names),repr(target_names[:120]))
for i,clip in enumerate(data.get("animations",[])):
 print("ANIM_NAME",i,repr(clip.get("name")))
