from qe_utils.projwfc import ProjwfcOut
import os
import numpy as np
import time

def test_projwfc():
    path = "tests/models"
    iatom = np.array([1,1,1,1,2,2,2,2])
    l = np.array([0,1,1,1,0,1,1,1])
    m = np.array([1,1,2,3,1,1,2,3])
    
    start = time.time()
    pwfcout = ProjwfcOut(os.path.join(path, "projwfc.out"))
    end = time.time()
    print("initialize time:{}".format(end - start))
    
    np.testing.assert_almost_equal(pwfcout.natomwfc,8)
    np.testing.assert_almost_equal(pwfcout.nbnd,60)
    np.testing.assert_almost_equal(pwfcout.nkstot,274)
    np.testing.assert_almost_equal(pwfcout.npwx,129)
    np.testing.assert_almost_equal(pwfcout.nkb,16)
    
    np.testing.assert_allclose(pwfcout.iatom, iatom)
    np.testing.assert_allclose(pwfcout.l, l)
    np.testing.assert_allclose(pwfcout.m, m)
    
    
    
    
    