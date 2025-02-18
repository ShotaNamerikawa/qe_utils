import click
from qe_utils.io_file import IOFiles
from qe_utils.plotband import write_plotband_input

NPROC = 22

@click.command()
@click.option('--toml_file',default="qe.toml")
@click.option('--nproc', default=NPROC)
@click.option('--natomwfc', default=None)
@click.option('--fermi_energy', type = float)
def make_plotband_input(toml_file:str, nproc = NPROC, natomwfc = None, fermi_energy = None):
    """write input of plotband.x.

    Parameters
    ----------
    toml_file : str
        toml file including names of input and output files.
    nproc : int, optional
        the option parameter of mpirun -n, by default NPROC
    """
    io_files = IOFiles.from_toml(toml_file, nproc = nproc)
    if natomwfc is not None:
        proj_orbs = range(1, int(natomwfc) + 1)
    else: proj_orbs = None
    write_plotband_input(io_files, proj_orbs= proj_orbs, E_F = fermi_energy)
