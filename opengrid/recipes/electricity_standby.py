
# coding: utf-8

# In[1]:

# opengrid imports
from opengrid.library import misc, houseprint, caching
from opengrid.library.analysis import DailyAgg
from opengrid import config
c=config.Config()

# other imports
import pandas as pd
import charts
import numpy as np
import os
import datetime as dt
import pytz
BXL = pytz.timezone('Europe/Brussels')


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
plt.rcParams['figure.figsize'] = 12,8


# In[2]:

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


# In[3]:

hp.sync_tmpos()


# In[ ]:

# The first time, this will take a very looong time to get all the detailed data for building the cache
# Afterwards, this is quick
starttime = dt.time(0, tzinfo=BXL)
endtime = dt.time(5, tzinfo=BXL)
caching.cache_results(hp=hp, sensors=sensors, resultname='elec_min_night_0-5', AnalysisClass=DailyAgg,  
                      agg='min', starttime=starttime, endtime=endtime)

caching.cache_results(hp=hp, sensors=sensors, resultname='elec_max_night_0-5', AnalysisClass=DailyAgg, 
                      agg='max', starttime=starttime, endtime=endtime)


# In[ ]:

cache_min = caching.Cache(variable='elec_min_night_0-5')
cache_max = caching.Cache(variable='elec_max_night_0-5')
dfdaymin = cache_min.get(sensors=sensors)
dfdaymax = cache_max.get(sensors=sensors)
dfdaymin.info()


# The next plot shows that some periods are missing.  Due to the cumulative nature of the electricity counter, we still have the total consumption.  However, it is spread out of the entire period.  So we don't know the standby power during these days, and we have to remove those days.  

# In[ ]:

if DEV:
    sensor = hp.search_sensors(key='3aa4')[0]
    df = sensor.get_data(head=pd.Timestamp('20151117'), tail=pd.Timestamp('20160104'))
    charts.plot(df, stock=True, show='inline')


# In[ ]:

def is_submeter(sensor, dfdaymin, dfdaymax):
    """
    Return True if this sensor is a sub-meter
    
    sensor = sensor object
    """
    
    
    other_sensors = sensor.device.get_sensors(sensortype='electricity')
    other_sensors.remove(sensor)
    if len(other_sensors) == 0:
        print("\n{} - {}: no other sensors, this must be main.".format(sensor.device.key, sensor.description))
        return False
    else:
        print("\n{} - {}: comparing with:".format(sensor.device.key, sensor.description))
        for o in other_sensors:
            # we only check the values for last day
            print("* {}:".format(o.description))
            sensormin = dfdaymin.ix[-1,sensor.key]
            sensormax = dfdaymax.ix[-1,sensor.key]
            try:
                othermin = dfdaymin.ix[-1].dropna()[o.key]
                othermax = dfdaymax.ix[-1].dropna()[o.key]
            except:
                print("  No data found for sensor {}".format(o.description))
                pass
            else:
                if (sensormin <= othermin) and (sensormax <= othermax):
                    print("  {} has lower daily min AND max, so it is a submeter.".format(sensor.description))                   
                    return True
                else:
                    print("  {} has higher daily min and/or max, we look further.".format(sensor.description))
        else:
            print("All other sensors have no data OR lower daily min and max. {} must be main.".format(sensor.description))
            return False
    
    


# In[ ]:

# The function is_submeter makes one obvious error: see results for FL03001566
for col in dfdaymin:
    is_submeter(hp.find_sensor(col), dfdaymin, dfdaymax)


# In[ ]:

# Clean out the data: 
# First remove sensors that are submeters
for col in dfdaymin:
    if is_submeter(hp.find_sensor(col), dfdaymin, dfdaymax):
        print("\n!!Removing submeter {}".format(col))
        dfdaymin = dfdaymin.drop(col, axis=1)
# Now remove days with too low values to be realistic
dfdaymin[dfdaymin < 10] = np.nan
# Now remove days where the minimum=maximum (within 1 Watt difference)
dfdaymin[(dfdaymax - dfdaymin) < 1] = np.nan


# In[ ]:

