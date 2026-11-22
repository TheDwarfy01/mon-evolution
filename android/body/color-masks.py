#!/usr/bin/env python3
"""Generate accurate, soft-edged recoloring masks from the transparent HD sprite.

Each mask is RGBA: skin, hair and irises for both photographed models.
The color controls use these layers with drawImage/source-in, never
getImageData (which can throw SecurityError in Android WebView).
"""
from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image

asset = Path(sys.argv[1])
base = np.array(Image.open(asset).convert('RGBA'))
assert base.shape == (1440, 1620, 4), base.shape
H, W = 1440, 810
y, x = np.mgrid[:H, :W].astype(np.float32)
x /= W; y /= H

def feather(lo, hi, grid, taper):
    return np.minimum(1, np.maximum(0, (grid-lo)/taper)) * np.minimum(1, np.maximum(0, (hi-grid)/taper))

def region(x0,x1,y0,y1,edge=.012):
    return feather(x0,x1,x,edge)*feather(y0,y1,y,edge)

def ellipse(cx,cy,rx,ry):
    d=((x-cx)/rx)**2+((y-cy)/ry)**2
    return np.clip((1-d)*12,0,1)

outputs = {'skin':[], 'hair':[], 'eyes':[]}
for index,sex in enumerate(('male','female')):
    img=base[:,index*W:(index+1)*W,:]
    rgb=img[:,:,:3].astype(np.float32)
    person=img[:,:,3].astype(np.float32)/255
    red, green, blue=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    brightness=(red+green+blue)/3
    warm=np.clip((red-green-5)/18,0,1)*np.clip((red-blue-10)/23,0,1)
    warm*=np.clip((red-48)/35,0,1)
    # Bare limbs and face occupy softly bounded anatomical zones.
    # Skin is selected by actual pixel color, so garment borders cannot tint.
    areas = (
      region(.39,.61,.065,.207,.016) + # face, with real cheek edge from warm color
      region(.41,.595,.167,.27,.014) + # neck and exposed clavicle
      region(.155,.392,.17,.67,.025) + # left arm/hand
      region(.608,.85,.17,.67,.025) + # right arm/hand
      region(.29,.5,.55,.95,.025) + # left leg
      region(.50,.71,.55,.95,.025)   # right leg
    )
    if sex=='female':
        areas += region(.26,.40,.19,.285,.012) + region(.60,.74,.19,.285,.012)
    skin=np.clip(areas,0,1)*warm*person
    skin=cv2.GaussianBlur(skin,(0,0),1.7)
    # Hair is identified in the photographed hairline, not the face below.
    # A soft forehead exclusion avoids a rectangular colored cap.
    crown=region(.335,.67,.008,.078,.013)
    left=region(.33,.433,.04,.177,.016)
    right=region(.57,.675,.04,.177,.016)
    hair_area=np.clip(crown+left+right,0,1)
    dark=np.clip((165-brightness)/95,0,1)
    skin_protection=1-.96*warm
    hair=np.clip(hair_area*dark*skin_protection*person,0,1)
    hair=cv2.GaussianBlur(hair,(0,0),2.0)
    # Actual pupils are near 11% of portrait height; the old .072
    # pointed at the forehead. Keep masks tiny for realism.
    eyeY=.110 if sex=='male' else .111
    eyes=(ellipse(.469,eyeY,.008,.0038)+ellipse(.535,eyeY,.008,.0038))
    eyes=np.clip(eyes,0,1)*person
    eyes=cv2.GaussianBlur(eyes,(0,0),.8)
    for key,a in [('skin',skin),('hair',hair),('eyes',eyes)]:
        rgba=np.full((H,W,4),255,dtype=np.uint8)
        rgba[:,:,3]=np.uint8(np.clip(a*255,0,255))
        outputs[key].append(rgba)
        count=np.mean(a>.05)
        if key=='skin' and not .025<count<.32: raise ValueError(f'{sex} skin coverage {count:.3f}')
        if key=='hair' and not .0008<count<.025: raise ValueError(f'{sex} hair coverage {count:.3f}')
        if key=='eyes' and not .000005<count<.0004: raise ValueError(f'{sex} eyes coverage {count:.6f}')
        print(f'{sex}/{key}: {count*100:.3f}% of portrait')
for kind,parts in outputs.items():
    outfile=asset.with_name('studio-'+kind+'-mask.png')
    Image.fromarray(np.concatenate(parts,axis=1),'RGBA').save(outfile,optimize=True)
    check=np.array(Image.open(outfile).convert('RGBA'))
    assert check.shape==(H,2*W,4) and np.max(check[:,:,3])>150
    assert check[H-1,0,3]==0 and check[H-1,2*W-1,3]==0
    print(kind, outfile.stat().st_size, 'bytes')
