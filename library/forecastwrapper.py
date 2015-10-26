# -*- coding: utf-8 -*-

__author__ = 'Jan'

import forecastio
import datetime as dt
from geopy import GoogleV3
from dateutil import rrule
import numpy as np
import pandas as pd
from copy import copy

class Weather(object):
    """
        Abstract Class
        Object that contains Weather Data from Forecast.io for multiple days as a Pandas Dataframe.
        Use Weather_Days and Weather_Hours for different resolutions.

        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.
    """
    def __init__(self, api_key, location, start, end=None, tz=None):
        """
            Constructor

            Parameters
            ----------
            api_key: string
                Forecast.io API Key
            location: string
                City, address, POI
            start: datetime-like object
                start of the interval to be searched
            end: datetime-like object (optional, default=None)
                end of the interval to be searched, if None, use current time
            tz: timezone string (optional)
                The lookup always happens in the timezone of the location
                tz specifies the timezone of the response.
                If none, tz is the timezone of the location
        """
        if end is None:
            end = pd.Timestamp('now', tz=tz)

        self.api_key = api_key

        #input location
        self._location = location
        #processed location
        self.geolocator = GoogleV3()
        self.location = self.geolocator.geocode(self._location)

        self.df = self.get_weather_df(start, end, tz)

    def _dayset(self, start, end):
        """
            Takes a start and end date and returns a set containing all dates between start and end

            Parameters
            ----------
            start: datetime-like object
            end: datetime-like object 

            Returns
            -------
            set of datetime objects
        """
        
        res = []
        for dt in rrule.rrule(rrule.DAILY, dtstart=start, until=end):
            res.append(dt)
        return sorted(set(res))

    def get_weather_df(self, start, end, tz=None):
        """
            Creates a Pandas DataFrame with all weather info.

            Parameters
            ----------
            start: datetime-like object
            end: datetime-like object 
            tz: timezone string (optional)
                default response is in the timezone of the weather location
        """
        #create list of time series per day
        dayList = [self.get_weather_ts(day) for day in self._dayset(start, end)]

        #concat list to dataframe
        res = pd.concat(dayList)

        #convert UNIX timestamps to datetime
        res['time'] = pd.DatetimeIndex(res['time'].astype('datetime64[s]'))

        #set time column as index
        res.set_index('time',inplace=True)
        #time returned by Forecast.io is always in UTC
        res = res.tz_localize('UTC')

        #save the dataframe in the timezone specified
        #if no tz is specified, use the timezone of the location
        if tz is None:
            tz = self.get_timezone()
        else:
            pass #tz = tz
        res = res.tz_convert(tz)

        return res

    def get_timezone(self):
        """
            Get the timezone of the weather location

            Returns
            -------
            timezone string
        """
        tz = self.geolocator.timezone((self.location.latitude,self.location.longitude))
        return tz.zone

