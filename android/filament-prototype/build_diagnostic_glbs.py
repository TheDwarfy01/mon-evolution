#!/usr/bin/env python3
"""Build simple unskinned CC0 body and cube GLBs for differential Filament testing."""
import json
import struct
import sys
from pathlib import Path

def pad(data, byte=b"\x00"):
    return data + byte * (-len(data) % 4)

def read_glb(blob):
    assert blob[:4] == b"glTF" and struct.unpack_from("<II", blob, 4) == (2, len(blob))
    jlen, jtag = struct.unpack_from("<II", blob, 12)
    assert jtag == 0x4e4f534a
    document = json.loads(blob[20:20+jlen])
    offset = 20 + jlen
    blen, btag = struct.unpack_from("<II", blob, offset)
    assert btag == 0x004e4942
    return document, blob[offset+8:offset+8+blen]

def accessor_data(document, binary, index, element_size):
    acc = document["accessors"][index]
    view = document["bufferViews"][acc["bufferView"]]
    assert view["buffer"] == 0 and not acc.get("byteOffset") and not view.get("byteStride")
    n = acc["count"] * element_size
    assert view["byteLength"] == n
    begin = view["byteOffset"]
    result = binary[begin:begin+n]
    assert len(result) == n
    return result, acc

def make_glb(label, vertices, indices, num_vertices, num_indices, tint):
    assert len(vertices) == num_vertices * 12
    assert len(indices) == num_indices * 2
    binary = pad(vertices) + pad(indices)
    json_glb = {
        "asset": {"version": "2.0", "generator": "Mon Evolution IMC Filament diagnostic"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer":0,"byteOffset":0,"byteLength":len(vertices),"target":34962},
            {"buffer":0,"byteOffset":len(pad(vertices)),"byteLength":len(indices),"target":34963}],
        "accessors":[{"bufferView":0,"componentType":5126,"count":num_vertices,"type":"VEC3"},
                     {"bufferView":1,"componentType":5123,"count":num_indices,"type":"SCALAR"}],
        "materials":[{"name":label,"doubleSided":True,
                      "pbrMetallicRoughness":{"baseColorFactor":tint,"metallicFactor":0,"roughnessFactor":1},
                      "extensions":{"KHR_materials_unlit":{}}}],
        "meshes":[{"name":label,"primitives":[{"attributes":{"POSITION":0},"indices":1,"material":0,"mode":4}]}],
        "nodes":[{"name":label,"mesh":0}],
        "scenes":[{"nodes":[0]}],"scene":0,"extensionsUsed":["KHR_materials_unlit"]
    }
    body = pad(json.dumps(json_glb,separators=(",",":")).encode("utf8"), b" ")
    result = struct.pack("<III",0x46546c67,2,12+8+len(body)+8+len(binary))
    result += struct.pack("<II",len(body),0x4e4f534a)+body
    result += struct.pack("<II",len(binary),0x004e4942)+binary
    return result

def main(source, target):
    doc, raw = read_glb(Path(source).read_bytes())
    body = doc["meshes"][0]["primitives"][0]
    verts, av = accessor_data(doc, raw, body["attributes"]["POSITION"],12)
    indices, ai = accessor_data(doc, raw, body["indices"],2)
    assert av["componentType"] == 5126 and ai["componentType"] == 5123
    assert av["count"] > 10000 and 0.75 < av["max"][1] - av["min"][1] < 2.5
    output = Path(target)
    output.mkdir(parents=True,exist_ok=True)
    output.joinpath("filament-simple-body.glb").write_bytes(make_glb(
        "Corps statique CC0",verts,indices,av["count"],ai["count"],[0.92,0.5,0.32,1]))
    # A simple, unlit cube proves the native engine can render even without the original asset.
    points=[(-.55,-.55,-.55),(-.55,-.55,.55),(-.55,.55,-.55),(-.55,.55,.55),
            (.55,-.55,-.55),(.55,-.55,.55),(.55,.55,-.55),(.55,.55,.55)]
    faces=[(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
           (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
    vb=b"".join(struct.pack("<fff",*p) for p in points)
    ib=b"".join(struct.pack("<H",i) for f in faces for i in f)
    output.joinpath("filament-test-cube.glb").write_bytes(make_glb(
        "Cube diagnostic",vb,ib,8,len(faces)*3,[1,.65,.1,1]))
    for filename in ("filament-simple-body.glb","filament-test-cube.glb"):
        path=output/filename
        assert path.stat().st_size > 500
        d, _=read_glb(path.read_bytes())
        assert len(d["meshes"])==1 and "skins" not in d and "animations" not in d
        print(filename, path.stat().st_size, "bytes")

if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: build_diagnostic_glbs.py base_body_anim.glb output_assets_dir")
    main(sys.argv[1],sys.argv[2])
