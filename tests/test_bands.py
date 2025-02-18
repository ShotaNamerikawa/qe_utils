from qe_utils.bands import *
from qe_utils.pwx_in import PWxIn
import time
import numpy as np

def test_filband():
    start = time.time()
    filband = Filband("tests/models/bands.dat")
    end = time.time()
    print("time: {} [sec]".format(end - start))
    
    num_k = 274
    num_band = 60
    e_max = 39.9250
    e_min = -21.9120
    
    np.testing.assert_almost_equal(filband.num_k, num_k)
    np.testing.assert_almost_equal(filband.num_band, num_band)
    np.testing.assert_almost_equal(filband.e_max, e_max)
    np.testing.assert_almost_equal(filband.e_min, e_min)
    
def test_filband_gnu():
    filband = Filband("tests/models/test_bands.out")
    filbandgnu = Filbandgnu.from_Filband(filband)
    print(filbandgnu.ek)
    filbandgnu.plot(savefig = "tests/models/test_filband.pdf", pwxin = PWxIn.from_pwx_input("tests/models/test_band_nscf.in"))