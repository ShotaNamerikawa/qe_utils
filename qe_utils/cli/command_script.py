from qe_utils.io_file import IOFiles
import click
import subprocess
import os

NPROC = 22

@click.command()
@click.option('--qe_script',default="qe_script.sh")
@click.option('--toml_file',default="qe.toml", help="toml file containing io file names.")
@click.option('--nproc',default=NPROC, help="the number of process for mpirun.")
def make_qe_command_script(qe_script:str, toml_file:str, nproc:int):
    """make scripts to execute Quantum Espresso commands.
    """
    
    iofiles = IOFiles.from_toml(toml_file, nproc = nproc)
    script_str = "#!/bin/bash \n" + iofiles.make_run_script()
    
    with open(qe_script,"w") as fp:
        fp.writelines(script_str)    
        
        
    
    