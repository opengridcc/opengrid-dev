# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
import sys
import datetime as dt
import pandas as pd
import requests
import os
import pytz
import re
import zipfile
import glob
import time

def pull_api(sensor, token, unit, interval='day', resolution='minute'):
   
    """     
   
    Function for downloading data from fluksometers
    
    Parameters
    ----------
    - interval : string specifying the interval (day, month, ...)
    - sensor :  sensor name (from the flukso.net sensor tab)
    - token :  sensor token (from the flukso.net sensor tab)
    - resolution : time resolution (e.g. minute, 15min, hour, day, week, month, 
      year, decade, night)
    - unit : unit of measurements (e.g. watt, kwhperyear, lperday)

    Note
    ----
    The Flukso Server will automatically restrict the data to what's available
    
    
    Returns
    -------
    Result of the http request with the raw data.  
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
        r = s.get(url, params=payload, headers=headers, verify=False)
    except:
        print("-------> Problem with HTTP request to Flukso <-------")
    
    # check variable
    if not r.ok:
        print("The flukso api GET request did not succeed.")
        print("Some details:")
        print("Request headers:")
        print(r.request.headers)
        print("Request url:")
        print(r.request.url)
    
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
        print("-------> Problem with Flukso data parsing <-------")
        raise
    
    #pdb.set_trace()
    ts = pd.TimeSeries(data=d)
    # Convert the index to a pandas DateTimeIndex 
    ts.index = pd.to_datetime(ts.index)
    
    return ts


def save_file(df, folder=None, file_type='csv', prefix=''):
    """
    Save the TimeSeries or DataFrame to csv or hdf with specified name
    
    Parameters
    ----------
    df : pandas Timeseries or Dataframe
    folder : folder, default=None
        Folder where the file will be saved. Defaults to os.getcwd()
    file_type : {'csv', 'hdf'}, default='csv'
        File type of the saved file.
    prefix = string, default=''
        Name prefix for the file name, usually FLxxxxxxx_sensorid
        
    Returns
    -------
    path : abspath
        Absolute path to the saved file
    """
    
   
    # save to file
    folder = folder or os.getcwd()
    s = df.index[0].strftime(format="%Y-%m-%d_%H-%M-%S")
    e = df.index[-1].strftime(format="%Y-%m-%d_%H-%M-%S")
    prefix = prefix + '_FROM_' + s + '_TO_' + e
    if file_type == 'csv':
        path = os.path.join(folder, prefix + '.csv')
        df.to_csv(path, header=False)
    elif file_type == 'hdf':
        path = os.path.join(folder, prefix + '.hdf')
        df.to_hdf(path, 'df', mode='w')
    else:
        raise Exception('fluksoapi.load: file_type should be either csv or hdf')
    return path

   
def load_file(path):
    """
    Load a previously saved csv or hdf file into a dataframe and return it.
    
    Parameters
    ----------
    path : path
        Path to a csv or hdf file.  Filename should be something like fluksoID_sensor_FROM_x_to_y.csv

    Returns
    -------
    df : pandas.DataFrame
        The dataframe will have a DatetimeIndex with UTC timezone.  The 
        column will be the sensor-ID, extracted from the csv filename. If invalid filename is given, an empty dataframe will be returned.
    
    """
    if len(path) == 0 or 'FROM' not in path:
        return pd.DataFrame()
    
    if '.csv' in path:
        df = pd.read_csv(path, index_col = 0, header=None, parse_dates=True)
        # Convert the index to a pandas DateTimeIndex 
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize('UTC')
        df.columns = [path.split('_')[-7]]
    elif '.hdf' in path:
        df = pd.read_hdf(path, 'df')
    return df


def load_sensor(folder, sensor, dt_start=None, dt_end=None, files=None, error_no_files=True):
    """
    Load sensor
    
    Parameters
    ----------
    folder : path
        Folder containing the hdf and/or csv files
    sensor : hex
        Sensor for which files are to be consolidated
    dt_start, dt_end: datetime or equivalent, optional
    files : optional
        if not provided, sensor files are searched in the folder
    error_no_files : boolean, default True
        If True a ValueError is raised, if False an empty dataframe is returned
    
    Returns
    -------
    combination: dataframe
    """
    files = files or glob.glob(os.path.join(folder, '*' + sensor + '*'))
    if len(files) == 0:
        if error_no_files:
            # if no valid (unhidden) files are found, raise a ValueError.
            raise ValueError('No files found for sensor {} in {}'.format(sensor, folder))
        else:
            print('No files found for sensor {} in {}'.format(sensor, folder))
            return pd.DataFrame()
    print("About to combine {} files for sensor {}".format(len(files), sensor))
    dfs = [load_file(f) for f in files]
    combination = dfs[0]
    for df in dfs[1:]:
        combination = combination.combine_first(df)
    combination = combination.ix[dt_start:dt_end]
    return combination


def consolidate_sensor(folder, sensor, file_type='csv', dt_day=None, remove_temp=False):
    """
    Merge all csv and/or hdf files for     
    - the given sensor
    - and the given day
    into a single csv or hdf file
    
    Parameters
    ----------
    folder : path
        Folder containing the csv and/or hdf files
    sensor : hex
        Sensor for which files are to be consolidated
    file_type : {'csv', 'hdf'}, default='csv'
        File type of the saved file.
    dt_day : (optional) datetime
        If a valid datetime is passed, only files containing data from this day
        will be considered
    remove_temp : (optional) Boolean, default=False
        If True, only the resulting consolidated file is kept, the files that
        have been consolidated are deleted.
        
    Returns
    -------
    path : path of the consolidated csv or hdf file
    
    """
    
    # List all files (ABSPATH) for the given sensor in the given path, without hidden files			
    # glob.glob() is equivalent to os.listdir(folder) without the hidden files (start with '.') 
    # and returned as absolute paths
    files = glob.glob(os.path.join(folder, '*' + sensor + '*'))
    if dt_day is not None:
        #only retain data from this day
        dt_day_string = dt_day.strftime(format="%Y-%m-%d")
        files = [f for f in files if dt_day_string in f]
        dt_start = dt.datetime.strptime(dt_day_string, "%Y-%m-%d")
        dt_end = dt_start + dt.timedelta(days=1)
    else:
        dt_start = dt_end = None
    if len(files) == 0:
        # if no valid (unhidden) files are found, raise a ValueError.
        raise ValueError('No files found for sensor {} in {}'.format(sensor, folder))
    elif len(files) == 1:
        print("One file found and retained for sensor {}".format(sensor))
        return files[0]
    else:
        combination = load_sensor(folder, sensor, dt_start, dt_end, files)
        if remove_temp:
            for f in files:
                os.remove(os.path.join(folder, f))
            print("Removed the {} temporary files".format(len(files)))
        
        # Obtain the new filename prefix, something like FX12345678_sensorid
        # the _FROM....hdf will be added by the save_hdf method
        prefix = files[-1].split('_FROM')[0]
        path = save_file(combination, folder, file_type=file_type, prefix=prefix)
        print('Saved ', path)
        return path


def consolidate_folder(folder, file_type='csv'):
    
    sensor_set = {x.split('_')[-7] for x in glob.glob(os.path.join(folder, '*'))}
    print('About to consolidate {} sensors'.format(len(sensor_set)))
    for sensor in sensor_set:
        consolidate_sensor(folder, sensor, file_type=file_type, remove_temp=True)
    

def synchronize(folder, unzip=True, consolidate=True, file_type='hdf'):
    """Download the latest zip-files from the opengrid droplet, unzip and consolidate.
    
    The files will be stored in folder/zip and unzipped and 
    consolidated into folder/csv
    
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    unzip : [True]/False
        If True, unzip the downloaded files to folder/csv
    consolidate : [True]/False
        If True, all csv files in folder/csv will be consolidated to a 
        single file per sensor
    
    Notes
    -----
    
    This will only unzip the downloaded files and then consolidate all
    csv files in the csv folder.  If you want to rebuild the consolidated
    csv from all available data you can either delete all zip files and 
    run this function or run _unzip(folder, consolidate=True) on the 
    data folder.
        
    """
    t0 = time.time()
    if not os.path.exists(folder):
        raise IOError("Provide your path to the data folder where a zip and csv subfolder will be created.")
    from opengrid import config
    # Get the pwd; start from the path of this current file 
    c = config.Config()
    pwd = c.get('opengrid_server', 'password')
    host = c.get('opengrid_server','host')
    port = c.get('opengrid_server','port')
    user = c.get('opengrid_server','user')
    URL = "".join(['http://',host,':',port,'/'])
    
    # create a session to the private opengrid webserver
    session = requests.Session()
    session.auth = (user, pwd)
    resp = session.get(URL)
    
    # make a list of all zipfiles
    pattern = '("[0-9]{8}.zip")' 
    zipfiles = re.findall(pattern, resp.content)
    zipfiles = [x.strip('"') for x in zipfiles]
    zipfiles.append('all_data_till_20140711.zip')
    
    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)
    
    downloadfiles = [] # these are the successfully downloaded files       
    for f in zipfiles:
        # download the file to zipfolder if it does not yet exist
        if not os.path.exists(os.path.join(zipfolder, f)):
            print("Downloading {}".format(f))       
            with open(os.path.join(zipfolder, f), 'wb') as handle:
                response = session.get('http://95.85.34.168:8080/' + f, stream=True)
        
                if not response.ok:
                    raise IOError('Something went wrong in downloading of {}'.format(f))
        
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            downloadfiles.append(f)
            
    t1 = time.time()
    # Now unzip and/or consolidate
    if unzip:
        _unzip(folder, downloadfiles)
    t2 = time.time()
    if consolidate:
        consolidate_folder(csvfolder, file_type=file_type)
    t3 = time.time()
    print('Download time: {} s'.format(t1-t0))
    print('Unzip time: {} s'.format(t2-t1))
    print('Consolidate time: {} s'.format(t3-t2))
    print('Total time: {} s'.format(t3-t0))
        

def _unzip(folder, files='all'):
    """
    Unzip zip files from folder/zip to folder/csv
        
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    files = 'all' (default) or list of files
        Unzip only these files
    
    """

    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)

    if files == 'all':
        files = os.listdir(zipfolder)
    print('About to unzip {} files'.format(len(files)))
    badfiles = []
    
    for f in files:
        # now unzip to zipfolder
        try:       
            z = zipfile.ZipFile(os.path.join(zipfolder, f), 'r')
            z.extractall(path=csvfolder)
        except:
            badfiles.append(f)
            pass
    
    if badfiles:
        print("Could not unzip these files:")
        for f in badfiles:
            print(f)
  
    
def update_tmpo(tmposession, hp):
    """
    Update the tmpo database with all sensors from a houseprint object.
    This does NOT synchronize the data, only loads the sensors.  
    
    Parameters
    ----------
    tmposession : tmpo.Session object
    hp : a Houseprint object
    
    Returns
    -------
    tmposession : return the tmpo.Session
    """
    
    # get a list of all sensors in the hp.  The list contains tuples (sensor,token)
    sensors_tokens = hp.get_all_sensors(tokens=True)
    for s,t in sensors_tokens:
        tmposession.add(s,t)

    print("This tmpo session was updated with in total {} sensors".format(len(sensors_tokens)))
    return tmposession
    
    
def load_tmpo(tmposession, sensors, start=None, end=None):
    """
    Load data from one or more sensors into a pandas DataFrame
    
    Parameters
    ----------
    tmposession : tmpo.Session object
        tmpo session
    sensors : Str or List
        String: single sensor to be loaded
        List: list of sensors to be loaded
    start, end : Datetime, float, int, string or pandas Timestamp (default=None)
        Anything that can be parsed into a pandas.Timestamp
        If start is None, load all available data
        If end is None, end is the current time
    
    Returns
    -------
    df : pandas DataFrame
        DataFrame with DatetimeIndex and sensor-ids as columname.  If only a 
        single sensor is given, return a DataFrame instead of a Timeseries.

    Raises
    ------
    If no data is found, do not return an empty dataframe but raise
    a ValueError.
    
    """

    if isinstance(sensors, str):
        sensors = [sensors]
    
    # convert start and end to epoch
    if start is None:
        startepoch = 0
    else:
        # use parse_date to convert to pd.Timestamp and from there to POSIX
        startepoch = _parse_date(start).value/1e9
        
        # convert start and end to epoch
    if end is None:
        endepoch = sys.maxint
    else:
        # use parse_date to convert to pd.Timestamp and from there to POSIX
        endepoch = _parse_date(end).value/1e9

    # get list of timeseries    
    dfs = []    
    for s in sensors:
        try:        
            ts = tmposession.series(sid=s, head=startepoch, tail=endepoch)
        except Exception as e:
            print("No tmpo data for sensor {}".format(s))
        else:
            if len(ts) > 0:
                dfs.append(ts)
    
    df = pd.concat(dfs, axis=1)
    # convert POSIX timestamp (seconds since epoch) to DatetimeIndex    
    df.index = pd.to_datetime((df.index.values*1e9).astype(int))    
    return df
    
    
def load(path_csv, sensors, start=None, end=None):
    """
    Load data from one or more sensors into a pandas DataFrame.  
    
    Parameters
    ----------
    path_csv : str
        Folder containing the csv files with data to be loaded
    sensors : str or list of str
        Sensors to be loaded
    start, end : Datetime, float, int, string or pandas Timestamp, optional
        Anything that can be parsed into a pandas.Timestamp
        If start and end are not provided, all available data is loaded.
    
    Returns
    -------
    df : pandas DataFrame
        DataFrame with DatetimeIndex and sensor ids as column names.

    Raises
    ------
    If no single sensor is found, do not return an empty dataframe but raise
    a ValueError. Not implemented.
    
    Notes
    -----
    Currently, this function only calls ``load_sensor`` (csv and/or hdf files).
    Ultimately, it will first call ``load_tmpo`` and if the tmpo database does
    not contain all historic data (depending on start), it will also call 
    ``load_sensor``. Not implemented.
    
    """
    if isinstance(sensors, str):
        sensors = [sensors]
    
    dataframes = [load_sensor(path_csv, sensor, start, end, error_no_files=False) for sensor in sensors]
    df = pd.concat(dataframes, axis=1)
    df.index = df.index.tz_convert(pytz.timezone('Europe/Brussels'))
    
    print('{} sensors loaded'.format(len(df.columns)))
    df = df.dropna(axis=1, how='all')
    print('{} sensors retained'.format(len(df.columns)))
    print("Size of dataframe: {}".format(df.shape))

    return df


def _parse_date(d):
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
