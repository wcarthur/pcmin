#!/usr/bin/env python
# coding: utf-8

import os
import sys
import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

from netCDF4 import Dataset
from cftime import num2pydate as cfnum2date

import xarray as xr
import pandas as pd

import numpy as np
from datetime import datetime

import seaborn as sns
sns.set_context("talk")
sns.set_style('whitegrid')

from git import Repo
r = Repo('')
commit = str(r.commit('HEAD'))

LOGGER = logging.getLogger()
logging.basicConfig(level='INFO', 
                    format="%(asctime)s: %(funcName)s: %(message)s",
                    filename='plotPI.log', filemode='w',
                    datefmt="%Y-%m-%d %H:%M:%S")
console = logging.StreamHandler(sys.stdout)
console.setLevel(getattr(logging, 'INFO'))
formatter = logging.Formatter('%(asctime)s: %(funcName)s:  %(message)s',
                                datefmt='%H:%M:%S', )
console.setFormatter(formatter)
LOGGER.addHandler(console)
LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
LOGGER.info(f"Code version: f{commit}")

sns.set_context("talk")
palette = sns.color_palette()

years = mdates.YearLocator()   # every year
months = mdates.MonthLocator()  # every month
years_fmt = mdates.DateFormatter('%Y')

erasource = "ECMWF Reanalysis version 5\nhttps://cds.climate.copernicus.eu/cdsapp"

def calculateMean(inputfile, domain, varname='vmax'):
    """
    :param str inputfile: Path to input PI file
    :param tuple domain: (minlon, maxlon, minlat, maxlat)

    :returns: 1-d series of (spatial) mean of the PI

    """
    minlon, maxlon, minlat, maxlat = domain
    ncobj = Dataset(inputfile, 'r')
    lat = ncobj.variables['latitude'][:]
    lon = ncobj.variables['longitude'][:]
    nctimes = ncobj.variables['time']
    n2t = np.vectorize(cfnum2date, excluded=['units', 'calendar'])
    dts = n2t(nctimes[:], units=nctimes.units,
            calendar=nctimes.calendar)

    idx = np.where((lon >= minlon) & (lon <= maxlon))[0]
    idy = np.where((lat >= minlat) & (lat <= maxlat))[0]

    data = np.nanmean(ncobj.variables[varname][:, idy, idx], axis=(1, 2))
    return dts, data

def plotMonthlyMean(inputfile, outputpath, domain=(145, 160, -25, -10)):

    dts, vmax = calculateMean(inputfile, domain)
    #io_vmax = calculateMean(inputfile, (100, 130, -25, -10))

    fig, ax = plt.subplots(figsize=(12, 6))
    label = fr"{domain[0]}-{domain[1]}$^\circ$E, {domain[2]}-{domain[3]}$^\circ$S"
    ax.plot(dts, vmax, color='r', label=label)
    locator = mdates.YearLocator(5)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_ylabel("Potential intensity (m/s)")
    ax.set_xlabel("Year")
    ax.legend()
    plt.text(-0.1, -0.2, f"Source: {erasource}",
             transform=ax.transAxes,
             fontsize='xx-small', ha='left',)
    plt.text(1.1, -0.2, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
             transform=ax.transAxes,
             fontsize='xx-small', ha='right')
    fig.tight_layout()
    plt.savefig(os.path.join(outputpath, "pcmin.monmean.png"), bbox_inches='tight')
    return

def plotMonthlyTrends(inputfile, outputpath, domain):

    """
    ds = xr.open_dataset(inputfile)
    minlon, maxlon, minlat, maxlat = domain
    dts, vmax = calculateMean(inputfile, domain)
    label = fr"{domain[0]}-{domain[1]}$^\circ$E, {domain[2]}-{domain[3]}$^\circ$S"
    for idx, da in ds.sel(latitude=slice(minlat, maxlat),
                          longitude=slice(minlon, maxlon)
                        ).groupby(ds.time.dt.month):
        breakpoint()
        LOGGER.info(f"Plotting monthly mean PI for {pd.to_datetime(da.time)[0].strftime('%B')} (XARRAY)")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.regplot(x=da.time.dt.year.values,
                    y=da.vmax.mean(dim=['longitude', 'latitude']),
                    label=label, ax=ax, scatter=False, truncate=True,
                    color=palette[0], line_kws={'alpha':0.5, 'linestyle':'--'})
        ax.plot(da.vmax.mean(dim=['longitude', 'latitude']))
        locator = mdates.YearLocator(5) 
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.set_ylabel("Potential intensity (m/s)")
        ax.set_xlabel("Year")
        ax.set_title(f"Mean potential intensity - {pd.to_datetime(da.time)[0].strftime('%B')}")
        ax.set_ylim((0, 100))
        ax.legend()
        plt.text(1.1, -0.2, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
                 transform=ax.transAxes,
                 fontsize='xx-small', ha='right')
        plt.text(-0.1, -0.2, f"Source: {erasource}",
                 transform=ax.transAxes,
                 fontsize='xx-small', ha='left',)
        fig.tight_layout()

        plt.savefig(os.path.join(outputpath, f"pcmin.monmean.{pd.to_datetime(da.time)[0].strftime('%m')}.xarray.png"), bbox_inches='tight')
        plt.close(fig)
    """
    for tdx in range(0, 12):
        dt = dts[tdx]
        LOGGER.info(f"Plotting monthly mean PI for {dt.strftime('%B')}")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.regplot(x=mdates.date2num(dts[tdx:491:12]), y=vmax[tdx:491:12], 
                    label=label, ax=ax, scatter=False, truncate=True, 
                    color=palette[0], line_kws={'alpha':0.5, 'linestyle':'--'})

        ax.plot(dts[tdx:491:12], vmax[tdx:491:12], color=palette[0])
        locator = mdates.YearLocator(5)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.set_ylabel("Potential intensity (m/s)")
        ax.set_xlabel("Year")
        ax.set_title(f"Mean potential intensity - {dt.strftime('%B')}")
        ax.set_ylim((0, 100))
        ax.legend()
        plt.text(1.1, -0.2, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
                 transform=ax.transAxes,
                 fontsize='xx-small', ha='right')
        plt.text(-0.1, -0.2, f"Source: {erasource}",
                 transform=ax.transAxes,
                 fontsize='xx-small', ha='left',)
        fig.tight_layout()

        plt.savefig(os.path.join(outputpath, f"pcmin.monmean.{dt.strftime('%m')}.png"), bbox_inches='tight')
        plt.close(fig)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--input', help="Input file")
    p.add_argument('-d', '--domain', nargs=4, type=float)
    p.add_argument('-o', '--output', help="Destination path for output")
    args = p.parse_args()

    inputfile = args.input
    outputpath = args.output
    domain = tuple(args.domain)

    plotMonthlyMean(inputfile, outputpath, domain)
    plotMonthlyTrends(inputfile, outputpath, domain)
    
