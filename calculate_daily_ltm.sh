#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N calc_dltm
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=24:00:00
#PBS -lmem=64GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0022
#PBS -joe
#PBS -lstorage=scratch/w85

module purge
module load pbs
module load dot

module load netcdf/4.6.3
module load cdo/1.9.8
module load openmpi/4.0.3

# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2
ECHO=/bin/echo
SCRATCH=/scratch/$PROJECT/$USER

BASEPATH=/scratch/$PROJECT/$USER/pcmin/

for m in {1..12..1}; do
    MONTHSTR=`date -d "2020/$m/1" "+%m"`
    STARTMONTH=`date -d "2020/$m/1" "+%m"`
    ENDMONTH=`date -d "2020/$m/1 +1 month -1 day" "+%m"`
    INPUTFILES=$BASEPATH/daily/pcmin.[0-9][0-9][0-9][0-9]$STARTMONTH[0-9][0-9]-[0-9][0-9][0-9][0-9]$ENDMONTH[0-9][0-9].nc
    OUTPUTFILE=$BASEPATH/dltm/pcmin.dltm.$MONTHSTR.nc
    $ECHO "Calculating average from all $MONTHSTR files using cdo -P 16 ensmean INPUTFILES $OUTPUTFILE"
    cdo -O -P 16 ensmean $INPUTFILES $OUTPUTFILE
    # Make time the record dimension:
    #TFILE = $BASEPATH/pcmin.dltm.$MONTHSTR.t.nc
    #ncks --mk_rec_dmn time $OUTPUTFILE $TFILE
    #rm $OUTPUTFILE
done

# Merge into a single file
$ECHO "Creating single daily long term mean pcmin file"
cdo -O mergetime $BASEPATH/dltm/pcmin.dltm.*.nc $BASEPATH/dltm/pcmin.day.ltm.nc

# Day of maximum:
cdo yearmaxidx $BASEPATH/dltm/pcmin.day.ltm.nc $BASEPATH/dltm/pcmin.daymaxidx.ltm.nc
cdo selyearidx $BASEPATH/dltm/pcmin.daymaxidx.ltm.nc $BASEPATH/dltm/pcmin.day.ltm.nc $BASEPATH/dltm/pcmin.daymax.ltm.nc

# Day of minimum:
cdo yearminidx $BASEPATH/dltm/pcmin.day.ltm.nc $BASEPATH/dltm/pcmin.dayminidx.ltm.nc
cdo selyearidx $BASEPATH/dltm/pcmin.dayminidx.ltm.nc $BASEPATH/dltm/pcmin.day.ltm.nc $BASEPATH/dltm/pcmin.daymin.ltm.nc

#rm $BASEPATH/pcmin.dltm.*.t.nc
