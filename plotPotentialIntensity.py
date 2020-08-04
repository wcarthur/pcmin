#!/usr/bin/env python
# coding: utf-8


import os
import sys
import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as feature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

import shapely.geometry as sg

from netCDF4 import Dataset
from cftime import num2date

import numpy as np
from datetime import datetime

import seaborn as sns

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
palette = [(1.000, 1.000, 1.000), (0.000, 0.627, 0.235), (0.412, 0.627, 0.235),
           (0.663, 0.780, 0.282), (0.957, 0.812, 0.000), (0.925, 0.643, 0.016),
           (0.835, 0.314, 0.118), (0.780, 0.086, 0.118)]
cmap = sns.blend_palette(palette, as_cmap=True)

dataPath = "C:/WorkSpace/data/pi"
monmean = os.path.join(dataPath, "pcmin.1979-2019.nc")
ncobj = Dataset(monmean, 'r')

lat = ncobj.variables['latitude'][:]
lon = ncobj.variables['longitude'][:]
nctimes = ncobj.variables['time']
n2t = np.vectorize(num2date, excluded=['units', 'calendar'])
dts = n2t(nctimes[:], units=nctimes.units,
          calendar=nctimes.calendar)

xx, yy = np.meshgrid(lon, lat)


for tdx, dt in enumerate(dts):
    LOGGER.info(f"Plotting {dt.strftime('%B %Y')}")
    vmax = ncobj.variables['vmax'][tdx, :, :]
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))
    ax.coastlines(resolution='10m', color='k', linewidth=1)
    ax.add_feature(feature.BORDERS)
    ax.add_feature(feature.LAND, color='beige')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlocator = mticker.MultipleLocator(10)
    gl.ylocator = mticker.MultipleLocator(5)
    ax.grid(True)
    cf = ax.contourf(xx, yy, vmax, cmap=cmap,
                     levels=np.arange(5, 121, 5), extend='both')
    cs = ax.contour(xx, yy, vmax, colors='k', levels=np.arange(
        5, 121, 5), linewidth=1, alpha=0.5)
    ax.set_ylim((-50, 0))
    ax.set_xlim((80, 180))
    plt.colorbar(cf, label='Potential intensity (m/s)',
                 extend='max', orientation='horizontal',
                 shrink=0.75, aspect=30, pad=0.055)
    ax.set_title(dt.strftime("%B %Y"))
    plt.savefig(os.path.join(dataPath, f"pcmin.{dt.strftime('%Y-%m')}.png"),
                bbox_inches='tight')
    plt.close(fig)
ncobj.close()

LOGGER.info("Plotting monthly long term mean maps")
monltm = os.path.join(dataPath, "pcmin.monltm.nc")
ncobj = Dataset(monltm, 'r')

lat = ncobj.variables['latitude'][:]
lon = ncobj.variables['longitude'][:]
nctimes = ncobj.variables['time']
dts = n2t(nctimes[:], units=nctimes.units,
          calendar=nctimes.calendar)

xx, yy = np.meshgrid(lon, lat)
for tdx, dt in enumerate(dts):
    LOGGER.info(f"Plotting {dt.strftime('%B')}")
    vmax = ncobj.variables['vmax'][tdx, :, :]
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))
    ax.coastlines(resolution='10m', color='k', linewidth=1)
    ax.add_feature(feature.BORDERS)
    ax.add_feature(feature.LAND, color='beige')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlocator = mticker.MultipleLocator(10)
    gl.ylocator = mticker.MultipleLocator(5)
    ax.grid(True)
    cf = ax.contourf(xx, yy, vmax, cmap=cmap,
                     levels=np.arange(5, 121, 5), extend='both')
    cs = ax.contour(xx, yy, vmax, colors='k', levels=np.arange(
        5, 121, 5), linewidth=1, alpha=0.5)
    ax.set_ylim((-50, 0))
    ax.set_xlim((80, 180))
    plt.colorbar(cf, label='Potential intensity (m/s)', extend='max',
                 orientation='horizontal',
                 shrink=0.75, aspect=30, pad=0.055)
    ax.set_title(f"Mean potential intensity - {dt.strftime('%B')}")
    plt.savefig(os.path.join(
        dataPath, f"pcmin.{dt.strftime('%m')}.png"), bbox_inches='tight')
    plt.close(fig)
ncobj.close()

LOGGER.info("Finished")
