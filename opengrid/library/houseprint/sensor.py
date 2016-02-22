__author__ = 'Jan Pecinovsky'

"""
A sensor generates a single data stream.
It can have a parent device, but the possibility is also left open for a sensor to stand alone in a site.
It is an abstract class definition which has to be overridden (by eg. a Fluksosensor).

This class contains all metadata concerning the function and type of the sensor (eg. electricity - solar, ...)
"""

from opengrid.library import misc
from opengrid import ureg

class Sensor(object):
    def __init__(self, key, device, site, type, description, system, quantity, unit, direction, tariff, cumulative):
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

    def get_data(self, head = None, tail = None, resample = 'min'):
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

        Parameters
        ----------
        diff : True (default) or False
            If True, the original data has been differentiated
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.

        Returns
        -------
        target : str
            String representation of the target unit, eg m3/h, kW, ...
        """

        if self.type == 'electricity':
            if diff:
                target = 'W'
            else:
                target = 'kWh'
        elif self.type == 'water':
            if diff:
                target = 'l/min'
            else:
                target = 'liter'
        elif self.type == 'gas':
            if diff:
                target = 'W'
            else:
                target = 'kWh'

        return target


    def _unit_conversion_factor(self, diff=True, resample='min', target='default'):
        """
        Return a conversion factor to convert the obtained data
        The method starts from the unit of the sensor, and takes
        into account sampling, differentiation (if any) and target unit.

        For gas, a default calorific value of 10 kWh/liter is used.

        Parameters
        ----------
        diff : True (default) or False
            If True, the original data has been differentiated
        resample : str (default='min')
            Sampling rate, if any.  Use 'raw' if no resampling.
        target : str , default='default'
            String representation of the target unit, eg m3/h, kW, ...

        Returns
        -------
        cf : float
            Multiplication factor for the original data to the target unit
        """


        # get the target
        if target == 'default':
            target = self._get_default_unit(diff=diff, resample=resample)

        if resample == 'raw':
            if diff:
                raise NotImplementedError("Differentiation always needs a sampled dataframe")

        if not self.type == 'gas':
            if not diff:
                source = self.unit
            else:
                # differentiation
                source = self.unit + '/' + resample

            return misc.unit_conversion_factor(source, target)
        else:
            # for gas, we need to take into account the calorific value
            # as of now, we use 10 kWh/l by default
            CALORIFICVALUE = 10
            q_src = 1*ureg(self.unit)
            q_int = q_src * ureg('Wh/liter')
            if not diff:
                source = list(q_int.units)[0] # string representing the unit, mostly kWh
            else:
                source = list(q_int.units)[0] + '/' + resample
            return CALORIFICVALUE * misc.unit_conversion_factor(source, target)

class Fluksosensor(Sensor):
    def __init__(self, key, token, device, type, description, system, quantity, unit, direction, tariff, cumulative):

        #invoke init method of abstract Sensor
        super(Fluksosensor, self).__init__(key = key,
                                           device = device,
                                           site = device.site,
                                           type = type,
                                           description = description,
                                           system = system,
                                           quantity = quantity,
                                           unit = unit,
                                           direction = direction,
                                           tariff = tariff,
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

        if self.cumulative == '' or self.cumulative is None:
            if self.type in ['water', 'gas', 'electricity']:
                self.cumulative = True
            else:
                self.cumulative = False


    # @Override :-D
    def get_data(self, head=None, tail=None, diff='default', resample='min', unit='default'):
        '''
        Connect to tmpo and fetch a data series

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
        Pandas Series with additional attribute 'unit' set to
        the string representation of the unit of the data.
        '''

        tmpos = self.site.hp.get_tmpos()

        if head is None:
            head = 0
        if tail is None:
            tail = 2147483647 #tmpo epochs max

        data = tmpos.series(sid = self.key,
                           head = head,
                           tail = tail)

        if not data.dropna().empty and resample != 'raw':

            if resample == 'hour':
                rule = 'H'
            elif resample == 'day':
                rule = 'D'
            else:
                rule = resample

            #interpolate to requested frequency
            newindex = data.resample(rule).index
            data = data.reindex(data.index + newindex)
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