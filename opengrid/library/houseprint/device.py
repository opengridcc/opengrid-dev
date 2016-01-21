__author__ = 'Jan Pecinovsky'

"""
A Device is an entity that can contain multiple sensors.
The generic Device class can be inherited by a specific device class, eg. Fluksometer
"""

import pandas as pd

class Device(object):
    def __init__(self, key, site):
        self.key = key
        self.site = site
        self.sensors = []

    def __repr__(self):
        return """
    {}
    Key: {}
    {} sensors
    """.format(self.__class__.__name__,
               self.key,
               len(self.sensors)
              )

    def get_sensors(self, sensortype = None):
        """
            Return a list with all sensors in this Device

            Parameters
            ----------
            sensortype: gas, water, electricity: optional

            Returns
            -------
            list of Sensors
        """
        return [sensor for sensor in self.sensors if sensor.type == sensortype or sensortype is None]

    def get_data(self, sensortype=None, head=None, tail=None, diff=False, resample='min', unit='default'):
        """
        Return a Pandas Dataframe with the joined data for all sensors in this device

        Parameters
        ----------
        sensors : list of Sensor objects
            If None, use sensortype to make a selection
        sensortype : string (optional)
            gas, water, electricity. If None, and Sensors = None,
            all available sensors in the houseprint are fetched
        head, tail: timestamps,
        diff : True (default) or False
            If True, the original data has been differentiated
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.
        unit : str , default='default'
            String representation of the target unit, eg m**3/h, kW, ...

        Returns
        -------
        Pandas DataFrame
        """

        sensors = self.get_sensors(sensortype)
        series = [sensor.get_data(head=head, tail=tail, diff=diff, resample=resample, unit=unit) for sensor in sensors]
        return pd.concat(series, axis=1)

    def number_of_sensors(self, sensortype=None):
        """

        Parameters
        ----------
        sensortype: gas, water, electricity

        Returns
        -------
        int
        """
        return len(self.get_sensors(sensortype=sensortype))


class Fluksometer(Device):
    def __init__(self, site, key, mastertoken = None):

        #invoke init method of generic Device
        super(Fluksometer, self).__init__(key, site)

        self.mastertoken = mastertoken