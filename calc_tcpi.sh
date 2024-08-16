#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N tcpi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=05:00:00
#PBS -lmem=160GB,ncpus=32,jobfs=4000MB
#PBS -W umask=0022
#PBS -joe
#PBS -o /home/547/cxa547/pcmin/logs/tcpi.out.log
#PBS -e /home/547/cxa547/pcmin/logs/tcpi.err.log
#PBS -lstorage=gdata/w85+gdata/rt52+gdata/hh5+scratch/w85

module use /g/data/hh5/public/modules
module load conda/analysis3

export PYTHONPATH=/scratch/w85/cxa547/python/lib/python3.10/site-packages:$PYTHONPATH

cd $HOME/pcmin

python calculate_tcpi.py -c calculate.ini > $HOME/pcmin/logs/calculate_tcpi.stdout 2>&1

