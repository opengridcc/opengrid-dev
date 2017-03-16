__author__ = 'Jan Pecinovsky, Roel De Coninck'

"""
A sensor generates a single data stream.
It can have a parent device, but the possibility is also left open for a sensor to stand alone in a site.
It is an abstract class definition which has to be overridden (by eg. a Fluksosensor).

This class contains all metadata concerning the function and type of the sensor (eg. electricity - solar, ...)
"""

from opengrid.library import misc
from opengrid import ureg
import pandas as pd
import tmpo, sqlite3


class Sensor(object):
    def __init__(self, key=None, device=None, site=None, type=None,
                 description=None, system=None, quantity=None, unit=None,
                 direction=None, tariff=None, cumulative=None):
        self.key = key
        self.device = device
        self.site = site
        self.type = type
        self.description = description
        self.system = system
        self.quantity = quantity
        self.unit = unit
        self.direction = direction
        self.tariff = tariff
        self.cumulative = cumulative

    def __repr__(self):
        return """
    {}
    Key: {}
    Type: {}
    """.format(self.__class__.__name__,
               self.key,
               self.type
               )

    def get_data(self, head=None, tail=None, resample='min'):
        """
        Return a Pandas Series with measurement data

        Parameters
        ----------
        head, tail: timestamps for the begin and end of the interval

        Notes
        -----
        This is an abstract method, because each type of sensor has a different way of fetching the data.

        Returns
        -------
        Pandas Series
        """

        raise NotImplementedError("Subclass must implement abstract method")

    def _get_default_unit(self, diff=True, resample='min'):
        """
        Return a string representation of the default unit for the requested operation
        If there is no unit, returns None

        Parameters
        ----------
        diff : True (default) or False
            If True, the original data has been differentiated
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.

        Returns
        -------
        target : str or None
            String representation of the target unit, eg m3/h, kW, ...
        """

        if self.type in ['electricity', 'gas', 'heat', 'energy']:
            if diff:
                target = 'W'
            else:
                target = 'kWh'
        elif self.type == 'water':
            if diff:
                target = 'l/min'
            else:
                target = 'liter'
        elif self.type == 'temperature':
            target = 'degC'
        elif self.type == 'pressure':
            target = 'Pa'
        elif self.type in ['battery']:
            target = 'V'
        elif self.type in ['current']:
            target = 'A'
        elif self.type in ['light']:
            target = 'lux'
        elif self.type == 'humidity':
            target = 'percent'
        elif self.type in ['error', 'vibration', 'proximity']:
            target = ''

        else:
            target = None

        return target

    def _unit_conversion_factor(self, diff=True, resample='min', target='default'):
        """
        Return a conversion factor to convert the obtained data
        The method starts from the unit of the sensor, and takes
        into account sampling, differentiation (if any) and target unit.

        For gas, a default calorific value of 10 kWh/liter is used.

        For some units, unit conversion does not apply, and 1.0 is returned.

        Parameters
        ----------
        diff : True (default) or False
            If True, the original data has been differentiated
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.
        target : str , default='default'
            String representation of the target unit, eg m3/h, kW, ...
            If None, 1.0 is returned

        Returns
        -------
        cf : float
            Multiplication factor for the original data to the target unit
        """

        # get the target
        if target == 'default':
            target = self._get_default_unit(diff=diff, resample=resample)
        if target is None:
            return 1.0

        if resample == 'raw':
            if diff:
                raise NotImplementedError("Differentiation always needs a sampled dataframe")

        # get the source
        if not self.type == 'gas':
            if not diff:
                source = self.unit
            else:
                # differentiation. Careful, this is a hack of the unit system.
                # we have to take care manually of some corner cases
                if self.unit:
                    source = self.unit + '/' + resample
                else:
                    source = self.unit

            return misc.unit_conversion_factor(source, target)
        else:
            # for gas, we need to take into account the calorific value
            # as of now, we use 10 kWh/l by default
            CALORIFICVALUE = 10
            q_src = 1 * ureg(self.unit)
            q_int = q_src * ureg('Wh/liter')
            if not diff:
                source = str(q_int.units)  # string representing the unit, mostly kWh
            else:
                source = str(q_int.units) + '/' + resample
            return CALORIFICVALUE * misc.unit_conversion_factor(source, target)

    def last_timestamp(self, epoch=False):
        """
        Get the last timestamp for a sensor

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
        raise NotImplementedError("Subclass must implement abstract method")


class Fluksosensor(Sensor):
    def __init__(self, key=None, token=None, device=None, type=None,
                 description=None, system=None, quantity=None, unit=None,
                 direction=None, tariff=None, cumulative=None, tmpos=None):

        # invoke init method of abstract Sensor
        super(Fluksosensor, self).__init__(key=key,
                                           device=device,
                                           site=device.site if device else None,
                                           type=type,
                                           description=description,
                                           system=system,
                                           quantity=quantity,
                                           unit=unit,
                                           direction=direction,
                                           tariff=tariff,
                                           cumulative=cumulative)

        if token != '':
            self.token = token
        else:
            self.token = device.mastertoken

        if self.unit == '' or self.unit is None:
            if self.type in ['water', 'gas']:
                self.unit = 'liter'
            elif self.type == 'electricity':
                self.unit = 'Wh'
            elif self.type == 'pressure':
                self.unit = 'Pa'
            elif self.type == 'temperature':
                self.unit = 'degC'
            elif self.type == 'battery':
                self.unit = 'V'
            elif self.type == 'light':
                self.unit = 'lux'
            elif self.type == 'humidity':
                self.unit = 'percent'
            elif self.type in ['error', 'vibration', 'proximity']:
                self.unit = ''


        if self.cumulative == '' or self.cumulative is None:
            if self.type in ['water', 'gas', 'electricity', 'vibration']:
                self.cumulative = True
            else:
                self.cumulative = False

        self._tmpos = tmpos

    @property
    def tmpos(self):
        if self._tmpos is not None:
            return self._tmpos
        elif self.device is not None:
            return self.device.tmpos
        else:
            raise AttributeError('TMPO session not defined')

    @property
    def has_data(self):
        """
        Checks if a sensor actually has data by checking the length of the
        tmpo block list

        Returns
        -------
        bool
        """
        tmpos = self.site.hp.get_tmpos()
        return len(tmpos.list(self.key)[0]) != 0

    def get_data(self, head=None, tail=None, diff='default', resample='min', unit='default', tz='UTC'):
        """
        Connect to tmpo and fetch a data series

        Parameters
        ----------
        sensors : list of Sensor objects
            If None, use sensortype to make a selection
        sensortype : string (optional)
            gas, water, electricity. If None, and Sensors = None,
            all available sensors in the houseprint are fetched
        head, tail: timestamps
            Can be epoch, datetime of pd.Timestamp, with our without timezone (default=UTC)
        diff : bool or 'default'
            If True, the original data will be differentiated
            If 'default', the sensor will decide: if it has the attribute
            cumulative==True, the data will be differentiated.
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.
        unit : str , default='default'
            String representation of the target unit, eg m**3/h, kW, ...
        tz : str, default='UTC'
            Specify the timezone for the index of the returned dataframe

        Returns
        -------
        Pandas Series with additional attribute 'unit' set to
        the string representation of the unit of the data.
        """

        if head is None:
            head = 0
        if tail is None:
            tail = 2147483647  # tmpo epochs max

        data = self.tmpos.series(sid=self.key, head=head, tail=tail)

        if data.dropna().empty:
            # Return an empty dataframe with correct name
            return pd.Series(name=self.key)

        data = data.tz_convert(tz)

        if resample != 'raw':

            if resample == 'hour':
                rule = 'H'
            elif resample == 'day':
                rule = 'D'
            else:
                rule = resample

            # interpolate to requested frequency
            newindex = data.resample(rule).first().index
            data = data.reindex(data.index.union(newindex))
            data = data.interpolate(method='time')
            data = data.reindex(newindex)

            if diff == 'default':
                diff = self.cumulative

            if diff:
                data = data.diff()

        # unit conversion
        if unit == 'default':
            unit = self._get_default_unit(diff=diff, resample=resample)
        ucf = self._unit_conversion_factor(diff=diff, resample=resample, target=unit)
        data *= ucf
        data.unit = unit

        return data

    def last_timestamp(self, epoch=False):
        """
        VERY HACKY CODE, WAITING FOR A PULL-REQUEST IN TMPO TO GO THROUGH

            Get the theoretical last timestamp for a sensor
            It is the mathematical end of the last block, the actual last sensor stamp may be earlier

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
        query = tmpo.SQL_TMPO_LAST
        sid = self.key
        tmpos = self.site.hp.get_tmpos()

        dbcon = sqlite3.connect(tmpos.db)
        dbcur = dbcon.cursor()
        dbcur.execute(tmpo.SQL_SENSOR_TABLE)
        dbcur.execute(tmpo.SQL_TMPO_TABLE)

        query = dbcur.execute(query, (sid,))
        try:
            rid, lvl, bid = query.fetchone()
        except TypeError:
            return None

        end_of_block = tmpos._blocktail(lvl, bid)

        dbcon.close()

        if epoch:
            return end_of_block
        else:
            return pd.Timestamp.fromtimestamp(end_of_block).tz_localize('UTC')