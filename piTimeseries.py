#!/usr/bin/env python
# coding: utf-8

import os
import sys
import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

from netCDF4 import Dataset
from cftime import num2date as cfnum2date

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

dataPath = "C:/WorkSpace/data/pi"
monmean = os.path.join(dataPath, "pcmin.1979-2019.nc")
ncobj = Dataset(monmean, 'r')

lat = ncobj.variables['latitude'][:]
lon = ncobj.variables['longitude'][:]
nctimes = ncobj.variables['time']
n2t = np.vectorize(cfnum2date, excluded=['units', 'calendar'])
dts = n2t(nctimes[:], units=nctimes.units,
         calendar=nctimes.calendar)

cs_idx = np.where((lon >= 145) & (lon <= 160))[0]
cs_jdy = np.where((lat >= -25) & (lat <= -10))[0]
io_idx = np.where((lon >= 100) & (lon <= 130))[0]
io_jdy = np.where((lat >= -25) & (lat <= -10))[0]

cs_vmax = np.nanmean(ncobj.variables['vmax'][:, cs_jdy, cs_idx], axis=(1,2))
io_vmax = np.nanmean(ncobj.variables['vmax'][:, io_jdy, io_idx], axis=(1,2))

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(dts, cs_vmax, color='r', label='Coral Sea')
ax.plot(dts, io_vmax, color='b', label='Indian Ocean')
locator = mdates.YearLocator(5)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_ylabel("Potential intensity (m/s)")
ax.set_xlabel("Year")
ax.legend()
fig.tight_layout()
plt.savefig(os.path.join(dataPath, "pcmin.monmean.png"), bbox_inches='tight')

for tdx in range(0, 12):
    dt = dts[tdx]
    LOGGER.info(f"Plotting monthly mean PI for {dt.strftime('%B')}")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.regplot(x=mdates.date2num(dts[tdx:491:12]), y=cs_vmax[tdx:491:12], label='Coral Sea', ax=ax, scatter=False, truncate=True, color=palette[0], line_kws={'alpha':0.5, 'linestyle':'--'})
    sns.regplot(x=mdates.date2num(dts[tdx:491:12]), y=io_vmax[tdx:491:12], label='Indian Ocean', ax=ax, scatter=False, truncate=True, color=palette[1], line_kws={'alpha':0.5, 'linestyle':'--'})

    ax.plot(dts[tdx:491:12], cs_vmax[tdx:491:12], color=palette[0])
    ax.plot(dts[tdx:491:12], io_vmax[tdx:491:12], color=palette[1])
    locator = mdates.YearLocator(5)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_ylabel("Potential intensity (m/s)")
    ax.set_xlabel("Year")
    ax.set_title(f"Mean potential intensity - {dt.strftime('%B')}")
    ax.set_ylim((40, 100))
    ax.legend()
    fig.tight_layout()

    plt.savefig(os.path.join(dataPath, f"pcmin.monmean.{dt.strftime('%m')}.png"), bbox_inches='tight')
    plt.close(fig)
