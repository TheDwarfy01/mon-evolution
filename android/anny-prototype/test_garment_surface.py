import unittest
import numpy as np
from garment_surface import fabric_solver,front_patch,gentle_chest_solver,adjacency,peak_relief
from native_weight import native_excursion,extend_native,boost_native_thighs

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
    def test_native_direction_doubles_previous_horizontal_excursion(self):
        x,y=np.meshgrid(np.linspace(-.14,.14,41),np.linspace(0.,1.,51))
        base=np.stack([x.ravel(),y.ravel(),np.full(x.size,.12)],axis=1).astype(np.float32)
        old=base.copy();old[:,2]+=.05
        native=base.copy();native[:,2]+=.08
        extended,factor=extend_native(base,old,native)
        self.assertAlmostEqual(factor,1.25,places=4)
        self.assertAlmostEqual(native_excursion(base,extended)/native_excursion(base,old),2.,places=4)
        np.testing.assert_array_equal(extended[:,:2],base[:,:2])
    def test_peak_relief_does_not_move_sternum_or_dig_a_trough(self):
        x,y=np.meshgrid(np.linspace(-.12,.12,41),np.linspace(-.09,.09,31))
        z=.20-.15*x*x-.12*y*y
        q=np.stack([x.ravel(),y.ravel(),z.ravel()],axis=1).astype(np.float32)
        f=[]
        for row in range(30):
            for col in range(40):
                i=row*41+col;f.extend([[i,i+1,i+41],[i+1,i+42,i+41]])
        f=np.array(f);graph=adjacency(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),len(q))
        weight=(np.abs(q[:,0])>.025).astype(np.float32)
        bumped=q.copy()
        bumped[:,2]+=.02*np.exp(-((np.abs(q[:,0])-.055)**2+q[:,1]**2)/.00005)
        solve=peak_relief(graph,weight,1.,.003)
        out=solve(bumped)
        np.testing.assert_array_equal(out[weight==0],bumped[weight==0])
        np.testing.assert_array_equal(out[:,:2],bumped[:,:2])
        self.assertGreater(float(np.max(bumped[:,2]-out[:,2])),.0002)
        self.assertLessEqual(float(np.max(bumped[:,2]-out[:,2])),.003001)
        self.assertTrue(np.all(out[:,2]<=bumped[:,2]+1e-8))
        self.assertLess(float(np.max(np.abs(solve(q)-q))),.0002)
    def test_thigh_boost_preserves_calf_hips_length_and_midline(self):
        x,y=np.meshgrid(np.linspace(-.16,.16,41),np.linspace(0.,1.,101))
        base=np.stack([x.ravel(),y.ravel(),np.zeros(x.size)],axis=1).astype(np.float32)
        native=base.copy();native[:,2]+=.02
        native[:,0]-=np.sign(base[:,0])*.008
        extended=base.copy()
        out=boost_native_thighs(base,extended,native,base)
        unchanged=(base[:,1]<=.25)|(base[:,1]>=.51)
        np.testing.assert_array_equal(out[unchanged],extended[unchanged])
        np.testing.assert_array_equal(out[:,1],extended[:,1])
        self.assertTrue(np.all(out[:,0]*base[:,0]>=0))
        lower=(base[:,1]>.32)&(base[:,1]<.38)
        self.assertGreater(float(np.mean(out[lower,2])),.015)
        self.assertLessEqual(float(np.linalg.norm(out-extended,axis=1).max()),.030001)
if __name__=='__main__':unittest.main()
