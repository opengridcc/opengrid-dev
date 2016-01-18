# -*- coding: utf-8 -*-
"""
General analysis functions.

Try to write all methods such that they take a dataframe as input
and return a dataframe or list of dataframes.
"""

import numpy as np
import pdb
import pandas as pd
from opengrid.library.misc import *


class Analysis(object):
    """
        Abstract class for Open Grid Analyses
    """

    def __init__(self, id = None):
        self.id = id

    def to_json(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def to_plt(self):
        raise NotImplementedError("Subclass must implement abstract method")


def daily_min(df, starttime=None, endtime=None):
    """

    Parameters
    ----------
    df: pandas.DataFrame
        With pandas.DatetimeIndex and one or more columns
    starttime, endtime :datetime.time objects
        For each day, only consider the time between starttime and endtime
        If None, use begin of day/end of day respectively

    Returns
    -------
    df_day : pandas.DataFrame with daily datetimindex and minima
    """

    df_daily_list = split_by_day(df, starttime, endtime)

    # create a dataframe with correct index
    df_res = pd.DataFrame(index=df.resample(rule='D', how='max').index, columns=df.columns)
    # fill it up, day by day
    for i,df_day in enumerate(df_daily_list):
        df_res.iloc[i,:] = df_day.min()

    return df_res


def daily_max(df, starttime=None, endtime=None):
    """

    Parameters
    ----------
    df: pandas.DataFrame
        With pandas.DatetimeIndex and one or more columns
    starttime, endtime :datetime.time objects
        For each day, only consider the time between starttime and endtime
        If None, use begin of day/end of day respectively

    Returns
    -------
    df_day : pandas.DataFrame with daily datetimeindex and maxima
    """

    df_daily_list = split_by_day(df, starttime, endtime)

    # create a dataframe with correct index
    df_res = pd.DataFrame(index=df.resample(rule='D', how='max').index, columns=df.columns)
    # fill it up, day by day
    for i,df_day in enumerate(df_daily_list):
        df_res.iloc[i,:] = df_day.max()

    return df_res