import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import YearLocator, DateFormatter
from datetime import date
from scipy.stats import linregress

sns.set_palette('Paired')

LOCATOR = YearLocator(10)
FORMATTER = DateFormatter("%Y")

datapath = "C:/WorkSpace/data/pi/trend/CS"
RCP = "RCP45"
modelnames = ["ACCESS1-0Q", "ACCESS1-3Q", "CCSM4Q",
              "CNRM-CM5Q", "CSIRO-Mk3-6-0Q", "GFDL-CM3Q",
              "GFDL-ESM2MQ", "HadGEM2Q", "MIROC5Q",
              "MPI-ESM-LRQ","NorESM1-MQ"]

filelist = [f for f in os.listdir(datapath) if RCP in f]

erafile = os.path.join(datapath, "ERA5.CS.mean.dat")
edf = pd.read_csv(os.path.join(datapath, "ERA5.CS.mean.dat"),
                 delimiter=' ', names=['date', 'vmax'],
                 skiprows=1, header=None, skipinitialspace=True,
                 index_col=False)

edf['date']= edf.date.apply(pd.to_datetime)
edf['month'] = [d.month for d in edf.date]
edf['year'] = [d.year for d in edf.date]

df = pd.read_csv(os.path.join(datapath, filelist[0]),
                 delimiter=' ', names=['date', 'vmax'],
                 skiprows=1, header=None, skipinitialspace=True, 
                 index_col=False)
                 
df['date'] = df.date.apply(pd.to_datetime)
df['month'] = [d.month for d in df.date]
df['year'] = [d.year for d in df.date]

df.drop('vmax', axis=1, inplace=True)

for m, f in zip(modelnames, filelist):
    d = pd.read_csv(os.path.join(datapath, f), delimiter=' ',
                    names=['date', 'vmax'], skiprows=1, header=None,
                    skipinitialspace=True, index_col=False)
    d.rename(columns={'vmax': m}, inplace=True)
    d['date'] = d.date.apply(pd.to_datetime)
    df = df.merge(d, on='date')


# This section calculates the trend in PI as a rate per year.
# Trends are calculated on individual months, since it may
# be that the long-term trend is dominated by out-of-season trends
df['dm'] = df['year'] + df['month']/12

regdf = pd.DataFrame(columns=['model', 'month', 'slope', 'intercept',
                              'r', 'p', 'stderr'])

for tdx in range(12):
    for m in modelnames:
        s, i, r, p, st = linregress(df.dm[tdx::12], df[m].values[tdx::12])
        regdf = regdf.append({'model': m,
                              'month': tdx+1,
                            'slope': s,
                            'intercept': i,
                            'r': r,
                            'p': p,
                            'stderr': st},
                            ignore_index=True)

regdf.set_index(['model', 'month'], inplace=True)
regdf.to_excel(os.path.join(datapath, f"regression.{RCP}.xlsx"))

x = np.arange(2020, 2100)


locator = mdates.YearLocator(10)
for tdx in range(12):
    dt = df.date[tdx]
    fig, ax = plt.subplots(figsize=(16,9))
    sns.regplot(x=mdates.date2num(edf.date[tdx::12]),
                y=edf['vmax'][tdx::12], label='ERA5',
                scatter=False, ax=ax, color='k')
    ax.plot(mdates.date2num(edf.date[tdx::12]),
            edf['vmax'][tdx::12], linewidth=1,
            color='k')

    for m in modelnames:
        color = next(ax._get_lines.prop_cycler)['color']
        sns.regplot(x=mdates.date2num(df.date[tdx::12]),
                    y=df[m][tdx::12], label=m,
                    scatter=False, truncate=True,
                    ax=ax, color=color,)
        ax.plot(mdates.date2num(df.date[tdx::12]),
                df[m][tdx::12], linewidth=1, color=color) 
    ax.xaxis.set_major_locator(LOCATOR)
    ax.xaxis.set_major_formatter(FORMATTER)
    ax.set_ylabel("Potential intensity (m/s)")
    ax.set_xlabel("Year")
    ax.set_title(f"Potential intensity trend - {dt.strftime('%B')}")
    ax.legend()
    fig.tight_layout()

    plt.savefig(os.path.join(datapath,
                             f"pcmin.trend.{dt.strftime('%m')}.{RCP}.png"),
                bbox_inches='tight')
    plt.close(fig)
