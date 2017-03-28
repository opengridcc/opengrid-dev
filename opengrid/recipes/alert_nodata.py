
# coding: utf-8

# In[ ]:

# opengrid imports
from opengrid.library import misc, houseprint, caching
from opengrid.library.analysis import DailyAgg
from opengrid import config
from opengrid.library.slack import Slack
from opengrid.library import alerts
c=config.Config()

# other imports
import pandas as pd
import json
import charts
import numpy as np
import os
import datetime as dt
import pytz
BXL = pytz.timezone('Europe/Brussels')


# In[ ]:

# Load houseprint from cache if possible, otherwise build it from source
try:
    hp_filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
    hp = houseprint.load_houseprint_from_file(hp_filename)
    print("Houseprint loaded from {}".format(hp_filename))
except Exception as e:
    print(e)
    print("Because of this error we try to build the houseprint from source")
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

# In[ ]:


sensors = hp.get_sensors() # sensor objects
t = []
for s in sensors:
    key = s.key
    lt = s.last_timestamp()
    if lt is None:
        continue
    nr_of_days = pd.Timestamp('now', tz='UTC') - lt
    t.append((key,nr_of_days))


# In[ ]:

df = pd.DataFrame(t).rename(columns={0: "sensor_id", 1: "timedelta"}).set_index('sensor_id')


# In[ ]:

df['seconds'] = df.timedelta.map(lambda x: x.total_seconds())
df['days'] = df.timedelta.map(lambda x: x.days)


# # Setup NoDataBot slack bot

# In[ ]:

slack_url = c.get('slack', 'webhook')
username = 'NoDataBot'
channel = "junk" # we don't want to clutter up everything
emoji = ':warning:'
title = 'No data for sensor'
description = 'We have not found data for the last 24 hours (= 86400 seconds) for the following sensor. The result is expressed in seconds.'

slack = Slack(url=slack_url, username=username, channel=channel, emoji=emoji)


# # Create the alerts and send

# In[ ]:

alerts.create_alerts(df, hp, 'no_sensor_data', slack, title, description, column='seconds')
