# -*- coding: utf-8 -*-
"""
One-time script to consolidate all existing data and convert to UTC time and 
save one csv file per day.  Right after running this script, the opengrid VM 
should have been converted to UTC time!!!!!!!!



Created on Sat Jul 12 01:13:24 2014

@author: roel
"""

import os, sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import pytz
import datetime as dt

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library import houseprint
from opengrid.library import fluksoapi

# script settings ############################################################
path_to_data = os.path.abspath('/home/roel/data/work/opengrid/backup_data_in_UTC')

files = [f for f in os.listdir(path_to_data) if f.endswith('.csv')]
        
for csv in files:
    
    df = fluksoapi.load_csv(os.path.join(path_to_data, csv))

    # save single csv file per day
    # Obtain the new filename
    prefix_end = csv.index('_FROM')
    prefix = csv[:prefix_end]        
    
    # first, create the datetimes for each day    
    days=df.resample(rule='D').index
    for i in range(len(days)-1):
        df_day = df.ix[days[i]:days[i+1]]
        if not df_day.isnull().all()[1]:
            fluksoapi.save_csv(df_day, csvpath=os.path.join(path_to_data, 'by_day'), 
                               fileNamePrefix=prefix)
        

    
