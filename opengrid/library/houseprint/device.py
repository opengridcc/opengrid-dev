__author__ = 'Jan Pecinovsky'

import pandas as pd

"""
A Device is an entity that can contain multiple sensors.
The generic Device class can be inherited by a specific device class, eg.
Fluksometer
"""


class Device(object):
    def __init__(self, key=None, site=None):
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

    def get_data(self, sensortype=None, head=None, tail=None, diff='default', resample='min', unit='default'):
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
        diff : bool or 'default'
            If True, the original data will be differentiated
            If 'default', the sensor will decide: if it has the attribute
            cumulative==True, the data will be differentiated.
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

        # workaround for https://github.com/pandas-dev/pandas/issues/12985
        series = [s for s in series if not s.empty]

        if series:
            df = pd.concat(series, axis=1)
        else:
            df = pd.DataFrame()

        # Add unit as string to each series in the df.  This is not persistent: the attribute unit will get
        # lost when doing operations with df, but at least it can be checked once.
        for s in series:
            try:
                df[s.name].unit = s.unit
            except:
                pass

        return df

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

    def last_timestamp(self, epoch=False):
        """
        Get the last timestamp for a device, by returning the latest timestamp
        of the sensors

        Parameters
        ----------
        epoch : bool
            default False
            If True return as epoch
            If False return as pd.Timestamp

        Returns
        -------
        pd.Timestamp | int
        """
        timestamps = [sensor.last_timestamp(epoch=epoch) for sensor in self.sensors]
        return max(timestamps)

    def add_sensor(self, sensor):
        """
        Parameters
        ----------
        sensor : Sensor
        """
        sensor.device = self
        self.sensors.append(sensor)


class Fluksometer(Device):
    def __init__(self, site=None, key=None, mastertoken=None, tmpos=None):

        # invoke init method of generic Device
        super(Fluksometer, self).__init__(key, site)

        self.mastertoken = mastertoken
        self._tmpos = tmpos

    @property
    def tmpos(self):
        if self._tmpos is not None:
            return self._tmpos
        elif self.site.tmpos is not None:
            return self.site.tmpos
        else:
            raise AttributeError('TMPO session not defined')
