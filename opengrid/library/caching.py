# -*- coding: utf-8 -*-
"""
General caching functionality. This module defines:

1. the Cache class
2. generic cache functions to store daily results

Created on Thu Jan  7 09:34:04 2016

@author: roel
"""
import os
import numpy as np
import pandas as pd
import dateutil
from opengrid import config
cfg = config.Config()
from opengrid.library import misc
from opengrid.library import analysis
from tqdm import tqdm

class Cache(object):
    """
    A class to handle daily aggregated data or intermediate results
    
    The file format for the data is result_sensor.csv
    """
    
    def __init__(self, variable, folder=None):
        """
        Create a cache object specifically for the specified variable
        
        Arguments
        ---------
        variable : str
            The name of the aggregated variable to be stored.
            Examples: elec_standby, water_max, ...
        folder : path
            Path where the files are stored
            If None, use the path specified in the opengrid configuration
            
        """
        self.variable = variable
        if folder is None:
            try:
                self.folder = os.path.join(os.path.abspath(cfg.get('data', 'folder')),'cache_day')
            except:
                raise ValueError("Specify a folder, either in the opengrid.cfg or when creating this cache object.")
        else:
            self.folder = os.path.abspath(folder)
            
        if not os.path.exists(self.folder):
            print("This folder does not exist: {}, it will be created".format(self.folder))
            os.mkdir(self.folder)
            
        print("Cache object created for variable: {}".format(self.variable))

   
    def _load(self, sensorkey):
        """
        Return a dataframe with cached data for this sensor.  If there is no
        cached data, return an empty dataframe

        Arguments
        ---------
        sensor : str
            sensor key, unique string identifier of the sensor.

        Returns
        -------
        df : tz-aware dataframe with cached daily results or empty dataframe.
        
        """
        # Find the file and read into a dataframe
        filename = self.variable + '_' + sensorkey + '.csv'
        path = os.path.join(self.folder, filename)
        
        if not os.path.exists(path):
            #print("Could not find {}".format(path))
            return pd.DataFrame()
        
        df = pd.read_csv(path, index_col = 0, header=0, parse_dates=True, date_parser=dateutil.parser.parse)
        return df
    
    
    def _write_single(self, df):
        """
        Write the dataframe with single sensor to csv according to the filename conventions

        Arguments
        ---------
        df : pandas DataFrame or Series
        """

        # handle both cases correctly: dataframe or series
        if isinstance(df, pd.DataFrame):
            if len(df.columns) != 1:
                raise ValueError("Wrong number of columns")
            df_temp = df.copy()
        elif isinstance(df, pd.Series):
            if df.name is None:
                raise ValueError("pandas Series needs a name with sensor id")
            df_temp = pd.DataFrame(df)

        sensor = df_temp.columns[0]
        # Find the file and read into a dataframe
        filename = self.variable + '_' + sensor + '.csv'
        path = os.path.join(self.folder, filename)
        
        df_temp.to_csv(path)
        #print("Values for {} written to {}".format(sensor, path))
        return True

    def _write(self, df):
        """
        Write the dataframe to csv according to the filename conventions

        Parameters
        ----------
        df : pandas DataFrame or Series
            This can be a multiple-column dataframe.  Each columns is a sensor_id.

        Returns
        -------
        True if all data is cached successfully

        Notes
        -----
        For each sensor found in df, a csv is saved to disk with filename
        self.folder/result_sensor.csv
        """

        if isinstance(df, pd.Series):
            return self._write_single(df)
        else:
            for sensor in df.columns:
                self._write_single(df[sensor])
            return True
    
    def get(self, sensors, start=None, end=None):
        """
        Return a dataframe with cached data for these sensors
        
        Arguments
        ---------
        sensors : list with Sensor objects
            Each element is a Sensor object with attribute 'key' as sensor_id
        start, end : Datetime, float, int, string or pandas Timestamp
            Anything that can be parsed into a pandas.Timestamp
            If None, return all cached data available
            
        Returns
        -------
        df : pandas DataFrame
            With single column, daily datetimeindex 
            and curtailed if start and/or end are given.
        """

        if not isinstance(sensors, list):
            raise TypeError("Sensors has to be a list with Sensor objects, not a {}".format(type(sensors)))

        dfs = []
        for sensor in sensors:
            dfs.append(self._load(sensor.key))
        df = pd.concat(dfs,axis=1)

        if len(df) == 0:
            return df
        
        if (start is None) & (end is None):
            # no truncating
            return df
        
        # truncate
        if start is None:
            t_start = misc.parse_date(0)
        else:
            t_start = misc.parse_date(start)
        
        if end is None:
            t_end = misc.parse_date('21000101')
        else:
            t_end = misc.parse_date(end)
            
        return df.loc[t_start:t_end,:]
   
    
    def check_df(self, df):
        """
        Verify that the dataframe is acceptable as a daily aggregation variable
        
        Arguments
        ---------
        df : pandas DataFrame
            
        Returns
        --------
        True/False
        
        Return False when the dataframe is empty or when the index does not have a daily frequency

        """
        if len(df) == 0:
            #print("Empty dataframe")
            return False
        
        if df.index.freqstr != 'D':
            if df.index.freqstr is not None:
                print("Wrong frequency of the index: '{}' (instead of 'D')".format(df.index.freqstr))
                return False
            else:
                # The df.index does not have a freqstr attribute for some reason. 
                # verify the frequency manually
                interval = np.round((df.index[-1] - df.index[0]).total_seconds()/(len(df.index)-1))
                if not interval == 86400:
                    print("Wrong frequency of the index: mean interval = {}s (instead of 86400)".format(interval))
                    return False
                
        return True
    

    def _update_single(self, df):
        """
        For a single sensor: update the stored dataframe with the given one

        Arguments
        ---------
        df : pandas DataFrame or Series
            If a dataframe, can only contain a single column with the sensor_id
            If a Series, the name attribute is the sensor_id

        Returns
        --------
        True if successfully updated
        """
        
        if not self.check_df(df):
            raise ValueError("Dataframe or Series not acceptable for updating.")

        # handle both cases correctly: dataframe or series
        if isinstance(df, pd.DataFrame):
            if len(df.columns) != 1:
                raise ValueError("Wrong number of columns")
            df_temp = df.copy()
        elif isinstance(df, pd.Series):
            if df.name is None:
                raise ValueError("pandas Series needs a name with sensor id")
            df_temp = pd.DataFrame(df)

        # Find the file and read into a dataframe
        sensor = df_temp.columns[0]
        df_old = self._load(sensor)
        df_old.update(df_temp)
        df_res = df_old.combine_first(df_temp)
        self._write(df_res)
        return True


    def update(self, df):
        """
        Updates the cached data for each sensor in df

        Arguments
        ----------
        df : pandas DataFrame or Series
            This can be a multiple-column dataframe.  Each columns is a sensor_id.

        Returns
        -------
        True if all data is cached successfully

        Notes
        -----
        For each sensor found in df, a csv is saved to disk with filename
        self.folder/result_sensor.csv. If such a file was already present,
        the values are updated with the ones provided in df (will overwrite
        overlapping days).
        """

        if isinstance(df, pd.Series):
            return self._update_single(df)
        else:
            for sensor in df.columns:
                try:
                    self._update_single(df[sensor])
                except ValueError:
                    pass
            return True


