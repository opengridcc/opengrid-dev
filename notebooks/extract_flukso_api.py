# -*- coding: utf-8 -*-
"""
Script to extract all minute sensor data from the flukso server through the 
flukso api.


Created on Mon Dec 30 04:24:28 2013 by Roel De Coninck
"""

import os, sys
import inspect


script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library.houseprint import load_houseprint_from_file
from opengrid.library import fluksoapi
from opengrid.library.storetimeseriesdata import storeTimeSeriesData

# script settings ############################################################
extract_all = True
save_all = True

##############################################################################

hp = load_houseprint_from_file(os.path.join(script_dir, 'hp_anonymous.pkl'))
all_sensordata = hp.get_all_fluksosensors()
print('Sensor data fetched')

i=0
if extract_all:
    print('Writing files:')
    for flukso_id, sensors in all_sensordata.items():
        for sensor_id, s in sensors.items():
            # sensor_id is 1-6, s is {}
            if s is not None and s:
                # determine the type of the measurement to set the unit                
                if s['Type'].lower().startswith('ele'):
                    unit = 'watt'
                else:
                    unit = 'lperday'
                # pull the data from the flukso server
                r = fluksoapi.pull_api(sensor=s['Sensor'], interval='day', token=s['Token'],
                                       unit=unit)
                if save_all:
                    storeTimeSeriesData(r.json(), s['Sensor'], s['Token'], unit)
                    ts = fluksoapi.parse(r)
                    fluksoapi.save_file(ts, folder=None, file_type='csv',
                                        prefix='_'.join([flukso_id, s['Sensor']]))
                    i=i+1
                    print('.'),
                    sys.stdout.flush()
    print('done')
print str(i) + " sensor data files saved"
