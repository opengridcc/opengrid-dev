__author__ = 'Jan Pecinovsky'

import geocoder
import astral
import math
import pandas as pd

class SolarInsolation():
    """
        Module to calculate Solar Insolation (direct intensity, global intensity, air mass) and
        basic solar parameters (angle) based on a location and a date.
        Formulas from pveducation.org
    """
    def __init__(self, location):
        """
            Parameters
            ----------
            location: String
        """
        self.location = geocoder.google(location)
        self.elevation = geocoder.google(self.location.latlng, method='Elevation').elevation
        self.astral = astral.Astral()

    def _airMass(self, angleFromVertical):
        """
            Raw formula to calculate air mass

            Parameters
            ----------
            angleFromVertical: float
                in radians

            Returns
            -------
            float
        """
        denom = math.cos(angleFromVertical) + 0.50572 * (96.07995 - angleFromVertical) ** -1.6364
        if denom >= 0:
            return 1 / denom
        else:
            return -1

    def airMass(self, datetime):
        """
            Calculate air mass for a given date and time

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
        """
        angleFromVertical = (math.pi/2) - self.solarElevation(datetime)
        return self._airMass(angleFromVertical)

    def _directIntensity(self, elevation, airMass):
        """
            Raw Formula to calculate direct solar beam intensity

            Parameters
            ---------
            elevation: float
                in meters
            airMass: float

            Returns
            -------
            float
                in W/m**2
        """
        elevation = elevation / 1000 #formula uses km
        di = 1.353 * ((1 - 0.14*elevation) * 0.7**airMass**0.678 + 0.14*elevation)
        return di*1000 #formula output is kW/m**2

    def directIntensity(self, datetime):
        """
            Calculate direct solar beam intensity for a given date and time

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
                in W/m**2
        """
        airMass = self.airMass(datetime)
        if airMass == -1:
            return 0
        return self._directIntensity(self.elevation, airMass)

    def _globalIrradiance(self, directIntensity):
        """
            Raw formula to calculate global solar irradiance

            Parameters
            ----------
            directIntensity: float
                in W/m**2

            Returns
            -------
            float
                in W/m**2
        """
        return 1.1 * directIntensity

    def globalIrradiance(self, datetime):
        """
            Calculate global solar irradiance for a given date and time

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
                in W/m**2
        """
        directIntensity = self.directIntensity(datetime)
        return self._globalIrradiance(directIntensity)

    def solarElevation(self, datetime):
        """
            Calculate angle of the sun above the horizon

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
                in radians
        """
        deg = self.astral.solar_elevation(dateandtime = datetime,
                                          latitude = self.location.lat,
                                          longitude = self.location.lng)
        return math.radians(deg)

    def df(self, start, end):
        """
            Creates a dataframe with the insolation in W/m**2 in hourly resolution

            Parameters
            ----------
            start, end: datetime.datetime

            Returns
            -------
            Pandas Dataframe
        """

        hours = pd.date_range(start=start, end=end, freq='h')
        gis = []
        for hour in hours:
            gis.append(self.globalIrradiance(hour))

        df = pd.DataFrame(gis, index=hours, columns = ['insolation'])
        return df.tz_localize('UTC')