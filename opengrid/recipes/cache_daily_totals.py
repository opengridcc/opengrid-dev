# -*- coding: utf-8 -*-
"""
Script to cache daily total elec, gas and water consumption for all sensors in the houseprint of OpenGrid

Created on 23/03/2017 by Roel De Coninck
"""

import os
import pandas as pd

from opengrid.library import houseprint, caching
from opengrid import config

c = config.Config()

# Load houseprint from cache if possible, otherwise build it from source
try:
    hp_filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
    hp = houseprint.load_houseprint_from_file(hp_filename)
    print("Houseprint loaded from {}".format(hp_filename))
except Exception as e:
    print(e)
    print("Because of this error we try to build the houseprint from source")
    hp = houseprint.Houseprint()

hp.init_tmpo()
hp.sync_tmpos()

# Get the cache objects for gas, elec and water, and update them, sensor by sensor
for sensortype in ['gas', 'elec', 'water']:
    cache = caching.Cache(variable=sensortype + '_daily_total')
    sensors = hp.get_sensors(sensortype=sensortype)
    df_cached = cache.get(sensors=sensors)

    # for each sensor:
    # 1. get the last timestamp of the cached daily total
    # 2. get the daily data since than
    # 3. fill up the cache with the new data
    for sensor in sensors:
        try:
            last_ts = df_cached[sensor.key].index[-1]
        except:
            last_ts = pd.Timestamp('1970-01-01')

        df = sensor.get_data(head=last_ts,
                                 resample='day',
                                 diff=False,
                                 tz='Europe/Brussels')
        df = df.diff().shift(-1).dropna()
        cache.update(df)

    print("Updated {} with data from {} sensors".format(sensortype + '_daily_total', len(sensors)))

