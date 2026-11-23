#!/usr/bin/env python3
"""Inspect validated GLB bind-pose rig positions in actual Three.js coordinates.
Pure stdlib: transforms glTF node quaternions and translations hierarchically.
"""
import json,struct,urllib.request
URL='https://raw.githubusercontent.com/kblood/CharacterCreator/852e48f316b90a0937234886630e4fb4cdfd1f78/output/base_body_anim.glb'
raw=urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'MonEvolutionPoseInspection'}),timeout=60).read()
length,ctype=struct.unpack_from('<II',raw,12)
data=json.loads(raw[20:20+length])
nodes=data['nodes']
parents={}
for i,n in enumerate(nodes):
 for ch in n.get('children',[]):parents[ch]=i
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def rotate(q,v):
 x,y,z,w=q
 u=[x,y,z]
 t=[2*(u[1]*v[2]-u[2]*v[1]),2*(u[2]*v[0]-u[0]*v[2]),2*(u[0]*v[1]-u[1]*v[0])]
 return [v[i]+w*t[i]+[u[1]*t[2]-u[2]*t[1],u[2]*t[0]-u[0]*t[2],u[0]*t[1]-u[1]*t[0]][i] for i in range(3)]
memo={}
def calc(i):
 if i in memo:return memo[i]
 n=nodes[i]
 local=n.get('translation',[0,0,0]);rot=n.get('rotation',[0,0,0,1])
 if i in parents:
  pt,pq=calc(parents[i])
  shifted=rotate(pq,local)
  pos=[pt[j]+shifted[j] for j in range(3)]
  quat=mul(pq,rot)
 else:pos=local;quat=rot
 memo[i]=(pos,quat)
 return memo[i]
want={'pelvis','spine_01','spine_02','spine_03','neck_01','head','clavicle_l','upperarm_l','lowerarm_l','hand_l','thigh_r','calf_r','foot_r','thigh_l','calf_l','foot_l'}
for i,n in enumerate(nodes):
 if n.get('name') in want:
  p,_=calc(i)
  print('WORLD_BONE',n['name'],*('%.4f'%v for v in p),flush=True)
