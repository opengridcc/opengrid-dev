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

    def get_data(self, sensortype = None, head = None, tail = None):
        """
            Return a Pandas Dataframe with joined data for all sensors in this Site

            Parameters
            ----------
            sensortype: gas, water, electricity: optional
            head, tail: timestamps

            Returns
            -------
            Pandas DataFrame
        """
        sensors = self.get_sensors(sensortype)
        series = [sensor.get_data(head=head,tail=tail) for sensor in sensors]
        return pd.concat(series, axis=1)