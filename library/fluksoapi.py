# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
from datetime import datetime as dt
from pandas import TimeSeries
import requests
import os
from time import mktime,strftime

def fluksoPower(start = dt(2013,1,21,0), end = dt.now(),
                sensor = '78022059b66cec92ebf8ea6ca98f979b',
                token = '8a11d349ab2b4ce43eea525d0ea26186',
                resolution = 'minute',
                unit = 'watt',
                csvpath = r'\\fs3E01\\3EProjectsBelgium\\iLAB_InnovationLaboratory\\CommonData\\Flukso\\Flukso1',
                fileNamePrefix = "3E_FLUKSO_1"):
    """
    Function for downloading data from flukso meters
    
    Parameters
    ----------
    - start : start time (default = installation of first flukso)
    - end : end time (default = now)
    - sensor :  sensor name (from the flukso.net user tab)
    - token :  sensor token (from the flukso.net user tab)
    - resolution: time resolution (e.g. minute, 15min, hour, day, week, month, 
      year, decade, night)
    - unit: unit of measurements (e.g. watt, kwhperyear)
    - csvpath : path for storing output file
    - fileNamePrefix: flukso name for the output file
    
    Note
    ----
    The Flukso Server will automatically restrict the data to what's available
    The csv output file will be named according to the data found on the server
    
    Returns
    -------
    CSV file with the requested timeseries, stored at the csvpath
    
    """
    start_unixtime = str(int(mktime(start.timetuple())))
    end_unixtime = str(int(mktime(end.timetuple())))
    
    payload = {'start'      :   start_unixtime,
               'end'        :   end_unixtime,
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
        array = r.json
    except:
        print "-------> Problem with HTTP request to Flukso <-------"
    
    # Create Dataframe   
    try:
        d = {}
        for tup in array:
            d[dt.fromtimestamp(tup[0])] = tup[1]
        Ts = TimeSeries(data=d)
        Ts = Ts[Ts != 'nan']
        s = strftime("%Y-%m-%d_%H-%M-%S",Ts.index[0].timetuple())    
        e = strftime("%Y-%m-%d_%H-%M-%S",Ts.index[-1].timetuple())
        Ts.to_csv(os.path.join(csvpath, fileNamePrefix + '_FROM_' + s + 
                                        '_TO_' + e + '.csv'))    
    except:
        print "-------> Problem with Flukso data parsing <-------"


if __name__=='__main__':
    # Get data of 3E's First Flukso Meter (Default Settings)
    fluksoPower()    
