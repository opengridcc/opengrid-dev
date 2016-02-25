# -*- coding: utf-8 -*-
"""
General analysis functions.

Try to write all methods such that they take a dataframe as input
and return a dataframe or list of dataframes.
"""

import datetime as dt


class Analysis(object):
    """
    Generic Analysis

    An analysis should have a dataframe as input
    self.result should be used as 'output dataframe'
    It also has output methods: to plot, to json...
    """
    def __init__(self, df):
        self.df = df
        self.result = df

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
        super(DailyAgg, self).__init__(df=df)

        if not self.df.empty:
            df = self.df
            df = df[(df.index.time >= starttime) & (df.index.time < endtime)]
            df = df.resample('D', how=agg)
            self.result = df


def daily_min(df, starttime=dt.time.min, endtime=dt.time.max):
    return DailyAgg(df=df, agg='min', starttime=starttime, endtime=endtime).result


def daily_max(df, starttime=dt.time.min, endtime=dt.time.max):
    return DailyAgg(df=df, agg='max', starttime=starttime, endtime=endtime).result
