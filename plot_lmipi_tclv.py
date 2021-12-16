"""
Extract lifetime maximum intensity from TCLV data

* Assumes files already contain normalised intensity - preferably scaled via QDM

"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from statsmodels.distributions.empirical_distribution import ECDF
sns.set_context('paper')

outputpath = "/g/data/w85/QFES_SWHA/hazard/input/tclv/lmipi"

models = ["ACCESS1-0Q", "ACCESS1-3Q", "CCSM4Q",
          "CNRM-CM5Q", "CSIRO-Mk3-6-0Q", "GFDL-CM3Q",
          "GFDL-ESM2MQ", "HadGEM2Q", "MIROC5Q",
          "MPI-ESM-LRQ", "NorESM1-MQ"]
inputperiods = ["2020-2039", "2040-2059", "2060-2079", "2080-2099"]
rcps = ["RCP45", "RCP85"]

def scatterplot(data, x, y, title, plotname):
    fig, ax = plt.subplots(1, 1)
    sns.scatterplot(data=data, x=x, y=y)
    ax.plot(np.arange(0, 101), np.arange(0, 101), linestyle='--', alpha=0.5)
    ax.set_xlabel('Daily LTM PI [m/s]')
    ax.set_ylabel('Maximum wind speed [m/s]')
    plt.title(title)
    plt.text(0.95, 0.025, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
             transform=fig.transFigure, ha='right', fontsize='xx-small',)
    plt.savefig(plotname)
    plt.close(fig)
    return


def pairplot(data, title, plotname):
    #fig, ax = plt.subplots(1, 1)
    fields = ['vmax', 'dailyltmvmax', 'monthlyvmax', 'monthlymaxvmax', 'month', 'lat']
    g = sns.pairplot(data[fields], corner=True, diag_kind="kde")
    g.map_lower(sns.kdeplot, levels=4, color=".2")
    plt.text(0.95, 0.025, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
             transform=g.figure.transFigure, ha='right', fontsize='xx-small',)
    plt.savefig(plotname)
    plt.close()
    return


def distplot(data, title, plotname):
    ni = data['vmax'] / (1.1* data['dailyltmvmax'])
    g = sns.displot(ni, bins=np.arange(0, 1.21, 0.05), stat='probability',
                    kde=True,)
    ecdf = ECDF(ni)
    pr = 1.0 - ecdf(1.0)
    label = rf"$P(v_{{max}} > PI)=${pr:.3f}"
    g.ax.axvline(1.0, color='k', linestyle=':', label=label)
    g.ax.set_title(title)
    g.ax.legend(fontsize='small')
    g.ax.set_xlabel(r"$v_{max} / PI$")
    g.tight_layout()
    plt.text(0.95, 0.025, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
             transform=g.figure.transFigure, ha='right', fontsize='xx-small',)
    plt.savefig(plotname)
    plt.close()
    return pr

prdf = pd.DataFrame(columns=['Model', 'RCP', 'Period', 'pr'])
i = 0
for m in models:
    for rcp in rcps:
        for ip in inputperiods:
            oname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.lmi.pi.csv")
            plotname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.png")
            print(oname)
            df = pd.read_csv(oname)
            scatterplot(data=df, x='dailyltmvmax', y='vmax',
                        title=f"{m} - {rcp} - {ip}",
                        plotname=plotname)
            plotname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.dist.png")
            pr = distplot(df, f"{m} - {rcp} - {ip}", plotname)
            plt.close('all')
            prdf.loc[i] = [m, rcp, ip, pr]
            plotname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.pairplot.png")
            pairplot(df, f"{m} - {rcp} - {ip}", plotname)
            i += 1

prdf.to_csv(os.path.join(outputpath, "PI_EP.csv"), float_format="%.4f")
prdf.groupby(['RCP', 'Period']).pr.agg(['mean', 'max']).to_csv(os.path.join(outputpath, "PI_EP_mean.csv"), float_format="%.4f")

for ip in inputperiods:
    for rcp in rcps:
        plotname = os.path.join(outputpath, f"{rcp}.{ip}.lmi.png")
        fig, axs = plt.subplots(3, 4, figsize=(12,10), sharex=True, sharey=True)
        for ax, m in zip(axs.flat, models):
            oname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.lmi.pi.csv")
            df = pd.read_csv(oname)
            df.name = m
            ax.scatter(df.dailyltmvmax, df.vmax, label=m, alpha=0.5)
            ax.plot(np.arange(0, 101), np.arange(0, 101), linestyle='--', alpha=0.5)
            ax.title.set_text(m)
        plt.setp(axs[-1, :], xlabel='Daily LTM PI [m/s]')
        plt.setp(axs[:, 0], ylabel='Maximum wind speed [m/s]')
        plt.title(f"{rcp} - {ip}")
        plt.text(0.95, 0.05, f"Created: {datetime.now():%Y-%m-%d %H:%M %z}",
             transform=fig.transFigure, ha='right', fontsize='xx-small',)
        plt.savefig(plotname)
        plt.close(fig)

for m in models:
    for ip in inputperiods:
        for rcp in rcps:
            oname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.lmi.pi.csv")
            plotname = os.path.join(outputpath, f"{m}.{rcp}.{ip}.pairplot.png")
            print(oname)
            df = pd.read_csv(oname)