#!/usr/bin/env python3
"""Build the standalone, CC0 MakeHuman hm08 morph pack (not bundled with the APK).
Upstream files are pinned to the MakeHuman source revision. No MakeHuman AGPL
application code is distributed: only CC0 mesh and sparse CC0 .target data.
"""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

REV = "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"
ROOT = ("https://raw.githubusercontent.com/makehumancommunity/makehuman/"
        + REV + "/makehuman/data/")
N_BODY = 13380
AGES = ("baby", "child", "young", "old")
WEIGHTS = ("minweight", "averageweight", "maxweight")
SEXES = ("female", "male")
OUT = Path(os.environ.get("MAKEHUMAN_PACK_OUT",
                          "android/generated/makehuman-pack-v1.json.gz"))
def download(path):
    url = ROOT + path
    print("MakeHuman CC0 asset:", path, flush=True)
    with urlopen(Request(url, headers={"User-Agent":"MonEvolutionIMC/3D-pack-builder"}),
                 timeout=45) as response:
        data = response.read(15_000_000)
    if not data or len(data) >= 15_000_000:
        raise RuntimeError("Invalid size for " + path)
    return data.decode("utf-8")

def build():
    obj = download("3dobjs/base.obj")
    vertices = []
    faces = []
    for line in obj.splitlines():
        if line.startswith("v "):
            p = line.split()
            vertices.append([round(float(p[1]), 4),
                             round(float(p[2]), 4),
                             round(float(p[3]), 4)])
        elif line.startswith("f "):
            parts = line.split()[1:]
            try:
                ids = [int(s.split("/")[0]) - 1 for s in parts]
            except ValueError:
                continue
            if len(ids) < 3 or min(ids) < 0 or max(ids) >= N_BODY:
                continue
            for k in range(1, len(ids)-1):
                faces.extend((ids[0], ids[k], ids[k+1]))
    if len(vertices) < N_BODY or len(faces) < 20000:
        raise RuntimeError("Unrecognised MakeHuman body topology")
    # The face mesh contains the first 13,380 vertices; the remaining vertices
    # are separate eye/teeth/tongue/helper objects not drawn in this body viewer.
    vertices = vertices[:N_BODY]
    targets = {}
    for sex in SEXES:
        for age in AGES:
            # Gender/age shape comes from phenotype targets. Universal targets
            # alone are small mass modifiers, not complete age-specific bodies.
            for variant in ("identity",) + WEIGHTS:
                name = ("caucasian-%s-%s" % (sex, age) if variant=="identity"
                        else "universal-%s-%s-averagemuscle-%s" % (sex, age, variant))
                lines = download("targets/macrodetails/%s.target" % name)
                sparse = []
                for line in lines.splitlines():
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) < 4:
                        continue
                    vertex = int(parts[0])
                    if not 0 <= vertex < N_BODY:
                        continue
                    dx, dy, dz = (round(float(v), 4) for v in parts[1:4])
                    if dx or dy or dz:
                        sparse.extend((vertex, dx, dy, dz))
                if len(sparse)%4:
                    raise RuntimeError("Corrupt sparse target: " + name)
                targets[sex + "-" + age + "-" + variant] = sparse
    data = {"version": 1, "upstream": "makehumancommunity/makehuman@" + REV,
            "license": "CC0-1.0", "bodyVertices": N_BODY,
            "positions": vertices, "triangles": faces, "targets": targets}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=True).encode()
    with OUT.open("wb") as fp:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fp,
                           compresslevel=9, mtime=0) as gz:
            gz.write(payload)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    (OUT.parent / (OUT.name + ".sha256")).write_text(
        digest + "  " + OUT.name + "\n", encoding="ascii")
    print("Pack generated:", OUT, OUT.stat().st_size,
          "bytes, faces:", len(faces)//3, "targets:", len(targets),
          "sha256:", digest)
    if OUT.stat().st_size > 12_000_000:
        raise RuntimeError("Pack exceeds 12 MB mobile download limit")
if __name__ == "__main__":
    build()
