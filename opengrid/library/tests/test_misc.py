# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 02:37:25 2013

@author: roel
"""

import os
import sys
import unittest
import inspect
import numpy as np
import pytz

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to OpenGrid to sys.path
sys.path.insert(1, os.path.join(test_dir, os.pardir, os.pardir, os.pardir))
from opengrid.library.misc import *


class MiscTest(unittest.TestCase):
    """
    Class for testing the misc functions
    """

    def test_parse_date_from_datetime(self):
        """Parsing a datetime into a pandas.Timestamp"""

        bxl = pytz.timezone('Europe/Brussels')
        dt_ = bxl.localize(dt.datetime(2014, 11, 23, 1, 2, 3))
        epoch = pytz.UTC.localize(dt.datetime(1970, 1, 1, 0, 0, 0))
        epoch_expected = (dt_ - epoch).total_seconds()

        pts = parse_date(dt_)
        self.assertEqual(pts.value / 1e9, epoch_expected)

    def test_parse_date_from_datetime_naive(self):
        """Parsing a naïve datetime into a pandas.Timestamp makes it UTC"""

        dt_ = pytz.UTC.localize(dt.datetime(2014, 11, 23, 1, 2, 3))
        epoch = pytz.UTC.localize(dt.datetime(1970, 1, 1, 0, 0, 0))
        epoch_expected = (dt_ - epoch).total_seconds()

        pts = parse_date(dt.datetime(2014, 11, 23, 1, 2, 3))
        self.assertEqual(pts.value / 1e9, epoch_expected)

    def test_parse_date_from_posix(self):
        """Parsing a float"""

        pts = parse_date(1416778251.460574)
        self.assertEqual(1416778251.460574, pts.value / 1e9)

    def test_parse_date_from_string(self):
        """Parsing some commong types of strings"""

        dt_ = pytz.UTC.localize(dt.datetime(2014, 11, 23, 1, 2, 3))
        epoch = pytz.UTC.localize(dt.datetime(1970, 1, 1, 0, 0, 0))
        epoch_expected = (dt_ - epoch).total_seconds()

        pts = parse_date('20141123 01:02:03')
        self.assertEqual(pts.value / 1e9, epoch_expected)

        pts = parse_date('2014-11-23 01:02:03')
        self.assertEqual(pts.value / 1e9, epoch_expected)

        pts = parse_date('2014-11-23T010203')
        self.assertEqual(pts.value / 1e9, epoch_expected)

    def test_time_to_timedelta(self):
        t = dt.time(2, 45, 23)
        self.assertEqual(time_to_timedelta(t).total_seconds(), 7200 + 45 * 60 + 23.0)

        t = dt.time(2, 45, 23, tzinfo=pytz.timezone('Europe/Brussels'))
        self.assertEqual(time_to_timedelta(t).total_seconds(), 7200 + 45 * 60 + 23.0)

    def test_split_by_day(self):
        index = pd.DatetimeIndex(start='20160101 03:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data=np.random.randn(80, 2), columns=['A', 'B'])

        # without specifying hours
        list_daily = split_by_day(df)
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], index[0])
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 00:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 23:51:15'))

        # specifying start
        list_daily = split_by_day(df, starttime=dt.time(1, 30))
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], pd.Timestamp('20160101 03:51:15'))
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 01:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 23:51:15'))

        # specifying start and end
        list_daily = split_by_day(df, starttime=dt.time(1, 30), endtime=dt.time(6))
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], pd.Timestamp('20160101 03:51:15'))
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 01:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 05:51:15'))

    def test_unit_conversion_factor(self):
        cf = unit_conversion_factor('liter/minute', 'm**3/hour')
        np.testing.assert_array_almost_equal(cf, 1 / 1e3 * 60.)

        cf = unit_conversion_factor('Wh/min', 'kW')
        np.testing.assert_array_almost_equal(cf, 60 / 1000.)

    def test_dayset(self):
        ds = dayset(start=pd.Timestamp('20160101'), end=pd.Timestamp('20160131'))
        comp = [dt.date(year=2016, month=1, day=day) for day in range(1, 32)]
        self.assertEqual(ds, comp)

    def test_split_irregular_date_list(self):
        d1 = dayset(start=pd.Timestamp('20160401'), end=pd.Timestamp('20160405'))
        d2 = dayset(start=pd.Timestamp('20160101'), end=pd.Timestamp('20160103'))
        date_list = d1 + d2
        split = split_irregular_date_list(date_list=date_list)
        self.assertEqual(split[0][0], dt.date(year=2016, month=1, day=1))
        self.assertEqual(split[0][1], dt.date(year=2016, month=1, day=3))
        self.assertEqual(split[1][0], dt.date(year=2016, month=4, day=1))
        self.assertEqual(split[1][1], dt.date(year=2016, month=4, day=5))

    def test_calculate_temperature_equivalent(self):
        temps = [8.3, 8.7, 9.2]
        t_equiv = calculate_temperature_equivalent(pd.Series(temps))
        last = t_equiv.iloc[-1]
        last_man = 0.6*temps[2] + 0.3*temps[1] + 0.1*temps[0]
        self.assertEqual(last, last_man)
        self.assertEqual(t_equiv.name, 'temp_equivalent')

    def test_calculate_degree_days(self):
        temp_equivs = [-5.0, 1.5, 25.5]
        hdd = calculate_degree_days(temperature_equivalent=pd.Series(temp_equivs), base_temperature=16.5)
        self.assertEqual(hdd.tolist(), [21.5, 15.0, 0.0])
        self.assertEqual(hdd.name, 'heating_degree_days_16.5')

        cdd = calculate_degree_days(temperature_equivalent=pd.Series(temp_equivs), base_temperature=24, cooling=True)
        self.assertEqual(cdd.tolist(), [0.0, 0.0, 1.5])
        self.assertEqual(cdd.name, 'cooling_degree_days_24')


if __name__ == '__main__':
    # http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python
    if sys.version_info.major >= 3:  # compatibility python 3
        ln = lambda f: getattr(MiscTest, f).__code__.co_firstlineno  # functions have renamed attributes
        lncmp = lambda _, a, b: (ln(a) > ln(b)) - (
        ln(a) < ln(b))  # cmp() was deprecated, see https://docs.python.org/3.0/whatsnew/3.0.html
    else:
        ln = lambda f: getattr(MiscTest, f).im_func.func_code.co_firstlineno
        lncmp = lambda _, a, b: cmp(ln(a), ln(b))

    unittest.TestLoader.sortTestMethodsUsing = lncmp

    suite1 = unittest.TestLoader().loadTestsFromTestCase(MiscTest)
    alltests = unittest.TestSuite([suite1])

    # selection = unittest.TestSuite()
    # selection.addTest(HouseprintTest('test_get_sensor'))

    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
