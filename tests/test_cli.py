import os
from click.testing import CliRunner
from qe_utils.cli.command_script import make_qe_command_script
from qe_utils.cli.write_plotband import make_plotband_input

def test_make_qe_command_script():
    #TODO: make more precise test.
    os.chdir("tests/models")
    runner = CliRunner() 
    result = runner.invoke(make_qe_command_script, ['--qe_script','qe_script.sh',
                                                    '--toml_file', 'qe.toml',
                                                    '--nproc',4])   
    assert result.exit_code == 0
    os.chdir("../..")
    
def test_make_plotband_input():
    #TODO: make more precise test.
    os.chdir("tests/models")
    runner = CliRunner() 
    result = runner.invoke(make_plotband_input, ['--toml_file',"qe.toml", '--nproc',4])   
    assert result.exit_code == 0
    os.chdir("../..")
    
    

    
    
