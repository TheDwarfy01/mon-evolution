"""Extend the existing native weight direction without a custom body sculpt."""
import numpy as np

def native_excursion(base,variant):
    # Robust horizontal excursion of trunk and legs, not arms, hair or height.
    h=float(np.ptp(base[:,1]))
    t=(base[:,1]-base[:,1].min())/h
    x=np.abs(base[:,0]-np.median(base[:,0]))/h
    region=(t>.14)&(t<.79)&(x<.15)
    assert np.count_nonzero(region)>30
    horizontal=(variant-base)[region][:,[0,2]]
    return float(np.quantile(np.linalg.norm(horizontal,axis=1),.95))

def extend_native(base,old_heavy,native_heavy):
    before=native_excursion(base,old_heavy)
    current=native_excursion(base,native_heavy)
    assert before>1e-5 and current>1e-5
    # Prefer the wider native parameter values; extend their displacement only
    # as necessary to reach twice the previous robust excursion.
    factor=float(np.clip(2.*before/current,1.,2.5))
    out=base+(native_heavy-base)*factor
    ratio=native_excursion(base,out)/before
    assert 1.80<=ratio<=2.5,(before,current,factor,ratio)
    assert np.isfinite(out).all()
    print('Native weight extension: old',before,'native',current,'factor',factor,'ratio',ratio)
    return out.astype(base.dtype),factor


def boost_native_thighs(base,extended,native_endpoint,without_thigh):
    """Increase thigh fullness using only the native thigh circumference direction.
    The smooth height envelope excludes hips, calves and feet, and protects the
    centre seam from any additional cross-leg overlap.
    """
    h=float(np.ptp(base[:,1]))
    t=(base[:,1]-base[:,1].min())/h
    cx=float(np.median(base[:,0]))
    # The lower thigh receives more emphasis than the upper thigh. Blend
    # smoothly to zero near the knee/calf and pelvic region.
    def smooth(v):
        v=np.clip(v,0.,1.)
        return v*v*(3.-2.*v)
    envelope=smooth((t-.25)/.075)*smooth((.51-t)/.075)
    lower=smooth((.43-t)/.10)
    gain=(1.10+.65*lower)*envelope
    extra=(native_endpoint-without_thigh)*gain[:,None]
    extra[:,1]=0.  # no change to leg length or joint height
    length=np.linalg.norm(extra,axis=1,keepdims=True)
    extra*=np.minimum(1.,(.030*h)/np.maximum(length,1e-9))
    side=np.where(base[:,0]>=cx,1.,-1.)
    old_gap=(extended[:,0]-cx)*side
    # Do not push an inner thigh farther through the central plane. Preserve
    # existing contact, and let the native outward volume increase elsewhere.
    extra[:,0]=side*np.maximum(extra[:,0]*side,-np.maximum(old_gap-.001*h,0.))
    out=extended+extra
    assert np.isfinite(out).all()
    assert np.array_equal(out[:,1],extended[:,1])
    assert np.array_equal(out[envelope==0],extended[envelope==0])
    for lo,hi in ((.31,.39),(.39,.47)):
        mask=(t>=lo)&(t<hi)
        assert np.count_nonzero(mask)>15
        print('Thigh native boost',lo,hi,'p90 horizontal',float(np.quantile(np.linalg.norm(extra[mask][:,[0,2]],axis=1),.90)))
        assert np.quantile(np.linalg.norm(extra[mask][:,[0,2]],axis=1),.90)>1e-5
    return out.astype(base.dtype)

def boost_native_belly(base,extended,native_endpoint,without_depth,without_waist,female):
    """Amplify native abdominal directions only, tapering before chest and hips."""
    h=float(np.ptp(base[:,1]))
    t=(base[:,1]-base[:,1].min())/h
    front,back=((10772,10797) if female else (10780,10975))
    sign=1. if base[front,2]>=base[back,2] else -1.
    mid=(base[front,2]+base[back,2])*.5
    def smooth(x):
        x=np.clip(x,0.,1.)
        return x*x*(3.-2.*x)
    envelope=smooth((t-.49)/.065)*smooth((.72-t)/.075)
    lower=1.+.35*smooth((.65-t)/.08)
    facing=smooth((base[:,2]-mid)*sign/(.055*h))
    depth=native_endpoint-without_depth
    waist=native_endpoint-without_waist
    extra=np.zeros_like(base)
    extra[:,2]=sign*np.maximum(sign*depth[:,2],0.)*envelope*lower*facing*2.2
    extra[:,0]=waist[:,0]*envelope*lower*.65
    length=np.linalg.norm(extra,axis=1,keepdims=True)
    extra*=np.minimum(1.,(.045*h)/np.maximum(length,1e-9))
    out=extended+extra
    assert np.isfinite(out).all()
    assert np.array_equal(out[envelope==0],extended[envelope==0])
    assert np.array_equal(out[:,1],extended[:,1])
    assert np.max(extra[:,2]*sign)>1e-4,'Native abdominal projection missing'
    print('Native belly reinforcement: maximum forward displacement',float(np.max(extra[:,2]*sign)))
    return out.astype(base.dtype)
