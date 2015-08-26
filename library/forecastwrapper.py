__author__ = 'Jan'

import datetime, forecastio
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
    def __init__(self, api_key, location, start, end=datetime.datetime.now(), tz=None):
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
            end: datetime object (optional, default=datetime.now())
                end of the interval to be searched
            tz: timezone string (optional)
                The lookup always happens in the timezone of the location
                tz specifies the timezone of the response.
                If none, tz is the timezone of the location
        """

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
            start: datetime object
            end: datetime object

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
            start: datetime object
            end: datetime object
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
        Weather_Days object contains a Pandas DataFrame with all weather data per day from Forecast.io
        + average temperature and 8 different types of degreedays are calculated

        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.

    """

    def __init__(self, api_key, location, start, end=datetime.datetime.now(), tz=None):
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
            end: datetime object (optional, default=datetime.now())
                end of the interval to be searched
            tz: timezone string (optional)
                The lookup always happens in the timezone of the location
                tz specifies the timezone of the response.
                If none, tz is the timezone of the location
        """

        #we need data from 2 days earlier to calculate degree days
        start = start - datetime.timedelta(days = 2)

        #init the superclass
        super(Weather_Days, self).__init__(api_key, location, start, end, tz)

        #add degree days to dataframe
        self.df = self._addDegreeDays(self.df)

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

        #convert to a single row in a dataframe and return
        daylist = [pd.Series(day_data)]
        return pd.concat(daylist,axis=1).T

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

    def _addDegreeDays(self, df):
        """
            Takes a dataframe of daily values and adds degree days.
            Degree days are calculated from a temperature equivalent: 0.6 * tempDay0 + 0.3 * tempDay-1 + 0.1 * tempDay-2
            Because we need the two previous days to calculate day0, the resulting dataframe will be 2 days shorter
                (you should pass dataframes that have two days more than you want)

            4 types of Heating Degree Days are calculated with baselines on 0, 15, 16.5 and 18
            4 types of Cooling Degree Days are calculated with baselines on 15, 16.5, 18 and 24

            Parameters
            ----------
            df: Pandas Dataframe

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
        res['heatingDegreeDays0'] = [max(0, 0 - val) for val in temp_equiv]
        res['heatingDegreeDays15'] = [max(0, 15 - val) for val in temp_equiv]
        res['heatingDegreeDays16.5'] = [max(0, 16.5 - val) for val in temp_equiv]
        res['heatingDegreeDays18'] = [max(0, 18 - val) for val in temp_equiv]

        res['coolingDegreeDays15'] = [max(0, val - 15) for val in temp_equiv]
        res['coolingDegreeDays16.5'] = [max(0, val - 16.5) for val in temp_equiv]
        res['coolingDegreeDays18'] = [max(0, val - 18) for val in temp_equiv]
        res['coolingDegreeDays24'] = [max(0, val - 24) for val in temp_equiv]

        return res

class Weather_Hours(Weather):
    """
        Weather_Hours object contains a Pandas DataFrame with all weather data hour from Forecast.io

        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.

    """
    def __init__(self, api_key, location, start, end=datetime.datetime.now(), tz=None):
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
            end: datetime object (optional, default=datetime.now())
                end of the interval to be searched
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
            date: datetime object

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