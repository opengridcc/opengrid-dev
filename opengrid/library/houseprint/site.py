__author__ = 'Jan Pecinovsky'

import pandas as pd

"""
A Site is a physical entity (a house, appartment, school, or other building).
It may contain multiple devices and sensors.
The Site contains most of the metadata, eg. the number of inhabitants, the size of the building, the location etc.
"""

class Site(object):
    def __init__(self, hp, key, size, inhabitants, postcode, construction_year, k_level, e_level, epc_cert):
        self.hp = hp #backref to parent
        self.key = key
        self.size = size
        self.inhabitants = inhabitants
        self.postcode = postcode
        self.construction_year = construction_year
        self.k_level = k_level
        self.e_level = e_level
        self.epc_cert = epc_cert

        self.devices = []
        self.sensors = []

    def __repr__(self):
        return """
    Site
    Key: {}
    {} devices
    {} sensors
    """.format(self.key,
               len(self.devices),
               len(self.sensors)
              )

    def get_sensors(self, sensortype = None):
        """
            Return a list with all sensors in this site

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
        df =  pd.concat(series, axis=1)

        # Add unit as string to each series in the df.  This is not persistent: the attribute unit will get
        # lost when doing operations with df, but at least it can be checked once.
        for s in series:
            try:
                df[s.name].unit = s.unit
            except:
                pass

        return df