# -*- coding: utf-8 -*-
"""
Script to cache daily total elec, gas and water consumption for all sensors in the houseprint of OpenGrid

Created on 23/03/2017 by Roel De Coninck
"""

import os
import pandas as pd
from tqdm import tqdm

from opengrid_dev.library import houseprint, caching
from opengrid_dev import config

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

# Get the cache objects for gas, elec and water, and update them, sensor by sensor
for sensortype in ['gas', 'electricity', 'water']:
    cache = caching.Cache(variable=sensortype + '_daily_total')
    sensors = hp.get_sensors(sensortype=sensortype)
    df_cached = cache.get(sensors=sensors)

    # for each sensor:
    # 1. get the last timestamp of the cached daily total
    # 2. get the daily data since than
    # 3. fill up the cache with the new data
    print('Caching daily totals for {}'.format(sensortype))
    for sensor in tqdm(sensors):
        try:
            last_ts = df_cached[sensor.key].dropna().index[-1]
            last_ts = last_ts.tz_convert('Europe/Brussels')
        except:
            last_ts = pd.Timestamp('1970-01-01', tz='Europe/Brussels')

        # Only get data until the end of the last day
        # Chunk the data retrieval and caching to avoid memory overflow
        end_ts = pd.Timestamp(pd.Timestamp('now', tz='Europe/Brussels'))
        months = pd.DatetimeIndex(start=last_ts, end=end_ts, freq='M').tolist()
        months.insert(0, last_ts - pd.Timedelta(days=2))
        months.append(end_ts)
        for start, end in zip(months[:-1], months[1:]):
            df = sensor.get_data(head=start - pd.Timedelta(days=1),
                                 tail=end,
                                 resample='day',
                                 diff=False,
                                 tz='Europe/Brussels')
            df = df.diff().shift(-1).dropna()
            if not len(df) == 0:
                cache.update(df)

    print("Updated {} with data from {} sensors".format(sensortype + '_daily_total', len(sensors)))

