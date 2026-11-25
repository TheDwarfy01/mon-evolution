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
