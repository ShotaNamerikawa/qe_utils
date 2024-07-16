import subprocess
import os

class PWxOut:
    """get information from output files of pw.x.
    """
    def __init__(self,pwx_out_file:str):
        if not os.path.isfile(pwx_out_file): 
            raise FileNotFoundError("output of pw.x, {} does not exist.".format(pwx_out_file))
        self.pwx_out_file = pwx_out_file
        
    def read(self):
        raise NotImplementedError("read is not implemented.")
            
    @property
    def fermi_energy(self):
        
        if not hasattr(self,"_fermi_energy"):
            #Use grep command in Linux to obtain fermi energy quickly.
            completedprocess = subprocess.run(["grep",  "Fermi", self.pwx_out_file], capture_output=True)
            if completedprocess.returncode != 0:
                raise ValueError("error when reading the Fermi energy.")
            self._fermi_energy = float(completedprocess.stdout.split()[4])
            
        return self._fermi_energy    
        
            