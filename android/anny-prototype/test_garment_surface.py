import unittest
import numpy as np
from garment_surface import fabric_solver

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
if __name__=='__main__':unittest.main()
