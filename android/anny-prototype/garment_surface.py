"""Constrained fabric and seam smoothing on the shared Anny topology."""
import numpy as np

def adjacency(edges,n):
    edges=np.unique(np.sort(edges,axis=1),axis=0)
    a=np.concatenate([edges[:,0],edges[:,1]])
    b=np.concatenate([edges[:,1],edges[:,0]])
    degree=np.bincount(a,minlength=n)
    return a,b,degree

def average(q,graph):
    a,b,degree=graph
    sums=np.stack([np.bincount(a,weights=q[b,k],minlength=len(q)) for k in range(3)],axis=1)
    return np.where(degree[:,None]>0,sums/np.maximum(degree[:,None],1),q)

def limit(q,original,radius):
    diff=q-original
    mag=np.linalg.norm(diff,axis=1,keepdims=True)
    return (original+diff*np.minimum(1.,radius/np.maximum(mag,1e-9))).astype(original.dtype)

def fabric_solver(f,groups,n,h):
    # Every material shares the same vertices, including its seam.
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    edge_groups=np.tile(groups,3)
    uniq,inv=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True)
    min_group=np.full(len(uniq),99,dtype=np.int32)
    max_group=np.full(len(uniq),-1,dtype=np.int32)
    np.minimum.at(min_group,inv,edge_groups)
    np.maximum.at(max_group,inv,edge_groups)
    seam_edges=uniq[(min_group!=max_group)&(max_group<=2)&(max_group>=1)]
    seam=adjacency(seam_edges,n)
    full=adjacency(uniq,n)
    incident=np.zeros((n,8),dtype=np.int32)
    for k in range(3):np.add.at(incident,(f[:,k],groups),1)
    cloth=incident[:,1]+incident[:,2]
    total=incident.sum(axis=1)
    # Fully covered vertices receive fabric smoothing; exposed skin remains fixed.
    interior=(cloth==total)&(total>0)&(seam[2]==0)
    weights=interior.astype(np.float32)[:,None]
    seam_weight=(seam[2]==2).astype(np.float32)[:,None]
    def solve(q):
        out=q.copy()
        # Relax neckline, cuffs and waist edges along the seam itself.
        for _ in range(7):
            out+=(.38*seam_weight*(average(out,seam)-out)).astype(out.dtype)
        out=limit(out,q,.008*h)
        seam_base=out.copy()
        # Suppress the small folds from the extrapolated body underneath.
        # Taubin pairs limit the loss of the overall volume.
        for _ in range(36):
            out+=(.48*weights*(average(out,full)-out)).astype(out.dtype)
            out-= (.18*weights*(average(out,full)-out)).astype(out.dtype)
        return limit(out,seam_base,.032*h)
    return solve,interior,seam[2]>0

def front_patch(reference,eligible,cx,cy,rx,ry,depth_limit,front_sign=1.,strength=1.):
    """Fit a smooth curved fabric panel to its perimeter, only changing depth.
    Reference-space selection keeps the same anatomical vertices for every morph.
    """
    x=(reference[:,0]-cx)/rx
    y=(reference[:,1]-cy)/ry
    r=np.sqrt(x*x+y*y)
    ring=eligible&(r>=.72)&(r<=1.25)
    core=eligible&(r<1.)
    design=np.stack([np.ones(len(x)),x,y,x*x,x*y,y*y],axis=1)
    if np.count_nonzero(ring)<12 or np.count_nonzero(core)<5:
        return lambda q:q.copy(),int(np.count_nonzero(core))
    A=design[ring]
    w=np.sqrt(np.maximum(.15,1.-np.abs(r[ring]-.98)))
    # Precompute the reference-space least-squares map, shared by all morphs.
    projection=np.linalg.pinv(A*w[:,None])
    # Smooth blend with zero displacement at the edge of the patch.
    blend=np.clip((1.-r[core])/.45,0.,1.)
    blend=blend*blend*(3.-2.*blend)*strength
    def solve(q):
        out=q.copy()
        target=design[core]@(projection@(q[ring,2]*w))
        diff=np.clip(target-q[core,2],-depth_limit,depth_limit)*blend
        out[core,2]+=diff.astype(out.dtype)
        return out
    return solve,int(np.count_nonzero(core))

def gentle_chest_solver(reference,eligible,faces,h,cx,cy,sign):
    """Remove small surface irregularities, not the rib-cage contour.
    Topological smoothing cannot fit across the opposite side of the torso.
    """
    x=(reference[:,0]-cx)/(.105*h)
    y=(reference[:,1]-cy)/(.064*h)
    r=np.hypot(x,y)
    w=np.clip((1-r)/.45,0,1)
    w=(w*w*(3-2*w)*eligible).astype(np.float32)
    graph=adjacency(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),len(reference))
    # Hard depth cap, at most 0.65% of height (~11 mm for a 170 cm figure).
    cap=.0065*h
    def solve(q):
        z=q[:,2].copy()
        out=q.copy()
        for _ in range(8):
            mean=average(out,graph)[:,2]
            out[:,2]+=(.32*w*(mean-out[:,2])).astype(out.dtype)
        out[:,2]=z+np.clip(out[:,2]-z,-cap,cap)*w
        return out
    return solve

