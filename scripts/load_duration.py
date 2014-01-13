# -*- coding: utf-8 -*-
"""
Script to extract all minute sensor data from the flukso server through the 
flukso api.


Created on Mon Dec 30 04:24:28 2013 by Roel De Coninck
"""

import os, sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library.houseprint import Houseprint
from opengrid.library import fluksoapi

# script settings ############################################################
water = True
gas = True
electricity = True
create_ts = False
path_to_data = os.path.join(script_dir, os.pardir, os.pardir, os.pardir, 'work', 'data')

##############################################################################

def get_timeseries(hp, sensortype):
    """
    Return list with pandas TimeSeries for all sensors of the given sensortype.
    The timeseries have the sensor hex as name.

    """
    
    timeseries = []
    # create list with sensors
    sensors = hp.get_sensors_by_type(sensortype)
    for sensor in sensors:
        # compose a single csv of all the data and load as timeseries
        try:
            csv = fluksoapi.consolidate(folder = path_to_data, sensor = sensor)
        except ValueError:
            # this sensor has no csv files: no problem            
            pass
        ts = fluksoapi.load_csv(csv)
        ts.name = sensor
        timeseries.append(ts)
    
    return timeseries



def load_duration(list_ts):
    """
    Make a simple plot with load duration curves for all timeseries in list_ts.
    """
    

    fig = plt.figure()
    ax = plt.subplot(111)    
    
    for ts in list_ts:
        arr = ts.values
        arr = arr.reshape(arr.size,)
        ax.plot(np.sort(arr), label = hp.get_flukso_from_sensor(ts.name))
        
    plt.legend()
    
    return fig, ax
        
if __name__ == '__main__':
    

    if create_ts:
        
        hp = Houseprint()
        hp.get_all_fluksosensors()
        print('Sensor data fetched')

        timeseries = {}
        for t in ['water', 'gas', 'electricity']:
            timeseries[t] = get_timeseries(hp, t)
    
    for t in ['water', 'gas', 'electricity']:
        if eval(t):
            load_duration(timeseries[t])
    