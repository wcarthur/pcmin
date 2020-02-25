#!/bin/bash

BASEPATH=/scratch/$PROJECT/$USER/pcmin
STARTYEAR=1979
COUNTER=0
for i in {0..40..1}; do
    for m in {1..12..1}; do
        YEAR=$(($STARTYEAR + $i))
        ENDDATE=`date -d "$YEAR/$m/1 +1 month -1 day" "+%Y%m%d"`
        STARTDATE=`date -d "$YEAR/$m/1" "+%Y%m%d"`
        DATESTR=$STARTDATE\_$ENDDATE
        INPUTFILE=$BASEPATH/pcmin.$DATESTR.nc
        MONTHFMT=`date -d "$YEAR/$m/1" "+%Y%m"`
        OUTPUTFILE=$BASEPATH/pcmin.$MONTHFMT.nc
        echo $INPUTFILE
        #cdo -monmean $INPUTFILE $OUTPUTFILE
        if [[ $? -ne 0 ]]; then
            echo "Looks like the command failed"
            echo "$MONTHFMT"
        else
            ((COUNTER+=1))
            echo "Processed $COUNTER files"
        fi
    done
done

#cdo -ydaymean pcmin.*_*.nc pcmin.dailyltm.nc