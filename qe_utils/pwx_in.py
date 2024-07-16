import tomllib
from qe_utils.namelist import NameList
class PWxIn:
    """io for input files of pw.x.
    """
    # TODO: change list of parameter to dict from parameters to thier type, valid value, and defalut value.
    valid_parameters
    
    def __init__(self,parameter_dict,check=True):
        self.parameter_dict = parameter_dict
        if check == True:
            self.check_and_sort_cards()
    
    @classmethod
    def from_toml(cls,toml):
        with open(toml,"rb") as fp:
            parameter_dict = tomllib.load(fp)
        return cls(parameter_dict)
    
    def check_and_sort_cards(self):
        """check card names and order are valid and order is sorted when it is wrong.
        """
        
        
    
    def read(self,input_file):
        """read parameters from an input file.

        Parameters
        ----------
        input_file : str
            input file of pw.x
        """
        namelist = NameList(input_file)
        
        
    def write(self,file):
        #TODO: Since order of parameter_dict must be in specific order, ordereddict must be used.