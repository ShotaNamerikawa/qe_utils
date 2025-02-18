from qe_utils.projwfc import ProjwfcOut
from qe_utils.pwx_in import PWxIn
import os
import numpy as np
import time

import pytest

# def test_projwfc():
#     path = "tests/models"
#     iatom = np.array([1,1,1,1,2,2,2,2])
#     l = np.array([0,1,1,1,0,1,1,1])
#     m = np.array([1,1,2,3,1,1,2,3])
    
#     start = time.time()
#     pwfcout = ProjwfcOut(os.path.join(path, "projwfc.out"))
#     end = time.time()
#     print("initialize time:{}".format(end - start))
    
#     np.testing.assert_almost_equal(pwfcout.natomwfc,8)
#     np.testing.assert_almost_equal(pwfcout.nbnd,60)
#     np.testing.assert_almost_equal(pwfcout.nkstot,274)
#     np.testing.assert_almost_equal(pwfcout.npwx,129)
#     np.testing.assert_almost_equal(pwfcout.nkb,16)
    
#     np.testing.assert_allclose(pwfcout.iatom, iatom)
#     np.testing.assert_allclose(pwfcout.l, l)
#     np.testing.assert_allclose(pwfcout.m, m)

@pytest.fixture(params = [(("tests/models/SrVO3_projwfc.out",), 
                           {"pwxin":PWxIn.from_pwx_input("tests/models/SrVO3_scf.in"), "fermi":5.4014}),
                          ], scope="module")
def projwfcout(request):
    return ProjwfcOut(*request.param[0], pdos_dir = "tests/models", **request.param[1])
    
# TODO: add tests for constructor of ProjwfcOut    

def test_read_projections(projwfcout):
    assert projwfcout.start_projection_block == 227 # the line starts projection block.
    proj = projwfcout.read_projections()
    print(proj)
    
def test_plot_pdos(projwfcout):
    proj = projwfcout.read_projections()
    max_orbs = projwfcout.plot_pdos(savefig = "tests/models/pdos.pdf")
    print(max_orbs)
    print(proj)
    
@pytest.mark.parametrize(["contribution_type", "expected"], [("integral",None), ("max", None)])
def test_sort_orbs_by_band_contribution(projwfcout, contribution_type, expected):
    result = projwfcout.sort_orbs_by_pdos_contribution(energy_range=[-2,4], contribution_type=contribution_type)
    print(projwfcout.orbitals)
    print("contribution to bands in descending order.")
    for i, value in zip(result[0],result[1]):
        print(f"{projwfcout.orbitals[i]} {value}")
        
def test_read_atomic_states(projwfcout):
    # FIXME: make test
    for i in range(projwfcout.natomwfc):
        if i == 0:
            assert [projwfcout.iatom[i], projwfcout.l[i], projwfcout.m[i]] == [1, 0, 1] # 
        print(f"{i} {projwfcout.iatom[i]} {projwfcout.l[i]} {projwfcout.m[i]}")
        
def test_sort_atom_proj(projwfcout):
    projection, indices = projwfcout.sort_atom_proj()
    print(indices[0,0,:]) # at (k=0, ek[iband = 0])
    print(projection[0,0,:])
    
    
    
    