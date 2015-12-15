__author__ = 'Jan Pecinovsky'

"""
A sensor generates a single data stream.
It can have a parent device, but the possibility is also left open for a sensor to stand alone in a site.
It is an abstract class definition which has to be overridden (by eg. a Fluksosensor).

This class contains all metadata concerning the function and type of the sensor (eg. electricity - solar, ...)
"""

class Sensor(object):
    def __init__(self, key, device, site, type, description, system, quantity, unit, direction, tariff):
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

class Fluksosensor(Sensor):
    def __init__(self, key, token, device, type, description, system, quantity, unit, direction, tariff):

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
                                          tariff = tariff)

        if token != '':
            self.token = token
        else:
            self.token = device.mastertoken

    # @Override :-D
    def get_data(self, head = None, tail = None, resample = 'min'):
        '''
            Connect to tmpo and fetch a data series

            Parameters
            ----------
            head, tail: optional timestamps

            Returns
            -------
            Pandas Series
        '''

        tmpos = self.site.hp.get_tmpos()

        if head is None:
            head = 0
        if tail is None:
            tail = 2147483647 #tmpo epochs max

        data = tmpos.series(sid = self.key,
                           head = head,
                           tail = tail)

        if resample == 'raw':
            return data

        if not data.dropna().empty:

            #interpolate on seconds
            newindex = data.resample('s').index
            data = data.reindex(data.index + newindex)
            data = data.interpolate(method='time')
            data = data.reindex(newindex)

            #resample as requested
            data = data.resample(resample)

        return data