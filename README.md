# qe_utils
Provide utilities to treat input & output files of QuantumEspresso.

# Basic Usage

Prepare a toml file named `qe.toml` in the root directory of QE calculations. The content of `qe.toml` is
```toml
[caltype1] #calculation type of QE such as scf, nscf, bands, ..., 
    input  = input-file name of caltype1
    output = output-file name of caltype1
    dir    = directory to execute caltype1 (optional)
[caltype2]
    input  = input-file name of caltype2
    output = output-file name of caltype2
```
(For more details about keys in the toml file, refer to the docstring of the `IOFiles` class in `qe_utils/io_file.py`.)

# Examples

## Make an input script for plotband.x
You can automatically make an input file for `plotband.x` by executing 
```bash
make_plotband_input 
```
in the terminal from the directory where `qe.toml` exists.

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
    dir     = "bands"
    input   = "bands.in"
    output  = "bands.out"
[bandsx]
    dir     = "bands"
    input   = "bandx.in"
    output  = "bandsx.out"
    filband = "bands.dat"
[projwfc]
    dir     = "bands"
    input   = "projwfc.in"
    output  = "projwfc.out"
```
.
### Step2
Execute 
```bash
make_qe_script
```
in the terminal from the directory where `qe.toml` exists.
Then, a file named `qe_script.sh` is created. For the `qe.toml` in step1, the content of 
`qe_script.sh` is
```bash
#!/bin/bash 
ROOTDIR=$(pwd)
pw.x < scf.in > scf.out
if [ ! -d bands ]; then
  # copy outdir of QE to bands for preventing overwriting.
  mkdir bands
  cp -rf ./work bands/
fi 
cd bands
pw.x < bands.in > bands.out
projwfc.x < projwfc.in > projwfc.out
pw.x < bandx.in > bandsx.out
cd $ROOTDIR
make_plotband_input --toml_file qe.toml
cd bands
plotband.x < plotband.in > plotband.out
cd $ROOTDIR
pw.x < nscf.in > nscf.out
```