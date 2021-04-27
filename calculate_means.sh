#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N calcpimeans
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=4:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0022
#PBS -joe
#PBS -lstorage=gdata/w85+scratch/w85

module load nco/4.9.2
module load cdo/1.9.8

BASEPATH=/scratch/$PROJECT/$USER/pcmin
STARTYEAR=1979
COUNTER=0
for i in {0..41..1}; do
    for m in {1..12..1}; do
        YEAR=$(($STARTYEAR + $i))
        ENDDATE=`date -d "$YEAR/$m/1 +1 month -1 day" "+%Y%m%d"`
        STARTDATE=`date -d "$YEAR/$m/1" "+%Y%m%d"`
        DATESTR=$STARTDATE\-$ENDDATE
        INPUTFILE=$BASEPATH/daily/pcmin.$DATESTR.nc
        MONTHFMT=`date -d "$YEAR/$m/1" "+%Y%m"`
        OUTPUTFILE=$BASEPATH/monthly/pcmin.$MONTHFMT.nc
        echo $INPUTFILE
        ncwa -C -x -v time -a time $INPUTFILE -O -o $OUTPUTFILE
        if [[ $? -ne 0 ]]; then
            echo "Looks like the command failed when processing $INPUTFILE"
        else
            ((COUNTER+=1))
            echo "Processed $INPUTFILE ($COUNTER)"
        fi
    done
    # concatenate individual monthly files into annual files
    ncecat -u time $BASEPATH/monthly/pcmin.$YEAR[0-9][0-9].nc -O -o $BASEPATH/annual/pcmin.$YEAR.nc
done

# Create a single file for all monthly mean data
ncrcat $BASEPATH/annual/pcmin.[0-9][0-9][0-9][0-9].nc $BASEPATH/annual/pcmin.$STARTYEAR-$YEAR.nc

# Calculate monthly long-term mean and anomalies:
cdo ymonmean $BASEPATH/annual/pcmin.$STARTYEAR-$YEAR.nc $BASEPATH/monthly/pcmin.monltm.nc
cdo ymonsub $BASEPATH/annual/pcmin.$STARTYEAR-$YEAR.nc $BASEPATH/monthly/pcmin.monltm.nc $BASEPATH/monthly/pcmin.$STARTYEAR-$YEAR.anom.nc

#cdo -ydaymean pcmin.*_*.nc pcmin.dailyltm.nc
