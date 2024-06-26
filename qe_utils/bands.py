import os
import math
import numpy as np


class Filband:
    """read data from filband
    """
    def __init__(self, filband_file:str = "bands.out"):
        """_summary_

        Parameters
        ----------
        filband_file : str, optional
            filband in bands.x , by default "bands.out"
        """
        self.filband_file = filband_file
        print("read filband from {}".format(self.filband_file))
        self.read_filband()
        
    def read_filband(self):
        assert os.path.isfile(self.filband_file), "filband file, {} not found".format(self.filband_file)
        with open(self.filband_file) as fp:
            first_line = fp.readline()
            self.num_band = int(first_line.split()[2].strip(","))
            self.num_k = int(first_line.split()[4])
            self.k_list = np.zeros([self.num_k,3])
            self.bands_en = np.zeros([self.num_k,self.num_band])
            num_line_for_one_k = math.ceil(self.num_band/10)+1
            lines = fp.readlines()
            for indk in np.arange(self.num_k):
                self.k_list[indk] = np.array(lines[indk*num_line_for_one_k].strip("\n").split(),dtype=np.float64)
                self.bands_en[indk] = np.array([line.strip("\n").split() for line in 
                                        lines[indk*num_line_for_one_k+1:(indk+1)*num_line_for_one_k]],
                                        dtype=np.float64).ravel()
                
    @property 
    def e_max(self):
        if not hasattr(self, "_e_max"):
            self._e_max = np.max(self.bands_en)
        return self._e_max
    
    @property 
    def e_min(self):
        if not hasattr(self, "_e_min"):
            self._e_min = np.min(self.bands_en)
        return self._e_min
        