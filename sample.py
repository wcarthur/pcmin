import os
import sys
import logging
import argparse
import cftime

from datetime import datetime
from calendar import monthrange
from configparser import ConfigParser
from netCDF4 import Dataset
from os.path import join as pjoin, realpath, isdir, dirname, splitext

import numpy as np

from git import Repo

import metutils
import nctools
from parallel import attemptParallel, disableOnWorkers

LOGGER = logging.getLogger()

r = Repo('')
commit = str(r.commit('HEAD'))

# Create a vectorized version of num2date to hasten calculation of times
n2t = np.vectorize(cftime.num2date, excluded=['units', 'calendar'])

# Load the track file
def loadTrackFile(trackfile):
    pass

def sampleDailyPI(dt, lon, lat, filepath):
    """
    Sample the actual PI values for a given datestamp

    :param dt: :class:`datetime.datetime` object containing the date of an observation
    :param str filepath: Basepath of the actual PI data

    :returns: Potential intensity maximum wind speed (m/s) and minimum pressure (hPa) 
    """

    startdate = datetime(dt.year, dt.month, 1)
    enddate = datetime(dt.year, dt.month, 
                       monthrange(dt.year, dt.month)[1])
    filedatestr = f"{startdate.strftime('%Y%m%d')}_{enddate.strftime('%Y%m%d')}"
    tfile = pjoin(filepath,  f'pcmin.{filedatestr}.nc')
    ncobj = Dataset(tfile)

    nctimes = ncobj.variables['time'] # Only retrieve the variable, not the values
    nclon = ncobj.variables['longitude'][:]
    nclat = ncbj.variables['latitude'][:]

    times = n2t(nctimes[:], units=nctimes.units,
                calendar=nctimes.calendar)
    tdx = np.where(times==dt)[0]
    idx = np.argmin(np.abs(nclon - lon))
    jdy = np.argmin(np.abs(nclat - lat))
    vmax = ncobj.variables['vmax'][tdx, jdy, idx]
    pmin = ncobj.variables['pmin'][tdx, jdy, idx]
    return vmax, pmin

def main():
    """
    Handle command line arguments and call processing functions

    """
    p = argparse.ArgumentParser()

    p.add_argument('-c', '--config_file', help="Configuration file")
    p.add_argument('-v', '--verbose',
                   help="Verbose output", 
                   action='store_true')
    p.add_argument('-y', '--year', help="Year to process (1979-2019)")

    args = p.parse_args()

    configFile = args.config_file
    config = ConfigParser()
    config.read(configFile)

    logFile = config.get('Logging', 'LogFile')
    logdir = dirname(realpath(logFile))

    # if log file directory does not exist, create it
    if not isdir(logdir):
        try:
            os.makedirs(logdir)
        except OSError:
            logFile = pjoin(os.getcwd(), 'pcmin.log')



    logLevel = config.get('Logging', 'LogLevel')
    verbose = config.getboolean('Logging', 'Verbose')
    datestamp = config.getboolean('Logging', 'Datestamp')
    if args.verbose:
        verbose = True
    if comm.size > 1 and comm.rank > 0:
        logFile += '-' + str(comm.rank)
        verbose = False


    if datestamp:
        base, ext = splitext(logFile)
        curdate = datetime.datetime.now()
        curdatestr = curdate.strftime('%Y%m%d%H%M')
        logfile = f"{base}.{curdatestr}.{ext.lstrip('.')}"

    logging.basicConfig(level=logLevel, 
                        format="%(asctime)s: %(funcName)s: %(message)s",
                        filename=logfile, filemode='w',
                        datefmt="%Y-%m-%d %H:%M:%S")

    if verbose:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(getattr(logging, logLevel))
        formatter = logging.Formatter('%(asctime)s: %(funcName)s:  %(message)s',
                                      '%H:%M:%S', )
        console.setFormatter(formatter)
        LOGGER.addHandler(console)

    LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
    LOGGER.info(f"Log file: {logfile} (detail level {logLevel})")
    LOGGER.info(f"Code version: f{commit}")

    allPIpath = config.get('Input', 'All')
    dailyLTMPath = config.get('Input', 'DailyLTM')
    MonthlyMeanPath = config.get('Input', 'MonthlyMean')
    MonthlyStdPath = config.get('Input', 'MonthlyStd')
    MonthlyPercPath = config.get('Input', 'MonthlyPerc')

    trackFile = config.get('Input', 'TrackFile')


