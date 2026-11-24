#!/usr/bin/env python3
"""Create a static CC0 Filament body with 9 reversible morphology controls.
This is a visual diagnostic, NOT a medical anatomical estimate."""
import json, math, struct, sys
from pathlib import Path
REGIONS=[('neck',.845,.055,'center'),('chest',.705,.082,'center'),
 ('arm',.745,.085,'arm'),('forearm',.648,.085,'arm'),('waist',.643,.057,'center'),
 ('belly',.600,.059,'center'),('hips',.557,.071,'center'),
 ('thigh',.340,.102,'leg'),('calf',.165,.082,'leg')]
def smooth(x):
 x=max(0.,min(1.,x));return x*x*(3.-2.*x)
def warp(key,x,y,z,lo,hi,change):
 h=hi-lo;t=(y-lo)/h;ax=abs(x)
 center,radius,kind=next((c,r,k) for name,c,r,k in REGIONS if name==key)
 vertical=math.exp(-.5*((t-center)/radius)**2)
 if kind=='center':
  arm=smooth((ax/h-.105)/.09)*smooth((t-.56)/.09)*(1-smooth((t-.82)/.075))
  influence=vertical*(1-arm);axis=0.
 elif kind=='arm':
  axis=math.copysign(h*max(.1025,min(.274,.1025+(.795-t)*.94)),x)
  influence=vertical*smooth((ax/h-.105)/.09)*smooth((t-.56)/.09)*(1-smooth((t-.82)/.075))
 else:
  axis=math.copysign(h*.125,x)
  influence=vertical*smooth((ax/h-.045)/.075)*(1-smooth((t-.43)/.14))
 a=change*influence
 return axis+(x-axis)*(1+a),y,z*(1+a)
def read(blob):
 assert blob[:4]==b'glTF' and struct.unpack_from('<II',blob,4)==(2,len(blob))
 n,t=struct.unpack_from('<II',blob,12);assert t==0x4e4f534a
 doc=json.loads(blob[20:20+n]);i=20+n;m,bt=struct.unpack_from('<II',blob,i)
 assert bt==0x004e4942
 return doc,bytearray(blob[i+8:i+8+m])
def build(source,out):
 doc,buf=read(Path(source).read_bytes())
 assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==8
 body=doc['meshes'][0]['primitives'][0]
 a=doc['accessors'][body['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
 assert a['type']=='VEC3' and a['componentType']==5126
 start=v.get('byteOffset',0)+a.get('byteOffset',0)
 points=list(struct.iter_unpack('<fff',buf[start:start+a['count']*12]))
 lo=min(p[1] for p in points);hi=max(p[1] for p in points)
 assert len(points)>10000 and 1.4<hi-lo<1.9
 names=[];targets=[]
 for key,*_ in REGIONS:
  for sign,suffix in [(1,'plus'),(-1,'moins')]:
   block=bytearray();changed=0
   for x,y,z in points:
    nx,ny,nz=warp(key,x,y,z,lo,hi,sign*.23)
    delta=(nx-x,ny-y,nz-z)
    changed+=abs(delta[0])+abs(delta[2])>1e-7
    block.extend(struct.pack('<fff',*delta))
   assert changed>50,(key,changed)
   while len(buf)%4:buf.append(0)
   doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(block)})
   buf.extend(block)
   doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,
      'componentType':5126,'count':len(points),'type':'VEC3'})
   targets.append({'POSITION':len(doc['accessors'])-1});names.append(key+'_'+suffix)
 assert len(targets)==18
 body['targets']=targets
 doc['meshes']=[{'name':'Corps 9 regions','primitives':[body],
       'weights':[0.]*18,'extras':{'targetNames':names}},
      {'name':'Visage stable','primitives':doc['meshes'][0]['primitives'][1:]}]
 doc['nodes']=[{'name':'Corps','mesh':0},{'name':'Visage','mesh':1}]
 doc['scenes']=[{'nodes':[0,1]}];doc['scene']=0
 doc['asset']['generator']='Mon Evolution IMC Filament 9 visual measurements (CC0 body)'
 doc['buffers'][0]['byteLength']=len(buf)
 js=json.dumps(doc,separators=(',',':')).encode('utf8');js+=b' '*(-len(js)%4)
 buf+=b'\0'*(-len(buf)%4)
 output=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(buf))
 output+=struct.pack('<II',len(js),0x4e4f534a)+js
 output+=struct.pack('<II',len(buf),0x004e4942)+bytes(buf)
 dest=Path(out);dest.write_bytes(output)
 verified,_=read(output)
 assert len(verified['meshes'][0]['primitives'][0]['targets'])==18
 assert len(verified['meshes'][1]['primitives'])==7
 assert 'skins' not in verified and 'animations' not in verified
 assert len(verified.get('images',[]))>=5
 print('Filament morph GLB',dest,len(output),'bytes')
if __name__=='__main__':
 assert len(sys.argv)==3
 build(sys.argv[1],sys.argv[2])
