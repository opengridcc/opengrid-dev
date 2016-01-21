
# coding: utf-8

# ### This script shows how to use the existing code in opengrid to create a baseload electricity consumption benchmark. 

# In[1]:

import os, sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import HourLocator, DateFormatter, AutoDateLocator
import datetime as dt
import time
import pytz
import pandas as pd
import pdb

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library import houseprint
from opengrid.library import fluksoapi
from opengrid.library import config
c=config.Config()

# find tmpo
sys.path.append(c.get('tmpo', 'folder'))
import tmpo

get_ipython().magic(u'matplotlib inline')
plt.rcParams['figure.figsize'] = 12,8


# ### Script settings

# In[2]:

number_of_days = 10


# ### We create one big dataframe, the columns are the sensors of type *electricity*

# In[3]:

hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')


# In[4]:

start = pd.Timestamp(time.time() - number_of_days*86400, unit='s')
print start


# In[5]:

tmpos = tmpo.Session()
sensors = hp.get_sensors_by_type('electricity')
#sensors.remove('b325dbc1a0d62c99a50609e919b9ea06')
dfcum = tmpos.dataframe(sids=sensors, head=start)
print "Size of dataframe before resampling: {}".format(dfcum.shape)
#print dfcum.head()
dfi = dfcum.resample(rule='60s', how='max')
dfi = dfi.interpolate(method='time')
dfi = dfi.diff()*3600/60
print "Size of dataframe after resampling: {}".format(dfi.shape)


# In[6]:

# plot a few dataframes to inspect them
for sensor in sensors[:5]:
    if sensor in dfi.columns:
        plt.figure()
        dfi[sensor].plot()
        plt.savefig(sensor+'.png')


# We define two low-level functions 

# In[7]:

def testvalid(row):
    return row['maxima'] > 0 and row['maxima'] <> row['minima']


# In[8]:

def get_minima(sensor):
    """
    Get the standby consumption for the covered days as an array.  
    Take care of days where this sensor has NO VALID stanby consumption
    """
    
    global minima
    
    res = np.ndarray(len(minima))
    for i,df in enumerate(minima):
        try: 
            res[i] = df[sensor]
        except:
            res[i] = np.nan
            
    return res


# ## Data handling
# 
# We have to filter out the data, we do three things:
# 
# 1. split the data in dataframes per day 
# 2. filter out the night-time hours (between 00h00 and 05h00)
# 3. we check if the resulting time series contain enough variation (negatives and constant signals are filtered out)

# In[9]:

df=dfi


# In[10]:

index_slices = [] # will contain the correct index slices for each of the analysed nights
minima = [] # each element in minima is a dataframe with standby consumption per valid sensor
valid_sensors = set() # we keep track of all sensors that yield a valid standby consumption for at least one day.


# find the date for which we still have the full night (between 01:00 and 05:00).  We will store it as datetime at 00:00 (local time)
hour = df.index[-1].hour # the hour of the last index.  
if hour >= 5:
    last_day = df.index[-1] - dt.timedelta(hours=hour)
else:
    last_day = df.index[-1] - dt.timedelta(days=1, hours=hour)

for day in range(number_of_days)[::-1]:
    #pdb.set_trace()
    dt_start = last_day - dt.timedelta(days=day) + dt.timedelta(hours=1) # start slicing at 01:00 local time
    dt_stop = last_day - dt.timedelta(days=day) + dt.timedelta(hours=5) # stop slicing at 05:00 local time
       
    df_night = df.ix[dt_start:dt_stop] # contains only data for a single night
    index_slices.append(df_night.index.copy())
        
    df_results = pd.DataFrame(index=df.columns)  #df_results contains the results of the analysis for a single night.  Index = sensorid
    df_results['minima'] = df_night.min(axis=0)
    df_results['maxima'] = df_night.max(axis=0)
    df_results['valid'] = df_results.apply(testvalid, axis=1)
    
    minima.append(df_results['minima'].ix[df_results.valid])
    valid_sensors.update(set(minima[-1].index.tolist()))
  


