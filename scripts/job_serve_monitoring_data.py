# -*- coding: utf-8 -*-
"""
This job does 3 things
- consolidate files of last day into 1 file (per day)
- create a zip file of all files for that day (for all sensors)
- put this zip file on the private web server


Created on Sat Jul 12 02:47:15 2014

@author: roel
"""

import os, sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import pytz
import datetime as dt
import zipfile

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library import houseprint
from opengrid.library import fluksoapi

##############################################################################
path_to_data = os.path.abspath('/usr/local/data')
path_to_webserver = os.path.abspath('/var/www/private')

# consolidate for yesterday
date = dt.datetime.now() - dt.timedelta(days=1)

# get all sensors
hp = houseprint.load_houseprint_from_file(os.path.join(script_dir, 'hp_anonymous.pkl'))
sensors = []
for flukso_id, d in hp.fluksosensors.items():
    for sensor_id, s in d.items():
        # sensor_id is 1-6, s is {}
        try:
            sensors.append(s['Sensor'])
        except:
            pass

print("{} sensors found".format(len(sensors)))

# create a empty zip-file with the date as filename
zipfilename = date.strftime(format="%Y%m%d")
with zipfile.ZipFile(os.path.join(path_to_webserver, zipfilename+'.zip'), 'w') as myzip:
    for sensor in sensors:
        # create a csv with the data of the given day
        csv=fluksoapi.consolidate_sensor(folder=path_to_data, sensor=sensor, dt_day=date)
        # add to myzip
        myzip.write(csv, arcname=os.path.split(csv)[-1])
        # and remove the file.  original files are kept
        os.remove(csv)
        
        
    
