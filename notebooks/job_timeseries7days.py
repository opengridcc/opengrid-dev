
# coding: utf-8

# ### This script shows how to use the existing code in opengrid to create a baseload electricity consumption benchmark. 

# In[ ]:

import os
import sys
import inspect
import numpy as np
import datetime as dt
import time
import pytz
import pandas as pd
import pdb
import tmpo
import charts
#import charts

from opengrid import config
from opengrid.library import houseprint

c=config.Config()
DEV = c.get('env', 'type') == 'dev' # DEV is True if we are in development environment, False if on the droplet

if not DEV:
    # production environment: don't try to display plots
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import HourLocator, DateFormatter, AutoDateLocator

if DEV:
    if c.get('env', 'plots') == 'inline':
        get_ipython().magic(u'matplotlib inline')
    else:
        get_ipython().magic(u'matplotlib qt')
else:
    pass # don't try to render plots
plt.rcParams['figure.figsize'] = 12,8


# ### Script settings
# 

# In[ ]:

number_of_days = 7


# ### We create one big dataframe, the columns are the sensors

# In[ ]:

hp = houseprint.Houseprint()
hp.init_tmpo()


# In[ ]:

start = pd.Timestamp(time.time() - number_of_days*86400, unit='s')


# In[ ]:

sensors = hp.get_sensors()
#sensors.remove('b325dbc1a0d62c99a50609e919b9ea06')


# In[ ]:

for sensor in sensors:
    s = sensor.get_data(head=start)
    try:    
        # plot with charts (don't show it) and save html
        charts.plot(pd.DataFrame(s), stock=True, 
                    save=os.path.join(c.get('data', 'folder'), 'figures', 'TimeSeries_'+sensor.key+'.html'), show=False)
    except Exception as e:
        print(e)