# ## Plots
# 
# The next plots are the current benchmarks, anonymous. The left figure shows where the given sensor (or family) is situated compared to all other families.  The right plot shows the night-time consumption for this night. 
# 
# In a next step, it would be nice to create an interactive plot (D3.js?) for the right side: it should show the night-time consumption **for the day over which the mouse hovers in the left graph**.  

# In[11]:

index_slices


# In[12]:

index_slices_days = [x[0] for x in index_slices[1:]]
index = pd.DatetimeIndex(freq='D', start=index_slices_days[0], periods=number_of_days)
print index


# In[13]:

df_=pd.concat(minima, axis=1)
df_.columns = index
df_


# In[14]:

df_statistics = df_.describe().T


# In[15]:

df_statistics


# In[16]:

df_.T.index


# In[17]:

for sensor in list(valid_sensors)[:]:
    plt.figure(figsize=(10,8))
    ax1=plt.subplot(211)
    ax1.plot_date(df_statistics.index, df_statistics[u'25%'], '-', lw=2, color='g', label=u'25%')
    ax1.plot_date(df_statistics.index, df_statistics[u'50%'], '-', lw=2, color='orange', label=u'50%')
    ax1.plot_date(df_statistics.index, df_statistics[u'75%'], '-', lw=2, color='r', label=u'75%')
    
    ax1.plot_date(df_.T.index, df_.T[sensor], 'rD', ms=7) 
    
    xticks = [x.strftime(format='%d/%m') for x in df_statistics.index]
    locs, lables=plt.xticks()
    plt.xticks(locs, xticks, rotation='vertical')
    plt.title(hp.get_flukso_from_sensor(sensor))
    ax1.grid()
    ax1.set_ylabel('Watt')
    
    ax2=plt.subplot(212)
    try:
        ax2.plot_date(index_slices[-1], df.ix[index_slices[-1]][sensor], 'b-', label='Afgelopen nacht')
        # rotate the labels
        plt.xticks(rotation='vertical')
        plt.legend()
    except:
        pass


# In[18]:

try:
    valid_sensors.remove('565de0a7dc64d8370aa321491217b85f') # the FLM of 3E does not fit in household standby benchmark
except:
    pass

for sensor in valid_sensors:
    plt.figure(figsize=(10,5))
    ax1=plt.subplot(121)
    box = [x.values for x in minima]
    ax1.boxplot(box, positions=range(days), notch=False)
    ax1.plot(range(days), get_minima(sensor), 'rD', ms=10, label=hp.get_flukso_from_sensor(sensor))
    xticks = [x[0].strftime(format='%d/%m') for x in index_slices]
    plt.xticks(range(days), xticks, rotation='vertical')
    ax1.grid()
    ax1.set_ylabel('W')
    plt.legend()
    #ax1.set_xticklabels([t.strftime(format='%d/%m') for t in df_all_perday.index.tolist()])

    ax2=plt.subplot(122)
    try:
        ax2.plot_date(index_slices[-1], df.ix[index_slices[-1]][sensor], 'b-')
        # rotate the labels
        plt.xticks(rotation='vertical')
    except:
        pass
    
    plt.savefig(os.path.join(path_to_data, 'figures', hp.get_flukso_from_sensor(sensor)+'png'), dpi=100)


# The stuff below were some experiments from the developer meeting on 10/10/2014

# In[19]:

hp.fluksosensors['FL03001556']


# In[20]:

plt.rcParams['figure.figsize'] = 12,8

ts=df.ix[index_slices[-1]]['1a1dac9c2ac155f95c58bf1d4f4b7d01'].copy()
ts.hist(bins=np.arange(0, 1000, 10))


# In[21]:

plt.plot(np.sort(ts.values)[::-1])
y,x = np.histogram(ts.values, bins=np.arange(0, 1000, 10))
#plt.plot(x,y)


# In[22]:

hp.fluksosensors['FL02000678']


# In[23]:

df['c1a78eacaa6a82d3257a278d3e99088a'].ix['20141007':].plot()


# In[24]:

df.index[-5:]


# In[25]:

ind = df.index.tz_convert(pytz.timezone('Europe/Brussels'))
ind[-1].date() - dt.timedelta(days=10)


# In[26]:

valid_sensors


# In[27]:

hp.get_all_sensors()


# In[28]:

hp.get_all_fluksosensors()['FL03001550']


# In[29]:



