# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 02:37:25 2013

@author: roel
"""

import os, sys
import unittest
import inspect
import numpy as np
import pdb
import datetime as dt
import pandas as pd
import pytz

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.insert(1, os.path.join(test_dir, os.pardir, os.pardir, os.pardir))
from opengrid.library.misc import *

class MiscTest(unittest.TestCase):
    """
    Class for testing the module fluksoapi
    """


    def test_parse_date_from_datetime(self):
        """Parsing a datetime into a pandas.Timestamp"""
        
        BXL = pytz.timezone('Europe/Brussels')
        dt_ = BXL.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = parse_date(dt_)
        self.assertEqual(pts.value/1e9, epoch_expected)
        
    
    def test_parse_date_from_datetime_naive(self):
        """Parsing a naïve datetime into a pandas.Timestamp makes it UTC"""
        
        dt_ = pytz.UTC.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = parse_date(dt.datetime(2014,11,23,1,2,3))
        self.assertEqual(pts.value/1e9, epoch_expected)
        
        
    def test_parse_date_from_posix(self):
        """Parsing a float"""
        
        pts = parse_date(1416778251.460574)
        self.assertEqual(1416778251.460574, pts.value/1e9)
        
    def test_parse_date_from_string(self):
        """Parsing some commong types of strings"""
        
        dt_ = pytz.UTC.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = parse_date('20141123 01:02:03')
        self.assertEqual(pts.value/1e9, epoch_expected)   
        
        pts = parse_date('2014-11-23 01:02:03')
        self.assertEqual(pts.value/1e9, epoch_expected)   

        pts = parse_date('2014-11-23T010203')
        self.assertEqual(pts.value/1e9, epoch_expected)

    def test_time_to_timedelta(self):

        t = dt.time(2,45,23)
        self.assertEqual(time_to_timedelta(t).total_seconds(), 7200+45*60+23.0)

        t = dt.time(2,45,23, tzinfo=pytz.timezone('Europe/Brussels'))
        self.assertEqual(time_to_timedelta(t).total_seconds(), 7200+45*60+23.0)

    def test_split_by_day(self):
        index = pd.DatetimeIndex(start='20160101 03:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data=np.random.randn(80,2), columns=['A', 'B'])

        # without specifying hours
        list_daily = split_by_day(df)
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], index[0])
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 00:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 23:51:15'))

        # specifying start
        list_daily = split_by_day(df, starttime = dt.time(1,30))
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], pd.Timestamp('20160101 03:51:15'))
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 01:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 23:51:15'))

        # specifying start and end
        list_daily = split_by_day(df, starttime=dt.time(1,30), endtime=dt.time(6))
        self.assertEqual(len(list_daily), 4)
        self.assertEqual(list_daily[0].index[0], pd.Timestamp('20160101 03:51:15'))
        self.assertEqual(list_daily[1].index[0], pd.Timestamp('20160102 01:51:15'))
        self.assertEqual(list_daily[1].index[-1], pd.Timestamp('20160102 05:51:15'))

    def test_unit_conversion_factor(self):
        cf = unit_conversion_factor('liter/minute', 'm**3/hour')
        np.testing.assert_array_almost_equal(cf, 1/1e3*60.)

        cf = unit_conversion_factor('Wh/min', 'kW')
        np.testing.assert_array_almost_equal(cf, 60/1000.)
    

if __name__ == '__main__':
    
    #http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python    
    ln = lambda f: getattr(MiscTest, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    unittest.TestLoader.sortTestMethodsUsing = lncmp

    suite1 = unittest.TestLoader().loadTestsFromTestCase(MiscTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
