import tomllib
import textwrap
import os
import copy
from collections import OrderedDict
from typing import Dict

NestedDict = Dict[str, Dict[str, str]]
NPROC = 22 #TODO :move this to file containing global variables.

class IOFiles:
    """treat all io files in QE.
    
    This class generate a script file to execute QE commands 
    from names of io files.
    
    Structure of self.io_dict
        io_dict = {caltype1: io_information_for_caltype1, caltype2: ..., root_dir(optional):path_to_root_dir}  
        
        and
        
        io_information_for_caltype 
        = {input : input file name, 
           output : output file name, 
           dir(optional) : relative path to directory in which calculation of caltype is executed,
           skip(optional) : boolean, whether caltype calculation will be not executed, by default False. 
           other io files(optional) : names of io files other than input and output}
           
    #TODO: automatically obtain the outdir of pw.x from input files of pw.x such as scf.in.     
    """
    
    order_cal = ["scf", "bands", "projwfc", "bandsx", "plotband", "nscf"] 
    #The fields of this list is in calculation order.
    
    def __init__(self, io_dict:NestedDict, root_dir = None, outdir:str = "./work", nproc:int|None = None, toml_file:str|None = None):
        self.outdir = outdir
        self.root_dir = root_dir
        self.toml_file = toml_file
        self.mpirun_str = "mpirun -n {}".format(nproc) if (nproc != None and nproc > 1) else ""
            
        self.unique_dir = [] #list of directories in which QE commands are executed.
            
            
        self._caltype_io = io_dict
        
        self._reorder_io_dict()
        self._check_skip_caltype()
        self._get_unique_dirs()
              
    @classmethod
    def from_toml(cls,toml_file,**kwargs):
        io_dict = cls._read_toml(toml_file)
        io_dict, root_dir, nproc = cls._read_and_pop_root_dir(io_dict)
        
        for key in ["root_dir", "nproc"]:
            #replace keyword arguments for __init__ if they are given by kwargs and they are not given by a toml file.
            if key in kwargs:
                if eval(f"{key} is not None"):
                    exec(f"{key} = {kwargs[key]}")
                del kwargs[key]
        
        return cls(io_dict, toml_file = toml_file, root_dir = root_dir, nproc = nproc, **kwargs)
        
    def make_run_script(self, caltype_list: list|None = None):
        """make a job script of QuantumEspresso.
        """
        dir_to_which_DFT_copied = copy.deepcopy(self.unique_dir)
        script_str = "" #String representing the content of a job script.
        
        if self.root_dir is not None:
            script_str += "cd {}\n".format(self.root_dir)
        script_str +=  "ROOTDIR=$(pwd) \n" 
        
        
        if caltype_list is None:
            caltype_list = self.non_skip_caltype
        else:
            # check all caltype in caltype_list 
            for caltype in caltype_list:
                assert caltype in self.caltype_io, "{} is not set.".format(caltype)
         
        for i, caltype in enumerate(caltype_list):
            
            input  = self.caltype_io[caltype]["input"]
            output = self.caltype_io[caltype]["output"]
            
            if "plotband" in caltype:            
                if self.toml_file is not None:
                    #If a toml file is given, input of plotband.x is automatically written.
                    script_str += "write_plotband --toml_file {}\n".format(self.toml_file)
            
            if "dir" in self.caltype_io[caltype]:
                # copy output directory of DFT calculations.
                # FIXME: use ln -s instead of cp for calculations only reading the output directory.
                dirname = self.caltype_io[caltype]["dir"]
                if dirname in dir_to_which_DFT_copied:
                    script_str += textwrap.dedent("""\
                                                  if [ ! -d {caldir} ]; then
                                                    # copy outdir of QE to {caldir} for preventing overwriting.
                                                    mkdir {caldir}
                                                    cp -rf {outdir} {caldir}/
                                                  fi \n""".format(caldir = dirname, outdir = self.outdir))
                    dir_to_which_DFT_copied.remove(dirname)
                
                if ("plotband" in caltype or i == 0 or 
                    not self._check_has_same_dir(caltype, caltype_list[caltype_list.index(caltype) -1])):    
                    script_str += "cd {}\n".format(dirname)                  
                
            if ("scf" in caltype) or ("nscf" in caltype) or ("bands" in caltype):
                command = "pw.x"
            elif "projwfc" in caltype:
                command = "projwfc.x"
            elif "bandsx" in caltype:
                command = "bands.x"
            elif "plotband" in caltype:
                command = "plotband.x"
            else:
                raise ValueError("caltype, {} is invalid".format(caltype))
            script_str += "{} {} < {} > {}\n".format(self.mpirun_str, command, input, output) 
                
            if "projwfc" in caltype and "filproj" in self.caltype_io[caltype]:
                # QE add a suffix, "projwfc_up", to filproj and
                # this prevents plotband.x to plot projectability bands
                # Therefore, we remove the suffix.
                script_str += "mv {filproj}.projwfc_up {filproj}\n".format(filproj = self.caltype_io[caltype]["filproj"])
            
            if ("plotband" in caltype or i == len(caltype_list) - 1 or 
                not self._check_has_same_dir(caltype, caltype_list[caltype_list.index(caltype) + 1])):    
                if "dir" in self.caltype_io[caltype]: script_str += "cd $ROOTDIR\n"
                
            #TODO: remove output directories of DFT calculations in the directories 
            #      other than that in the root directory.
        
        return script_str
    
    @classmethod
    def _read_and_pop_root_dir(cls,io_dict):
        """if root_dir is given in io_dict, read the value and delete it.

        Parameters
        ----------
        io_dict : _type_
            _description_
        """
        root_dir = None
        nproc = None
        
        if "root_dir" in io_dict:
            root_dir = io_dict["root_dir"]
            del io_dict["root_dir"]
        if "nproc" in io_dict:
            nproc = io_dict["nproc"]
            del io_dict["nproc"]
            
        return io_dict, root_dir, nproc
            
            
    
    def _reorder_io_dict(self):
        """reorder caltype_io in calculation order.
        """
        caltype_io_true_order = OrderedDict()
        
        for caltype in self.order_cal:
            if caltype in self._caltype_io:
                caltype_io_true_order[caltype] = self._caltype_io[caltype]
                
        self._caltype_io = caltype_io_true_order
        
    def _check_skip_caltype(self):
        self.non_skip_caltype = []
        for caltype, caltype_io in self._caltype_io.items():
            if not "skip" in caltype_io or caltype_io["skip"] != True:
                self.non_skip_caltype.append(caltype)
                
    def _get_unique_dirs(self):
        for caltype_io in self.caltype_io.values():
            if "dir" in caltype_io:
                #FIXME: this is ugly implementation repeating if block for the same condition.
                if not caltype_io["dir"] in self.unique_dir:
                    self.unique_dir.append(caltype_io["dir"])
                
    def get_proper_path(self,caltype:str,iofile:str):
        """join paths of dir and iofiles in self.caltype_io.
        Use this method to obtain value in self.caltype_io
        """
        if caltype in self.caltype_io and iofile in self.caltype_io[caltype]:             
            
            iofile = self.caltype_io[caltype][iofile]
            dir = self.root_dir if self.root_dir is not None else ""

            if "dir" in self.caltype_io[caltype]:
                return os.path.join(dir,self.caltype_io[caltype]["dir"], iofile)
            else:
                return os.path.join(dir, iofile)
        else:
            raise ValueError("caltype or iofile is not in self.caltype_io")

                    
    def _check_has_same_dir(self, caltype1:str, caltype2:str):
        """check directories of different caltypes are the same.

        Parameters
        ----------
        ind_caltype : int
            index of caltype of self.caltype_io
        diff_num : int
            check directory of caltype next door to self.caltype_io[ind_caltype] by diff_num.
        """
        if "dir" in caltype1 and "dir" in caltype2:
            if caltype1["dir"] == caltype2["dir"]: return True
        return False
        
    @property
    def caltype_io(self) -> NestedDict:
        """
        format:
            _caltype_io[caltype] = {"input" = inputfile name of caltype, 
                                    "output" = outputfile name of caltype}
            (e.g. caltype = "scf")
        Returns
        -------
        dict
            dictionary containing input & outputfile name 
        """
        return self._caltype_io
    
    @classmethod
    def _read_toml(cls, toml_file:str):
        """
        format in toml file:
        
        toml```
        root_dir (optional) = root dir name of all calculations.
        [caltype1]
            input  = input-file name of caltype1
            output = output-file name of caltype1
            dir    = directory to execute caltype1 (optional)
        [caltype2]
            input  = input-file name of caltype2
            output = output-file name of caltype2
        ```
            
        For caltypes which give output files other than normal output,
        you can give their file names. For example, you can give a "filband" 
        field to specify the "filband" output from bands.x such as
        
        [bandsx]
            input   = input-file name of bandsx
            output  = output-file name of bandsx
            filband = filband name of bandsx
        ...
        
        Parameters
        ----------
        toml_file : str
            toml file containing information of input and output files in caltype.
        """
        with open(toml_file,'rb') as fp:
            _caltype_io = tomllib.load(fp)
        # TODO: add output field or raise error if they are not given by a toml file.
        return _caltype_io
        
