#!/bin/sh
umask 0022
module load cdo

MODELLIST=ACCESS1-0Q,ACCESS1-3Q,CCSM4Q,CNRM-CM5Q,CSIRO-Mk3-6-0Q,GFDL-CM3Q,GFDL-ESM2MQ,HadGEM2Q,MIROC5Q,MPI-ESM-LRQ,NorESM1-MQ
RCPLIST=45,85 

INPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/pi/Monthly
OUTPUTPATH=/scratch/w85/cxa547/pcmin/trend/IO

MASK=/g/data/w85/QFES_SWHA/hazard/input/seamask.nc

for MODEL in ${MODELLIST//,/ }; do
    for RCP in ${RCPLIST//,/ }; do
        INPUT=$INPUTPATH/Cyclone_PI_$MODEL\_rcp$RCP.*.nc
        OUTPUT=$OUTPUTPATH/$MODEL.RCP$RCP.mean.dat
        echo "Processing $MODEL (RCP$RCP)"
        echo "Input file: $INPUT"
        #cdo -outputtab,date,value -select,name=vmax -fldmean -sellonlatbox,145,160,-25,-10 -mul $MASK $INPUT > $OUTPUT
        cdo -outputtab,date,value -select,name=vmax -fldmean -sellonlatbox,100,130,-25,-10 -mul $MASK $INPUT > $OUTPUT
    done
done