def torso_panel_solver(reference,shirt,h,female,faces):
    # Existing front/back anatomical anchors from the Anny renderer.
    chest,waist,belly=((1780,3910),(4142,4128),(10772,10797)) if female else ((1762,3911),(4141,4024),(10780,10975))
    pairs=np.array([chest,waist,belly])
    front=reference[pairs[:,0]]
    back=reference[pairs[:,1]]
    sign=1. if np.median(front[:,2]-back[:,2])>=0 else -1.
    center_y=(front[:,1]+back[:,1])*.5
    mid_z=(front[:,2]+back[:,2])*.5
    order=np.argsort(center_y)
    mid=np.interp(reference[:,1],center_y[order],mid_z[order])
    eligible=shirt&((reference[:,2]-mid)*sign>.005*h)
    cx=float((reference[:,0].min()+reference[:,0].max())*.5)
    # Navel: local front patch, no reduction of the overall belly circumference.
    belly_y=float(front[2,1])
    navel,count=front_patch(reference,eligible,cx,belly_y,.066*h,.055*h,.023*h,sign)
    print('Anny navel panel vertices',count)
    assert count>=5,'Anny navel garment patch not found'
    if female:
        return navel
    # Replace the wide polynomial patch: it cut a trough into the rib cage
    # on heavy morphs. Use bounded local smoothing instead.
    chest_y=float(front[0,1])
    pecs=gentle_chest_solver(reference,eligible,faces,h,cx,chest_y,sign)
    def solve(q):
        return navel(pecs(q))
    return solve

def male_pec_finish(reference,shirt,faces,h):
    """Very local fabric peak relief: preserve sternum and the native rib cage."""
    front=reference[1762];back=reference[3911]
    sign=1. if front[2]>=back[2] else -1.
    cx=float((reference[:,0].min()+reference[:,0].max())*.5)
    mid_z=float((front[2]+back[2])*.5)
    ax=np.abs(reference[:,0]-cx)/h
    y=(reference[:,1]-front[1])/h
    # Taper around each pectoral, excluding the sternum, side and lower belly.
    r=np.hypot((ax-.053)/.043,y/.047)
    w=np.clip((1.-r)/.50,0.,1.)
    w=(w*w*(3.-2.*w)*shirt*((reference[:,2]-mid_z)*sign>.004*h)).astype(np.float32)
    assert np.count_nonzero(w)>5,'Pectoral fabric region not found'
    graph=adjacency(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),len(reference))
    return peak_relief(graph,w,sign,.003*h)

def peak_relief(graph,weight,sign,cap):
    """No global fit: only suppress outward high-frequency peaks, with a hard cap."""
    def solve(q):
        z=q[:,2].copy()
        out=q.copy()
        for _ in range(5):
            mean=average(out,graph)[:,2]
            outward=np.maximum(0.,(out[:,2]-mean)*sign)
            out[:,2]-=(sign*.35*weight*outward).astype(out.dtype)
        moved=np.clip((z-out[:,2])*sign,0.,cap)*weight
        out[:,2]=z-sign*moved
        return out
    return solve

def natural_surface_solver(reference,faces,body,h):
    """Smooth connected body surfaces, preserving broad volume and facial detail."""
    t=(reference[:,1]-reference[:,1].min())/h
    def smooth(x):
        x=np.clip(x,0.,1.)
        return x*x*(3.-2.*x)
    # Protect face, hair, fingers and feet. Stronger finish around trunk and thighs.
    x=np.abs(reference[:,0]-np.median(reference[:,0]))/h
    weight=(smooth((t-.06)/.10)*smooth((.87-t)/.09)*smooth((.33-x)/.12)*body)
    trunk=smooth((t-.25)/.12)*smooth((.81-t)/.10)
    weight=(weight*(.45+.55*trunk)).astype(np.float32)[:,None]
    graph=adjacency(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),len(reference))
    def solve(q):
        out=q.copy()
        # Paired positive/negative passes suppress local bumps with less shrinkage.
        for _ in range(18):
            out+=(.46*weight*(average(out,graph)-out)).astype(out.dtype)
            out-=(.39*weight*(average(out,graph)-out)).astype(out.dtype)
        # Bound the total displacement, preserving the native broad silhouette.
        return limit(out,q,.009*h)
    return solve
