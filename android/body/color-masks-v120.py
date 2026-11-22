#!/usr/bin/env python3
"""v1.6.120: correct iris alignment, hairline protection and upper-thigh artefacts.

Generate accurate, soft-edged recoloring masks from the transparent HD sprite.

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
    # The previous female leg mask started at y=.55, BELOW the shorts hem.
    # Recoloring thus began abruptly halfway down the thigh, creating the
    # striking horizontal pale band reported on both screenshots.
    # Expand *above* the real shorts hem, then gate by warm skin pixels.
    # Garments remain untouched, irrespective of the selected skin colour.
    upper = (
      region(.375,.625,.040,.218,.010) +   # entire face incl. forehead
      region(.393,.604,.148,.286,.010) +   # neck and exposed neckline
      region(.148,.423,.153,.683,.015) +   # left arm and hand
      region(.576,.862,.153,.683,.015)     # right arm and hand
    )
    # Start under the garment but ABOVE its exposed-skin boundary.
    # No geometric edge may cross bare skin in either portrait.
    if sex=='female':
        legs=region(.275,.725,.477,.975,.012)
        upper+=region(.267,.416,.175,.30,.014)+region(.584,.755,.175,.30,.014)
    else:
        legs=region(.265,.735,.532,.975,.016)
    skin=np.clip(upper+legs,0,1)*warm*person
    skin=cv2.GaussianBlur(skin,(0,0),1.9)*person
    # Hair follows an anatomical polygon, rather than a large rectangular
    # cap that included the forehead and even dark eyebrow pixels.
    # The root is calculated from the original image; no new hair is painted.
    def hair_polygon(points):
        vertices=np.array([[(round(px*W),round(py*H)) for px,py in points]],np.int32)
        alpha=np.zeros((H,W),np.uint8)
        cv2.fillPoly(alpha,vertices,255)
        return cv2.GaussianBlur(alpha.astype(np.float32)/255,(0,0),2.3)
    if sex=='male':
        crown=hair_polygon([
          (.332,.052),(.344,.034),(.385,.020),(.421,.009),(.495,.004),
          (.559,.008),(.612,.021),(.656,.045),(.660,.067),
          (.631,.085),(.615,.069),(.582,.060),(.532,.057),(.483,.055),
          (.431,.060),(.405,.069),(.362,.088),(.340,.078)])
        left=region(.334,.385,.044,.099,.007)
        right=region(.613,.671,.040,.099,.007)
    else:
        crown=hair_polygon([
          (.372,.058),(.392,.033),(.438,.015),(.461,.003),
          (.531,.002),(.571,.012),(.615,.029),(.649,.058),
          (.657,.081),(.621,.098),(.610,.078),(.576,.070),
          (.534,.067),(.488,.064),(.431,.071),(.395,.095),
          (.366,.098)])
        left=region(.350,.416,.055,.145,.007)
        right=region(.588,.657,.055,.145,.007)
    # Extend female lower side locks without tinting the face.
    if sex=='female':
        left=np.maximum(left,region(.342,.423,.090,.204,.009))
        right=np.maximum(right,region(.580,.666,.090,.204,.009))
    hair_area=np.clip(crown+left+right,0,1)
    # Most importantly: *exclude* facial features; the eyebrows should
    # never become gold/white when a hair colour is chosen.
    forehead=region(.412,.592,.071,.130,.004)
    dark=np.clip((170-brightness)/100,0,1)
    skin_protection=1-.995*warm
    hair=np.clip(hair_area*(1-forehead)*dark*skin_protection*person,0,1)
    # Exclude disconnected flecks, including the top-left male speck.
    binary=np.uint8(hair>.12)
    n, labels, stats, _=cv2.connectedComponentsWithStats(binary,8)
    if n>1:
        largest=1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
        keep=np.uint8(labels==largest)
        keep=cv2.dilate(keep,np.ones((5,5),np.uint8),iterations=1)
        hair*=cv2.GaussianBlur(keep.astype(np.float32),(0,0),1.1)
    hair=cv2.GaussianBlur(hair,(0,0),1.6)*person
    # Locate each iris using photograph pixels; previous coordinates are
    # search-window anchors, never the final recoloring centres.
    eyeY=.088 if sex=='male' else .094
    eyeXs=(.470,.534) if sex=='male' else (.466,.529)
    gray=cv2.cvtColor(img[:,:,:3],cv2.COLOR_RGB2GRAY).astype(np.float32)
    eyes=np.zeros((H,W),np.float32)
    for expected_x in eyeXs:
        cx,cy=int(expected_x*W),int(eyeY*H)
        x0,x1=max(0,cx-10),min(W,cx+11)
        y0,y1=max(0,cy-5),min(H,cy+7)
        patch=gray[y0:y1,x0:x1]
        smoothed=cv2.GaussianBlur(patch,(3,3),.75)
        yy,xx=np.mgrid[y0:y1,x0:x1]
        distance=((xx-cx)/9.)**2+((yy-cy)/5.)**2
        score=smoothed+28*distance
        py,px=np.unravel_index(np.argmin(score),score.shape)
        ix,iy=x0+int(px),y0+int(py)
        local=ellipse(ix/W,iy/H,.0053,.0025)
        darkness=np.clip((150-gray)/75,0,1)
        # The center of each detected iris must remain opaque even for
        # naturally light eyes; darkness is only a subtle edge guide.
        eyes=np.maximum(eyes,local*(.88+.12*darkness))
        print(f'{sex} iris: expected ({cx},{cy}), detected ({ix},{iy})')
    eyes=cv2.GaussianBlur(eyes,(0,0),.55)*person
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
