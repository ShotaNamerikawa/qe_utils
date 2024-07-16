import os
from click.testing import CliRunner
from qe_utils.cli.command_script import make_qe_command_script
from qe_utils.cli.write_plotband import write_plotband

def test_make_qe_command_script():
    #TODO: make more precise test.
    path = "tests/models"
    runner = CliRunner() 
    result = runner.invoke(make_qe_command_script, ['--qe_script',os.path.join(path,'qe_script.sh'),
                                                    '--toml_file',os.path.join(path, "qe.toml"),
                                                    '--nproc',4])   
    
    assert result.exit_code == 0
    
def test_write_plotband():
    #TODO: make more precise test.
    path = "tests/models"
    runner = CliRunner() 
    result = runner.invoke(write_plotband, ['--toml_file',os.path.join(path, "qe.toml"), '--nproc',4])   
    
    assert result.exit_code == 0
    
    

    
    
