import os
import numpy as np
import re
import tomllib

class ProjwfcIn:  #TODO: make a super class for reading input.
    def __init__(self, input_dict:dict):
        for key, value in input_dict.items(): 
            setattr(self, key, value)
        
    @classmethod
    def from_toml(cls,toml_file, *args, **kwargs):
        with open(toml_file,'rb') as fp:
            toml_dict = tomllib.load(fp)
        cls(toml_dict, *args, **kwargs)
    
    def check_file_compat_with_bandsx(self,bandsxin): 
        """check self.filproj = bandsxin.filband + ".proj"

        Parameters
        ----------
        bandsxin : _type_

        Returns
        -------
        bool
            whether self.filproj = bandsxin.filband + ".proj" or not.
        """
        return self.filproj.replace(".proj","") == bandsxin.filband

class ProjwfcOut:
    """treat information in output files of projwfc.x
    #TODO: test this works for all output files.
    """
    def __init__(self, projwfc_out_file:str, read = True):
        if not os.path.isfile(projwfc_out_file):
            raise FileNotFoundError("projwfc output file, {} is not found.".format(projwfc_out_file))
        self.projwfc_out_file = projwfc_out_file
        if read == True:
            self.read()
        
    def read(self):
        """parse projwfc.out
        """
        with open(self.projwfc_out_file) as fp:
            while True:
                line = fp.readline()
                if not line:
                    break
                if "Problem Sizes" in line:
                    self.read_problem_size(fp)
                if "Atomic states used for projection" in line:
                    self.read_atomic_states(fp) 
                    
    def read_problem_size(self,fp):
        """read Problem Sizes block.

        Parameters
        ----------
        fp : _type_
            _description_
        """
        self.natomwfc = int(fp.readline().split()[2])
        self.nbnd     = int(fp.readline().split()[2])
        self.nkstot   = int(fp.readline().split()[2])
        self.npwx     = int(fp.readline().split()[2])
        self.nkb      = int(fp.readline().split()[2])
                
        
    def read_atomic_states(self,fp):
        """
        read correspondance between states and orbits.
        Parameters
        ----------
        fp : _type_
            _description_
        """
        self.iatom = np.zeros(self.natomwfc,dtype=int)
        
        fp.readline()
        fp.readline()
        for istate in range(self.natomwfc): #istate is state in output file - 1 
            #TODO: check that space in line appears at same position in any case.
            line = fp.readline().split()
            
            self.iatom[istate] = int(line[4])
            self.l[istate] = int(re.search("[0-9\.]+",line[9]).group())
            
            if "m" in line[10]:
                self.m[istate] = int(re.search("[0-9\.]+",line[11]).group())
            
            elif "j" in line[10]:
                self.j[istate] = re.search("[0-9\.]+",line[10]).group()
                self.m_j[istate] = re.search("[-0-9\.]+",line[-1]).group()
                
            else:
                raise NotImplementedError("""reading line of this pattern:
                                          {} 
                                          is not implemented.""".format(line))
                
        
    def read_projection(self, fp):
        """read projectability for each k

        Parameters
        ----------
        fp : _type_
            _description_

        Raises
        ------
        NotImplementedError
            _description_
        """
        raise NotImplementedError("read_projection is not implemented.")
    
    def read_filband(self):
        raise NotImplementedError("read_filband is not implemented.")
    
    @property
    def j(self):
        if not hasattr(self, "_j"):
            self._j = np.zeros(self.natomwfc,dtype=np.float64)
        return self._j
    
    @property 
    def m_j(self):
        if not hasattr(self, "_m_j"):
            self._m_j = np.zeros(self.natomwfc,dtype=np.float64)
        return self._m_j
    
    @property
    def l(self):
        if not hasattr(self, "_l"):
            self._l = np.zeros(self.natomwfc,dtype=int)
        return self._l

    @property 
    def m(self):
        if not hasattr(self, "_m"):
            self._m = np.zeros(self.natomwfc,dtype=int)
        return self._m 
    
    @property
    def spinorb(self):
        return hasattr(self, "_m_j")