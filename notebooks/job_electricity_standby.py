
# coding: utf-8

# In[ ]:

# opengrid imports
from opengrid.library import misc, houseprint, caching, analysis
from opengrid import config
c=config.Config()

# other imports
import os
import pandas as pd
import charts
import numpy as np


# configuration for the plots
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


# In[ ]:

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
#hp.sync_tmpos()


# In[ ]:

# The first time, this will take a very looong time to get all the detailed data for building the cache
# Afterwards, this is quick
caching.cache_results(hp=hp, sensors=sensors, function='daily_min', resultname='elec_daily_min')
caching.cache_results(hp=hp, sensors=sensors, function='daily_max', resultname='elec_daily_max')


# In[ ]:

cache_min = caching.Cache(variable='elec_daily_min')
cache_max = caching.Cache(variable='elec_daily_max')
dfdaymin = cache_min.get(sensors=sensors)
dfdaymax = cache_max.get(sensors=sensors)


# The next plot shows that some periods are missing.  Due to the cumulative nature of the electricity counter, we still have the total consumption.  However, it is spread out of the entire period.  So we don't know the standby power during these days, and we have to remove those days.  

# In[ ]:


# Clean out the data: 
# First remove days with too low values to be realistic
dfdaymin[dfdaymin < 10] = np.nan
# Now remove days where the minimum=maximum (within 1 Watt difference)
dfdaymin[(dfdaymax - dfdaymin) < 1] = np.nan


# In[ ]:

if DEV:
    charts.plot(dfdaymin, stock=True, show='inline')


# In[ ]:

standby_statistics = dfdaymin.T.describe(percentiles=[0.1,0.5,0.9]).T


# In[ ]:

if DEV:
    charts.plot(standby_statistics[['10%', '50%', '90%']], stock=True, show='inline')


# In[ ]:

# Get detailed profiles for the last day
now = pd.Timestamp('now', tz='UTC')
start_of_day = now - pd.Timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)




# ### Boxplot approach.  Possible for a period of maximum +/- 2 weeks. 

# In[ ]:

# choose a period
look_back_days = 10
start = now - pd.Timedelta(days=look_back_days)
dfdaymin_period = dfdaymin.ix[start:].dropna(axis=1, how='all')
sensors = map(hp.find_sensor, dfdaymin_period.columns)
df_details = hp.get_data(sensors = sensors, head=start_of_day)
# In[ ]:

box = [dfdaymin_period.loc[i,:].dropna().values for i in dfdaymin_period.index]
for sensor in dfdaymin_period.columns:
    plt.figure(figsize=(10,5))
    ax1=plt.subplot(121)
    ax1.boxplot(box, positions=range(len(box)), notch=False)
    ax1.plot(range(len(box)), dfdaymin_period[sensor], 'rD', ms=10, label='Sluipverbruik')
    xticks = [x.strftime(format='%d/%m') for x in dfdaymin_period.index]
    plt.xticks(range(len(box)), xticks, rotation='vertical')
    plt.title(hp.find_sensor(sensor).device.key + ' - ' + sensor)
    ax1.grid()
    ax1.set_ylabel('Watt')
    plt.legend(numpoints=1, frameon=False)
    ax2=plt.subplot(122)
    try:
        ax2.plot_date(df_details[sensor].index, df_details[sensor].values, 'b-', label='Afgelopen nacht')
        #ax2.xaxis_date() #Put timeseries plot in local time
        # rotate the labels
        plt.xticks(rotation='vertical')
        ax2.set_ylabel('Watt')
        ax2.grid()
        plt.legend(loc='upper right', frameon=False)
        plt.tight_layout()
    except Exception as e:
        print(e)
    else:
        plt.savefig(os.path.join(c.get('data', 'folder'), 'figures', 'standby_horizontal_'+sensor+'.png'), dpi=100)
        pass
    
    if not DEV:
        plt.close()


# ### Percentile approach.  Useful for longer time periods, but tweaking of graph still needed

# In[ ]:

# choose a period
look_back_days = 100
start = now - pd.Timedelta(days=look_back_days)
dfdaymin_period = dfdaymin.ix[start:].dropna(axis=1, how='all')
df = dfdaymin_period.join(standby_statistics[['10%', '50%', '90%']], how='left')    


# In[ ]:

for sensor in dfdaymin_period.columns:
    plt.figure(figsize=(10,8))
    ax1=plt.subplot(211)
    ax1.plot_date(df.index, df[u'10%'], '-', lw=2, color='g', label=u'10% percentile')
    ax1.plot_date(df.index, df[u'50%'], '-', lw=2, color='orange', label=u'50% percentile')
    ax1.plot_date(df.index, df[u'90%'], '-', lw=2, color='r', label=u'90% percentile')
    ax1.plot_date(df.index, df[sensor], 'rD', ms=7, label='Your standby power') 
    ax1.legend()
    xticks = [x.strftime(format='%d/%m') for x in df.index]
    locs, lables=plt.xticks()
    plt.xticks(locs, xticks, rotation='vertical')
    plt.title(hp.find_sensor(sensor).device.key + ' - ' + sensor)
    ax1.grid()
    ax1.set_ylabel('Watt')
    
    ax2=plt.subplot(212)
    try:
        ax2.plot_date(df_details[sensor].index, df_details[sensor].values, 'b-', label='Afgelopen nacht')
        #ax2.xaxis_date() #Put timeseries plot in local time
        # rotate the labels
        plt.xticks(rotation='vertical')
        ax2.set_ylabel('Watt')
        ax2.grid()
        plt.legend(loc='upper right', frameon=False)
        plt.tight_layout()
    except Exception as e:
        print(e)
    else:
        plt.savefig(os.path.join(c.get('data', 'folder'), 'figures', 'standby_vertical_'+sensor+'.png'), dpi=100)
        pass
    if not DEV:
        plt.close()


# In[ ]:



