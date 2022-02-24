#!/bin/bash
#PBS -q copyq
#PBS -l walltime=10:00:00
#PBS -l storage=scratch/w85+gdata/fj6
#PBS -l mem=2GB
#PBS -l wd
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au

# Craig Arthur, 2020-04-28
# Moving pcmin data to an externally accessible endpoint

cd /scratch/w85/cxa547/pcmin 

DEST=/g/data/fj6/PI/
find ./ -type f -print0 | xargs -0 md5sum > pcmin.md5
cp -Rpu /scratch/w85/cxa547/pcmin/dltm/ /g/data/fj6/PI/
cp -Rpu /scratch/w85/cxa547/pcmin/annual/ /g/data/fj6/PI/
cp -Rpu /scratch/w85/cxa547/pcmin/monthly/ /g/data/fj6/PI/
cp -Rpu /scratch/w85/cxa547/pcmin/daily/ /g/data/fj6/PI/
cp -Rpu /scratch/w85/cxa547/pcmin/trend/ /g/data/fj6/PI/
cp -pu /scratch/w85/cxa547/pcmin/README.rst /g/data/fj6/PI/

cd /g/data/fj6/PI/
md5sum -c /scratch/w85/cxa547/pcmin/pcmin.md5 > pcmin.md5check

