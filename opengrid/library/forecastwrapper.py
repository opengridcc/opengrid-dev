__author__ = 'Jan Pecinovsky'

import datetime as dt
from copy import copy
import forecastio
import geopy
import numpy as np
import pandas as pd
import pytz

from .misc import dayset


class Weather():
    """
        Object that contains Weather Data from Forecast.io for multiple days as a Pandas Dataframe.
        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.
    """

    def __init__(self, api_key, location, start, end=None, tz=None):
        """
            Constructor

            Parameters
            ----------
            api_key : string
                Forecast.io API Key
            location : string OR iterable with 2 floats, latitude and longitude
                String can be City, address, POI. Iterable = [lat,lng]
            start : datetime-like object
                start of the interval to be searched
            end : datetime-like object (optional, default=None)
                end of the interval to be searched, if None, use current time
            tz : timezone string (optional)
                tz specifies the timezone of the response.
                If none, response will be in the timezone of the location
        """

        self.start = start
        if end is None:
            end = pd.Timestamp('now', tz=tz)
        self.end = end

        self.api_key = api_key

        # input location
        if isinstance(location, str):
            self.location = self._get_geolocator().geocode(location)
        else:
            self.location = geopy.location.Location(
                point=geopy.location.Point(latitude=location[0], longitude=location[1]))

        if tz is not None:
            self.tz = tz
        else:
            self.tz = self.lookup_timezone()

        self.forecasts = [self._get_forecast(date=date) for date in dayset(start=start, end=end)]

    def days(self,
             include_average_temperature=True,
             include_temperature_equivalent=True,
             include_heating_degree_days=True,
             heating_base_temperatures=[16.5],
             include_cooling_degree_days=True,
             cooling_base_temperatures=[18],
             include_daytime_cloud_cover=True,
             include_daytime_temperature=True
             ):
        """
        Create a dataframe with all weather data in daily resolution

        Parameters
        ----------
        include_average_temperature : bool (optional, default: True)
            Include automatic calculation of average temperature from hourly data
        include_temperature_equivalent : bool (optional, default: True)
            Include Temperature Equivalent to dataframe
        include_heating_degree_days : bool (optional, default: True)
            Add heating degree days to the dataframe
        heating_base_temperatures : list of numbers (optional, default 16.5)
            List of possible base temperatures for which to calculate heating degree days
        include_cooling_degree_days : bool (optional, default: False)
            Add cooling degree days to the dataframe
        cooling_base_temperatures : list of numbers (optional, default 18)
            List of possible base temperatures for which to calculate cooling degree days
        include_daytime_cloud_cover : bool (optional, default: True)
            Include average Cloud Cover during daytime hours (from sunrise to sunset)
        include_daytime_temperature : bool (optional, default: True)
            Include average Temperature during daytime hours (from sunrise to sunset)

        Returns
        -------
        Pandas Dataframe
        """
        if include_heating_degree_days or include_cooling_degree_days:
            include_temperature_equivalent = True

        if include_temperature_equivalent:
            include_average_temperature = True

        # if temperature_equivalent is needed,
        # we need to add 2 days before the start
        if include_temperature_equivalent:
            self._add_forecast(self.start - pd.Timedelta(days=1))
            self._add_forecast(self.start - pd.Timedelta(days=2))

        day_list = [self._forecast_to_day_series(forecast=forecast,
                                                 include_average_temperature=include_average_temperature,
                                                 include_daytime_cloud_cover=include_daytime_cloud_cover,
                                                 include_daytime_temperature=include_daytime_temperature
                                                 ) for forecast in self.forecasts]

        frame = pd.concat(day_list)
        frame = self._fix_index(frame).sort_index()

        if include_temperature_equivalent:
            frame = self._add_temperature_equivalent(frame)

        if include_heating_degree_days:
            frame = self._add_heating_degree_days(df=frame, base_temperatures=heating_base_temperatures)

        if include_cooling_degree_days:
            frame = self._add_cooling_degree_days(df=frame, base_temperatures=cooling_base_temperatures)

        return frame.truncate(before=self.start, after=self.end)

    def hours(self):
        """
        Create a dataframe with all weather data in hourly resolution

        Returns
        -------
        Pandas Dataframe
        """
        day_list = [self._forecast_to_hour_series(forecast) for forecast in self.forecasts]
        frame = pd.concat(day_list)
        return self._fix_index(frame).truncate(before=self.start, after=self.end)

    def _get_geolocator(self):
        """
            Only create the geolocator if needed

            Returns
            -------
            geopy.geolocator
        """
        if not hasattr(self, 'geolocator'):
            self.geolocator = geopy.GoogleV3()
        return self.geolocator

    def _get_forecast(self, date):
        """
            Get the raw forecast object for a given date

            Parameters
            ----------
            date : datetime-like object

            Returns
            -------
            forecastio forecast
        """
        return forecastio.load_forecast(self.api_key, self.location.latitude, self.location.longitude, date)

    def _get_forecast_dates(self):
        """
        Return a set with the dates of all forecasts in self.forecasts

        Returns
        -------
        set of datetime.date
        """
        dates = []
        for forecast in self.forecasts:
            tz_string = forecast.json['timezone']
            time = forecast.currently().time

            # the time is in UTC, we need to localize it.
            tz = pytz.timezone(tz_string)
            time_utc = tz.fromutc(time)

            dates.append(time_utc.date())
        return set(dates)

    def _add_forecast(self, date):
        """
        Add a forecast to the list of forecasts

        Parameters
        ----------
        date: datetime-like object
        """
        if date.date() not in self._get_forecast_dates():
            self.forecasts.append(self._get_forecast(date))

    def _forecast_to_hour_series(self, forecast):
        """
        Transforms the hourly data of a forecast object to a pandas dataframe

        Parameters
        ----------
        forecast : Forecast object

        Returns
        -------
        Pandas Dataframe

        """
        hour_list = [pd.Series(hour.d) for hour in forecast.hourly().data]
        frame = pd.concat(hour_list, axis=1).T
        return frame

    def _fix_index(self, frame):
        """
        Transform a column of a dataframe to a datetimeindex, set as the index and localize

        Parameters
        ----------
        frame : Pandas Dataframe

        Returns
        -------
        Pandas Dataframe

        """
        frame['time'] = pd.DatetimeIndex(frame['time'].astype('datetime64[s]'))
        frame.set_index('time', inplace=True)
        frame = frame.tz_localize('UTC')
        frame = frame.tz_convert(self.tz)
        return frame

    def lookup_timezone(self):
        """
        Lookup the timezone using the location information

        Returns
        -------
        String (Pytz timezone)
        """
        tz = self._get_geolocator().timezone((self.location.latitude, self.location.longitude))
        return tz.zone

    def _forecast_to_day_series(
            self,
            forecast,
            include_average_temperature,
            include_daytime_cloud_cover,
            include_daytime_temperature
    ):
        """
        Transforms the daily data of a forecast object to a pandas dataframe

        Parameters
        ----------
        include_daytime_cloud_cover : bool
        include_daytime_temperature : bool
        include_average_temperature : bool
        forecast : Forecast Object

        Returns
        -------
        Pandas dataframe

        """
        data = forecast.daily().data[0].d

        if include_average_temperature:
            average_temperature = self._get_daily_average(forecast=forecast, key='temperature')
            data.update({'temperature': average_temperature})
        if include_daytime_cloud_cover:
            daytime_cloud_cover = self._get_daytime_average(forecast=forecast, key='cloudCover')
            data.update({'daytimeCloudCover': daytime_cloud_cover})
        if include_daytime_temperature:
            daytime_temperature = self._get_daytime_average(forecast=forecast, key='temperature')
            data.update({'daytimeTemperature': daytime_temperature})

        frame = [pd.Series(data)]
        return pd.concat(frame, axis=1).T

    def _get_daily_average(self, forecast, key):
        """
        Calculate the average daily value for a given forecast and a given key from the hourly values

        Parameters
        ----------
        forecast : Forecast object
        key : String

        Returns
        -------
        float
        """
        # make a list of all hourly values for the given key
        values = [hour.d[key] for hour in forecast.hourly().data]
        # calculate the mean, round to 2 significant figures and return
        return round(np.mean(values), 2)

    def _get_daytime_average(self, forecast, key):
        """
        Calculate the average for a given value during daytime hours (from sunrise to sunset)

        Parameters
        ----------
        forecast : Forecast Object
        key : String

        Returns
        -------
        float
        """
        # extract values from forecast
        try:
            values = [hour.d[key] for hour in forecast.hourly().data]
        except KeyError:
            return None

        # make a time series
        time = [hour.d['time'] for hour in forecast.hourly().data]
        ts = pd.Series(data=values, index=time)
        ts.index = pd.DatetimeIndex(ts.index.astype('datetime64[s]'))

        # get sunrise and sunset
        sunrise = dt.datetime.utcfromtimestamp(forecast.daily().data[0].d['sunriseTime'])
        sunset = dt.datetime.utcfromtimestamp(forecast.daily().data[0].d['sunsetTime'])

        # truncate timeseries
        ts = ts.truncate(before=sunrise, after=sunset)

        # return mean of truncated timeseries
        return round(ts.mean(), 2)

    def _add_temperature_equivalent(self, df):
        """
        Adds the temperature equivalent to the data frame
        according to the formula: 0.6 * tempDay0 + 0.3 * tempDay-1 + 0.1 * tempDay-2
        Because we need the two previous days to calculate day0, the resulting dataframe will be 2 days shorter
        (you should pass dataframes that have two days more than you want)

        Parameters
        ----------
        df : Pandas Dataframe

        Returns
        -------
        Pandas Dataframe
        """

        # select temperature column from dataframe
        temperature = df['temperature']
        # calculate the temperature equivalent, using two days before day0
        temperature_equivalent = [
            0.6 * temperature.values[ix] + 0.3 * temperature.values[ix - 1] + 0.1 * temperature.values[ix - 2] for ix in
            range(0, len(df)) if ix > 1]

        # the response will be 2 days shorter
        res = copy(df[2:])

        # add the temperature equivalent to the response
        res['temperatureEquivalent'] = temperature_equivalent

        return res

    def _add_heating_degree_days(self, df, base_temperatures):
        """
        Add heating degree days to the dataframe.
        They are calculated by subtracting the temperature equivalent from a base temperature
        Note: Degree days cannot be negative

        Parameters
        ----------
        df : Pandas Dataframe
        base_temperatures : list of numbers

        Returns
        -------
        Pandas Dataframe
        """

        for base in base_temperatures:
            df['heatingDegreeDays{}'.format(base)] = [max(0, base - equivalent) for equivalent in
                                                      df['temperatureEquivalent']]

        return df

    def _add_cooling_degree_days(self, df, base_temperatures):
        """
        Add cooling degree days to the dataframe.
        They are calculated by subtracting a base temperature from the temperature equivalent.
        Note: Degree days cannot be negative

        Parameters
        ----------
        df : Pandas Dataframe
        base_temperatures : list of numbers

        Returns
        -------
        Pandas Dataframe
        """

        for base in base_temperatures:
            df['coolingDegreeDays{}'.format(base)] = [max(0, equivalent - base) for equivalent in
                                                      df['temperatureEquivalent']]

        return df