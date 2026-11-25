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
