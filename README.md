# qe_utils
Provide utilities to treat input & output files of QuantumEspresso.

# Examples

## Make a jobscript from a toml file
By using `qe_utils`, you can make a jobscript semi-automatically.

### Step1
Make a toml file named `qe.toml`. For example, the content of `qe.toml` is like
```toml
[scf]
    input   = "scf.in"
    output  = "scf.out"
[nscf]
    input   = "nscf.in"
    output  = "nscf.out"
[plotband]
    dir     = "bands"
    input   = "plotband.in"
    output  = "plotband.out"
[bands]
    dir = "bands"
    input   = "bands.in"
    output  = "bands.out"
[bandsx]
    dir = "bands"
    input   = "bandx.in"
    output  = "bandsx.out"
    filband = "bands.dat"
[projwfc]
    dir     = "bands"
    input   = "projwfc.in"
    output  = "projwfc.out"
```
.
(For more details about keys in the toml file, refer to the docstring of the `IOFiles` class in `qe_utils/io_file.py`.)
### Step2
Execute 
```bash
make_qe_script
```
in a terminal from the directory where `qe.toml` exists.
Then, a file named `qe_script.sh` is created. For the above `qe.toml`, the content of 
`qe_script.sh` is
```bash
#!/bin/bash 
ROOTDIR=$(pwd) 
mpirun -n 22 pw.x < scf.in > scf.out
if [ ! -d bands ]; then
  # copy outdir of QE to bands for preventing overwriting.
  mkdir bands
  cp -rf ./work bands/
fi 
cd bands
mpirun -n 22 pw.x < bands.in > bands.out
cd $ROOTDIR
cd bands
mpirun -n 22 projwfc.x < projwfc.in > projwfc.out
cd $ROOTDIR
cd bands
mpirun -n 22 pw.x < bandx.in > bandsx.out
cd $ROOTDIR
write_plotband --toml_file qe.toml
cd bands
mpirun -n 22 plotband.x < plotband.in > plotband.out
cd $ROOTDIR
mpirun -n 22 pw.x < nscf.in > nscf.out
```