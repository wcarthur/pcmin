"""
Calculate Potential Intensity and related diagnostics


Some elements of this code have been adapted from the `tcpyPI` code created by Daniel Gilford
https://github.com/dgilford/tcpyPI

MIT License

Copyright (c) 2020 Daniel Gilford

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import os
import sys
import glob
import logging
import argparse
import datetime
from calendar import monthrange
from configparser import ConfigParser
from os.path import join as pjoin, realpath, isdir, dirname, splitext

import dask
import numpy as np
import xarray as xr
from git import Repo

from tcpyPI import pi
import tcpyPI.utilities as tcPIutils

LOGGER = logging.getLogger()
repo = Repo('', search_parent_directories=True)
COMMIT = str(repo.commit('HEAD'))

CKCD = 0.9


def filedatestr(year, month):
    """
    Return a string of the file date for a given year and month.

    """
    startdate = datetime.datetime(year, month, 1)
    enddate = datetime.datetime(year, month, monthrange(year, month)[1])

    return f"{startdate.strftime('%Y%m%d')}-{enddate.strftime('%Y%m%d')}"


def filelist(basepath, year):
    """
    Generate a list of files that contain the required variables for the
    given year. As we are working with monthly mean data, we can open
    all files for a given year using `xr.open_mfdataset`. This includes all
    variables, so we end up with a dataset that has the required variables
    available.
    """

    sstfiles = glob.glob(f"{basepath}/single-levels/monthly-averaged/sst/{year}/sst_*.nc")
    mslfiles = glob.glob(f"{basepath}/single-levels/monthly-averaged/msl/{year}/msl_*nc")
    tfiles = glob.glob(f"{basepath}/pressure-levels/monthly-averaged/t/{year}/t_*.nc")
    qfiles = glob.glob(f"{basepath}/pressure-levels/monthly-averaged/q/{year}/q_*.nc")

    return [*sstfiles, *mslfiles, *tfiles, *qfiles]


def main():
    """
    Handle command line arguments and call processing functions

    """
    p = argparse.ArgumentParser()

    p.add_argument('-c', '--config_file', help="Configuration file")
    p.add_argument('-v', '--verbose',
                   help="Verbose output",
                   action='store_true')
    p.add_argument('-y', '--year', help="Year to process (1979-2020)")

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
                                      datefmt='%H:%M:%S', )
        console.setFormatter(formatter)
        LOGGER.addHandler(console)

    LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
    LOGGER.info(f"Log file: {logfile} (detail level {logLevel})")
    LOGGER.info(f"Code version: f{COMMIT}")

    if args.year:
        year = int(args.year)
    else:
        year = 2015

    minLon = config.getfloat('Domain', 'MinLon')
    maxLon = config.getfloat('Domain', 'MaxLon')
    minLat = config.getfloat('Domain', 'MinLat')
    maxLat = config.getfloat('Domain', 'MaxLat')

    LOGGER.info(f"Domain: {minLon}-{maxLon}, {minLat}-{maxLat}")

    basepath = config.get("Input", "Path")
    outpath = config.get("Output", "Path")

    if not os.path.exists(outpath):
        LOGGER.info(f"Making output path: {outpath}")
        os.makedirs(outpath)

    startYear = config.getint("Input", "StartYear")
    endYear = config.getint("Input", "EndYear")
    for year in range(startYear, endYear + 1):
        processYear(year, basepath, outpath, config)
    LOGGER.info("Completed")


def processYear(year, basepath, outpath, config):
    infiles = filelist(basepath, year)
    ds = xr.open_mfdataset(infiles)

    minLon = config.getfloat('Domain', 'MinLon')
    maxLon = config.getfloat('Domain', 'MaxLon')
    minLat = config.getfloat('Domain', 'MinLat')
    maxLat = config.getfloat('Domain', 'MaxLat')
    
    # Take a subset of the data based on the domain set in the config file:
    # NOTE: Order of latitude dimension is 90N - 90S, so maxLat *must* be
    # the northern edge of the domain.
    # The vertical level also needs to be reversed for this structure of the
    # ERA5 data (level=slice(None, None, -1))
    subds = ds.sel(longitude=slice(minLon, maxLon),
                   latitude=slice(maxLat, minLat),
                   level=slice(None, None, -1))
    outds = run(subds.chunk(dict(level=-1)))

    outputfile = os.path.join(outpath,
                              f"pcmin.{year}.nc")

    LOGGER.info(f"Saving data to {outputfile}")

    description = (f"Maximum potential intensity calculated using Emanuel's algorithm "
                    f"and ERA5 reanalysis data for the Australian region ")
    curdate = datetime.datetime.now()
    history = (f"{curdate:%Y-%m-%d %H:%M:%s}: {' '.join(sys.argv)}")
    outds.attrs['title'] = f"TC potential intensity for {year}"
    outds.attrs['description'] = description
    outds.attrs['history'] = history
    outds.attrs['version'] = COMMIT
    outds.to_netcdf(outputfile)


def run(ds):
    """
    Run the PI and diagnostic calculations.

    :param ds: `xr.Dataset` containing required SST, MSL, T and Q variables
    :returns: `xr.Dataset` containing PI, TO, OTL, EFF, DISEQ variables

    NOTES:
    - the diagnostics take SST in Celsius, while the PI function takes
      SST in Kelvin. I handle this in the call to the diagnostics.

    """

    result = xr.apply_ufunc(
        pi,
        ds['sst']-273.15, ds['msl'], ds['level'], ds['t']-273.15, ds['q'],
        kwargs=dict(CKCD=CKCD, ascent_flag=0,
                    diss_flag=1, ptop=50, miss_handle=1),
        input_core_dims=[[], [], ['level',], ['level',], ['level',]],
        output_core_dims=[[], [], [], [], []],
        vectorize=True,
        dask='parallelized'
    )

    vmax, pmin, ifl, t0, otl = result
    out_ds = xr.Dataset({
        'vmax': vmax,
        'pmin': pmin,
        'ifl': ifl,
        't0': t0,
        'otl': otl,
        'sst': ds['sst']
    })

    # add names and units
    out_ds.vmax.attrs['standard_name'] ='Maximum Potential Intensity'
    out_ds.vmax.attrs['units'] = 'm/s'
    out_ds.pmin.attrs['standard_name']= 'Minimum Central Pressure'
    out_ds.pmin.attrs['units'] = 'hPa'
    out_ds.ifl.attrs['standard_name'] = 'pyPI Flag'
    out_ds.t0.attrs['standard_name'] = "Outflow temperature"
    out_ds.t0.attrs['units'] = 'K'
    out_ds.otl.attrs['standard_name'] = "Outflow temperature level"
    out_ds.otl.attrs['units'] = 'hPa'

    # Calculate thermodynamic efficiency and disequilibrium:
    eff = (ds['sst'] - out_ds['t0']) / out_ds['t0']
    diseq = out_ds['vmax']**2/(CKCD*eff)

    out_ds['eff'] = eff
    out_ds.eff.attrs['standard_name'] = "Tropical cyclone efficiency"
    out_ds.eff.attrs['units'] = "unitless fraction"

    out_ds['diseq'] = diseq
    out_ds.diseq.attrs['standard_name'] = "Thermodynamic Disequilibrium"
    out_ds.diseq.attrs['units'] = "J/kg"

    return out_ds


if __name__ == "__main__":
    main()