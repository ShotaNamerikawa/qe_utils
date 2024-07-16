import numpy as np
from qe_utils import pwx_out

def test_pwx_out():
    pwxout = pwx_out.PWxOut("tests/models/nscf.out")
    np.testing.assert_almost_equal(pwxout.fermi_energy, -2.3042)