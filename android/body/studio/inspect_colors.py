#!/usr/bin/env python3
"""Print CC0 body GLB primitive material metadata to diagnose skin color mismatch."""
import json,struct,urllib.request
url="https://raw.githubusercontent.com/kblood/CharacterCreator/852e48f316b90a0937234886630e4fb4cdfd1f78/output/base_body_anim.glb"
raw=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"MonEvolutionMaterialAudit"}),timeout=60).read()
assert raw[:4]==b'glTF'
size,kind=struct.unpack_from("<II",raw,12)
data=json.loads(raw[20:20+size])
print("BODY_MATERIAL_COUNT",len(data.get("materials",[])),flush=True)
for i,material in enumerate(data.get("materials",[])):
 pbr=material.get("pbrMetallicRoughness",{})
 print("BODY_MATERIAL",i,repr(material.get("name")),"baseColor",pbr.get("baseColorFactor"),"texture",pbr.get("baseColorTexture"),"alpha",material.get("alphaMode"),flush=True)
for i,mesh in enumerate(data.get("meshes",[])):
 print("BODY_MESH",i,repr(mesh.get("name")),flush=True)
 for j,prim in enumerate(mesh.get("primitives",[])):
  attrib=prim.get("attributes",{})
  mat=prim.get("material",-1)
  ref=data["materials"][mat].get("name","(unnamed)") if mat>=0 else "(default)"
  pos=data["accessors"][attrib["POSITION"]]
  print("BODY_PRIM",i,j,"mat",mat,repr(ref),"count",pos["count"],"attrs",sorted(attrib.keys()),"bbox",pos.get("min"),pos.get("max"),flush=True)
