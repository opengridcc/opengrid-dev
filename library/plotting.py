# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 18:03:24 2014

@author: KDB
"""
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.dates import date2num, num2date, HourLocator, DayLocator, AutoDateLocator, DateFormatter
from matplotlib.colors import LogNorm
from dateutil.relativedelta import relativedelta

def carpet(timeseries, **kwargs):
    """
    Draw a carpet plot of a pandas timeseries.
    
    The carpet plot reads like a letter. Every day one line is added to the 
    bottom of the figure, minute for minute moving from left (morning) to right 
    (evening).
    The color denotes the level of consumption and is scaled logarithmically.
    If vmin and vmax are not provided as inputs, the minimum and maximum of the 
    colorbar represent the minimum and maximum of the (resampled) timeseries.

    Parameters
    ----------
    timeseries : pandas.Series
    vmin, vmax : If not None, either or both of these values determine the range
    of the z axis. If None, the range is given by the minimum and/or maximum
    of the (resampled) timeseries.
    zlabel, title : If not None, these determine the labels of z axis and/or
    title. If None, the name of the timeseries is used if defined.
    cmap : matplotlib.cm instance, default coolwarm
    """

    #define optional input parameters
    cmap = kwargs.pop('cmap', cm.coolwarm)
    norm = kwargs.pop('norm', LogNorm())
    interpolation = kwargs.pop('interpolation', 'nearest')
    cblabel = kwargs.pop('zlabel', timeseries.name if timeseries.name else '')
    title = kwargs.pop('title', 'carpet plot: ' + timeseries.name if timeseries.name else '')

    #data preparation
    if timeseries.dropna().empty:
        print 'skipped {} - no data'.format(title)
        return
    ts = timeseries.resample('min', how='mean', label='left', closed='left')
    vmin = max(1., kwargs.pop('vmin', ts[ts>0].min()))
    vmax = max(vmin, kwargs.pop('vmax', ts.quantile(.999)))

    #convert to dataframe with date as index and time as columns by
    #first replacing the index by a MultiIndex
    #tz_convert('UTC'): workaround for https://github.com/matplotlib/matplotlib/issues/3896
    mpldatetimes = date2num(ts.index.tz_convert('UTC').astype(dt.datetime))
    ts.index = pd.MultiIndex.from_arrays([np.floor(mpldatetimes), 2 + mpldatetimes % 1]) #'2 +': matplotlib bug workaround.
    #and then unstacking the second index level to columns
    df = ts.unstack()

    #data plotting

    fig, ax = plt.subplots()
    #define the extent of the axes (remark the +- 0.5  for the y axis in order to obtain aligned date ticks)
    extent = [df.columns[0], df.columns[-1], df.index[-1] + 0.5, df.index[0] - 0.5]
    im = plt.imshow(df, vmin=vmin, vmax=vmax, extent=extent, cmap=cmap, aspect='auto', norm=norm, interpolation=interpolation, **kwargs)

    #figure formatting

    #x axis
    ax.xaxis_date()
    ax.xaxis.set_major_locator(HourLocator(interval=2))
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.xaxis.grid(True)
    plt.xlabel('UTC Time')

    #y axis
    ax.yaxis_date()
    dmin, dmax = ax.yaxis.get_data_interval()
    number_of_days = abs(relativedelta(num2date(dmin), num2date(dmax)).days)
    #AutoDateLocator is not suited in case few data is available
    if number_of_days <= 35:
        ax.yaxis.set_major_locator(DayLocator())
    else:
        ax.yaxis.set_major_locator(AutoDateLocator())
    ax.yaxis.set_major_formatter(DateFormatter("%a, %d %b %Y"))

    #plot colorbar
    cbticks = np.logspace(np.log10(vmin), np.log10(vmax), 11, endpoint=True)
    cb = plt.colorbar(format='%.0f', ticks=cbticks)
    cb.set_label(cblabel)

    #plot title
    plt.title(title)

    return im
