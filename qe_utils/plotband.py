"""make input file for plotband
"""

def write_plotband_info(file_name,E_F,proj_orbs = None, fil_band = "bands.out",gnu_file="projbands.gnu",e_delta=5,e_bottom=None, e_top = None):
    with open(file_name,"w") as fp:
        fp.write(fil_band) #output of bands.x
        if proj_orbs is None:
            fp.write("{} ".format())
        else:
            for orb in proj_orbs:
                fp.write("{:d} ".format(orb))
        fp.write()
        fp.write(str(E_F)) #write Fermi energy.
        fp.write("{}  {}".format(e_delta, E_F)) #tick of energy and the top of energy.
        fp.write(gnu_file)
        fp.write()
    
    