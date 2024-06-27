import os
import math
import numpy as np
from qe_utils.io_file import IOFiles

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
        self.read()
        
    @classmethod
    def from_iofiles(self,iofiles:IOFiles):
        pass
        
    def read(self):
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
                
                #FIXME: the performance of the code below might not be good.
                bands_en = []
                for line in lines[indk*num_line_for_one_k+1:(indk+1)*num_line_for_one_k]:
                    bands_en += [float(value) for value in line.strip("\n").split()]
                self.bands_en[indk] = bands_en 
                
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
        
    def __str__(self):
        print("""
              num_k   :{}
              num_band:{}
              e_min   :{}
              e_max   :{}
              """.format(self.num_k, self.num_band, self.e_min, self.e_max))
        