__author__ = 'Jan Pecinovsky'

import datetime as dt
import forecastio
from forecastio.models import Forecast
from geopy import Location, Point, GoogleV3
import numpy as np
import pandas as pd
import pytz
from cached_property import cached_property
from tqdm import tqdm
import os
import pickle


from .misc import dayset, calculate_temperature_equivalent, \
    calculate_degree_days
from opengrid import config
cfg = config.Config()


class Weather():
    """
        Object that contains Weather Data from Forecast.io for multiple days as a Pandas Dataframe.
        NOTE: Forecast.io allows 1000 requests per day, after that you have to pay. Each requested day is 1 request.
    """

    def __init__(self, location, start, end=None, tz=None, cache=True):
        """
            Constructor

            Parameters
            ----------
            location : str | tuple(float, float)
                String can be City, address, POI. tuple = (lat, lng)
            start : datetime.datetime | pandas.Timestamp
                start of the interval to be searched
            end : datetime.datetime | pandas.Timestamp, optional
                end of the interval to be searched
                if None, use current time
            tz : str, optional
                tz specifies the timezone of the response.
                If none, response will be in the timezone of the location
            cache : bool
                use the cache or not
        """
        self.api_key = cfg.get('Forecast.io', 'apikey')
        self._location = location
        self._start = start
        self._end = end
        self._tz = tz
        self.cache = cache

        self._forecasts = []

    @cached_property  # so we don't have to lookup every time it is called
    def location(self):
        """
        Get the location, but as a geopy location object

        Returns
        -------
        Location
        """
        # if the input was a string, we do a google lookup
        if isinstance(self._location, str):
            location = GoogleV3().geocode(self._location)

        # if the input was an iterable, it is latitude and longitude
        elif hasattr(self._location, '__iter__'):
            lat, long = self._location
            gepoint = Point(latitude=lat, longitude=long)
            location = Location(point=gepoint)

        else:
            raise ValueError('Invalid location')

        return location

    @property
    def start(self):
        """
        Return localized start time

        Returns
        -------
        datetime.datetime | pandas.Timestamp
        """
        if self._start.tzinfo is None:
            return self.tz.localize(self._start)
        else:
            return self._start

    @property
    def end(self):
        """
        Return localized end time

        Returns
        -------
        datetime.datetime | pandas.Timestamp
        """
        if self._end is None:
            return pd.Timestamp('now', tz=self.tz.zone)
        elif self._end.tzinfo is None:
            return self.tz.localize(self._end)
        else:
            return self._end

    @property
    def tz(self):
        """
        Get the timezone

        Returns
        -------
        pytz.timezone
        """

        # if the user has specified a zone, use that one
        if self._tz is not None:
            tz = self._tz

        # if there already are some forecasts, the timezone is in there
        elif self._forecasts:
            tz = self._lookup_timezone()

        # use Google geocoder to lookup timezone
        else:
            lat, long, _alt = self.location.point
            tz = GoogleV3().timezone(location=(lat, long)).zone

        # return as a pytz object
        return pytz.timezone(tz)

    @property
    def forecasts(self):
        """
        Get a list of all forecast objects

        Returns
        -------
        list(Forecast)
        """
        # we stick the list in self._forecasts, only if it is still empty
        if not self._forecasts:
            # get list of seperate days
            days = dayset(start=self.start, end=self.end)
            # wrap in a tqdm so we get the progress bar
            for date in tqdm(days):
                self._forecasts.append(self._get_forecast(date=date))

        return self._forecasts

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
            frame['temperatureEquivalent'] = calculate_temperature_equivalent(temperatures=frame.temperature)
            frame.dropna(subset=['temperatureEquivalent'], inplace=True)

        if include_heating_degree_days:
            for base in heating_base_temperatures:
                frame['heatingDegreeDays{}'.format(base)] = calculate_degree_days(
                    temperature_equivalent=frame.temperatureEquivalent, base_temperature=base
                )

        if include_cooling_degree_days:
            for base in cooling_base_temperatures:
                frame['coolingDegreeDays{}'.format(base)] = calculate_degree_days(
                    temperature_equivalent=frame.temperatureEquivalent, base_temperature=base, cooling=True
                )

        return frame

    def hours(self):
        """
        Create a dataframe with all weather data in hourly resolution

        Returns
        -------
        Pandas Dataframe
        """
        day_list = [self._forecast_to_hour_series(forecast) for forecast in self.forecasts]
        frame = pd.concat(day_list)
        return self._fix_index(frame).sort_index().truncate(before=self.start, after=self.end)

    def _get_forecast(self, date):
        """
            Get the raw forecast object for a given date

            Parameters
            ----------
            date : datetime.date

            Returns
            -------
            forecastio forecast
        """
        # Forecast takes a dt.datetime
        # conversion from dt.date to dt.datetime, there must be a better way, right?
        time = dt.datetime(year=date.year, month=date.month, day=date.day)

        f = None
        if self.cache:
            f = self._load_from_cache(date)

        if not f:
            # We specifically ask for si units,
            # so we can inject the SOLAR argument to get solar data
            # which is in beta (januari 2017)
            f = forecastio.load_forecast(key=self.api_key,
                                         lat=self.location.latitude,
                                         lng=self.location.longitude,
                                         time=time,
                                         units='si&solar'
                                         )
            if self.cache:
                self._save_in_cache(f, date)

        return f

    def _get_forecast_dates(self):
        """
        Return a set with the dates of all forecasts in self.forecasts

        Returns
        -------
        set of datetime.date
        """
        dates = []
        for forecast in self.forecasts:
            time = forecast.currently().time

            # the time is in UTC, we need to localize it.
            tz = pytz.timezone(self._lookup_timezone())
            time_utc = tz.fromutc(time)

            dates.append(time_utc.date())
        return set(dates)

    def _add_forecast(self, date):
        """
        Add a forecast to the list of forecasts

        Parameters
        ----------
        date : dt.date | dt.datetime | pd.Timestamp
        """
        # for if you pass a datetime instead of a date
        if hasattr(date, 'date'):
            date = date.date()

        if date not in self._get_forecast_dates():
            self._forecasts.append(self._get_forecast(date))

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
        def flatten(j):
            """
            Extracts the 'solar' part from the response json,
            renames the fields and includes them along with everything else
            """
            try:
                solar = j.pop('solar')
            except KeyError:
                return j
            else:
                # give the properties some more verbose names
                new_names = {'altitude': 'SolarAltitude',
                             'dni': 'DirectNormalIrradiance',
                             'ghi': 'GlobalHorizontalIrradiance',
                             'dhi': 'DiffuseHorizontalIrradiance',
                             'etr': 'ExtraTerrestrialRadiation',
                             'azimuth': 'SolarAzimuth'
                             }
                solar = {new_names[key]: val for key, val in solar.items()}
                j.update(solar)
                return j

        hour_list = [pd.Series(flatten(hour.d)) for hour in forecast.hourly().data]
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
        frame = frame.tz_convert(self.tz.zone)
        return frame

    def _lookup_timezone(self):
        """
        Lookup the timezone in the JSON of the first forecast

        Returns
        -------
        String (Pytz timezone)
        """
        tz = self.forecasts[0].json['timezone']
        return tz

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

    @property
    def cache_folder(self):
        location_str = "{}_{}".format(round(self.location.latitude, 4),
                                      round(self.location.longitude, 4))

        forecast_folder = os.path.join(os.path.abspath(cfg.get('data', 'folder')),
                            'forecasts')
        location_folder = os.path.join(forecast_folder, location_str)

        for folder in [forecast_folder, location_folder]:
            if not os.path.exists(folder):
                print("This folder does not exist: {}, it will be created".format(folder))
                os.mkdir(folder)

        return location_folder

    def _pickle_path(self, date):
        filename = str(date) + '.pkl'
        path = os.path.join(self.cache_folder, filename)
        return path

    def _save_in_cache(self, f, date):
        """
        Save Forecast object to cache

        Parameters
        ----------
        f : Forecast
        date : datetime.date
        """

        pickle.dump(f, open(self._pickle_path(date), "wb"))

    def _load_from_cache(self, date):
        """
        Load Forecast object from cache

        Parameters
        ----------
        date : datetime.date

        Returns
        -------
        Forecast
        """
        path = self._pickle_path(date)
        if os.path.exists(path):
            return pickle.load(open(path, "rb"))
        else:
            return None
