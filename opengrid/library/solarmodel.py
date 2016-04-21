__author__ = 'Jan Pecinovsky'

import geocoder
import astral
import math
import pandas as pd

class SolarInsolation(object):
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

    def _backgroundIrradiance(self, directIntensity):
        """
        Calculate the background irradiance, which is 10% of the direct intensity
        :param directIntensity: float
        :return: float
        """

        return 0.1 * directIntensity

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
        return directIntensity + self._backgroundIrradiance(directIntensity)

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

    def solarAzimuth(self, datetime):
        """
        Calculate the azimuth of the sun

        :param datetime: datetime.datetime
        :return: float
            in radians
        """

        deg = self.astral.solar_azimuth(dateandtime=datetime,
                                        latitude=self.location.lat,
                                        longitude=self.location.lng)
        return math.radians(deg)

class PVModel(SolarInsolation):
    """
        Module that models a theoretically perfect PV installation,
        extending the Solar Insolation Model, but adding PV orientation and tilt.
    """

    def __init__(self, location, orient=180, tilt=35):
        """
            Parameters
            ----------
            location: String
            orient: number (optional, default=180 (south))
                degrees (0-360)
            tilt: number (optional, default=35)
                degrees
        """

        super(PVModel, self).__init__(location = location)
        self.orient = math.radians(orient)
        self.tilt = math.radians(tilt)

    def directIntensity(self, datetime):
        """
            Calculate the direct solar beam intensity for a given date and time,
            but compensate for the PV orientation and tilt

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
                in W/m**2
        """
        di = super(PVModel, self).directIntensity(datetime)
        a = self.solarElevation(datetime)
        b = self.tilt
        c = self.orient
        d = self.solarAzimuth(datetime)

        PVdi = di * (math.cos(a)*math.sin(b)*math.cos(c-d) + math.sin(a)*math.cos(b))

        #PVdi cannot be negative
        return max(0, PVdi)

    def globalIrradiance(self, datetime):
        """
            Calculate global solar irradiance for a given date and time
            needed to override, because background irradiance is not influenced by PV orientation and tilt

            Parameters
            ----------
            datetime: datetime.datetime

            Returns
            -------
            float
                in W/m**2
        """
        #calculate the direct intensity without influence of tilt and orientation
        di = super(PVModel, self).directIntensity(datetime)

        #add the tilted and oriented direct intensity to the background irradiance
        return self.directIntensity(datetime) + self._backgroundIrradiance(di)