class Weather_Days(Weather):
    """
        Weather_Days object contains a Pandas DataFrame with all weather data 
        at daily resolution from Forecast.io.
        Additionally, heating degreedays are added by default for a base
        temperature of 16.5 degC. Different base temperature can be provided and 
        also cooling degreedays can be added
        
        NOTE
        ====
        Forecast.io allows 1000 requests per day for a free account. 
        Each requested day is 1 request. Paid accounts are available. 

    """

    def __init__(self,
                 api_key,
                 location,
                 start,
                 end = None,
                 tz = None,
                 heatingDegreeDays = True,
                 heatingBaseTemps = [16.5],
                 coolingDegreeDays = False,
                 coolingBaseTemps = [18],
                 daytimeCloudCover = True,
                 daytimeTemperature = True
                 ):
        """
            Constructor

            Parameters
            ----------
            api_key: string
                Forecast.io API Key
            location: string
                City, address, POI
            start: datetime object
                start of the interval to be searched
            end: datetime object (optional, default=None)
                end of the interval to be searched, if None, use current time.
            tz: timezone string (optional)
                The lookup always happens in the timezone of the location
                tz specifies the timezone of the response.
                If none, tz is the timezone of the location
            heatingDegreeDays: bool (optional, default: True)
                Add heating degree days to the dataframe
            heatingBaseTemps: list of numbers (optional, default 16.5)
                List of possible base temperatures for which to calculate heating degree days
            coolingDegreeDays: bool (optional, default: False)
                Add cooling degree days to the dataframe
            coolingBaseTemps: list of numbers (optional, default 18)
                List of possible base temperatures for which to calculate cooling degree days
            daytimeCloudCover: bool (optional, default: True)
                Include average Cloud Cover during daytime hours (from sunrise to sunset)
            daytimeTemperature: bool (optional, default: True)
                Include average Temperature during daytime hours (from sunrise to sunset)
        """

        #we need data from 2 days earlier to calculate degree days
        if heatingDegreeDays or coolingDegreeDays:
            start = start - pd.Timedelta(days = 2)

        self.daytimeCloudCover = daytimeCloudCover
        self.daytimeTemperature = daytimeTemperature

        #init the superclass
        super(Weather_Days, self).__init__(api_key, location, start, end, tz)

        #add degree days to dataframe
        if heatingDegreeDays or coolingDegreeDays:
            self.df = self._addDegreeDays(self.df, heatingDegreeDays, heatingBaseTemps, coolingDegreeDays, coolingBaseTemps)

    def get_weather_ts(self, date):
        """
            Get one single row of the final dataframe, representing data from a single day.

            Parameters
            ----------
            date: datetime object

            Returns
            -------
            Pandas Dataframe
        """
        #get forecast
        forecast = forecastio.load_forecast(self.api_key, self.location.latitude, self.location.longitude, date)
        day_data = forecast.daily().data[0].d

        #calculate average temperature and add to day_data
        avg_temp = self._get_daily_avg(forecast = forecast, key = 'temperature')
        day_data.update({'temperature':avg_temp})

        #add daytime Cloud Cover
        if self.daytimeCloudCover:
            dtcc = self._get_daytime_avg(forecast = forecast, key= 'cloudCover')
            day_data.update({'daytimeCloudCover':dtcc})
        #add daytime Temperature
        if self.daytimeTemperature:
            dtt = self._get_daytime_avg(forecast = forecast, key='temperature')
            day_data.update({'daytimeTemperature':dtt})

        #convert to a single row in a dataframe and return
        daylist = [pd.Series(day_data)]
        return pd.concat(daylist,axis=1).T

    def _get_daytime_avg(self, forecast, key):
        """
        Calculate the average for a given value during daytime hours (from sunrise to sunset)
        :param forecast: Forecast object
        :param key: String
            parameter to average (eg. 'cloudCover')
        :return: float
        """
        #extract values from forecast
        try:
            values = [hour.d[key] for hour in forecast.hourly().data]
        except KeyError:
            return None

        #make a time series
        time = [hour.d['time'] for hour in forecast.hourly().data]
        ts = pd.Series(data = values, index=time)
        ts.index = pd.DatetimeIndex(ts.index.astype('datetime64[s]'))

        #get sunrise and sunset
        sunrise = dt.datetime.utcfromtimestamp(forecast.daily().data[0].d['sunriseTime'])
        sunset = dt.datetime.utcfromtimestamp(forecast.daily().data[0].d['sunsetTime'])

        #truncate timeseries
        ts = ts.truncate(before=sunrise, after=sunset)

        #return mean of truncated timeseries
        return round(ts.mean(), 2)

    def _get_daily_avg(self, forecast, key):
        """
            Calculate the average daily value for a given forecast and a given key from the hourly values

            Parameters
            ----------
            forecast: Forecast object
            key: string
                parameter to average (eg. 'temperature')

            Returns
            -------
            float
        """
        #make a list of all hourly values for the given key
        values = [hour.d[key] for hour in forecast.hourly().data]
        #calculate the mean, round to 2 significant figures and return
        return round(np.mean(values),2)

    def _addDegreeDays(self, df, heatingDegreeDays, heatingBaseTemps, coolingDegreeDays, coolingBaseTemps):
        """
            Takes a dataframe of daily values and adds degree days.
            Degree days are calculated from a temperature equivalent: 0.6 * tempDay0 + 0.3 * tempDay-1 + 0.1 * tempDay-2
            Because we need the two previous days to calculate day0, the resulting dataframe will be 2 days shorter
                (you should pass dataframes that have two days more than you want)

            Parameters
            ----------
            df: Pandas Dataframe
                should contain a column named 'temperature'
            heatingDegreeDays: bool
                add heating degree days
            heatingBaseTemps: list of numbers
                base temperatures to be used to calculate heating degree days
            coolingDegreeDays: bool
                add cooling degree days
            coolingBaseTemps: list of numbers
                base temperatures to be used to calculate cooling degree days

            Returns
            -------
            Pandas Dataframe
        """
        #select temperature column from dataframe
        temp = df['temperature']
        #calculate the temperature equivalent, using two days before day0
        temp_equiv = [0.6 * temp.values[ix] + 0.3 * temp.values[ix-1] + 0.1 * temp.values[ix-2] for ix in range(0,len(df)) if ix>1]

        #the response will be 2 days shorter
        res = copy(df[2:])

        #add degree days to response
        if heatingDegreeDays:
            for baseTemp in heatingBaseTemps:
                res['heatingDegreeDays{}'.format(baseTemp)] = [max(0, baseTemp - val) for val in temp_equiv]
        if coolingDegreeDays:
            for baseTemp in coolingBaseTemps:
                res['coolingDegreeDays{}'.format(baseTemp)] = [max(0, val - baseTemp) for val in temp_equiv]

        return res

class Weather_Hours(Weather):
    """
        Weather_Hours object contains a Pandas DataFrame with all weather data hour from Forecast.io

        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.

    """
    def __init__(self, api_key, location, start, end=None, tz=None):
        """
            Constructor

            Parameters
            ----------
            api_key: string
                Forecast.io API Key
            location: string
                City, address, POI
            start: datetime object
                start of the interval to be searched
            end: datetime object (optional, default=None)
                end of the interval to be searched, if None, use current time
            tz: timezone string (optional)
                The lookup always happens in the timezone of the location
                tz specifies the timezone of the response.
                If none, tz is the timezone of the location
        """

        super(Weather_Hours, self).__init__(api_key, location, start, end, tz)

    def get_weather_ts(self, date):
        """
            Create a Dataframe for a single day, a row per hour

            Parameters
            ----------
            date: datetime-like object

            Returns
            -------
            Pandas Dataframe
        """
        #get forecast
        forecast = forecastio.load_forecast(self.api_key, self.location.latitude, self.location.longitude, date)

        #create a Pandas Series per hour
        day_data = forecast.hourly().data
        hourlist = [pd.Series(hour.d) for hour in day_data]

        #concatenate hourly series, transform and return
        return pd.concat(hourlist,axis=1).T