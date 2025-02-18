"""make input files of plotband.x
"""
import os 
from qe_utils.pwx_out import PWxOut
from qe_utils.bands import Filband
from qe_utils.io_file import IOFiles
from qe_utils.projwfc import ProjwfcOut
import click

def write_plotband_input(io_files:IOFiles, E_F = None, proj_orbs = None, gnu_file="projbands.gnu", 
                         gnu_dat_file = "projbands.gnu.dat", ps_file = "projbands.ps", 
                         e_delta=5, e_bottom=None, e_top = None):
    # TODO: create class to store input paramters.
    #preprocess
    assert "plotband" in io_files.caltype_io, "plotband cannot read from io_files."
    assert "bandsx"   in io_files.caltype_io, "io_files does not have information of bands.x"
    assert "filband"  in io_files.caltype_io["bandsx"], "bands.x does not output filband"
    
    filband = Filband(io_files.get_proper_path("bandsx","filband"))
    
    if E_F is None:
        #try to find E_F from nscf.out or scf.out
        try:
            for file in [io_files.get_proper_path("nscf","output"), io_files.get_proper_path("scf","output")]: 
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
        #indices of orbitals projectability to which is calculated.
        try:
            projwfcout = ProjwfcOut(io_files.get_proper_path("projwfc","output"))
            natomwfc = projwfcout.natomwfc
            proj_orbs = range(1, natomwfc + 1)
            if proj_orbs is None:
                raise ValueError()
        except FileNotFoundError as e:
            print(e)
            raise click.ClickException("file is not found.")
        except ValueError as e:
            print(e)
            raise click.ClickException("proj_orbs is None.")
        except Exception:
            raise Exception("proj_orbs is not found.")
        
    if e_top is None or e_bottom is None:
        if e_top is None:
            e_top = filband.e_max
        if e_bottom is None:
            e_bottom = filband.e_min
            
    #end preprocess
        
    with open(io_files.get_proper_path("plotband","input"),"w") as fp:
        fp.write(io_files.caltype_io["bandsx"]["filband"] + "\n") #output of bands.x
        for orb in proj_orbs:
            fp.write("{:d} ".format(orb))
        fp.write("\n")
        fp.write("{}  {} \n".format(e_bottom, e_top))
        fp.write(gnu_dat_file + "\n")
        fp.write(ps_file + "\n")
        fp.write(str(E_F) + "\n") #write Fermi energy.
        fp.write("{}  {} \n".format(e_delta, E_F)) #tick of energy and the top of energy.
        fp.write(gnu_file)
   
