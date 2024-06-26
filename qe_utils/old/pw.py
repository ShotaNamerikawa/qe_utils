"""
analyze input of pw.x.
"""

import re

class PW:
    """treat information of input of pw.x
    """
    Namelists = ["CONTROL", "SYSTEM", "ELECTRONS", "IONS", "CELL", "FCP", ""]
    
    def __init__(self, *args, **kwargs):
        pass
    
    def read_from_raw(self,input_file):
        """read information from a input-file of QE.

        Parameters
        ----------
        input_file : _type_
            _description_
        """
        with open(input_file) as fp:
            lines = fp.readlines()
            for i, line in enumerate(lines):
                if line.strip("&") in self.Namelists:
                
    def read_from_toml(self,toml):
        pass 
    
    def read_name_list(self,lines):
        
        
    
    def make_input(self, output_file):
        """

        make input data for pw.x

        Parameters
        ----------
        output_file : _type_
            _description_
        """
    
    def check_params(self):
        """check whether parameters in an input file are valid or not.

        Raises
        ------
        NotImplementedError
            _description_
        """
        raise NotImplementedError("check params not implemented")
        
    
class SCF(PW):
    def __init__(self, *args, **kwargs):
        pass
    
class NSCF(PW):
    def __init__(self, *args, **kwargs):
        pass