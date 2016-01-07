# -*- coding: utf-8 -*-
"""
General caching functionality

Created on Thu Jan  7 09:34:04 2016

@author: roel
"""
import os
from opengrid import config
cfg = config.Config()
from opengrid.library.misc import *

class Cache(object):
    """
    A class to handle daily aggregated data or intermediate results
    
    The file format for the data is result_sensor.csv
    """
    
    def __init__(self, result, folder=None):
        """
        Create a cache object specifically for the specified result
        
        Arguments
        ---------
        result : str
            The name of the aggregated result to be stored.
            Examples: elec_standby, water_max, ...
        folder : path
            Path where the files are stored
            If None, use the path specified in the opengrid configuration
            
        """
        self.result = result
        if folder is None:
            try:
                self.folder = os.path.abspath(cfg.get('data', 'folder'))
            except:
                raise ValueError("Specify a folder, either in the opengrid.cfg or when creating this cache object.")
        else:
            self.folder = os.path.abspath(folder)
            
        if not os.path.exists(self.folder):
            print("This folder does not exist: {}, it will be created".format(self.folder))
            os.mkdir(self.folder)
            
        print("Cache object created for result: {}".format(self.result))

   
    def _load(self, sensor):
        """
        Return a dataframe with cached data for this sensor.  If there is no
        cached data, return an empty dataframe
        
        sensor : str
            Unique identifier for this sensor
        
        """
        # Find the file and read into a dataframe
        filename = self.result + '_' + sensor + '.csv'
        path = os.path.join(self.folder, filename)
        
        if not os.path.exists(path):
            print("Could not find {}".format(path))
            return pd.DataFrame()
        
        df = pd.read_csv(path, index_col = 0, header=0, parse_dates=True)
        return df
    
    
    def _write(self, df):
        """
        Write the dataframe to csv according to the filename conventions
        """
        
        if not self.check_df(df):
            return False
        
        # Find the file and read into a dataframe
        filename = self.result + '_' + sensor + '.csv'
        path = os.path.join(self.folder, filename)
        
        df.to_csv(path)
        print("Dataframe written to {}".format(path))
        return True
    
    
    def get(self, sensor, start=None, end=None):
        """
        Return a dataframe with cached data for this sensor
        
        Arguments
        ---------
        sensor : str
            Unique identifier for this sensor
        start, end : Datetime, float, int, string or pandas Timestamp
            Anything that can be parsed into a pandas.Timestamp
            If None, return all cached data available
            
        Returns
        -------
        df : pandas DataFrame
            With single column, daily datetimeindex 
            and curtailed if start and/or end are given.
        """
       
        df = self._load(sensor)
        
        if (start is None) & (end is None):
            return df
        
        # truncate if necessary  
        if start is None:
            t_start = parse_date(0)
        else:
            t_start = parse_date(start)
        
        if end is None:
            t_end = parse_date('21000101')
        else:
            t_end = parse_date(end)
            
        return df.loc[t_start:t_end,:]
   
    
    def check_df(self, df):
        """
        Verify that the dataframe is acceptable as a daily aggregation result
        
        Arguments
        ---------
        df : pandas DataFrame
            
        Returns
        --------
        True/False
        
        Return False when the dataframe is empty, when it does not have a single
        column or when the index does not have a daily frequency        
        
        
        """
        if len(df) == 0:
            print("Empty dataframe")
            return False
        
        if len(df.columns) != 1:
            print("Wrong number of columns")
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
    
    
    
    def update(self, df):
        """
        Update the stored dataframe with the given dataframe if it contains 
        new results
        """
        
        if not self.check_df(df):
            return

        # Find the file and read into a dataframe
        sensor = df.columns[0]        
        df_old = self._load(sensor) 
        df_old.update(df)
        self._write(df_old)
        return             
   
   