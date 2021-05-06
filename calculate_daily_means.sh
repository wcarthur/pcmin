#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N calc_daily_mean
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=02:00:00
#PBS -lmem=64GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0022
#PBS -v NJOBS,NJOB,YEAR
#PBS -joe
#PBS -e /home/547/cxa547/pcmin/logs/calculate_daily_means.error.log
#PBS -o /home/547/cxa547/pcmin/logs/calculate_daily_means.output.log
#PBS -lstorage=scratch/w85

module purge
module load pbs
module load dot

module load netcdf/4.6.3
module load cdo/1.9.8
module load nco/4.9.2

module load openmpi/4.0.3

# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2
ECHO=/bin/echo
SCRATCH=/scratch/$PROJECT/$USER

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
$ECHO "Calculating daily PI for $YEAR"

cd $SCRATCH/pcmin/daily

cdo mergetime pcmin.${YEAR}????-${YEAR}????.nc pcmin.${YEAR}0101-${YEAR}1231.nc > $HOME/pcmin/logs/calculate_daily_mean.stdout.$YEAR 2>&1
if [[ $? -ne 0 ]]; then
    $ECHO "The command appears to have failed for ${YEAR}"
    exit 0
fi

if [ $NJOB -lt $NJOBS ]; then
    NJOB=$(($NJOB+1))
    $ECHO "Submitting job number $NJOB in sequence of $NJOBS jobs"
    qsub -v NJOB=$NJOB,NJOBS=$NJOBS,YEAR=$YEAR ${0}
else
    $ECHO "Finished last job in sequence"
fi
