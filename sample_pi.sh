#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N samplepi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=12:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -o /home/547/cxa547/pcmin/logs/samplepi.out.log
#PBS -e /home/547/cxa547/pcmin/logs/samplepi.err.log
#PBS -lstorage=gdata/w85+scratch/w85

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load geos
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$HOME/pcmin:$HOME/tcrm:$HOME/tcrm/Utilities
# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2

cd $HOME/pcmin

python3 $HOME/pcmin/sample.py -c $HOME/pcmin/sample.ini > $HOME/pcmin/logs/sample_pi.stdout 2>&1
#python3 $HOME/pcmin/sample_tcha.py -c $HOME/pcmin/sample_tcha.ini > $HOME/pcmin/logs/sample_tcha.stdout 2>&1