def cache_results(hp, sensors, resultname, AnalysisClass, chunk=True, **kwargs):
    """
    Run an analysis on a set of sensors and cache the results

    Parameters
    ----------
    sensors : list with Sensor objects
        Each element is a Sensor object with attribute 'key' as sensor_id
    AnalysisClass : object
        Class from the analysis library for the doing the analysis
    resultname : string
        Name of the cached variable, eg. elect_standby or water_daily_max
    kwargs : dict
        Additional keyword arguments are passed to the instantiation of the analysis class
    chunk : boolean, default=True
        If True, cache day_by_day to reduce memory use.

    Returns
    -------
    True if all data has been successfully cached.

    """

    # The method would run perfectly on all sensorids at once.
    # However, this leads to large dataframes and large RAM use.
    # Therefore, we create a for loop over the sensor ids
    # update: to reduce RAM use, we add another loop to run over the days

    import importlib
    cache = Cache(variable=resultname)

    for sensor in tqdm(sensors):
        # Get whatever is available as cache
        # and only extract timeseries from tmpos since the last day
        df_cached = cache.get([sensor])
        try:
            last_day = df_cached.index[-1]
        except IndexError:
            last_day = pd.Timestamp('2013-01-01', tz='UTC')

        if chunk:
            for d in pd.DatetimeIndex(start=last_day, freq='D', end=pd.Timestamp.today()):
                # get new data for a single day, full resolution
                df_new = hp.get_data(sensors = [sensor], head=d, tail=d + pd.Timedelta(days=1))

                # apply the method
                df_day = AnalysisClass(df_new, **kwargs).result

                # cache the results
                cache.update(df_day)
        else:
            # get new data, full resolution
            df_new = hp.get_data(sensors=[sensor], head=last_day)

            # apply the method
            df_day = AnalysisClass(df_new, **kwargs).result

            # cache the results
            cache.update(df_day)
    return True





