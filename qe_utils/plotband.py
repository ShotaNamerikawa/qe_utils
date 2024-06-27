"""make input file for plotband
"""
import os 
from qe_utils.pwx_out import PWxOut
from qe_utils.bands import Filband
from qe_utils.io_file import IOFiles
from qe_utils.projwfc import ProjwfcOut
import click

def write_plotband_input(io_files:IOFiles, E_F = None, proj_orbs = None, gnu_file="projbands.gnu", gnu_dat_file = "projbands.gnu.dat", ps_file = "projbands.ps" ,e_delta=5, e_bottom=None, e_top = None):
    #preprocess
    assert "plotband" in io_files.caltype_io, "plotband cannot read from io_files."
    
    filband = Filband(io_files.caltype_io["bandsx"]["filband"])
    
    if E_F is None:
        try:
            for file in [io_files.caltype_io["nscf"]["output"],io_files.caltype_io["scf"]["output"]]: 
                if not os.path.isfile(file):
                    continue
                E_F = PWxOut(file).fermi_energy
                break
            if E_F is None:
                raise FileNotFoundError("Output of both scf and nscf could not be found.")
        except FileNotFoundError as e:
            print(e)
        except Exception:
            print("could not obtain the Fermi energy.")
        
    if proj_orbs is None:
        try:
            natomwfc = ProjwfcOut(io_files.caltype_io["projwfc"]["output"]).natomwfc
            proj_orbs = range(1, natomwfc + 1)
        except FileNotFoundError as e:
            print(e)
        except ValueError as e:
            print(e)
        except Exception:
            print("could not obtain proj_orbs.")
        
    if e_top is None or e_bottom is None:
        if e_top is None:
            e_top = filband.e_max
        if e_bottom is None:
            e_bottom = filband.e_min
            
    #end preprocess
        
    with open(io_files.caltype_io["plotband"]["input"],"w") as fp:
        fp.write(filband.filband_file + "\n") #output of bands.x
        for orb in proj_orbs:
            fp.write("{:d} ".format(orb))
        fp.write("\n")
        fp.write("{}  {} \n".format(e_bottom, e_top))
        fp.write(gnu_dat_file + "\n")
        fp.write(ps_file + "\n")
        fp.write(str(E_F) + "\n") #write Fermi energy.
        fp.write("{}  {} \n".format(e_delta, E_F)) #tick of energy and the top of energy.
        fp.write(gnu_file)
   
