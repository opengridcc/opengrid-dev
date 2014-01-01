# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
from datetime import datetime as dt
from pandas import TimeSeries
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


def save2csv(r, csvpath=None, fileNamePrefix=''):
    """
    Parse and save to csv
    """
    
    
    # Create Dataframe   
    try:
        d = {}
        for tup in r.json():
            d[dt.fromtimestamp(tup[0])] = tup[1]
        #pdb.set_trace()
        Ts = TimeSeries(data=d)
        # this line gives an error.  Should be checked, but for now I keep the nan's        
        # Ts = Ts[Ts != 'nan']
        
    except:
        print "-------> Problem with Flukso data parsing <-------"
        raise

    # save to file
    if csvpath is None:
        csvpath = os.getcwd()
    s = strftime("%Y-%m-%d_%H-%M-%S",Ts.index[0].timetuple())    
    e = strftime("%Y-%m-%d_%H-%M-%S",Ts.index[-1].timetuple())
    Ts.to_csv(os.path.join(csvpath, fileNamePrefix + '_FROM_' + s + 
                                    '_TO_' + e + '.csv'))    
   
