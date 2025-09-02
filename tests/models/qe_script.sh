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
