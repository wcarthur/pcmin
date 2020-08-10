import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FormatStrFormatter
from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
import numpy as np
import xarray as xr

start_time = '1979-01-01'
end_time = '2019-12-31'

# Select NCEP/NCAR parameter and level
param = 'vmax'
level = 250

# Remote get dataset using OPeNDAP method via xarray
#ds = xr.open_dataset('http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/'
#                     'ncep.reanalysis/pressure/{}.{}.nc'.format(param, start_time[:4]))
ds = xr.open_dataset("C:/Workspace/data/pi/pcmin.1979-2019.anom.nc")
# Create slice variables subset domain
time_slice = slice(start_time, end_time)
lat_slice = slice(-30, -10)
lon_slice = slice(100, 170)

# Get data, selecting time, level, lat/lon slice
data = ds[param].sel(time=time_slice,
                     latitude=lat_slice,
                     longitude=lon_slice)

# Compute weights and take weighted average over latitude dimension
weights = np.cos(np.deg2rad(data.latitude.values))
avg_data = (data * weights[None, :, None]).sum(dim='latitude') / np.sum(weights)

# Get times and make array of datetime objects
vtimes = data.time.values.astype('datetime64[ms]').astype('O')

# Specify longitude values for chosen domain
lons = data.longitude.values
# Start figure
fig = plt.figure(figsize=(6, 16))

# Use gridspec to help size elements of plot; small top plot and big bottom plot
gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 8], hspace=0.15)

# Tick labels
x_tick_labels = [u'100\N{DEGREE SIGN}E', u'120\N{DEGREE SIGN}E',
                 u'140\N{DEGREE SIGN}E', u'160\N{DEGREE SIGN}E']

# Top plot for geographic reference (makes small map)
ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree(central_longitude=0))
ax1.set_extent([100, 170, -30, -5], ccrs.PlateCarree(central_longitude=0))
ax1.set_yticks([-25, -20, -15, -10])
ax1.yaxis.set_major_formatter(FormatStrFormatter('%.0fN'))
ax1.set_xticks([100, 120, 140, 160,])
ax1.set_xticklabels(x_tick_labels)
ax1.grid(linestyle='dotted', linewidth=2)
ax1.set_aspect('auto')


# Add geopolitical boundaries for map reference
ax1.add_feature(cfeature.COASTLINE.with_scale('50m'))
ax1.add_feature(cfeature.LAKES.with_scale('50m'), color='black', linewidths=0.5)

# Set some titles
plt.title('Hovmoller Diagram', loc='left')
plt.title('ERA5 Reanalysis', loc='right')

# Bottom plot for Hovmoller diagram
ax2 = fig.add_subplot(gs[1, 0])
ax2.invert_yaxis()  # Reverse the time order to do oldest first

# Plot of chosen variable averaged over latitude and slightly smoothed
clevs = np.arange(-25, 25, 2.5)
cf = ax2.contourf(lons, vtimes, mpcalc.smooth_n_point(
    avg_data, 9, 2), clevs, cmap=plt.cm.bwr, extend='both')
cs = ax2.contour(lons, vtimes, mpcalc.smooth_n_point(
    avg_data, 9, 2), clevs, colors='k', linewidths=0.5)
cbar = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50, extendrect=True)
cbar.set_label('m $s^{-1}$')

# Make some ticks and tick labels
ax2.set_xticks([100, 120, 140, 160])
ax2.set_xticklabels(x_tick_labels)
ax2.set_yticks(vtimes[5::24])
ax2.set_yticklabels(vtimes[5::24])
ax2.yaxis.set_major_formatter(DateFormatter('%Y'))


# Set some titles
plt.title('Potential intensity (m/s)', loc='left', fontsize=10)
plt.title('Time Range: {0:%b %Y} - {1:%b %Y}'.format(vtimes[0], vtimes[-1]),
          loc='right', fontsize=10)


#plt.subplots_adjust()

plt.savefig("C:/Workspace/data/pi/pcmin.1979-2019.anom.png", bbox_inches="tight")
