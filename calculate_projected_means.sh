#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N calcpimeans
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=24:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0022
#PBS -joe
#PBS -lstorage=gdata/w85

module load nco/4.9.2
module load cdo/1.9.8

FS=$IFS

BASEPATH=/scratch/$PROJECT/$USER/pcmin
STARTYEAR=2020

MODELLIST="ACCESS1-0Q,ACCES1-3Q,CCSM4Q,CNRM-CM5Q,CSIRO-Mk3-6-0,GFDL-CM3Q,GFDL-ESM2MQ,HadGEM2Q,MIROC5Q,MPI-ESM-LRQ,NorESM1-MQ"
RCPLIST="rcp45,rcp85" 
COUNTER=0
IFS=,
for i in {0..60..20}; do
    YEAR=$(($STARTYEAR + $i))
    ENDYEAR=$(($YEAR + 19))
    DATESTR=$YEAR\_$ENDYEAR
    for MODEL in $MODELLIST; do
        for RCP in $RCPLIST; do
            INPUTFILE=$BASEPATH/Monthly/Cyclone_PI_$MODEL\_$RCP.Aust.*.nc
            OUTPUTFILE=$BASEPATH/monthly/pcmin.$MODEL\_$RCP.$YEAR-$ENDYEAR.nc
            echo $INPUTFILE
            echo $OUTPUTFILE
            CMD="cdo -ymonmean -selyear,$YEAR/$ENDYEAR $INPUTFILE -O $OUTPUTFILE"
            echo $CMD
            #$CMD
            #if [[ $? -ne 0 ]]; then
            #    echo "Looks like the command failed when processing $INPUTFILE"
            #else
            #    echo "Processed $INPUTFILE ($YEAR)"
            #fi
        done
    done
done

IFS=$FS
