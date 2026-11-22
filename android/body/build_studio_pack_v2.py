#!/usr/bin/env python3
"""Create a separate CC0 MakeHuman Studio v2 asset archive for Android.

This packages only *generated CC0 assets* from CharacterCreator, not the
GPL-3.0 application or viewer code. We implement our own Three.js (MIT) viewer.
The source commit is pinned for reproducibility and licence provenance.
"""
from pathlib import Path
from urllib.request import urlopen, Request
import hashlib
import json
import os
import struct
import zipfile

UPSTREAM="852e48f316b90a0937234886630e4fb4cdfd1f78"
ROOT=f"https://raw.githubusercontent.com/kblood/CharacterCreator/{UPSTREAM}/output/"
ASSETS=[
    "base_body_anim.glb",
    "hair_short02.glb",
    "hair_bob02.glb",
    "hair_long01.glb",
    "hair_afro01.glb",
    "hair_ponytail01.glb",
    "hair_braid01.glb",
    "hair_short04.glb",
    "clothing_tshirt.glb",
    "clothing_shirt.glb",
    "clothing_hoodie.glb",
    "clothing_jeans.glb",
    "clothing_shorts.glb",
    "clothing_skirt.glb",
    "clothing_shoes.glb",
]
OUTPUT=Path(os.environ.get("STUDIO_PACK_OUT","android/generated/makehuman-studio-v2.zip"))
def glb_info(blob,name):
    if len(blob)<256 or blob[:4]!=b"glTF":
        raise RuntimeError(f"{name}: invalid glTF/GLB header")
    magic,version,total=struct.unpack_from("<III",blob,0)
    if version!=2 or total!=len(blob):
        raise RuntimeError(f"{name}: invalid GLB length/version")
    offset=12
    n,chunk_type=struct.unpack_from("<II",blob,offset)
    if chunk_type!=0x4e4f534a:
        raise RuntimeError(f"{name}: missing GLB JSON")
    model=json.loads(blob[offset+8:offset+8+n])
    morph_names=set()
    for mesh in model.get("meshes",[]):
        for name in mesh.get("extras",{}).get("targetNames",[]):
            morph_names.add(name)
    return dict(meshes=len(model.get("meshes",[])),
        skins=len(model.get("skins",[])),
        clips=len(model.get("animations",[])),
        morphs=len(morph_names),
        materialCount=len(model.get("materials",[])),
        textures=len(model.get("textures",[])),
        bytes=len(blob))
def get(name):
    print("Téléchargement CC0 MakeHuman Studio:",name,flush=True)
    req=Request(ROOT+name,headers={"User-Agent":"MonEvolutionIMC-CC0-Studio-v2"})
    with urlopen(req,timeout=60) as response:
        blob=response.read(18_000_000)
    if not blob or len(blob)>=18_000_000:
        raise RuntimeError("File too large or empty: "+name)
    return blob
def build():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    manifest={"version":2,"format":"makehuman-studio",
              "source":"kblood/CharacterCreator@"+UPSTREAM,
              "assetLicense":"CC0-1.0",
              "viewerLicense":"MIT (Three.js and independent Mon Evolution code)",
              "files":{}}
    with zipfile.ZipFile(OUTPUT,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6,allowZip64=False) as bundle:
        for name in ASSETS:
            body=get(name)
            info=glb_info(body,name)
            if name=="base_body_anim.glb" and (info["meshes"]<1 or
               info["skins"]<1 or info["clips"]<1 or info["morphs"]<20):
                raise RuntimeError("Base model lacks skin, animations or morphs: "+str(info))
            info["sha256"]=hashlib.sha256(body).hexdigest()
            manifest["files"][name]=info
            bundle.writestr(name,body,compress_type=zipfile.ZIP_DEFLATED)
        bundle.writestr("manifest.json",json.dumps(manifest,separators=(",",":")))
        bundle.writestr("LICENSE-CC0.txt",
            "All packaged generated GLB assets are designated CC0-1.0 by the CharacterCreator rights holder. "
            "Generated using upstream CC0 MakeHuman system assets. "
            "Source: github.com/kblood/CharacterCreator commit "+UPSTREAM+
            ". This pack includes no GPL application code. "
            "The runtime uses Three.js under the MIT license.\n")
    with zipfile.ZipFile(OUTPUT) as z:
        assert len(z.namelist())==len(ASSETS)+2
        assert z.testzip() is None
    hash_=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    (OUTPUT.parent/(OUTPUT.name+".sha256")).write_text(hash_+"  "+OUTPUT.name+"\n")
    print("Studio 3D v2:",OUTPUT.stat().st_size,"bytes",
          len(ASSETS),"GLB files. SHA256",hash_,flush=True)
    if not (9_000_000<OUTPUT.stat().st_size<60_000_000):
        raise RuntimeError("Unexpected Studio asset pack size")
if __name__=="__main__":
    build()
