import click
import numpy as np
import itertools

from qe_utils.projwfc import ProjwfcOut
from qe_utils.pwx_in import PWxIn
    
@click.group()
@click.argument("projwfc_out")
@click.argument("pw_in")
@click.option("--fermi", help="the value of Fermi energy. If given, energy relative to the value is shown.")
@click.option("--pdos_dir", default="./", help="the directory where the pdos files are stored.")
@click.pass_context
def projwfc(ctx, projwfc_out:str, pw_in:str, fermi, pdos_dir):
    """get information from the output of projwfc.x
    
      PROJWFC_OUT is the output file of projwfc.x\n
      PW_IN is the input file of pw.x corresponding to the input of projwfc.x
    """
    if type(fermi) == str:
        fermi = float(fermi)
    pwxin = PWxIn.from_pwx_input(pw_in)
    ctx.obj = ProjwfcOut(projwfc_out, pdos_dir = pdos_dir if pdos_dir else "./", fermi = fermi, pwxin = pwxin)

@projwfc.command()
@click.pass_context
def kpoints(ctx):
    """show all kpoints
    """
    ctx.obj.read_projections()
    print("ik, kpoints")
    for ik, k in enumerate(ctx.obj.k):
        print(f"{ik} {k}")

@projwfc.command()
@click.pass_context
def states(ctx):
    """show relation between the pseudo-orbital index and its atomic center and quantum angular momentum numbers.
    """
    if ctx.obj.soc: NotImplementedError("soc case is not implemented.")
    print("pso index: atom, position, azimuthal, magnetic")
    for i, (iatom, l, m) in enumerate(zip(ctx.obj.iatom, ctx.obj.l, ctx.obj.m)):
        atom = ctx.obj.pwxin.atom_positions[iatom][0]
        x,y,z = ctx.obj.pwxin.atom_positions[iatom][1]
        print(f"{i:3d}: {atom:2s} {x:.3f} {y:.3f} {z:.3f} {l} {m}")
    
    
@projwfc.command()
@click.option("--bands", help = "band indices.")
@click.option("--kpoints", help="coordinates of the kpoint")
@click.option("--atomwfcs", help="the indices of atomic wave functions for which the projections are shown")
@click.option("--threshold", help = "threshold of projection to be printed.", type = float)
@click.pass_context
def projections(ctx, kpoints, bands, atomwfcs, threshold:float = 0):
    """print projection value of each orbital at band energies
    
    There are two formats for the `atomwfcs` option.
    The formats of the option are:
        1. "index1, index2, ..., indexn"
        2. "start:stop:[step]"
    """
    ctx.obj.read_projections()
    inputs = [kpoints, bands, atomwfcs]
    num_for_k_band_wfc = [ctx.obj.nk, ctx.obj.nbnd, ctx.obj.natomwfc]
    inputs = [convert_to_array(ipt) if ipt else np.arange(ntot) for ipt, ntot in zip(inputs, num_for_k_band_wfc)]
    print("# k-index, band-index, wfc-index, energy, projection")
    for ik, ibnd, iwf in itertools.product(*inputs):
        ek = ctx.obj.ek[ik,ibnd]
        proj_value = ctx.obj.proj[ik,ibnd,iwf]
        if proj_value > threshold:
            print(f"{ik:3d} {ibnd:3d} {iwf:3d}  {ek:+9.5f} {proj_value:.3f}")
    
def convert_to_array(string:str):
    if ":" in string:
        return np.arange(*[int(num) for num in string.split(":")])
    else:
        return np.array([int(num) for num in string.split()])
    
@projwfc.command()
@click.option("--emin",type = float, help="the bottom of energy range")
@click.option("--emax",type = float, help="the top of energy range")
@click.option("--evaluation",default = "integral", 
              help="""type of how to evaluate contribution of orbitals from pdos.
              2 types of options are available (by default, integral):
                max: the maximum value of pdos in selected energy range
                integral: integral of projected dos in selected energy range""")
@click.pass_context
def sort_orbs(ctx, emin:float, emax:float, evaluation:str):
    """sort orbitals according to their contributions to bands in selected energy range.
    
    "the name of the output file of projwfc.x"
    "the name of the input file of pw.x corresponding to the input of projwfc.x"
    """
    if not emin or not emax:
        energy_range = None
    else:
        energy_range = [emin, emax]
        print("energy range is {emin}:{emax}")
    projout = ctx.obj
    result = projout.sort_orbs_by_pdos_contribution(energy_range=energy_range, contribution_type= evaluation)
    for i, value in zip(result[0],result[1]):
        print(f"{projout.orbitals[i]} {value}")
                
if __name__ == "__main__":
    projwfc()
    