# -*- coding: utf-8 -*-
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

    def __init__(self, location, start, end=None, cache=True):
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
            cache : bool
                use the cache or not
        """
        self.api_key = cfg.get('Forecast.io', 'apikey')
        self._location = location
        self._start = start
        self._end = end
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
        Get the local timezone of the requested location

        Returns
        -------
        pytz.timezone
        """
        # if there already are some forecasts, the timezone is in there
        if self._forecasts:
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

    def days(
            self,
            heating_base_temperatures=[16.5],
            cooling_base_temperatures=[18],
            irradiances=None,
            wind_orients=None
    ):
        """
        Create a dataframe with all weather data in daily resolution

        Parameters
        ----------
        heating_base_temperatures : list of numbers (optional, default 16.5)
            List of possible base temperatures for which to calculate heating degree days
        cooling_base_temperatures : list of numbers (optional, default 18)
            List of possible base temperatures for which to calculate cooling degree days
        irradiances : list[tuple], optional
            Calculate the global solar irradiance for multiple surfaces with a
            given orientation and tilt (in Wh/m^2)
            List with tuples. tuple = (orientation, tilt)
            Orientation in degrees from north (0 = north, 90 = east, ...)
            Tilt in degrees (0 = horizontal, 90 = vertical)
        wind_orients : list[int] | list[float], optional
            Calculate the wind force on surfaces with a given orientations
            Orientation in degrees from north (0 = north, 90 = east, ...)

        Returns
        -------
        pandas.DataFrame
        """

        # add 2 days before to calculate degree days
        self._add_forecast(self.start - pd.Timedelta(days=1))
        self._add_forecast(self.start - pd.Timedelta(days=2))

        # create a dataframe from the daily observations
        day_list = [self._forecast_to_day_series(forecast=forecast) for forecast in self.forecasts]
        frame = pd.concat(day_list)
        frame = self._fix_index(frame).sort_index()

        # add aggregates from hourly observations to the dataframe
        hourly_frame = self.hours(irradiances=irradiances,
                                  no_truncate=True,
                                  wind_orients=wind_orients)
        temperature = hourly_frame.temperature.resample('d').mean()
        ghi = hourly_frame.GlobalHorizontalIrradiance.dropna().resample('d').sum()
        tilted_gi = hourly_frame.filter(regex='^GlobalIrradiance').dropna().resample('d').sum()
        wind_force = hourly_frame.filter(regex='^windComponent').dropna().resample('d').sum()
        frame = pd.concat([frame, temperature, ghi, tilted_gi, wind_force], axis=1)
        frame = frame.tz_convert(self.tz.zone)  # because the concat loses tz info

        # add temperature equivalent and degree days
        frame['temperatureEquivalent'] = calculate_temperature_equivalent(temperatures=frame.temperature)
        frame.dropna(subset=['temperatureEquivalent'], inplace=True)

        for base in heating_base_temperatures:
            frame['heatingDegreeDays{}'.format(base)] = calculate_degree_days(
                temperature_equivalent=frame.temperatureEquivalent, base_temperature=base
            )

        for base in cooling_base_temperatures:
            frame['coolingDegreeDays{}'.format(base)] = calculate_degree_days(
                temperature_equivalent=frame.temperatureEquivalent, base_temperature=base, cooling=True
            )

        return frame

    def hours(self, irradiances=None, no_truncate=False, wind_orients=None):
        """
        Create a dataframe with all weather data in hourly resolution

        Parameters
        ----------
        irradiances : list[tuple], optional
            Calculate the global solar irradiance for multiple surfaces with a
            given orientation and tilt
            List with tuples. tuple = (orientation, tilt)
            Orientation in degrees from north (0 = north, 90 = east, ...)
            Tilt in degrees (0 = horizontal, 90 = vertical)
        no_truncate : bool
            do not truncate to the exact timestamps
            useful for when using the hour dataframe to do aggregations
        wind_orients : list[int] | list[float], optional
            Calculate the wind force on surfaces with a given orientations
            Orientation in degrees from north (0 = north, 90 = east, ...)

        Returns
        -------
        pandas.DataFrame
        """
        day_list = [self._forecast_to_hour_series(forecast) for forecast in self.forecasts]
        frame = pd.concat(day_list)
        frame = self._fix_index(frame)
        frame.sort_index(inplace=True)
        if not no_truncate:
            frame = frame.truncate(before=self.start, after=self.end)

        if irradiances is not None:
            for ir in irradiances:
                frame = self._add_irradiance(frame=frame, orient=ir[0], tilt=ir[1])

        if wind_orients is not None:
            for orient in wind_orients:
                frame = self._add_wind_components(frame=frame, orient=orient)

        return frame

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

        hour_list = [pd.Series(self._flatten_solar(hour.d)) for hour in forecast.hourly().data]
        frame = pd.concat(hour_list, axis=1).T
        frame.temperature = frame.temperature.astype(float)
        return frame

    @staticmethod
    def _flatten_solar(j):
        """
        Extracts the 'solar' part from the response json,
        renames the fields and includes them along with everything else

        Parameters
        ----------
        j : dict

        Returns
        -------
        dict
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

            # workaround for the 90 bug by Dark Sky
            # add 90 and take modulo 360 to stay between 0 and 360
            j.update({'SolarAzimuth': (j.get('SolarAzimuth') + 90) % 360})

            return j

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

    def _forecast_to_day_series(self, forecast):
        """
        Transforms the daily data of a forecast object to a pandas dataframe

        Parameters
        ----------
        forecast : forecastio.models.Forecast

        Returns
        -------
        pandas.DataFrame

        """
        data = forecast.daily().data[0].d
        frame = [pd.Series(data)]
        return pd.concat(frame, axis=1).T

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

    @staticmethod
    def irradiance_on_tilted_surface(dni, dhi, altitude, azimuth, orient, tilt):
        """
        Calculate the global solar radiation on a tilted surface

        Parameters
        ----------
        dni : pandas.Series
            Direct Normal Irradiance
        dhi : pandas.Series
            Diffuse Horizontal Irradiance
        altitude : pandas.Series
            altitude of the sun above the horizon (in degrees)
            0 = horizon, 90 = right above
        azimuth : pandas.Series
            location of the sun in respect to North (in degrees)
            0 = North, 90 = East, 180 = South, 270 = West
        orient : int|float
            orientation of the surface
            0 = North, 90 = East, 180 = South, 270 = West
        tilt : int|float
            tilt of the surface
            0 = Horizontal, 90 = Vertical

        Returns
        -------
        pandas.Series
        """
        a = np.radians(altitude.astype(float))
        b = np.radians(float(tilt))
        c = np.radians(float(orient))
        d = np.radians(azimuth.astype(float))

        direct = dni * (np.cos(a) * np.sin(b) * np.cos(c - d) + np.sin(a) * np.cos(b))
        direct[direct < 0] = 0
        return direct + dhi

    def _add_irradiance(self, frame, orient, tilt):
        """
        Add a column to the frame with the global irradiance on a surface for
        a given orientation and tilt

        Parameters
        ----------
        frame : pandas.DataFrame
        orient : float|int
            in degrees from north
        tilt : float|int
            in degrees from horizontal

        Returns
        -------
        pandas.DataFrame
        """
        new_col = self.irradiance_on_tilted_surface(
            dni=frame.DirectNormalIrradiance,
            dhi=frame.DiffuseHorizontalIrradiance,
            altitude=frame.SolarAltitude,
            azimuth=frame.SolarAzimuth,
            orient=orient,
            tilt=tilt
        )
        name = "GlobalIrradianceO{}T{}".format(int(orient), int(tilt))

        frame[name] = new_col

        return frame

    @staticmethod
    def wind_on_oriented_face(bearing, speed, orient):
        """
        Calculate the wind speed with respect to a given orientation
        (of a building wall for example)

        Parameters
        ----------
        bearing : pandas.Series
        speed : pandas.Series
        orient : int | float

        Returns
        -------
        pandas.Series
        """
        b = np.radians(bearing.astype(float))
        o = np.radians(float(orient))

        wind = speed * np.cos(b - o)
        wind[wind < 0] = 0
        return wind

    def _add_wind_components(self, frame, orient):
        """
        Add columns to the frame with
            the wind speed,
            the wind speed squared (force or pressure)
            the wind speed cubed (power on a turbine)
        for a given orientation

        Parameters
        ----------
        frame : pandas.DataFrame
        orient : float|int
            in degrees from north

        Returns
        -------
        pandas.DataFrame
        """
        oriented_speed = self.wind_on_oriented_face(
            bearing=frame.windBearing,
            speed=frame.windSpeed,
            orient=orient
        )

        name = "windComponent{}".format(int(orient))
        frame[name] = oriented_speed

        name = "windComponentSquared{}".format(int(orient))
        frame[name] = oriented_speed ** 2

        name = "windComponentCubed{}".format(int(orient))
        frame[name] = oriented_speed ** 3

        return frame
