from qe_utils.plotband import write_plotband_input
from qe_utils.io_file import IOFiles

def test_plotband():
    path = "tests/models"
    io_dict = dict(scf   = dict(input = "scf.in", output = "scf.out"),
                   nscf  = dict(input = "nscf.in", output = "nscf.out"),
                   bands = dict(input = "bands.in", output = "bands.out"),
                   projwfc = dict(input = "projwfc.in", output =  "projwfc.out"),
                   bandsx = dict(input = "bandsx.in", filband = "bands.dat"),
                   plotband = dict(input = "plotband.in")
                   )
    iofiles = IOFiles(io_dict,root_dir=path)
    write_plotband_input(iofiles)