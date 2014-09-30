# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
import datetime as dt
import pandas as pd
import requests
import os
from time import mktime,strftime
import pdb
import inspect
import requests
import re
import zipfile

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
            d[dt.datetime.fromtimestamp(tup[0])] = tup[1]
        
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

   
def find_csv(folder, sensor):
    """
    Find csv file corresponding to sensor in the given folder.  Run consolidate
    first if there are multiple csv files for a given sensor.
    
    Parameters
    ----------
    
    folder : path
        Folder containing the csv files
    sensor : hex
        Sensor for which files are to be consolidated
        
    Returns
    -------
    
    path : pathname to found csv
    
    Raises
    ------
    
    ValueError when more than one file is found
    """
    
    files = os.listdir(folder)
    found = filter(lambda x: x.find(sensor) > -1, files)

    if len(found) > 1:
        raise ValueError("More than one csv-file found for sensor {}.\nRun fluksoapi.consolidate() first".format(sensor))
    else:
        return found[0]
    
    

def load_csv(csv):
    """
    Load a previously saved csv file into a dataframe and return it.
    
    Parameters
    ----------
    csv : path
        Path to a csv file.  Filename should be something like fluksoID_sensor_FROM_x_to_y.csv

    Returns
    -------
    df : pandas.DataFrame
        The dataframe will have a DatetimeIndex with UTC timezone.  The 
        column will be the sensor-ID, extracted from the csv filename
    
    """
    
    df = pd.read_csv(csv, index_col = 0, header=None, parse_dates=True)
    # Convert the index to a pandas DateTimeIndex 
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize('UTC')
    df.columns = [csv.split('_')[1]]
    
    return df
    

def consolidate_sensor(folder, sensor, dt_day=None, remove_temp=False):
    """
    Merge all csv files for a given sensor into a single csv file
    
    - the given sensor
    - and the given day
    into a single csv file
    
    Parameters
    ----------
    folder : path
        Folder containing the csv files
    sensor : hex
        Sensor for which files are to be consolidated
    dt_day : (optional) datetime
        If a valid datetime is passed, only files containing data from this day 
        will be considered
    remove_temp : (optional) Boolean, default=False
        If True, only the resulting consolidated csv is kept, the files that
        have been consolidated are deleted.
    """

    if dt_day is not None:    
        dt_day_string = dt_day.strftime(format="%Y-%m-%d")     
    
    # Get all files for the given sensor in the given path    
    files = [f for f in os.listdir(folder) if f.find(sensor) > -1]
    if dt_day is not None:
        files = [f for f in files if f.find(dt_day_string) > -1]

    if files == []:
        raise ValueError('No files found for sensor '+sensor+' in '+folder)
    
    print("About to consolidate {} files for sensor {}".format(len(files), sensor))
    
    timeseries = [load_csv(os.path.join(folder, f)) for f in files]
    combination = timeseries[0]    
    for ts in timeseries[1:]:
        combination = combination.combine_first(ts)
    
    if dt_day is not None:
        # only retain data from this day
        dt_start = dt.datetime.strptime(dt_day_string, "%Y-%m-%d")
        dt_end = dt_start + dt.timedelta(days=1)
        combination = combination.ix[dt_start:dt_end]
        
        
    # Obtain the new filename
    prefix_end = files[-1].index('_FROM')
    prefix = files[-1][:prefix_end]    
    
    csv = save_csv(combination, csvpath = folder, fileNamePrefix=prefix)
    print 'Saved ', csv
    
    if remove_temp:    
        for f in files:
            os.remove(os.path.join(folder, f))
        print("Removed the {} temporary files".format(len(files)))

    return csv


def consolidate_folder(folder):
    
    sensorlist = [x.split('_')[1] for x in os.listdir(folder)]
    sensors = set(sensorlist)
    
    for s in sensors:
        consolidate_sensor(folder, s, remove_temp=True) 
        

def synchronize_old(folder, consolidate=True):
    """Download the latest zip-files from the opengrid droplet and unzip.
    
    The files will be stored in folder/zip and unzipped to folder/csv
    
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    consolidate : [True]/False
        If True, all csv files in folder/csv will be consolidated to a 
        single file per sensor
        
    """
    
    if not os.path.exists(folder):
        raise IOError("Provide your path to the data folder where a zip and csv subfolder will be created.")
    
    # Get the pwd; start from the path of this current file 
    sourcedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    pwdfile = file(os.path.join(sourcedir, 'og.txt'))
    pwd = pwdfile.readlines()[1].rstrip()
    
    # create a session to the private opengrid webserver
    session = requests.Session()
    session.auth = ('opengrid', pwd)
    resp = session.get('http://95.85.34.168:8080/')
    
    # make a list of all zip files
    pattern = '("[0-9]{8}.zip")' 
    files = re.findall(pattern, resp.content)
    files = [x.strip('"') for x in files]
    
    
    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)
    
    for f in files:
        # download the file to zipfolder if it does not yet exist
        if not os.path.exists(os.path.join(zipfolder, f)):        
            with open(os.path.join(zipfolder, f), 'wb') as handle:
                response = session.get('http://95.85.34.168:8080/' + f, stream=True)
        
                if not response.ok:
                    raise IOError('Something went wrong in downloading of {}'.format(f))
        
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            
            # now unzip to zipfolder
            z = zipfile.ZipFile(os.path.join(zipfolder, f), 'r')
            z.extractall(path=csvfolder)
        
    if consolidate:
        # create a set of unique sensor id's in the csv folder        
        consolidate_folder(csvfolder)
            

def synchronize(folder):
    """Download the latest zip-files from the opengrid droplet.
    
    The files will be stored in folder/zip
    
    Parameters
    ----------
    
    folder : path
        The *data* folder.  If not containing subfolders *zip* and *csv*, 
        these will be created.

    """
    
    if not os.path.exists(folder):
        raise IOError("Provide your path to the data folder where a zip and csv subfolder will be created.")
    
    # Get the pwd; start from the path of this current file 
    sourcedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    pwdfile = file(os.path.join(sourcedir, 'og.txt'))
    pwd = pwdfile.readlines()[1].rstrip()
    
    # create a session to the private opengrid webserver
    session = requests.Session()
    session.auth = ('opengrid', pwd)
    resp = session.get('http://95.85.34.168:8080/')
    
    # make a list of all zip files
    pattern = '("[0-9]{8}.zip")' 
    files = re.findall(pattern, resp.content)
    files = [x.strip('"') for x in files]
    
    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)
            
    for f in files:
        # download the file to zipfolder if it does not yet exist
        if not os.path.exists(os.path.join(zipfolder, f)):        
            with open(os.path.join(zipfolder, f), 'wb') as handle:
                response = session.get('http://95.85.34.168:8080/' + f, stream=True)
        
                if not response.ok:
                    raise IOError('Something went wrong in downloading of {}'.format(f))
        
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            

def unzip(folder, consolidate=True):
    """
    Unzip all zip files from folder/zip to folder/csv and consolidate if wanted
    
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    consolidate : [True]/False
        If True, all csv files in folder/csv will be consolidated to a 
        single file per sensor
    
    """

    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)

    files = os.listdir(zipfolder)
    badfiles = []
    
    for f in files:
        # now unzip to zipfolder
        try:       
            z = zipfile.ZipFile(os.path.join(zipfolder, f), 'r')
            z.extractall(path=csvfolder)
        except:
            badfiles.append(f)
            pass
        
    if consolidate:
        # create a set of unique sensor id's in the csv folder        
        consolidate_folder(csvfolder)            
  
    

 
    