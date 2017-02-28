__author__ = 'Jan Pecinovsky'

from opengrid.config import Config

config = Config()

import os
import sys
import json
import jsonpickle
import datetime as dt
import pandas as pd

# compatibility with py3
if sys.version_info.major >= 3:
    import pickle
else:
    import cPickle as pickle

import tmpo

# compatibility with py3
if sys.version_info.major >= 3:
    from .site import Site
    from .device import Device, Fluksometer
    from .sensor import Sensor, Fluksosensor
else:
    from site import Site
    from device import Device, Fluksometer
    from sensor import Sensor, Fluksosensor

"""
The Houseprint is a Singleton object which contains all metadata for sites, devices and sensors.
It can be pickled, saved and passed around
"""


class Houseprint(object):
    def __init__(self,
                 gjson=None,
                 spreadsheet="Opengrid houseprint (Responses)",
                 empty_init=False
                 ):
        """
            Parameters
            ---------
            gjson: Path to authentication json
            spreadsheet: String, name of the spreadsheet containing the metadata
        """

        self.sites = []
        self.timestamp = dt.datetime.utcnow()  # Add a timestamp upon creation

        if not empty_init:
            if gjson is None:
                gjson = config.get('houseprint', 'json')
            self.gjson = gjson
            self.spreadsheet = spreadsheet
            self._parse_sheet()

    def reset(self):
        """
        Connect to the Google Spreadsheet again and re-parse the data
        """
        self.__init__(gjson=self.gjson, spreadsheet=self.spreadsheet)
        if hasattr(self, '_tmpos'):
            self._add_sensors_to_tmpos()  

    def __repr__(self):
        return """
    Houseprint
    Created on {} (UTC)
    {} sites
    {} devices
    {} sensors
    """.format(self.timestamp,
               len(self.sites),
               sum([len(site.devices) for site in self.sites]),
               sum([len(site.sensors) for site in self.sites])
               )

    def _parse_sheet(self):
        """
            Connects to Google, fetches the spreadsheet and parses the content
        """

        import gspread
        from oauth2client.client import SignedJwtAssertionCredentials

        print('Opening connection to Houseprint sheet')
        # fetch credentials
        json_key = json.load(open(self.gjson))
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(
            json_key['client_email'],
            json_key['private_key'].encode('ascii'),
            scope
        )

        # authorize and login
        gc = gspread.authorize(credentials)
        gc.login()

        # open sheets
        print("Opening spreadsheets")
        sheet = gc.open(self.spreadsheet)
        sites_sheet = sheet.worksheet('Accounts')
        devices_sheet = sheet.worksheet('Devices')
        sensors_sheet = sheet.worksheet('Sensors')

        print('Parsing spreadsheets')
        # 3 sub-methods that parse the different sheets
        self._parse_sites(sites_sheet)
        self._parse_devices(devices_sheet)
        self._parse_sensors(sensors_sheet)

        print('Houseprint parsing complete')

    def _parse_sites(self, sheet):
        """
            Sub method of _parse_sheet() that parses only the 'sites' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about sites
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Key'] == '':
                continue
            new_site = Site(hp=self,
                            key=r['Key'],
                            size=r['House size'],
                            inhabitants=r['Number of inhabitants'],
                            postcode=r['postcode'],
                            construction_year=r['construction year'],
                            k_level=r['K-level'],
                            e_level=r['E-level'],
                            epc_cert=r['EPC certificate'])
            self.sites.append(new_site)

        print('{} Sites created'.format(len(self.sites)))

    def _parse_devices(self, sheet):
        """
            Sub method of _parse_sheet() that parses only the 'devices' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about devices
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Key'] == '':
                continue

            # find parent site and check if it exists
            site = self.find_site(r['Parent site'])
            if site is None:
                raise ValueError('Device {} was given an invalid site key {}'.format(r['Key'], r['Parent site']))

            # create a new device according to its manufacturer
            if r['manufacturer'] == 'Flukso':
                new_device = Fluksometer(site=site, key=r['Key'])
            else:
                raise NotImplementedError('Devices from {} are not supported'.format(r['manufacturer']))

            # add new device to parent site
            site.devices.append(new_device)

        print('{} Devices created'.format(sum([len(site.devices) for site in self.sites])))

    def _parse_sensors(self, sheet):
        """
            Sub method of _parse_sheet() that parses only the 'sensors' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about sensors
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Sensor_id'] == '': continue

            # find parent. If a parent device is specified, us that, otherwise use a parent site directly
            if r['parent device'] != '':
                device = self.find_device(r['parent device'])
                if device is None:
                    raise ValueError(
                        'Sensor {} was given an invalid device key {}. \
                        Leave the device field empty if you want to add a sensor without a device'.format(
                            r['Sensor_id'], r['parent device']))
            else:
                site = self.find_site(r['parent site'])
                if site is None:
                    raise ValueError(
                        'Sensor {} was given an invalid site key {}'.format(r['Sensor_id'], r['parent site']))

            # create new sensor according to its manufacturer
            if r['manufacturer'] == 'Flukso':
                new_sensor = Fluksosensor(
                    device=device,
                    key=r['Sensor_id'],
                    token=r['token'],
                    type=r['sensor type'],
                    description=r['name by user'],
                    system=r['system'],
                    quantity=r['quantity'],
                    unit=r['unit'],
                    direction=r['direction'],
                    tariff=r['tariff'],
                    cumulative=None  # will be determined based on type
                )
            else:
                raise NotImplementedError('Sensors from {} are not supported'.format(r['manufacturer']))

            new_sensor.device.sensors.append(new_sensor)

        print('{} sensors created'.format(sum([len(site.sensors) for site in self.sites])))

    def get_sensors(self, sensortype=None):
        """
            Return a list with all sensors

            Parameters
            ----------
            sensortype: gas, water, electricity: optional

            Returns
            -------
            list of sensors
        """
        res = []
        for site in self.sites:
            for sensor in site.get_sensors(sensortype=sensortype):
                res.append(sensor)
        return res

    def get_devices(self):
        """
            Return a list with all devices

            Returns
            -------
            list of devices
        """
        res = []
        for site in self.sites:
            for device in site.devices:
                res.append(device)
        return res

    def search_sites(self, **kwargs):
        """
            Parameters
            ----------
            kwargs: any keyword argument, like key=mykey

            Returns
            -------
            List of sites satisfying the search criterion or empty list if no
            variable found.
        """

        result = []
        for site in self.sites:
            for keyword, value in kwargs.items():
                if getattr(site, keyword) == value:
                    continue
                else:
                    break
            else:
                result.append(site)

        return result

    def search_sensors(self, **kwargs):
        """
            Parameters
            ----------
            kwargs: any keyword argument, like key=mykey

            Returns
            -------
            List of sensors satisfying the search criterion or empty list if no
            variable found.
        """

        result = []
        for sensor in self.get_sensors():
            for keyword, value in kwargs.items():
                if value in getattr(sensor, keyword):
                    continue
                else:
                    break
            else:
                result.append(sensor)

        return result

    def find_site(self, key):
        """
            Parameters
            ----------
            key: string

            Returns
            -------
            Site
        """

        for site in self.sites:
            if site.key == key:
                return site
        return None

    def find_device(self, key):
        """
            Parameters
            ----------
            key: string

            Returns
            -------
            Device
        """
        for device in self.get_devices():
            if device.key.lower() == key.lower():
                return device
        return None

    def find_sensor(self, key):
        """
            Parameters
            ----------
            key: string

            Returns
            -------
            Sensor
        """
        for sensor in self.get_sensors():
            if sensor.key.lower() == key.lower():
                return sensor
        return None

    def save(self, filename):
        """
        Save the houseprint object

        Parameters
        ----------
        * filename : str
            Filename, if relative path or just filename, it is appended to the
            current working directory

        """
        # temporarily delete tmpo session
        try:
            tmpos_tmp = self._tmpos
            delattr(self, '_tmpos')
        except:
            pass

        frozen = jsonpickle.encode(self)

        abspath = os.path.join(os.getcwd(), filename)
        with open(abspath, 'w') as f:
            f.write(frozen)

        print("Saved houseprint to {}".format(abspath))

        # restore tmposession if needed
        try:
            setattr(self, '_tmpos', tmpos_tmp)
        except:
            pass

    def init_tmpo(self, tmpos=None, path_to_tmpo_data=None):
        """
            Flukso sensors need a tmpo session to obtain data.
            It is overkill to have each flukso sensor make its own session, syncing would
            take too long and be overly redundant.
            Passing a tmpo session to the get_data function is also bad form because 
            we might add new types of sensors that don't use tmpo in the future.
            This is why the session is initialised here.

            A tmpo session as parameter is optional.  If passed, no additional sensors are added.
            
            If no session is passed, a new one will be created using the location in the config file.
            It will then be populated with the flukso sensors known to the houseprint object

            Parameters
            ----------

            tmpos : tmpo session
            path_to_tmpo_data : str
        """

        if tmpos is not None:
            self._tmpos = tmpos
        else:
            try:
                path_to_tmpo_data = config.get('tmpo', 'data')
            except:
                path_to_tmpo_data = None

            self._tmpos = tmpo.Session(path_to_tmpo_data)
            self._add_sensors_to_tmpos()

        print("Using tmpo database from {}".format(self._tmpos.db))

    def _add_sensors_to_tmpos(self):
        """
        Add all flukso sensors in the houseprint to the tmpo session
        """
        fluksosensors = [sensor for sensor in self.get_sensors() if isinstance(sensor, Fluksosensor)]

        for sensor in fluksosensors:
            self._tmpos.add(sensor.key, sensor.token)

    def get_tmpos(self):
        """
            Returns
            -------
            TMPO session
        """
        if hasattr(self, '_tmpos'):
            return self._tmpos
        else:
            self.init_tmpo()
            return self._tmpos

    @property
    def tmpos(self):
        return self.get_tmpos()

    def sync_tmpos(self):
        """
            Add all Flukso sensors to the TMPO session and sync
        """
        tmpos = self.get_tmpos()
        tmpos.sync()

    def get_data(self, sensors=None, sensortype=None, head=None, tail=None, diff='default', resample='min',
                 unit='default'):
        """
        Return a Pandas Dataframe with joined data for the given sensors

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
        
        """
        if sensors is None:
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

    def get_data_dynamic(self, sensors=None, sensortype=None, head=None,
                         tail=None, diff='default', resample='min',
                         unit='default'):
        """
        Yield Pandas Series for the given sensors

        Parameters
        ----------
        sensors : list(Sensor), optional
            If None, use sensortype to make a selection
        sensortype : str, optional
            gas, water, electricity. If None, and Sensors = None,
            all available sensors in the houseprint are fetched
        head : dt.datetime | pd.Timestamp | int, optional
        tail : dt.datetime | pd.Timestamp | int, optional
        diff : bool | str('default')
            If True, the original data will be differentiated
            If 'default', the sensor will decide: if it has the attribute
            cumulative==True, the data will be differentiated.
        resample : str
            default='min'
            Sampling rate, if any.  Use 'raw' if no resampling.
        unit : str
            default='default'
            String representation of the target unit, eg m**3/h, kW, ...

        Yields
        ------
        Pandas.Series
        """
        if sensors is None:
            sensors = self.get_sensors(sensortype)

        for sensor in sensors:
            ts = sensor.get_data(head=head, tail=tail, diff=diff,
                                  resample=resample, unit=unit)
            if ts.empty:
                continue
            else:
                yield ts

    def add_site(self, site):
        """
        Parameters
        ----------
        site : Site
        """
        site.hp = self
        self.sites.append(site)


def load_houseprint_from_file(filename):
    """
    Return a static (=anonymous) houseprint object

    Parameters
    ----------
    filename : str
    """

    with open(filename, 'r') as f:
        hp = jsonpickle.decode(f.read())
    return hp
