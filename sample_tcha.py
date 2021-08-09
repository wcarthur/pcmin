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
import pandas as pd
from scipy.interpolate import interp1d

from git import Repo

import metutils
import maputils
import nctools
from loadData import maxWindSpeed
from parallel import attemptParallel, disableOnWorkers

LOGGER = logging.getLogger()

r = Repo('')
commit = str(r.commit('HEAD'))

# Create a vectorized version of num2date to hasten calculation of times
n2t = np.vectorize(cftime.num2date, excluded=['units', 'calendar'])

# Load the track file
def loadTrackFile(trackfile):
    """
    :param str trackfile: path to the file containing TC data

    :returns:  `pandas.DataFrame` of TC data (only a limited number of attributes)
    """
    converters = {'datetime': lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M")}
    try:
        df = pd.read_csv(trackfile, na_values=[' '], 
                            converters=converters)
    except:
        LOGGER.exception(f"Failed to open {trackfile}")
        LOGGER.exception(f"{sys.exc_info()[0]}")

    df = calculateMaxWind(df, dtname='datetime')

    return df

def calculateMaxWind(df, dtname='ISO_TIME'):
    """
    Calculate a maximum gust wind speed based on the central pressure deficit and the 
    wind-pressure relation defined in Holland (2008). This uses the function defined in 
    the TCRM code base, and simply passes the correct variables from the data frame
    to the function
    
    This returns a `DataFrame` with an additional column (`vmax`), which represents an estimated
    0.2 second maximum gust wind speed.
    
    'CycloneNumber', 'Datetime', 'TimeElapsed', 'Longitude', 'Latitude',
       'Speed', 'Bearing', 'CentralPressure', 'EnvPressure', 'rMax',
       'geometry', 'category', 'pdiff', 'ni'
    """
    idx = df.CycloneNumber.values
    varidx = np.ones(len(idx))
    varidx[1:][idx[1:]==idx[:-1]] = 0
    
    df['vmax'] = maxWindSpeed(varidx, np.ones(len(df.index)),
                              df.lon.values, df.lat.values,
                              df.CentralPressure.values, 
                              df.EnvPressure.values, gustfactor=1.223)
    return df

def getidx(gridlon, gridlat, ptlon, ptlat, distance=500):
    """
    Determine the indices of points in a grid that are within 
    the specified distance of a given point. 

    NOTE: The point does not have to lie within the grid.

    :param gridlon: `numpy.ndarray` of longitude points from a grid to interrogate
    :param gridlat: `numpy.ndarray` of latitude points from a grid to interrogate
    :param float ptlon: longitude of the point of interest. 
    :param float ptlat: latitude of the point of interest.
    :param float distance: Search distance from point (`ptlon`, `ptlat`)

    :returns: list of indices of all grid points that are within 
    `distance` kilometres of the given location. 
    """

    dist = maputils.gridLatLonDist(ptlon, ptlat, gridlon, gridlat)
    idy, idx = np.where(dist <= distance)
    msg = (f"Mean location of chosen points: "
           f"{np.mean(gridlon[idx]):.2f}E, "
           f"{np.mean(gridlat[idy]):.2f}S")
    LOGGER.debug(msg)
    LOGGER.debug(f"Number of grid points selected: {len(idx)}")

    return idx, idy

def sampleMonthlyPI(dt, lon, lat, filepath, distance):
    """
    Sample monthly mean PI
    
    :param dt: :class:`datetime.datetime` object containing the 
               date of an observation
    :param float lon: Longitude of the observation
    :param float lat: Latitude of the observation
    :param str filepath: Basepath of the actual monthly mean PI data

    :returns: Monthly mean potential intensity maximum wind speed 
              (m/s) and minimum pressure (hPa) for the month of 
              the observation
    """
    LOGGER.info(f"Extracting monthly mean data for {dt.strftime('%Y-%m-%d %H:%M')}")

    try:
        ncobj = Dataset(filepath)
    except:
        LOGGER.exception(f"Error loading {filepath}")
        raise

    nctimes = ncobj.variables['time'] # Only retrieve the variable, not the values
    nclon = ncobj.variables['longitude'][:]
    nclat = ncobj.variables['latitude'][:]

    if (lon > nclon.max()) or (lon < nclon.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    if (lat > nclat.max()) or (lat < nclat.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    times = n2t(nctimes[:], units=nctimes.units,
                calendar=nctimes.calendar)
    tdx = np.argmin(np.abs(times - dt.to_pydatetime()))
    idx, jdy = getidx(nclon, nclat, lon, lat, distance)

    vmax = np.nanmean(ncobj.variables['vmax'][tdx, jdy, idx])
    pmin = np.nanmean(ncobj.variables['pmin'][tdx, jdy, idx])
    LOGGER.debug(f"Monthly mean Vmax: {vmax:.1f} m/s | Pmin {pmin:.1f} hPa")
    return vmax, pmin

def sampleMonthlyLTMPI(dt, lon, lat, filepath, distance):
    """
    Sample monthly long term mean PI
    
    :param dt: :class:`datetime.datetime` object containing the 
               date of an observation
    :param float lon: Longitude of the observation
    :param float lat: Latitude of the observation
    :param str filepath: Basepath of the actual monthly mean PI data

    :returns: Monthly mean potential intensity maximum wind speed 
              (m/s) and minimum pressure (hPa) for the month of 
              the observation
    """
    LOGGER.info(f"Extracting monthly long term mean data for {dt.strftime('%Y-%m-%d %H:%M')}")
    # Daily long term mean data file stores datetime for the 
    # first year in the collection - 1979
    if (dt.month == 2) & (dt.day == 29):
        # Edge case - leap year - just use the previous day's value
        LOGGER.debug("Date represents Feb 29 - using previous day's data")
        ltmdt = datetime(1979, dt.month, 28, dt.hour, 0)
    else:
        ltmdt = datetime(1979, dt.month, dt.day, dt.hour, 0)

    try:
        ncobj = Dataset(filepath)
    except:
        LOGGER.exception(f"Error loading {filepath}")
        raise

    nctimes = ncobj.variables['time'] # Only retrieve the variable, not the values
    nclon = ncobj.variables['longitude'][:]
    nclat = ncobj.variables['latitude'][:]

    if (lon > nclon.max()) or (lon < nclon.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    if (lat > nclat.max()) or (lat < nclat.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0

    times = n2t(nctimes[:], units=nctimes.units,
                calendar=nctimes.calendar)
    #tdx = np.argmin(np.abs(times - dt.to_pydatetime()))
    idx, jdy = getidx(nclon, nclat, lon, lat, distance)

    # Extract the data for all times within the distance of the observation
    # and average spatially (should give 12 values)
    vmax = np.nanmean(np.nanmean(ncobj.variables['vmax'][:, jdy, idx], axis=2), axis=1)
    pmin = np.nanmean(np.nanmean(ncobj.variables['pmin'][:, jdy, idx], axis=2), axis=1)
    
    # Interpolate to the day of month using 1-d interpolation. `
    #vmaxinterp = interp1d(nctimes[:], vmax, fill_value='extrapolate', kind='cubic')
    #pmininterp = interp1d(nctimes[:], pmin, fill_value='extrapolate', kind='cubic')
    
    #vmaxltm = vmaxinterp(cftime.date2num(ltmdt, units=nctimes.units, calendar=nctimes.calendar))
    #pminltm = pmininterp(cftime.date2num(ltmdt, units=nctimes.units, calendar=nctimes.calendar))
    LOGGER.debug(f"Monthly LTM Vmax: {vmax[dt.month-1]:.1f} m/s | Pmin {pmin[dt.month-1]:.1f} hPa")
    return vmax[dt.month-1], pmin[dt.month-1]


def sampleDailyLTMPI(dt, lon, lat, filepath, distance):
    """
    Sample daily long term mean PI
    
    :param dt: :class:`datetime.datetime` object containing the date of an observation
    :param float lon: Longitude of the observation
    :param float lat: Latitude of the observation
    :param str filepath: Basepath of the actual PI data

    :returns: Potential intensity maximum wind speed (m/s) and minimum pressure (hPa) 
    """
    LOGGER.info(f"Extracting daily long term mean data for {dt.strftime('%Y-%m-%d %H:%M')}")

    # Daily long term mean data file stores datetime for the 
    # first year in the collection - 1979
    if (dt.month == 2) & (dt.day == 29):
        # Edge case - leap year - just use the previous day's value
        LOGGER.debug("Date represents Feb 29 - using previous day's data")
        ltmdt = datetime(1979, dt.month, 28, dt.hour, 0)
    else:
        ltmdt = datetime(1979, dt.month, dt.day, dt.hour, 0)

    LOGGER.debug(f"Loading {filepath}")
    try:
        ncobj = Dataset(filepath)
    except:
        LOGGER.exception(f"Error loading {filepath}")
        raise

    nctimes = ncobj.variables['time'] # Only retrieve the variable, not the values
    nclon = ncobj.variables['longitude'][:]
    nclat = ncobj.variables['latitude'][:]

    if (lon > nclon.max()) or (lon < nclon.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    if (lat > nclat.max()) or (lat < nclat.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    times = n2t(nctimes[:], units=nctimes.units,
                calendar=nctimes.calendar)
    tdx = np.where(times==ltmdt)[0]
    idx, jdy = getidx(nclon, nclat, lon, lat, distance)

    vmax = np.nanmean(ncobj.variables['vmax'][tdx, jdy, idx])
    pmin = np.nanmean(ncobj.variables['pmin'][tdx, jdy, idx])
    LOGGER.debug(f"Daily LTM Vmax: {vmax:.1f} m/s | Pmin {pmin:.1f} hPa")

    return vmax, pmin

def sampleDailyPI(dt, lon, lat, filepath, distance):
    """
    Sample the actual PI values for a given datestamp

    :param dt: :class:`datetime.datetime` object containing the date of an observation
    :param float lon: Longitude of the observation
    :param float lat: Latitude of the observation
    :param str filepath: Basepath of the actual PI data

    :returns: Potential intensity maximum wind speed (m/s) and minimum pressure (hPa) 
    """
    LOGGER.info(f"Extracting data for {dt.strftime('%Y-%m-%d %H:%M')} at {lon}E, {lat}S")
    # Pesky NT timezones!
    dt = dt.replace(minute=0)
    startdate = datetime(dt.year, dt.month, 1)
    enddate = datetime(dt.year, dt.month, 
                       monthrange(dt.year, dt.month)[1])
    filedatestr = f"{startdate.strftime('%Y%m%d')}_{enddate.strftime('%Y%m%d')}"
    tfile = pjoin(filepath,  f'pcmin.{filedatestr}.nc')
    LOGGER.debug(f"Loading {tfile}")
    try:
        ncobj = Dataset(tfile)
    except:
        LOGGER.exception(f"Error loading {tfile}")
        raise

    nctimes = ncobj.variables['time'] # Only retrieve the variable, not the values
    nclon = ncobj.variables['longitude'][:]
    nclat = ncobj.variables['latitude'][:]

    if (lon > nclon.max()) or (lon < nclon.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0
    if (lat > nclat.max()) or (lat < nclat.min()):
        LOGGER.warn(f"Point lies outside the data grid")
        return 0, 0

    times = n2t(nctimes[:], units=nctimes.units,
                calendar=nctimes.calendar)
    tdx = np.where(times==dt)[0]
    idx, jdy = getidx(nclon, nclat, lon, lat, distance)

    # Note the idx and idy are a collection of grid points, so need
    # to take the mean, ignoring any missing values:
    vmax = np.nanmean(ncobj.variables['vmax'][tdx, jdy, idx])
    pmin = np.nanmean(ncobj.variables['pmin'][tdx, jdy, idx])
    LOGGER.debug(f"Daily Vmax: {vmax:.1f} m/s | Pmin {pmin:.1f} hPa")

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
    """if comm.size > 1 and comm.rank > 0:
        logFile += '-' + str(comm.rank)
        verbose = False"""


    if datestamp:
        base, ext = splitext(logFile)
        curdate = datetime.now()
        curdatestr = curdate.strftime('%Y%m%d%H%M')
        logFile = f"{base}.{curdatestr}.{ext.lstrip('.')}"

    logging.basicConfig(level=logLevel, 
                        format="%(asctime)s: %(funcName)s: %(message)s",
                        filename=logFile, filemode='w',
                        datefmt="%Y-%m-%d %H:%M:%S")

    if verbose:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(getattr(logging, logLevel))
        formatter = logging.Formatter('%(asctime)s: %(funcName)s:  %(message)s',
                                      '%H:%M:%S', )
        console.setFormatter(formatter)
        LOGGER.addHandler(console)

    LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
    LOGGER.info(f"Log file: {logFile} (detail level {logLevel})")
    LOGGER.info(f"Code version: f{commit}")

    allPIpath = config.get('Input', 'All')
    dailyLTMPath = config.get('Input', 'DailyLTM')
    dailyPath = config.get('Input', 'Daily')
    monthlyMeanPath = config.get('Input', 'MonthlyMean')
    monthlyLTMPath = config.get('Input', 'MonthlyLTM')
    distance = config.getint('Input', 'Distance')

    trackFile = config.get('Input', 'TrackFile')
    outputFile = config.get('Output', 'TrackFile')

    obstc = loadTrackFile(trackFile)
    #obstc['dailyvmax'] = np.zeros(len(obstc.index))
    #obstc['dailypmin'] = np.zeros(len(obstc.index))
    obstc['dailyltmvmax'] = np.zeros(len(obstc.index))
    obstc['dailyltmpmin'] = np.zeros(len(obstc.index))

    #obstc['monthlyvmax'] = np.zeros(len(obstc.index))
    #obstc['monthlypmin'] = np.zeros(len(obstc.index))
    obstc['monthlyltmvmax'] = np.zeros(len(obstc.index))
    obstc['monthlyltmpmin'] = np.zeros(len(obstc.index))
    obstc['monthlyltmaxvmax'] = np.zeros(len(obstc.index))
    obstc['monthlyltmaxpmin'] = np.zeros(len(obstc.index))
    

    for idx, row in obstc.iterrows():
        #vmax, pmin = sampleDailyPI(row['datetime'], row['lon'], row['lat'], dailyPath, distance)
        #obstc.loc[idx, 'dailyvmax'] = vmax
        #obstc.loc[idx, 'dailypmin'] = pmin
        vmax, pmin = sampleDailyLTMPI(row['datetime'], row['lon'], row['lat'], dailyLTMPath, distance)
        obstc.loc[idx, 'dailyltmvmax'] = vmax
        obstc.loc[idx, 'dailyltmpmin'] = pmin
        vmax, pmin = sampleMonthlyLTMPI(row['datetime'], row['lon'], row['lat'], monthlyLTMPath, distance)
        obstc.loc[idx, 'monthlyvmax'] = vmax
        obstc.loc[idx, 'monthlypmin'] = pmin        

    obstc.to_csv(outputFile, float_format="%.2f")
    LOGGER.info(f"Finished {sys.argv[0]}")

if __name__ == '__main__':
    main()
