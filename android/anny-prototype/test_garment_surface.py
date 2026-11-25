import unittest
import numpy as np
from garment_surface import fabric_solver,front_patch,gentle_chest_solver

class GarmentTests(unittest.TestCase):
    def test_smoothing_preserves_exposed_skin_and_vertex_count(self):
        v=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[.5,.5,.3],[2,0,0],[2,1,0]],dtype=np.float32)
        f=np.array([[0,1,4],[1,2,4],[2,3,4],[3,0,4],[1,5,6],[1,6,2]])
        g=np.array([1,1,1,1,0,0])
        solve,interior,seam=fabric_solver(f,g,len(v),1.)
        out=solve(v)
        self.assertEqual(out.shape,v.shape)
        np.testing.assert_array_equal(out[5:],v[5:])
        self.assertTrue(interior[4])
        self.assertLess(out[4,2],v[4,2])
        self.assertLessEqual(float(np.linalg.norm(out[4]-v[4])),.032001)
        self.assertTrue(seam[1] and seam[2])
        self.assertTrue(np.isfinite(out).all())
    def test_front_panel_removes_bump_and_keeps_broad_curvature(self):
        x,y=np.meshgrid(np.linspace(-1.5,1.5,51),np.linspace(-1.5,1.5,51))
        x=x.ravel();y=y.ravel()
        z=.4-.06*x*x-.03*y*y
        base=np.stack([x,y,z],axis=1)
        front=base.copy()
        r=np.hypot(x,y)
        front[:,2]+=.12*np.exp(-(r/.13)**2)
        back=base.copy();back[:,2]-=1.
        q=np.concatenate([front,back])
        reference=np.concatenate([base,back])
        eligible=np.arange(len(q))<len(base)
        solve,count=front_patch(reference,eligible,0.,0.,1.,1.,.2)
        self.assertGreater(count,100)
        out=solve(q)
        i=np.argmin(r)
        self.assertLess(abs(out[i,2]-base[i,2]),.001)
        np.testing.assert_array_equal(out[~eligible],q[~eligible])
        np.testing.assert_array_equal(out[:,:2],q[:,:2])
        np.testing.assert_array_equal(out[:len(base)][r>=1.],front[r>=1.])
        # Chest-sized twin bulges and the same underlying broad curve.
        q[:len(base),2]=z+.09*np.exp(-((x-.32)**2+y*y)/.035)+.09*np.exp(-((x+.32)**2+y*y)/.035)
        out=solve(q)
        self.assertLess(np.max(np.abs(out[:len(base),2]-z)),.025)
        # Negative defect (indentation) is also flattened.
        q[:len(base),2]=z-.12*np.exp(-(r/.13)**2)
        self.assertLess(abs(solve(q)[i,2]-z[i]),.001)
    def test_chest_never_collapses_broad_envelope(self):
        x,y=np.meshgrid(np.linspace(-.14,.14,41),np.linspace(-.10,.10,31))
        z=.22-.25*x*x-.15*y*y
        q=np.stack([x.ravel(),y.ravel(),z.ravel()],axis=1).astype(np.float32)
        f=[]
        for row in range(30):
            for col in range(40):
                i=row*41+col
                f.extend([[i,i+1,i+41],[i+1,i+42,i+41]])
        eligible=np.ones(len(q),dtype=bool)
        solve=gentle_chest_solver(q,eligible,np.array(f),1.,0.,0.,1.)
        out=solve(q)
        self.assertLessEqual(float(np.max(np.abs(out[:,2]-q[:,2]))),.006501)
        np.testing.assert_array_equal(out[:,:2],q[:,:2])
        self.assertLess(float(np.max(np.abs(out[:,2]-q[:,2]))),.001)
        bumped=q.copy();bumped[:,2]+=.025*np.exp(-(q[:,0]**2+q[:,1]**2)/.0001)
        fixed=solve(bumped)
        center=np.argmin(q[:,0]**2+q[:,1]**2)
        self.assertLess(fixed[center,2],bumped[center,2])
        self.assertGreaterEqual(fixed[center,2],bumped[center,2]-.006501)
if __name__=='__main__':unittest.main()
