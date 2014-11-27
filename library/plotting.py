# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 18:03:24 2014

@author: KDB
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.dates import DayLocator, AutoDateFormatter, date2num
from matplotlib.colors import LogNorm

def carpet(timeseries, vmin=None, vmax=None, zlabel=None, title=None):
    """
    Draw a carpet plot of a pandas timeseries.

    Parameters
    ----------
    timeseries : pandas.Series
    vmin, vmax : If not None, either or both of these values determine the range
    of the z axis. If None, the range is given by the minimum and/or maximum
    of the (resampled) timeseries.
    zlabel, title : If not None, these determine the labels of z axis and/or
    title. If None, the name of the timeseries is used if defined.
    """
    fig, ax = plt.subplots()

    #prepare data
    ts = timeseries.resample('min', how='mean', label='left',closed='left')
    ts.index = pd.MultiIndex.from_arrays([ts.index.hour + ts.index.minute/60., date2num(ts.index.date)])
    df = ts.unstack().T
    extent = [df.columns[0], df.columns[-1], df.index[-1] + 0.5, df.index[0] - 0.5]

    #scale z axis
    if vmin is None:
        vmin = ts.min()
    vmin = max(vmin, 1.)
    if vmax is None:
        vmax = max(vmin, ts.max())

    plt.imshow(df, cmap=cm.coolwarm, aspect='auto', extent=extent, vmin=vmin, vmax=vmax, norm=LogNorm(), interpolation='nearest')

    #scale x axis
    plt.xlim(extent[0],extent[1])
    ax.xaxis.set_ticks(np.arange(0., 25., 1.))

    #scale y axis
    plt.ylim(extent[2],extent[3])
    ax.yaxis_date()
    date_locator = DayLocator(interval=1)
    date_formatter = AutoDateFormatter(date_locator)
    ax.yaxis.set_major_locator(date_locator)
    ax.yaxis.set_major_formatter(date_formatter)

    #plot colorbar
    vticks = np.logspace(np.log10(vmin), np.log10(vmax), 11, endpoint=True)
    cb = plt.colorbar(format='%.2f', ticks=vticks)

    #plot axis labels and title
    plt.xlabel('Hour of the day')
    plt.ylabel('Day of the year')
    if zlabel is not None:
        cb.set_label(zlabel)
    elif timeseries.name:
        cb.set_label(timeseries.name)
    if title is not None:
        plt.title(title)
    elif timeseries.name:
        plt.title('carpet plot: ' + timeseries.name)
