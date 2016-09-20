# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 10:31:00 2016

@author: roel
"""
from opengrid import ureg
import pandas as pd
from dateutil import rrule
import datetime as dt
from itertools import groupby, count
import pytz


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
    return pd.Timedelta(seconds=t.hour * 3600 + t.minute * 60 + t.second + t.microsecond * 1e-3)


def split_by_day(df, starttime=dt.time.min, endtime=dt.time.max):
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
    """
    if df.empty:
        return None

    df = df[(df.index.time >= starttime) & (df.index.time < endtime)]  # slice between starttime and endtime
    list_df = [group[1] for group in df.groupby(df.index.date)]  # group by date and create list
    return list_df


def unit_conversion_factor(source, target):
    """
    Shorthand function to get a conversion factor for unit conversion.

    Parameters
    ----------
    source, target : str
        Unit as string, should be parsable by pint

    Returns
    -------
    cf : float
        Conversion factor. Multiply the source value with this factor to
        get the target value.  Works only for factorial conversion!

    """

    if not source or not target:
        return 1
    if source == target:
        return 1
    else:
        return 1 * ureg(source).to(target).magnitude


def dayset(start, end):
    """
        Takes a start and end date and returns a set containing all dates between start and end

        Parameters
        ----------
        start : datetime-like object
        end : datetime-like object

        Returns
        -------
        set of datetime objects
    """

    res = []
    for day in rrule.rrule(rrule.DAILY, dtstart=start, until=end):
        res.append(day.date())
    return sorted(set(res))


def split_irregular_date_list(date_list):
    """
    Takes a list of dates and groups it into blocks of continuous dates.
    It returns the begin and end of those blocks

    eg. A list with continuous dates from januari to march and september to october will be split into two lists

    Parameters
    ----------
    date_list : list of datetime.date

    Returns
    -------
    list of tuples of datetime.date
    """
    date_list = sorted(date_list)
    def as_range(g):
        l = list(g)
        return l[0], l[-1]

    return [as_range(g) for _, g in groupby(date_list, key=lambda n, c=count(): n - dt.timedelta(days=next(c)))]


def calculate_temperature_equivalent(temperatures):
    """
    Calculates the temperature equivalent from a series of average daily temperatures
    according to the formula: 0.6 * tempDay0 + 0.3 * tempDay-1 + 0.1 * tempDay-2

    Parameters
    ----------
    series : Pandas Series

    Returns
    -------
    Pandas Series
    """

    ret = 0.6*temperatures + 0.3*temperatures.shift(1) + 0.1*temperatures.shift(2)
    ret.name = 'temp_equivalent'
    return ret


def calculate_degree_days(temperature_equivalent, base_temperature, cooling=False):
    """
    Calculates degree days, starting with a series of temperature equivalent values

    Parameters
    ----------
    temperature_equivalent : Pandas Series
    base_temperature : float
    cooling : bool
        Set True if you want cooling degree days instead of heating degree days

    Returns
    -------
    Pandas Series
    """

    if cooling:
        ret = temperature_equivalent - base_temperature
    else:
        ret = base_temperature - temperature_equivalent

    # degree days cannot be negative
    ret[ret < 0] = 0

    prefix = 'cooling' if cooling else 'heating'
    ret.name = '{}_degree_days_{}'.format(prefix, base_temperature)

    return ret


def last_midnight(timezone):
    """
    Return the timestamp of the last midnight in a given timezone

    Parameters
    ----------
    timezone: str
        pytz timezone

    Returns
    -------
    datetime
    """

    tz = pytz.timezone(timezone)
    now = dt.datetime.now(tz=tz)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return midnight