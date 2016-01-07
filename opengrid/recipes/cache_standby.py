# -*- coding: utf-8 -*-
"""
Recipe to store the standby power consumption overnight

Created on Thu Jan  7 10:31:00 2016

@author: roel
"""

from opengrid.library import houseprint
from opengrid.library import caching

hp = houseprint.Houseprint()
sensors = hp.get_sensors(sensortype='electricity') # sensor objects

# Remove some sensors
exclude = [
            '565de0a7dc64d8370aa321491217b85f' # 3E
          ]
solar = [x.key for x in hp.search_sensors(type='electricity', system='solar')]
exclude += solar

for s in sensors:
    if s.key in exclude:
        sensors.remove(s)

hp.init_tmpo()
hp.sync_tmpos()

cache = caching.Cache(result='elec_standby')

for s in sensors[:1]:
    # get cached data
    df_cached = cache.get(s.key)
    try:
        last_day = df_cached.index[-1]
    except IndexError:
        last_day = 0

    # get new data, full resolution
    df_new = hp.get_data(sensors = [s], head=last_day)

    print("Now make a dataframe with daily index, and standby power")

