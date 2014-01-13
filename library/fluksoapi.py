# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
from datetime import datetime as dt
import pandas as pd
import requests
import os
from time import mktime,strftime
import pdb

def pull_api(sensor, token, unit, interval='day', resolution = 'minute'):
   
    """     
   
    Function for downloading data from fluksometers
    
    Parameters
    ----------
    - inverval: string specifying the interval (day, month, ...)
    - sensor :  sensor name (from the flukso.net sensor tab)
    - token :  sensor token (from the flukso.net sensor tab)
    - resolution: time resolution (e.g. minute, 15min, hour, day, week, month, 
      year, decade, night)
    - unit: unit of measurements (e.g. watt, kwhperyear, lperday)

    Note
    ----
    The Flukso Server will automatically restrict the data to what's available
    
    
    Returns
    -------
    Resulf of the http request with the raw data.  
    Use the save2csv function to parse and save.
    
    """
    
    payload = {'interval'   :   interval,
               'resolution' :   resolution,
               'unit'       :   unit}
               
    headers = {'Accept'     :   'application/json', 
               'X-Version'  :   '1.0', 
               'X-Token'    :   token}  
               
    url = 'https://api.flukso.net' + '/sensor/' + sensor 
    
    # Send Request
    try:    
        s = requests.Session()
        r = s.get(url, params = payload, headers = headers, verify=False)
    except:
        print "-------> Problem with HTTP request to Flukso <-------"
    
    # check result
    
    if not r.ok:
        print "The flukso api GET request did not succeed."
        print "Some details:"
        print "Request headers:"
        print r.request.headers
        print "Request url:"
        print r.request.url
        
        
    
    return r


def parse(r):
    """
    Parse and return a pandas TimeSeries object
    """
    
    
    # Create TimeSeries   
    try:
        d = {}
        for tup in r.json():
            d[dt.fromtimestamp(tup[0])] = tup[1]
        
    except:
        print "-------> Problem with Flukso data parsing <-------"
        raise
    
    #pdb.set_trace()
    Ts = pd.TimeSeries(data=d)
    # Convert the index to a pandas DateTimeIndex 
    Ts.index = pd.to_datetime(Ts.index)
    # this line gives an error.  Should be checked, but for now I keep the nan's        
    # Ts = Ts[Ts != 'nan']
    
    return Ts


def save_csv(Ts, csvpath=None, fileNamePrefix=''):
    """
    Save the TimeSeries or DataFrame to csv with specified name
    """
    
   
    # save to file
    if csvpath is None:
        csvpath = os.getcwd()
    s = Ts.index[0].strftime(format="%Y-%m-%d_%H-%M-%S")
    e = Ts.index[-1].strftime(format="%Y-%m-%d_%H-%M-%S")
        
    csv = os.path.join(csvpath, fileNamePrefix + '_FROM_' + s + 
                                    '_TO_' + e + '.csv')
    
    Ts.to_csv(csv, header=False)
    return csv    

   
def load_csv(csv):
    """
    Load a previously saved csv file into a timeseries or dataframe and 
    return it.
    """
    
    ts = pd.read_csv(csv, index_col = 0, header=None, parse_dates=True)
    # Convert the index to a pandas DateTimeIndex 
    ts.index = pd.to_datetime(ts.index)
    return ts
    
def consolidate(folder, sensor):
    """
    Merge all csv files in folder for the given sensor into one csv file.
    """

    # Get all files for the given sensor in the given path    
    files = [f for f in os.listdir(folder) if f.find(sensor) > -1]

    if files == []:
        raise ValueError('No files found for sensor '+sensor+' in '+folder)
    
    timeseries = [load_csv(os.path.join(folder, f)) for f in files]
    combination = timeseries[0]    
    for ts in timeseries[1:]:
        combination = combination.combine_first(ts)
    
    # Obtain the new filename
    prefix_end = files[0].index('_FROM')
    prefix = files[0][:prefix_end]
    csv = save_csv(combination, csvpath = folder, fileNamePrefix=prefix)
    
    print 'Saved ', csv
    return csv
    

    