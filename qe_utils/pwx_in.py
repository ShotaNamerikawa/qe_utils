import tomllib
import re
import numpy as np
from collections import OrderedDict
from importlib import resources
from qe_utils.namelist import NameList
from typing import Dict, Any

class PWxIn:
    """parse and write pw.x files.
    
    
    Attributes
    ----------
        namelist_dict:OrderedDict
            dictionaries whose keys are the name converted to upper case 
            in name_list of pw.x inputs and the values are dictionaries.
            The value dictionaries represent; paramter_name -> parameter_value
            
            
        card_dict:OrderedDict
            dictionaries; card name converted to upper case -> dict(options = the value of option, body = the string in the card section)
            
        name_params: OrderedDict
            class instance whose keys are parameter names and values are the type of the parameters.
            the parameters in the Namelist sections.
            
        card_params: OrderedDict
            class instance whose keys are parameter names and values are the type of the parameters.
            the parameters in the card sections.
    """
    # TODO: change list of parameter to dict from parameters to their type, valid value, and defalut value.
    @classmethod
    def get_name_card_paras(cls):
        """
        obtain parameters in namelists and cards.
        
        # NOTE: should this method to moved to another class?
        """
        resource_path = resources.files("qe_utils") / "data/QE_INPUT_PW.toml"
        with resource_path.open('rb') as file:
            name_card_dict = tomllib.load(file)
            
        cls.namelist_params = OrderedDict()
        cls.card_params = OrderedDict()
        
        #FIXME: parameter strings such as "A, B, C, cosAB, cosAC, cosBC" must be divided.
        for key in name_card_dict:
            if "&" in key:
                # assumes string of namelist starts with &
                cls.namelist_params[key] = name_card_dict[key]
            else:
                cls.card_params[key] = name_card_dict[key]   
                    
    def __init__(self,namelist_dict:Dict[str,Dict],card_dict:Dict[str,Any], check=True):
        if not hasattr(self, "namelist_params"):
            self.get_name_card_paras()
        self.namelist_dict:Dict[str,Dict] = namelist_dict
        self.card_dict = card_dict
        self._high_sym_labels:list[tuple] = None 
        if check == True:
            self.check_and_sort_namelists()        
            
    @classmethod
    def from_pwx_input(cls, pwx_input):
        """read data of a pw.x input file

        Parameters
        ----------
        pwx_input : str|Path
            string or Path of a pw.x input file.
        """
        cls.get_name_card_paras()
        parameter_dict, card_dict = cls.read_from_pwx_input(pwx_input)
        return cls(parameter_dict, card_dict)
        
    @classmethod
    def from_toml(cls, toml:str, check:bool = True):
        """read from a toml file in which pw.x inputs are written.

        Parameters
        ----------
        toml : str
            the name of a toml file
        check : bool, optional
            _description_, by default True

        Returns
        -------
        _type_
            _description_
        """
        with open(toml,"rb") as fp:
            parameter_dict = tomllib.load(fp)
        return cls(parameter_dict, check = check)
    
    @property
    def calculation(self):
        return self.namelist_dict["&CONTROL"]["calculation"].strip("\'")
    
    @property
    def atom_positions(self):
        """the position of atoms
        """
        return [(pos_str[0], np.array([float(pos_str[1]), float(pos_str[2]), float(pos_str[3])]) ) for pos_str in self.card_dict["ATOMIC_POSITIONS"]["body"]]
    
    @property
    def high_sym_labels(self):
        """return the labels of high symmetry kpoints
        
        Returns
        -------
        list
            [("the name of high symmetry kpoints", the position of the kpoint) for i in range(num_high_sym_kpoints)]
        """

        if not self._high_sym_labels:
            self.get_high_sym_labels()
        return self._high_sym_labels
    
    def get_high_sym_labels(self):
        if not "bands" in self.calculation:
            raise ValueError("the input is not for band calculations.")
        self._high_sym_labels = []    
        # skip the first line corresponding to the total number of high symmetry kpoints
        for line in self.card_dict["K_POINTS"]["body"][1:]: 
            # the name of kpoints, the position of it, the number of kpoints between interval.
            self._high_sym_labels.append((line[-1], [float(line[i]) for i in range(3)], int(line[3])))
    
    def check_and_sort_namelists(self):
        """check whether namelist names and order are valid
        
        Order is sorted when it is wrong.
        """
        valid_namelists = self.namelist_params.keys()  
        for namelist in self.namelist_dict: 
            # convert non-uppercase namelist to uppercase.
            if namelist.upper() != namelist:
                self.namelist_dict[namelist.upper()] = self.namelist_dict.pop(namelist)
                namelist = namelist.upper()
            
            if not namelist.upper() in valid_namelists: # valid_namelist is upper case.
                raise ValueError(f"invalid card {namelist} is included in parameter_dict.")
            
            #TODO: implement code to reorder parameter_dict in correct order.
            
            input_parameters = set(self.namelist_dict[namelist])
            valid_parameters = set(self.namelist_params[namelist.upper()])
            # TODO: make judging input parameters is proper works correctly!
            # if not input_parameters <= valid_parameters:
            #     non_valid = input_parameters - (input_parameters & valid_parameters)
            #     raise ValueError("parameter(s) {} in {} is(are) not valid".format(non_valid, namelist))

            for parameter in self.namelist_dict[namelist]:
                if "type" in self.namelist_dict[namelist][parameter]:
                    try:
                        converted_type = self.convert_QE_INPUT_types(self.namelist_dict[namelist][parameter]["type"])
                        parameter_value = self.namelist_dict[namelist][parameter]
                        if converted_type == float:
                            # convert Fortran float into Python float.
                            parameter_value = parameter_value.replace("d","e") 
                        converted_type(parameter_value)
                    except:
                        raise ValueError("{} cannot converted into {}".format(self.namelist_dict[namelist][parameter], converted_type))     
            
    def check_syntax(self,card):
        """check syntax of cards

        Parameters
        ----------
        card : str
            names of cards.
        """
        if card == "ATOMIC_SPECIES":
            self.check_atomicspicies_syntax()
        else:
            # not implemented cards are skipped.
            pass
            
    def check_atomicspicies_syntax(self):
        """check atomic species section is in the proper format.

        Raises
        ------
        KeyError
            _description_
        ValueError
            _description_
        """
        params = self.card_dict["ATOMIC_SPECIES"] 
        cards_option = params["options"]
        if cards_option == "automatic":
            pass            
        elif cards_option == "gamma":
            pass
        else:
            if not "nks" in cards_option:
                raise KeyError("nks is not found.")
            try:
                converted_type = self.convert_QE_INPUT_types(params["nks"]["type"])
                parameter_value = converted_type(self.card_params["ATOMIC_SPECIES"]["nks"])
            except:
                raise ValueError("value of nks {} cannot be converted into {}".format(parameter_value, converted_type))
            species = np.array(params["body"])
            for i, eltype in enumerate([str, float, str]): # element, mass, pseudo potentials
                try:
                    species[:,i].astype(eltype)
                except:
                    print("{} th line of ATOMIC_SPECIES has invalid-type elements.")
                    
    def convert_QE_INPUT_types(self,typename)->type:
        """convert Fortran types to python types.

        Parameters
        ----------
        typename : str
            the name of types in Fortran.

        Returns
        -------
        type
            the python type
        """
        if typename == "CHARACTER":
            return str
        elif typename == "LOGICAL":
            return bool
        elif typename == "INTEGER":
            return int
        elif typename == "REAL":
            return float   
    
    @classmethod
    def read_from_pwx_input(cls,input_file):
        """read parameters from an input file of pw.x.

        Parameters
        ----------
        input_file : str
            input file of pw.x
        """
        namelist = NameList(input_file)
        # TODO: make additional_lines to dict
        card_dict = cls.parse_card_string( namelist.non_namelist_lines)# After implment convert-to-dict method. remove this.
        return namelist.namelist, card_dict
    
    @classmethod
    def parse_card_string(cls, card_string:str):
        """parse a string containing card sections.

        Parameters
        ----------
        card_string : str
            string containing card sections.
            
        Returns
        -------
        dict
            dict containing parsed data 
            the keys of the dict are card names and the values are dictionaries 
            whose keys are
            - body: the body part of card.
            - options: the option in {} next to the card name.
        """
        card_lines = card_string
        cards_dict = OrderedDict()
        iscard = False
        
        for line in card_lines:
            line = line.strip()
            for valid_card in cls.card_params:
                if valid_card in line:
                    # start of card
                    read_card = valid_card
                    iscard = True
                    cards_dict[read_card] = OrderedDict()
                    cards_dict[read_card]["body"] = []
                    first_line_of_card = line.split()
                    if len(first_line_of_card) > 1:
                        cards_dict[read_card]["options"] = first_line_of_card[1]
                    break
            if iscard is True:
                iscard = False
            elif line: # blank line is skipped.
                cards_dict[read_card]["body"].append([var for var in line.split()])
             
        return cards_dict
        
    def change_parameter(self,parameter_dict:dict):
        """change parameters in namelist.

        Parameters
        ----------
        parameter_dict : dict
            _description_
        """
        self.namelist_dict.update(parameter_dict)        
        
    def write_to_file(self,file):
        """write input parameters to a file which can be an argument of pw.x

        Parameters
        ----------
        file : str|Path
            the name of an output file.
        """
        with open(file,"w") as fp:
            for namelist in self.namelist_dict:
                fp.write(namelist + "\n")
                for key,value in self.namelist_dict[namelist].items():
                    fp.write("{} = {}\n".format(key,value))
                fp.write("/")
                
            for card in self.card_dict:
                fp.write(card + "\n")
                for non_array in self.card_dict[card].keys():
                    fp.write("{}\n".format(self.card_dict[card][non_array]))
                fp.write(self.card_dict[card]["body"])
                fp.write("\n")
                
    def write_array(self,Array,fp):
        """write array part in cards.
        
        Parameters
        ----------
        array : string
            _description_
        fp : _type_
            file pointer
        """
        for line in Array:
            line_str = ""
            for value in line:
                line_str += f"{value} "
            line_str = line_str.strip()
            fp.write(f"{line_str}\n")
            
                
                