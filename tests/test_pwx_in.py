from qe_utils.pwx_in import PWxIn

def test_PWxIn():
    pwxin = PWxIn.from_pwx_input("tests/models/scf.in")
    print(set(pwxin.namelist_params["&SYSTEM"]))
    print(pwxin.card_dict)
    print(pwxin.atom_positions)
    
def test_high_sym_kpoints():
    pwxin = PWxIn.from_pwx_input("tests/models/band_nscf.in")
    print(pwxin.high_sym_labels)
    
if __name__ == "__main__":
    test_PWxIn()