#!/bin/bash
#PBS -q copyq
#PBS -l walltime=10:00:00
#PBS -l storage=scratch/w85+gdata/w85
#PBS -l mem=2GB
#PBS -l wd
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au

# Craig Arthur, 2020-04-28
# Moving pcmin data to an externally accessible endpoint

cd /scratch/w85/cxa547 
find ./pcmin -type f -print0 | xargs -0 md5sum > pcmin.md5
cp -Rpu /scratch/w85/cxa547/pcmin/dltm/ /g/data/w85/data/pcmin/
cp -Rpu /scratch/w85/cxa547/pcmin/annual/ /g/data/w85/data/pcmin/
cp -Rpu /scratch/w85/cxa547/pcmin/monthly/ /g/data/w85/data/pcmin/
cp -Rpu /scratch/w85/cxa547/pcmin/daily/ /g/data/w85/data/pcmin/
cp -Rpu /scratch/w85/cxa547/pcmin/trend/ /g/data/w85/data/pcmin/
cp -pu /scratch/w85/cxa547/pcmin/README.rst /g/data/w85/data/pcmin/

cd /g/data/w85/data
md5sum -c /scratch/w85/cxa547/pcmin.md5 > pcmin.md5check

