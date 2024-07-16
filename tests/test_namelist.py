from qe_utils.namelist import NameList
def test_namelist():
    namelist = NameList("tests/models/scf.in")
    print(namelist.namelist)
    
test_namelist()