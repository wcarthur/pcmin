#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N calcpi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=05:00:00
#PBS -lmem=128GB,ncpus=32,jobfs=4000MB
#PBS -W umask=0022
#PBS -v NJOBS,NJOB,YEAR
#PBS -joe
#PBS -lstorage=gdata/w85+gdata/rt52+scratch/w85

# Run this with the following command line:
#
# qsub -v NJOBS=42,YEAR=1979 calc_pi.sh
#
# This will run the process for 42 years, starting 1979

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load openmpi
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$HOME/pcmin
# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2
umask 0022

ECHO=/bin/echo

if [ X$NJOBS == X ]; then
    $ECHO "NJOBS (total number of jobs in sequence) is not set - defaulting to 1"
    export NJOBS=1
else
    if [ X$NJOB == X ]; then
    $ECHO "NJOBS set to $NJOBS"
    fi 
fi
  
if [ X$NJOB == X ]; then
    $ECHO "NJOB (current job number in sequence) is not set - defaulting to 1"
    export NJOB=1
fi

#
# Quick termination of job sequence - look for a specific file 
#
if [ -f STOP_SEQUENCE ] ; then
    $ECHO  "Terminating sequence at job number $NJOB"
    exit 0
fi

if [ X$NJOB == X1 ]; then
    $ECHO "This is the first year - it's not a restart"
    export YEAR=1979
    
else
    export YEAR=$(($YEAR+1))
fi
$ECHO "Processing PI for $YEAR"

cd $HOME/pcmin

mpirun -np $PBS_NCPUS python3 calculate.py -c calculate.ini -y $YEAR > calculate.stdout.$YEAR 2>&1

if [ $NJOB -lt $NJOBS ]; then
    NJOB=$(($NJOB+1))
    $ECHO "Submitting job number $NJOB in sequence of $NJOBS jobs"
    qsub -v NJOB=$NJOB,NJOBS=$NJOBS,YEAR=$YEAR calc_pi.sh
else
    $ECHO "Finished last job in sequence"
fi
