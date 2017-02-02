# -*- coding: utf-8 -*-
"""
General analysis functions.

Try to write all methods such that they take a dataframe as input
and return a dataframe or list of dataframes.
"""

import datetime as dt
import pandas as pd


class Analysis(object):
    """
    Generic Analysis

    An analysis should have a dataframe as input
    self.result should be used as 'output dataframe'
    It also has output methods: plot, to json...
    """
    def __init__(self, df, *args, **kwargs):
        self.df = df
        self.do_analysis(*args, **kwargs)

    def do_analysis(self, *args, **kwargs):
        # To be overwritten by inheriting class
        self.result = self.df.copy()

    def plot(self):
        self.result.plot()

    def to_json(self):
        return self.result.to_json()


class DailyAgg(Analysis):
    def __init__(self, df, agg, starttime=dt.time.min, endtime=dt.time.max):
        """
        Parameters
        ----------
        df : pandas.DataFrame
            With pandas.DatetimeIndex and one or more columns
        agg : str
            'min', 'max', or another aggregation function
        starttime, endtime : datetime.time objects
            For each day, only consider the time between starttime and endtime
            If None, use begin of day/end of day respectively
        """
        super(DailyAgg, self).__init__(df, agg, starttime=starttime, endtime=endtime)

    def do_analysis(self, agg, starttime=dt.time.min, endtime=dt.time.max):
        if not self.df.empty:
            df = self.df[(self.df.index.time >= starttime) & (self.df.index.time < endtime)]
            df = df.resample('D', how=agg)
            self.result = df
        else:
            self.result = pd.DataFrame()










