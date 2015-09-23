__author__ = 'Jan Pecinovsky'

import json, gspread, datetime, os, sys
from oauth2client.client import SignedJwtAssertionCredentials
import pandas as pd

#compatibility with py3
if sys.version_info.major == 3:
    import pickle
else:
    import cPickle as pickle

#The invoking script should have added the path to the tmpo library
import tmpo

#compatibility with py3
if sys.version_info.major == 3:
    from .site import Site
    from .device import Fluksometer
    from .sensor import Fluksosensor
else:
    from site import Site
    from device import Fluksometer
    from sensor import Fluksosensor

"""
The Houseprint is a Singleton object which contains all metadata for sites, devices and sensors.
It can be pickled, saved and passed around
"""

class Houseprint(object):
    def __init__(self, gjson, spreadsheet="Opengrid houseprint (Responses)"):
        """
            Parameters
            ---------
            gjson: Path to authentication json
            spreadsheet: String, name of the spreadsheet containing the metadata
        """

        self.sites = []
        self._parse_sheet(gjson, spreadsheet)
        self.timestamp = datetime.datetime.utcnow() #Add a timestamp upon creation

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

    def _parse_sheet(self, gjson, spreadsheet):
        """
            Connects to Google, fetches the spreadsheet and parses the content

            Parameters
            ----------
            gjson: Path to authenication json
            spreadsheet: String
                Name of the spreadsheet to connect to.
        """

        print('Opening connection to Houseprint sheet')
        #fetch credentials
        json_key = json.load(open(gjson))
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

        #authorize and login
        gc = gspread.authorize(credentials)
        gc.login()

        #open sheets
        print("Opening spreadsheets")
        sheet = gc.open(spreadsheet)
        sites_sheet = sheet.worksheet('Accounts')
        devices_sheet = sheet.worksheet('Devices')
        sensors_sheet = sheet.worksheet('Sensors')

        print('Parsing spreadsheets')
        #3 sub-methods that parse the different sheets
        self._parse_sites(sites_sheet)
        self._parse_devices(devices_sheet)
        self._parse_sensors(sensors_sheet)

        print('Houseprint parsing complete')

    def _parse_sites(self, sheet):
        """
            Submethod of _parse_sheet() that parses only the 'sites' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about sites
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Key'] == '': continue
            new_site = Site(hp = self,
                            key = r['Key'],
                           size = r['House size'],
                           inhabitants = r['Number of inhabitants'],
                           postcode = r['postcode'],
                           construction_year = r['construction year'],
                           k_level = r['K-level'],
                           e_level = r['E-level'],
                           epc_cert = r['EPC certificate'])
            self.sites.append(new_site)

        print('{} Sites created'.format(len(self.sites)))

    def _parse_devices(self, sheet):
        """
            Submethod of _parse_sheet() that parses only the 'devices' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about devices
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Key'] == '': continue

            #find parent site and check if it exists
            site = self.find_site(r['Parent site'])
            if site is None:
                raise ValueError('Device {} was given an invalid site key {}'.format(r['Key'], r['Parent site']))

            #create a new device according to its manufacturer
            if r['manufacturer'] == 'Flukso':
                new_device = Fluksometer(site = site, key = r['Key'])
            else:
                raise NotImplementedError('Devices from {} are not supported'.format(r['manufacturer']))

            #add new device to parent site
            site.devices.append(new_device)

        print('{} Devices created'.format(sum([len(site.devices) for site in self.sites])))

    def _parse_sensors(self, sheet):
        """
            Submethod of _parse_sheet() that parses only the 'sensors' sheet

            Parameters
            ----------
            sheet: GSpread worksheet
                sheet containing metadata about sensors
        """

        records = sheet.get_all_records()

        for r in records:
            if r['Sensor_id'] == '': continue

            #find parent. If a parent device is specified, us that, otherwise use a parent site directly
            if r['parent device'] != '':
                device = self.find_device(r['parent device'])
                if device is None:
                    raise ValueError('Sensor {} was given an invalid device key {}. Leave the device field empty if you want to add a sensor without a device'.format(r['Sensor_id'], r['parent device']))
            else:
                site = self.find_site(r['parent site'])
                if site is None:
                    raise ValueError('Sensor {} was given an invalid site key {}'.format(r['Sensor_id'],r['parent site']))

            #create new sensor according to its manufacturer
            if r['manufacturer'] == 'Flukso':
                new_sensor = Fluksosensor(device = device,
                                         key = r['Sensor_id'],
                                         token = r['token'],
                                         type = r['sensor type'],
                                         description = r['name by user'],
                                         system = r['system'],
                                         quantity = r['quantity'],
                                         unit = r['unit'],
                                         direction = r['direction'],
                                         tariff = r['tariff'])
            else:
                raise NotImplementedError('Sensors from {} are not supported'.format(r['manufacturer']))

            #add sensor to device AND site
            if new_sensor.device is not None:
                new_sensor.device.sensors.append(new_sensor)
            new_sensor.site.sensors.append(new_sensor)

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
            for sensor in site.get_sensors(sensortype = sensortype):
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

    def find_site(self, key):
        '''
            Parameters
            ----------
            key: string

            Returns
            -------
            Site
        '''
        for site in self.sites:
            if site.key == key:
                return site
        return None

    def find_device(self, key):
        '''
            Parameters
            ----------
            key: string

            Returns
            -------
            Device
        '''
        for device in self.get_devices():
            if device.key == key:
                return device
        return None

    def find_sensor(self, key):
        '''
            Parameters
            ----------
            key: string

            Returns
            -------
            Sensor
        '''
        for sensor in self.get_sensors():
            if sensor.key == key:
                return sensor
        return None

    def save(self, filename):
        """
        Pickle the houseprint object

        Parameters
        ----------
        * filename : str
            Filename, if relative path or just filename, it is appended to the
            current working directory

        """
        if hasattr(self,'_tmpos'):
            #temporarily delete tmpo session
            tmpos_tmp = self._tmpos
            self._tmpos = None

        abspath = os.path.join(os.getcwd(), filename)
        f=file(abspath, 'w')
        pickle.dump(self, f)
        f.close()

        print("Saved houseprint to {}".format(abspath))

        if hasattr(self,'_tmpos'):
            #restore tmpo session
            self._tmpos = tmpos_tmp

    def init_tmpo(self, tmpos=None, path_to_tmpo_data=None):
        """
            Fluksosensors need a tmpo session to obtain data.
            It is overkill to have each fluksosensor make its own session, syncing would take too long and be overly redundant.
            Passing a tmpo session to the get_data function is also bad form because we might add new types of sensors that don't use tmpo in the future.
            This is why the session is initialised here.

            A tmpo session as parameter is optional.
            If no session is passed, a new one will be created using the location in the config file.
        """

        if tmpos is not None:
            self._tmpos = tmpos
        else:
            self._tmpos = tmpo.Session(path_to_tmpo_data)

    def get_tmpos(self):
        """
            Returns
            -------
            TMPO session
        """
        if hasattr(self,'_tmpos'):
            return self._tmpos
        else:
            raise RuntimeError('No TMPO session was set, use the init_tmpo method to add or create a TMPO Session')

    def sync_tmpos(self):
        """
            Add all Fluksosensors to the TMPO session and sync
        """
        tmpos = self.get_tmpos()
        fluksosensors = [sensor for sensor in self.get_sensors() if isinstance(sensor,Fluksosensor)]

        for sensor in fluksosensors:
            tmpos.add(sensor.key, sensor.token)

        tmpos.sync()

    def get_data(self, sensortype=None, head=None, tail=None, resample='min'):
        """
            Return a Pandas Dataframe with joined data for all sensors in the houseprint

            Parameters
            ----------
            sensortype: gas, water, electricity: optional
            head, tail: timestamps
        """
        sensors = self.get_sensors(sensortype)
        series = [sensor.get_data(head=head,tail=tail,resample=resample) for sensor in sensors]
        return pd.concat(series, axis=1)

def load_houseprint_from_file(filename):
    """Return a static (=anonymous) houseprint object"""

    f = open(filename, 'r')
    hp = pickle.load(f)
    f.close()
    return hp