dfdaymin.info()


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
now = pd.Timestamp('now', tz=BXL)
dt_start_of_last_day = pd.Timestamp(dfdaymin.index[-1].date(), tz=BXL)
dt_end_of_last_day = dt_start_of_last_day + pd.Timedelta(hours=endtime.hour, minutes=endtime.minute)
sensors = map(hp.find_sensor, dfdaymin.columns)
df_details = hp.get_data(sensors = sensors, head=dt_start_of_last_day, tail=dt_end_of_last_day)
df_details.fillna(method='ffill', inplace=True)
df_details.fillna(method='bfill', inplace=True)


# ### Boxplot approach.  Possible for a period of maximum +/- 2 weeks. 

# In[ ]:

# choose a period
look_back_days = 10
dt_start_of_period = dt_start_of_last_day - pd.Timedelta(days=look_back_days-1)
dfdaymin_period = dfdaymin.ix[dt_start_of_period:].dropna(axis=1, how='all')


# In[ ]:

box = [dfdaymin_period.loc[i,:].dropna().values for i in dfdaymin_period.index]
for sensor in dfdaymin_period.columns:
    fig=plt.figure(figsize=(10,5))
    ax1=plt.subplot(121)
    ax1.boxplot(box, positions=range(len(box)), notch=False)
    ax1.plot(range(len(box)), dfdaymin_period[sensor], 'rD', ms=10, label='Standby power')
    xticks = [x.strftime(format='%d/%m') for x in dfdaymin_period.index]
    plt.xticks(range(len(box)), xticks, rotation='vertical')
    plt.title(hp.find_sensor(sensor).device.key + ' - ' + hp.find_sensor(sensor).description)
    ax1.grid()
    ax1.set_ylabel('Watt')
    plt.legend(numpoints=1, frameon=False)
    ax2=plt.subplot(122)
    try:
        ax2.plot_date(df_details[sensor].index, df_details[sensor].values, 'b-', label='Last night')
        ax2.xaxis_date(tz=BXL) #Put timeseries plot in local time
        # rotate the labels
        plt.xticks(rotation='vertical')
        ax2.set_ylabel('Watt')
        ax2.set_xlabel('Local time (BXL)')
        ax2.grid()
        
        xax = ax2.get_xaxis() # get the x-axis
        xax.set_major_locator(HourLocator())
        xax.set_minor_locator(MinuteLocator(30))
        
        adf = xax.get_major_formatter() # the the auto-formatter

        adf.scaled[1./24] = '%H:%M'  # set the < 1d scale to H:M
        adf.scaled[1.0] = '%Y-%m-%d' # set the > 1d < 1m scale to Y-m-d
        adf.scaled[30.] = '%Y-%m' # set the > 1m < 1Y scale to Y-m
        adf.scaled[365.] = '%Y' # set the > 1y scale to Y

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
look_back_days = 40
dt_start_of_period = dt_start_of_last_day - pd.Timedelta(days=look_back_days-1)
dfdaymin_period = dfdaymin.ix[dt_start_of_period:].dropna(axis=1, how='all')
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
    locs, lables=plt.xticks()
    xticks = [x.strftime(format='%d/%m') for x in num2date(locs)]
    plt.xticks(locs, xticks, rotation='vertical')
    plt.title(hp.find_sensor(sensor).device.key + ' - ' + sensor)
    ax1.grid()
    ax1.set_ylabel('Watt')
    
    ax2=plt.subplot(212)
    try:
        ax2.plot_date(df_details[sensor].index, df_details[sensor].values, 'b-', label='Detailed consumption of last night')
        ax2.xaxis_date(tz=BXL) #Put timeseries plot in local time
        # rotate the labels
        plt.xticks(rotation='vertical')
        ax2.set_ylabel('Watt')
        ax2.set_xlabel('Local time (BXL)')
        ax2.grid()
        
        xax = ax2.get_xaxis() # get the x-axis
        xax.set_major_locator(HourLocator())
        xax.set_minor_locator(MinuteLocator(30))
        
        adf = xax.get_major_formatter() # the the auto-formatter

        adf.scaled[1./24] = '%H:%M'  # set the < 1d scale to H:M
        adf.scaled[1.0] = '%Y-%m-%d' # set the > 1d < 1m scale to Y-m-d
        adf.scaled[30.] = '%Y-%m' # set the > 1m < 1Y scale to Y-m
        adf.scaled[365.] = '%Y' # set the > 1y scale to Y
        
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



