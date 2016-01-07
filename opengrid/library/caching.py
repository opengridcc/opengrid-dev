# -*- coding: utf-8 -*-
"""
General caching functionality

Created on Thu Jan  7 09:34:04 2016

@author: roel
"""
import os
from opengrid import config
cfg = config.Config()

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
            
            
        
   
    def get(self, sensor, start=None, end=None):
        """
        Obtain dataframe with cached data for this sensor
        """
       
        pass
   
    def update(self, df):
        """
        Update the stored dataframe with the given dataframe if it contains 
        new results
        """
       
        pass
   
   