
# coding: utf-8

# ## This script shows the visualization of electricity, water and gas consumption using carpet plots
# 
# To get started, first run the 'Synchronize data' script
# 
# #### Imports and paths

# In[ ]:

import os
import time
import pandas as pd


from opengrid_dev import config
from opengrid_dev.library import plotting
from opengrid_dev.library import houseprint

c=config.Config()

try:
    if os.path.exists(c.get('tmpo', 'data')):
        path_to_tmpo_data = c.get('tmpo', 'data')
except:
    path_to_tmpo_data = None

# configuration for the plots
DEV = c.get('env', 'type') == 'dev' # DEV is True if we are in development environment, False if on the droplet
print("Environment configured for development: {}".format(DEV))
if not DEV:
    # production environment: don't try to display plots
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.dates import MinuteLocator, HourLocator, DateFormatter, AutoDateLocator, num2date

if DEV:
    if c.get('env', 'plots') == 'inline':
        get_ipython().magic(u'matplotlib inline')
    else:
        get_ipython().magic(u'matplotlib qt')
else:
    pass # don't try to render plots

plt.rcParams['figure.figsize'] = 16,8

# path to data
path_to_data = c.get('data', 'folder')
if not os.path.exists(path_to_data):
    raise IOError("Provide your path to the data in your config.ini file. ")
else:
    path_to_fig = os.path.join(path_to_data, 'figures')
    if not os.path.isdir(path_to_fig): os.makedirs(path_to_fig)


# In[ ]:

c.get('data','folder')


# ### Loading meta data and user variables

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

end = pd.Timestamp(time.time(), unit='s')
start = end - pd.Timedelta('21 days')


# ### Water sensors

# In[ ]:

water_sensors = hp.get_sensors(sensortype='water')
print("{} water sensors".format(len(water_sensors)))


# In[ ]:

for sensor in water_sensors:
    ts = sensor.get_data(head=start, tail=end)
    if not ts.dropna().empty:
        plotting.carpet(ts, title=' - '.join([sensor.device.key, sensor.description, sensor.key]), zlabel=r'Flow [l/min]')
        plt.savefig(os.path.join(path_to_fig, 'carpet_'+sensor.type+'_'+sensor.key), dpi=100)
        if not DEV:
            plt.close()


# ### Gas sensors

# In[ ]:

gas_sensors = hp.get_sensors(sensortype=('gas'))
print("{} gas sensors".format(len(gas_sensors)))


# In[ ]:

for sensor in gas_sensors:
    ts = sensor.get_data(head=start, tail=end)
    if not ts.dropna().empty:
        plotting.carpet(ts, title=' - '.join([sensor.device.key, sensor.description, sensor.key]), zlabel=r'Gas consumption [W]')
        plt.savefig(os.path.join(path_to_fig, 'carpet_'+sensor.type+'_'+sensor.key), dpi=100)
        if not DEV:
            plt.close()


# ### Electricity sensors

# In[ ]:

elec_sensors = hp.get_sensors(sensortype=('electricity'))
print("{} electricity sensors".format(len(elec_sensors)))


# In[ ]:

for sensor in elec_sensors:
    ts = sensor.get_data(head=start, tail=end)
    if not ts.dropna().empty:
        plotting.carpet(ts, title=' - '.join([sensor.device.key, sensor.description, sensor.key]), zlabel=r'Power [W]')
        plt.savefig(os.path.join(path_to_fig, 'carpet_'+sensor.type+'_'+sensor.key), dpi=100)
        if not DEV:
            plt.close()


# In[ ]:



