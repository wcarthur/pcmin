# Potential intensity of tropical cyclones

This code is used to calculate the potential intensity of tropical cyclones (TCs), using the code published by Kerry Emanuel. It is essentially a wrapper around the FORTRAN subroutine provided in the links below, for use with ERA5 Reanalysis data available at the National Computational Facility (NCI) (project `ub4`).

The code is intended to be run on the NCI's `gadi` machine, with access to `ub4`. There is a significant amount of bespoke code in this, designed around the folder structure and actual data holdings of the ERA5 data at NCI. 

For example, pressure level data is held only for a limited subdomain over Australia and southeast Asia, while surface variables have global coverage. This requires some trick manipulation of the coordinate indices to ensure they align correctly. 

Note also the pressure level data is ordered from lowest pressure to highest pressure - highest to lowest altitude. The pcmin.f subroutine requires the input to be in the opposite order. Before using the code here, please check the ordering of the pressure level data. 

### Dependencies

* python-netCDF4
* numpy
* cftime
* mpi4py

### Installation

We use the standard Python setup tools to build the extension, making use of the numpy.f2py module to automatically wrap the FORTRAN code with a Python interface

`python setup.py install` 

### Running the code

Set up a suitable configuration file (see `calculate.ini`). In many cases, I suspect users will need to do more than simply update the configuration file to get this running. The configuration file is currently only used to specify top-level input paths, output location and the logging settings. Other Sections/Options are currently not used.

Run

`python calculate.py -h` 

for a basic description of command line arguments.

To run in a parallel environment:

`mpirun -np <ncpus> python calculate.py -c calculate.ini -y <year>`



### Links

* Reference: https://emanuel.mit.edu/limits-hurricane-intensity 
* Code: ftp://texmex.mit.edu/pub/emanuel/TCMAX/
* ERA5 data: https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5 
* Reanalysis project (ub4): https://my.nci.org.au/mancini/project/ub4
