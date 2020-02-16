"""
Using the pcmin function, and data from the ERA5 reanalysis project,
calculate gridded potential intensity values.
"""

import os

import logging
import argparse
import datetime
from calendar import monthrange
from configparser import ConfigParser
from os.path import join as pjoin, realpath, isdir, dirname, splitext

import numpy as np
from netCDF4 import Dataset

import metutils
import nctools

LOGGER = logging.getLogger()


def main():
    """
    Handle command line arguments and call processing functions

    """
    p = argparse.ArgumentParser()

    p.add_argument('-c', '--config_file', help="Configuration file")
    p.add_argument('-v', '--verbose',
                   help="Verbose output", 
                   action='store_true')
    arg = parser.parse_args()

    configFile = args.config_file
    config = ConfigParser()
    config.read(configFile)

    logfile = config.get('Logging', 'LogFile')
    logdir = dirname(realpath(logfile))

    # If log file directory does not exist, create it
    if not isdir(logdir):
        try:
            os.makedirs(logdir)
        except OSError:
            logfile = pjoin(os.getcwd(), 'pcmin.log')

    logLevel = config.get('Logging', 'LogLevel')
    verbose = config.getboolean('Logging', 'Verbose')
    datestamp = config.getboolean('Logging', 'Datestamp')

    if args.verbose:
        verbose = True

    if datestamp:
        base, ext = splitext(logFile)
        curdate = datetime.datetime.now()
        curdatestr = curdate.strftime('%Y%m%d%H%M')
        logfile = f"{base}.{curdatestr}.{ext.lstrip('.')}"
    
    logging.basicConfig(level=logLevel, 
                        format="%(asctime)s: %(message)s",
                        filename=logfile, filemode='w')
    LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
    LOGGER.info(f"Log file: {logfile} (detail level {logLevel})")

    year = 2019
    month = 12
    LOGGING.info(f"Processing {year}-{month}")
    startdate = datetime.datetime(year, month, 1)
    enddate = datetime.datetime(year, month, monthrange(year, month)[1])

    filedatestr = f"{startdate.strftime("%Y%m%d")}_{enddate.strftime("%Y%m%d")}"

    sstpath = config.get('Input', 'SST')
    sstfile = pjoin(sstpath, year, f'SSTK_era5_global_{filedatestr}.nc' )
    sstobj = nctools.ncLoadFile(sstfile)
    sst = nctools.ncGetData(sstobj,'sst')

    lon = nctools.ncGetDims(sstobj, 'longitude')
    lat = nctools.ncGetDims(sstobj, 'latitude')
    nx = len(lon)
    ny = len(lat)
    slppath = config.get('Input', 'SLP')
    slpfile = pjoin(slppath, year, f'MSL_era5_global_{filedatestr}.nc')
    slpobj = nctools.ncLoadFile(slpfile)
    slpvar = nctools.ncGetVar(slpobj, 'msl')
    slp = slpvar[:]

    tpath = config.get('Input', 'Temp')
    tfile = pjoin(tpath, year, f'T_era5_global_{filedatestr}.nc')
    tobj = nctools.ncLoadFile(tfile)
    tvar = nctools.ncGetVar('T')
    t = metutils.convert(tvar[:], tvar.units, 'C')

    rpath = config.get('Input', 'Humidity')
    rfile = pjoin(tpath, year, f'R_era5_global_{filedatestr}.nc')
    # This is actually relative humidity, we need to convert to mixing ratio
    rh = nctools.ncGetData(rfile, 'r')
    # Calculate mixing ratio - this function returns mixing ratio in g/kg
    r = metutils.rHToMixRat(rh, t, ppt, tvar.units)

    times = nctools.ncGetTimes(ncLoadFile(sstfile))
    nt = len(times)
    levels = nctools.ncGetDims(ncLoadFile(tfile), 'level')
    nz = len(levels)
    # Create an array of the pressure variable that 
    # matches the shape of the temperature and mixing ratio
    # variables.
    pp = np.zeros(t.shape[0:2])
    pp[::,:] = levels
    ppt = np.repeat(pp, len(times))



    pcminarray = np.vectorize(pcmin)

    pmin, vmax, ifl = pcminarray(sst, slp, t, r, ppt)



if __name__ == "__main__":
    main()