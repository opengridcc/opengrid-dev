
# coding: utf-8

# ### This script shows how to use the existing code in opengrid to create an interactive timeseries plot.

# In[ ]:

import os
import pytz
BXL = pytz.timezone('Europe/Brussels')
import pandas as pd
import charts
from time import time

from opengrid import config
c=config.Config()
DEV = c.get('env', 'type') == 'dev' # DEV is True if we are in development environment, False if on the droplet

from opengrid.library import houseprint


# ### Script settings
# 

# In[ ]:

number_of_days = 7


# ### We create a dataframe per sensor

# In[ ]:

hp = houseprint.Houseprint()


# In[ ]:

start = pd.Timestamp(time() - number_of_days*86400, unit='s')


# In[ ]:

sensors = hp.get_sensors()
#sensors.remove('b325dbc1a0d62c99a50609e919b9ea06')


# In[ ]:

for sensor in sensors:
    s = sensor.get_data(head=start)
    # do an ugly operation to get localtime.  A simple tz_convert does not work: charts will always plot 
    # in UTC.
    new_index_list = []
    for index_utc in s.index:
        new_index_list.append(index_utc + index_utc.tz_convert(BXL).utcoffset())
    s.index = pd.DatetimeIndex(new_index_list)
    try:    
        # plot with charts (don't show it) and save html
        charts.plot(pd.DataFrame(s), stock=True, 
                    save=os.path.join(c.get('data', 'folder'), 'figures', 'TimeSeries_'+sensor.key+'.html'), show=False)
    except Exception as e:
        print(e)


# In[ ]:



