# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 10:31:00 2016

@author: roel
"""

import pandas as pd
import datetime as dt


def parse_date(d):
    """
    Return a pandas.Timestamp if possible.  
    
    Parameters
    ----------
    d : Datetime, float, int, string or pandas Timestamp
        Anything that can be parsed into a pandas.Timestamp
        
    Returns
    -------
    pts : pandas.Timestamp
    
    Raises
    ------
    ValueError if it was not possible to create a pandas.Timestamp
    """
    
    if isinstance(d, float) or isinstance(d, int):
        # we have a POSIX timestamp IN SECONDS.
        pts = pd.Timestamp(d, unit='s')
        return pts
        
    try:
        pts = pd.Timestamp(d)
    except:
        raise ValueError("{} cannot be parsed into a pandas.Timestamp".format(d))
    else:
        return pts


def time_to_timedelta(t):
    """
    Return a pandas Timedelta from a time object

    Parameters
    ----------
    t : datetime.time

    Returns
    -------
    pd.Timedelta

    Notes
    ------
    The timezone of t (if present) is ignored.
    """
    return pd.Timedelta(seconds=t.hour*3600+t.minute*60+t.second+t.microsecond*1e-3)


def split_by_day(df, starttime=None, endtime=None):
    """
    Return a list with dataframes, one for each day

    Parameters
    ----------
    df : pandas DataFrame with datetimeindex
    starttime, endtime :datetime.time objects
        For each day, only return a dataframe between starttime and endtime
        If None, use begin of day/end of day respectively

    Returns
    -------
    list, one dataframe per day.

    Notes
    -----
    The returned dataframes are simply slices of the original dataframe.
    If both starttime and endtime are None, there is an overlap in the index
    of subsequent dataframes whenever an index with time 00:00:00 is present.
    """

    if starttime is None:
        timedelta_start = pd.Timedelta(seconds=0)
    else:
        timedelta_start = time_to_timedelta(starttime)

    if endtime is None:
        timedelta_end = pd.Timedelta(days=1)
    else:
        timedelta_end = time_to_timedelta(endtime)

    index_daily = df.resample(rule='D', how='max').index
    list_df = []
    for i in index_daily:
        ts_start = i + timedelta_start
        ts_end = i + timedelta_end
        list_df.append(df.ix[ts_start:ts_end])

    return list_df