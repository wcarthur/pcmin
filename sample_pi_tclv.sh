#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N samplepi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=3:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -o /home/547/cxa547/pcmin/logs/samplepi_tclv.out.log
#PBS -e /home/547/cxa547/pcmin/logs/samplepi_tclv.err.log
#PBS -lstorage=gdata/w85+scratch/w85

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load geos

umask 0011

export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$HOME/pcmin:$HOME/tcrm:$HOME/tcrm/Utilities
# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2

cd $HOME/pcmin

FS=$IFS

BASEPATH=/scratch/w85/swhaq/hazard/output/QLD
PIPATH=/g/data/w85/QFES_SWHA/hazard/input/pi
TCLVPATH=/g/data/w85/QFES_SWHA/hazard/input/tclv/lmi
OUTPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/tclv/lmipi
CONFIGTEMPLATE=$HOME/pcmin/sample_tclv.template.ini
GROUPLIST="GROUP1,GROUP2"
MDLLIST="ACCESS1-0Q,ACCESS1-3Q,CCSM4Q,CNRM-CM5Q,CSIRO-Mk3-6-0Q,GFDL-CM3Q,GFDL-ESM2MQ,HadGEM2Q,MIROC5Q,MPI-ESM-LRQ,NorESM1-MQ"
PERIODS="2020-2039,2040-2059,2060-2079,2080-2099"
RCPLIST="rcp45,rcp85"
IFS=","

for MDL in $MDLLIST; do
    for R in $RCPLIST; do 
	for P in $PERIODS; do
	    echo $MDL, $R, $P
	    MONLTMPI=$PIPATH/monltm/pcmin.$MDL\_$R.$P.nc
	    MONMEANPI=$PIPATH/monmean/Cyclone_PI_$MDL\_$R.$P.monmean.nc
	    MONMAXPI=$PIPATH/monmean/Cyclone_PI_$MDL\_$R.$P.monmax.nc
	    DAILYLTMPI=$PIPATH/dltm/Cyclone_PI_$MDL\_$R.$P.ltm.nc
	    # Update the configuration file with the location of the appropriate PI data
	    CONFIGFILE=$HOME/pcmin/config/sample_tclv.$MDL.$R.$P.ini
	    echo $CONFIGFILE
	    sed 's|{MONLTMPCMIN}|'$MONLTMPI'|g' $CONFIGTEMPLATE > $CONFIGFILE
	    sed -i 's|{MONMEANPI}|'$MONMEANPI'|g' $CONFIGFILE
	    sed -i 's|{MONMAXPI}|'$MONMAXPI'|g' $CONFIGFILE
	    sed -i 's|{DAILYLTMPI}|'$DAILYLTMPI'|g' $CONFIGFILE
	    
	    # Update the configuration file with the location of the appropriate TCLV data
	    TRACKFILE=$TCLVPATH/$MDL.${R^^}.$P.csv
	    sed -i 's|{TCLVFILE}|'$TRACKFILE'|g' $CONFIGFILE 

	    # Update the location of the output file
	    OUTPUTFILE=$OUTPUTPATH/$MDL.${R^^}.$P.lmi.pi.csv
	    sed -i 's|{OUTPUTFILE}|'$OUTPUTFILE'|g' $CONFIGFILE

	    # Update the logfile:
	    LOGFILE=$MDL.${R^^}.$P
	    sed -i 's|{LOGFILE}|'$LOGFILE'|g' $CONFIGFILE
	    
	    # Run the sample.py script
	    cd $HOME/pcmin

	    python3 $HOME/pcmin/sample_tclv.py -c $CONFIGFILE > $HOME/pcmin/logs/sample_pi.$MDL.$R.$P.stdout 2>&1
	    
	done
    done
done


FS=$IFS

