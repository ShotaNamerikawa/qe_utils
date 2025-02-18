"""projwfc

This module contains classes to treat input and output of projwfc.x commands

Especially, Projwfc class is useful to get information of projected dos and 
intuition about initial guess of Wannierization.
"""

import os
import numpy as np
import scipy.integrate as integrate
import re
import tomllib
import itertools
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Iterable, Callable

from qe_utils.pwx_in import PWxIn

class ProjwfcIn:  #TODO: make a super class for reading input.
    """parse projwfc.x input files.
    """
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
    
    Attributes
    ----------
    nkstot: int
        the total number of k points for all spins
    """
    def __init__(self, projwfc_out_file:str, pdos_dir = "./",
                 fermi:float|None = None,
                 pwxin:PWxIn|None = None,
                 nproc:int|None = int,
                 ):
        self.fermi = fermi
        self.pwxin = pwxin
        if not os.path.isfile(projwfc_out_file):
            raise FileNotFoundError("projwfc output file, {} is not found.".format(projwfc_out_file))
        self.projwfc_out_file = projwfc_out_file
        self.pdos_dir = pdos_dir
        
        self.proj_read = False
        
        self._read()
        self.get_pdos_files()
        self.get_relation_orbital_vs_pdosfile()
        # TODO: add methods to check collinear
        self.non_collin = False
        
    @property
    def fermi(self):
        return self._fermi
    
    @fermi.setter
    def fermi(self, fermi:float|None):
        if not fermi:
            self._fermi = 0
        else:
            self._fermi = fermi
            
    @property
    def orbitals(self)->list[str]:
        """string representing orbitals of pdos easy to read
        NOTE: the order is corresponding to that of files read from a directory.
        """
        return self._orbitals
    
    @orbitals.setter
    def orbitals(self, orbitals):
        self._orbitals = orbitals
        
    @property
    def nk(self):
        return self._nk
    
    @nk.setter
    def nk(self, nkstot:int):
        """since nkstot = 2*total_k, it is divided by 2.
        """
        self._nk = int(nkstot/2)
        
    def _read(self):
        """parse the output of projwfc.x
        
        FIXME: judge block from line may be ugly. 
        """
        with open(self.projwfc_out_file) as fp:
            for line_index, line in enumerate(fp):
                if "Problem Sizes" in line:
                    self.read_problem_size(fp)
                if "Atomic states used for projection" in line:
                    # self.projection_block_line is the index of line where "k = ..." first appears in the file.
                    self.start_projection_block = line_index + self.natomwfc + 9 # 5 for problem size and 4 for additional lines
                    self.read_atomic_states(fp)
                # TODO: read Lowdin Charges
                    
    def read_problem_size(self,fp):
        """read Problem Sizes block.

        Parameters
        ----------
        fp : _type_
            _description_
        """
        self.natomwfc = int(fp.readline().split()[2])
        self.nbnd     = int(fp.readline().split()[2])
        self.nkstot   = int(fp.readline().split()[2]) # the total number of kpoints for all kpoints.
        self.npwx     = int(fp.readline().split()[2])
        self.nkb      = int(fp.readline().split()[2])
        
        self.nk = self.nkstot # automatically divided by 2. See the setter of nk
                
    def read_atomic_states(self,fp):
        """ read correspondance between states and orbits.
        
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
            
            self.iatom[istate] = int(line[4]) - 1 # Fortran index to python index
            self.l[istate] = int(re.search(r"[0-9\.]+",line[9]).group())
            
            if "m" in line[10]:
                self.m[istate] = int(re.search(r"[0-9\.]+",line[11]).group())
            
            elif "j" in line[10]: # NOTE: soc can be checked from this.
                self.j[istate] = re.search(r"[0-9\.]+",line[10]).group()
                self.m_j[istate] = re.search(r"[-0-9\.]+",line[-1]).group()
                
            else:
                raise NotImplementedError("""reading line of this pattern:
                                          {} 
                                          is not implemented.""".format(line))
                
    def read_projections(self):
        """read projections.
        This method must be executed once to obtain the projections of bands.
        """
        if not self.proj_read:
            with open(self.projwfc_out_file) as fp:
                self._read_projections(fp, self.start_projection_block)
        return self.proj
        
    def _read_projections(self, fp, start_index:int|None = None):
        """read projectability for each k and e(k).
        
        NOTE: by fp.readline()
        
        This method first read a block containing the projectability of bands at a k point.
        Then each k block are read in more detail and the projectability of each k point
        are obtained in multiprocess calculations.
        
        
        
        projwfc.x also outputs the energy at k points but it is NOT read for improving performance.
        

        Parameters
        ----------
        fp : _type_
            _description_
        """
        # skip already read lines. 
        if start_index:
            tmp_fp = itertools.islice(fp, self.start_projection_block, None)
        else:
            tmp_fp = fp
        self.k = np.zeros([self.nk, 3])
        self.ek = np.zeros([self.nk, self.nbnd])
        self.proj = np.zeros([self.nk, self.nbnd, self.natomwfc])
        kblocks = self._get_kblocks(tmp_fp)
        for ik, kblock in enumerate(kblocks): # TODO: execute parallel calculation.
            try:
                self.k[ik], self.ek[ik], self.proj[ik] = self._get_projectability_at_a_kpoint(kblock)
            except:
                raise Exception(f"ik:{ik}, kblocks:{kblock[0]}")
        self.proj_read = True

    def _get_kblocks(self, fp):
        """get lines containing projectability for each kpoint.
        
        This is a generator of k blocks to reduce memory consumption.

        Parameters
        ----------
        fp : _type_
            file pointer.
        """
        self.k = np.zeros([self.nk,3])
        ik = 0
        inside_block = False
        for line in fp:
            if line in "Lowdin Charges:":
                break
            if not inside_block and "k = " in line:
                ik += 1
                inside_block = True
                block_lines = []  # 新しいブロックの開始
            elif "k = " in line:
                inside_block = False
                yield block_lines # for true calculation.
            if inside_block:
                block_lines.append(line)
      
    def _get_projectability_at_a_kpoint(self, kblock_lines:list[str]):
        """read the projectability of the bands at each k block.

        Parameters
        ----------
        kblock_lines : list[str]
            lines of the block at a k point including projectability of each line.
        ik : int
            the index of the k point.
            
        Returns
        -------
        NDArray :
            the projectability of bands at a kpoint 
        """
        iline = 0 # the first line is " k = ..." and it is neglected.
        ibnd = 0
        proj_per_k = np.zeros([self.nbnd, self.natomwfc]) # projectability of bands at a kpoint.
        energy_per_k = np.zeros([self.nbnd])

        match = re.search(r"k *= *(-*[0-9\.]+) +(-*[0-9\.]+) +(-*[0-9\.]+)", kblock_lines[iline])
        
        k = np.array([float(match.group(i+1)) for i in range(3)])
        while True:
            # an iteration of this while block is for a band.
            iline += 1
            # ==== e( number) = energy eV ==== line
            match = re.search(r"==== e\( *([0-9]+)\) = *(-*[\.0-9]+) eV ====", kblock_lines[iline]) # "==== e\( *([0-9]+)\) = *(-*[\.0-9]+) eV ===="
            energy_per_k[int(match.group(1))-1] = float(match.group(2))
            
            # the first line of projection includes " *psi *= *", and it is removed here.
            kblock_lines[iline+1] = re.sub(r"^ *psi *= *","", kblock_lines[iline+1])
            
            while True:
                # This block is for from a line just below # "==== e( number) = energy eV ==== " to "|psi|^2 = .*"
                iline += 1
                if "|psi|^2" in kblock_lines[iline]:
                    break
                # NOTE: the format in the output of projwfc.x is 
                #       "projectability*[#the index of a pseudo atomic orbital]+projectability*[#the index of a pseudo atomic orbital]"
                #       re.sub convert this into [projectability, the orbital index, projectability, the orbital index, ...]
                line = re.sub(r"\*\[# *|\]"," ", kblock_lines[iline]).split()
                proj_per_k[ibnd,[int(val) - 1 for val in line[1::2]]] = [float(val) for val in line[0::2]] 
                # int(val) - 1 is due to Fortran count.
            if iline == len(kblock_lines) - 2: # the last |psi|^2 appears at len(kblock_lines) - 2
                # reach the last line.
                break
            ibnd += 1 # the end of a band block.
            
        return k, energy_per_k, proj_per_k
                
    def get_relation_orbital_vs_pdosfile(self):
        """get the correspondence between orbitals and pdos file names.
        
        NOTE: File name extension of projwfc.x@qe-v7.3.1 is decided in PP/src/partialdos.f90:partialdos

        Parameters
        ----------
        pwxin : PWxIn
            PWxIn corresponding to outdir/prefix in the input of projwfc.x
        """
        self.orbitals:list[tuple[str,Iterable|int,str]] = []
        for name in self.pdos_files:
            match = re.search(r".*atm#([0-9]+)\((.*)\).*#([0-9]+\([spd]\))", name)
            atom_num = int(match.group(1))
            # the index of the file -> (element, position or atom index, angular momentum (for no soc))
            self.orbitals.append((match.group(1), 
                                          self.pwxin.atom_positions[atom_num - 1] if self.pwxin else atom_num,
                                          match.group(3)))
        # For plot label
        if self.pwxin:
            self.pdos_labels = [f"{orbital[1][0]}_{str(orbital[1][1][0])}_{str(orbital[1][1][1])}_{str(orbital[1][1][2])}_{orbital[2]}" for orbital in self.orbitals]
        else:
            self.pdos_labels = self.pdos_files
                
    def get_pdos_files(self):
        """get pdos files from a directory.
        
        Execute this method after the "read" method.

        """
        print("warning: soc case is not implemented.")
        self.atom_indices = []
        self.atom_names = []
        self.wfc_indices = []
        self.angular = []
        self.pdos_files = []
        for file in os.listdir(self.pdos_dir):
            match = re.search(r"\.pdos_atm#([0-9]+)\((.*)\)_wfc#([0-9]+)\((.*)\)", file)
            # match.group[0] = atom index [1] = atom_name 
            if not match: continue
            self.atom_indices.append(match.group(1))
            self.atom_names.append(match.group(2))
            self.wfc_indices.append(match.group(3))
            self.angular.append(match.group(4))
            self.pdos_files.append(file) 
            
    def plot_pdos(self, 
                  savefig:str|None = None, 
                  show_plt:bool = False, 
                  show_legend:bool = True,
                  xlim:list|None = [-5,5]
                  ):
        """plot projected dos.

        Parameters
        ----------
        savefig : str | None, optional
            save the output figure to a file, by default None
        show_plt : bool, optional
            whether execute plt.show(), by default False
        show_legend : bool, optional
            whether ax.legend() is exeucted, 
            If too many orbitals are plotted, legend is NOT shown
            even though this parameter is True, by default False
        xlim : list | None, optional
            xlim of the figure, by default [-5,5]
        """
        # TODO: return correspondence between label colors and orbitals.
        if not hasattr(self, "file_names"): self.get_pdos_files()
        fig, ax = plt.subplots()
        for i, (file, label) in enumerate(zip(self.pdos_files, self.pdos_labels)):
            data = np.loadtxt(str(Path(self.pdos_dir)/file))
            ax.plot(data[:,0] - self.fermi, data[:,1], label= label) # FIXME: this does not work in general condition.
        ax.set_xlabel("energy")
        ax.set_ylabel("pdos")
        if xlim: ax.set_xlim(xlim)
        if show_legend and len(self.pdos_labels) < 6: 
            # FIXME: if too many orbitals are given, the legend is too difficult to see.
            ax.legend() 
        if savefig:
            plt.savefig(savefig)
        if show_plt: plt.show()
    
    def sort_orbs_by_pdos_contribution(self, 
                                       energy_range:list|None = None, 
                                       contribution_type:str|Callable = "max"):
        """sort orbitals by contributions to the projected dos in the selected energy range.
        
        Contribution types are
            "max": The max value of the pdos of orbitals
            # TODO: calculate pdos integral value to judge contribution
        You can also pass a user-defined function to contribution_type;
            func(dos_in_energy_range)-> float value
        to sort orbitals. Be carful that the larger an orbital contributes to bands,
        the larger returned value of func is.

        Parameters
        ----------
        energy_range : list
            sort orbitals according to contribution to bands in this range.
            The zero point of energy is the Fermi energy of the system if it is given in the contstructor.
        contribution_type : str | function, optional
            the type to judge how orbitals contribute to bands, by default "max"
        
        Returns
        -------
        tuple[np.array,np.array]
            order of orbitals and contribution value of them
        """
        orb_contribution = np.zeros(len(self.pdos_files))
        initial_data = np.loadtxt(str(Path(self.pdos_dir)/self.pdos_files[0]))
        
        # get index corresponding to energy_range
        if energy_range:
            index = np.where((energy_range[0] <= (initial_data[:,0] - self.fermi)) & ((initial_data[:,0] - self.fermi) <= energy_range[1]))[0]
        else:
            index = np.ones(initial_data[:,0].shape[0], dtype = bool)
        energy_points = initial_data[index,0]
        
        # get function to evaluate contribution of each orbital from 
        if callable(contribution_type):
            contribution_func = contribution_type
        elif contribution_type == "max":
            contribution_func = np.max
        elif contribution_type == "integral":
            contribution_func = lambda dos: integrate.simpson(dos, 
                                                              x = energy_points,
                                                              dx = energy_points[1] - energy_points[0])
            
        # evaluate orbital contributions from projected dos in selected energy range.
        for i, file in enumerate(self.pdos_files):
            data = np.loadtxt(str(Path(self.pdos_dir)/file))
            # TODO: check the pdos format of QE to judge whether the line below is valid in any case.
            orb_contribution[i] = contribution_func(data[index,1]) # NOTE: ldos is used for contribution evaluation.
            
        orb_order = np.argsort(orb_contribution)[::-1] # orb_order[0] maximally contributes the bands
        return orb_order, orb_contribution[orb_order]
        
    def convert_label(self):
        raise NotImplementedError
    
    def read_filband(self):
        raise NotImplementedError("read_filband is not implemented.")
    
    def get_projections(self, kpoints:list[int]|None = None, bands:list[int]|None = None, atomwfcs:list[int]|None = None):
        """get projections based on k points, bands and orbitals.
        
        Returns
        -------
        NDArray
            projections whose shape is (num_kpoints, num_bands, num_natomorbs)
        """
        if not kpoints:
            kpoints = np.arange(self.nk)
        if not bands:
            bands = np.arange(self.nbnd)
        if not atomwfcs:
            atomwfcs = np.arange(self.natomwfc)
        return self.proj[kpoints[:,None,None], bands[None,:,None], atomwfcs[None,None,:]]
            
    def sort_atom_proj(self, **get_projections_kwargs):
        """sort projection value for atomwfc at each (k,e(k))
        
        NOTE: indices is that in the outputs of projwfc.x - 1.

        Returns
        -------
        tuple[NDArray]
            sorted_value and index for atomic wave functions.
        """
        selected_proj = self.get_projections(**get_projections_kwargs) if get_projections_kwargs else self.proj
        sorted_indices = np.argsort(selected_proj, axis = 2)[:,:,::-1] # from large value to small
        return np.take_along_axis(selected_proj, sorted_indices, axis=2), sorted_indices
    
    def get_zero_projections(self, **get_projections_kwargs):
        """get indices of orbitals whose projections to bands are zero.

        Returns
        -------
        _type_
            _description_
        """
        selected_proj = self.get_projections(**get_projections_kwargs) if get_projections_kwargs else self.proj
        return np.where(selected_proj == 0)
    
    def extract_atom_bands(self, ik, istates, threshold:float = 0.1):
        """extract band indices atomic wave function projectability exceed threshold.
        
        Parameters
        ----------
        ik : _type_
            _description_
        istates : bool
            _description_

        Returns
        -------
        _type_
            _description_
        """
        bands = [[] for i in range(istates)]
        for istate in istates:
            # FIXME: for loop can be removed using numpy functions?
            bands[istate] = np.where(self.proj[ik,:, istate] > threshold)
        return bands
    
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
    def soc(self):
        return hasattr(self, "_m_j")
    