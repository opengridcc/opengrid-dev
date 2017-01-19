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

    # define optional input parameters
    cmap = kwargs.pop('cmap', cm.coolwarm)
    norm = kwargs.pop('norm', LogNorm())
    interpolation = kwargs.pop('interpolation', 'nearest')
    cblabel = kwargs.pop('zlabel', timeseries.name if timeseries.name else '')
    title = kwargs.pop('title', 'carpet plot: ' + timeseries.name if timeseries.name else '')

    # data preparation
    if timeseries.dropna().empty:
        print('skipped {} - no data'.format(title))
        return
    ts = timeseries.resample('min', how='mean', label='left', closed='left')
    vmin = max(0.1, kwargs.pop('vmin', ts[ts > 0].min()))
    vmax = max(vmin, kwargs.pop('vmax', ts.quantile(.999)))

    # convert to dataframe with date as index and time as columns by
    # first replacing the index by a MultiIndex
    # tz_convert('UTC'): workaround for https://github.com/matplotlib/matplotlib/issues/3896
    mpldatetimes = date2num(ts.index.tz_convert('UTC').astype(dt.datetime))
    ts.index = pd.MultiIndex.from_arrays(
        [np.floor(mpldatetimes), 2 + mpldatetimes % 1])  # '2 +': matplotlib bug workaround.
    # and then unstacking the second index level to columns
    df = ts.unstack()

    # data plotting

    fig, ax = plt.subplots()
    # define the extent of the axes (remark the +- 0.5  for the y axis in order to obtain aligned date ticks)
    extent = [df.columns[0], df.columns[-1], df.index[-1] + 0.5, df.index[0] - 0.5]
    im = plt.imshow(df, vmin=vmin, vmax=vmax, extent=extent, cmap=cmap, aspect='auto', norm=norm,
                    interpolation=interpolation, **kwargs)

    # figure formatting

    # x axis
    ax.xaxis_date()
    ax.xaxis.set_major_locator(HourLocator(interval=2))
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.xaxis.grid(True)
    plt.xlabel('UTC Time')

    # y axis
    ax.yaxis_date()
    dmin, dmax = ax.yaxis.get_data_interval()
    number_of_days = (num2date(dmax) - num2date(dmin)).days
    # AutoDateLocator is not suited in case few data is available
    if abs(number_of_days) <= 35:
        ax.yaxis.set_major_locator(DayLocator())
    else:
        ax.yaxis.set_major_locator(AutoDateLocator())
    ax.yaxis.set_major_formatter(DateFormatter("%a, %d %b %Y"))

    # plot colorbar
    cbticks = np.logspace(np.log10(vmin), np.log10(vmax), 11, endpoint=True)
    cb = plt.colorbar(format='%.0f', ticks=cbticks)
    cb.set_label(cblabel)

    # plot title
    plt.title(title)

    return im


def fanchart(timeseries, **kwargs):
    """
    Draw a fan chart of the daily consumption profile.

    The fan chart shows the different quantiles of the daily consumption, with
    the blue line representing the median, and the black line the average.
    By default, the consumption of the whole day is taken, but one can select
    the hours of interest, e.g. night time standby consumption.

    Parameters
    ----------
    timeseries : pandas.Series
    start_hour, end_hour : int or float, optional
        Start and end hours of period of interest, default values are 0, 24
        As of now, ensure that start_hour < end_hour
    ylabel, title : str
        If not None, these determine the labels of y axis and/or title.
        If None, the name of the timeseries is used if defined.
    """

    start_hour = 2. + kwargs.pop('start_hour', 0.) / 24.
    end_hour = 2. + kwargs.pop('end_hour', 24.) / 24.
    ylabel = kwargs.pop('ylabel', timeseries.name if timeseries.name else '')
    title = kwargs.pop('title', 'carpet plot: ' + timeseries.name if timeseries.name else '')
    # data preparation
    if timeseries.dropna().empty:
        print('skipped {} - no data'.format(title))
        return
    ts = timeseries.resample('min', how='mean', label='left', closed='left')

    # convert to dataframe with date as index and time as columns by
    # first replacing the index by a MultiIndex
    # tz_convert('UTC'): workaround for https://github.com/matplotlib/matplotlib/issues/3896
    mpldatetimes = date2num(ts.index.tz_convert('UTC').astype(dt.datetime))
    ts.index = pd.MultiIndex.from_arrays(
        [np.floor(mpldatetimes), 2 + mpldatetimes % 1])  # '2 +': matplotlib bug workaround.
    # and then unstacking the second index level to columns
    df = ts.unstack()
    df = df.T.truncate(start_hour, end_hour)

    num = 20
    num_max = 4
    df_quant = df.quantile(np.linspace(0., 1., 2 * num + 1))

    # data plotting

    fig, ax = plt.subplots()
    im = plt.plot(df.columns, df_quant.iloc[num], 'b', label='median')
    for i in range(1, num):
        plt.fill_between(df.columns, df_quant.iloc[num - i], df_quant.iloc[min(num + i, 2 * num - num_max)], color='b',
                         alpha=0.05)
    plt.plot(df.columns, df.mean(), 'k--', label='mean')
    plt.legend()

    # x axis
    ax.xaxis_date()
    plt.xlim(df.columns[0], df.columns[-1])
    plt.ylabel(ylabel)

    # plot title
    plt.title(title)
    plt.grid(True)

    return im
