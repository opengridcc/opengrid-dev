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
sys.path.append(os.path.join(test_dir, os.pardir, os.pardir))
from opengrid.library import fluksoapi

class FluksoapiTest(unittest.TestCase):
    """
    Class for testing the module fluksoapi
    """

    def test_consolidate_single(self):
        """Return abspath if a single file found"""
        
        datafolder = os.path.join(test_dir, 'data')
        self.assertRaises(ValueError, fluksoapi.consolidate_sensor, datafolder, 'f81fb35a62f59a987d8eea3ffc845ed0')
        
        csv_expected = os.path.join(datafolder, 'FL12345678_sensorS_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv' )
        self.assertEqual(csv_expected,
                         fluksoapi.consolidate_sensor(datafolder, 'sensorS'))
                         
        
                         
    def test_consolidate_multiple(self):
        """Consolidate and return single filename if more than one file found"""
        
        datafolder = os.path.join(test_dir, 'data')
        csv_expected = os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_08-02-00_TO_2014-01-08_16-01-00.csv' )
        self.assertEqual(csv_expected, fluksoapi.consolidate_sensor(datafolder, 'sensorD'))
                         
        os.remove(csv_expected)


    def test_consolidate_raises(self):
        """Raise ValueError if no file found"""
        
        datafolder = os.path.join(test_dir, 'data')
        self.assertRaises(ValueError, fluksoapi.consolidate_sensor, datafolder, 'thissensordoesnotexist')
        

        
    def test_consolidate(self):
        """Consolidating 2 files and checking variable"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'sensorD')
              
        ts1 = fluksoapi.load_file(os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertTrue(np.isnan(ts1['sensorD'].loc[dt.datetime(2014,1,8,8,0,0, tzinfo=pytz.UTC)]))       
        ts2 = fluksoapi.load_file(os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv'))    
        #ts = fluksoapi.load_file(os.path.join(datafolder, 'f81fb35a62f59a987d8eea3ffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_16-01-00.csv'))
        #pdb.set_trace()        

        ts = fluksoapi.load_file(new_csv)        
        self.assertEqual(ts.index[0], ts1.index[0])
        self.assertEqual(ts.index[-1], ts2.index[-1])
        self.assertEqual(ts['sensorD'].loc['2014-01-08 08:00:00'], 1120.0, "Last file should overwrite identical indices")
        os.remove(new_csv)


    def test_consolidate_with_hidden_file(self):
        """Consolidate should skip hidden file"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'sensorH')
                                             
        self.assertEqual(new_csv, os.path.join(datafolder, 'FL12345678_sensorH_FROM_2014-01-07_12-02-00_TO_2014-01-08_16-01-00.csv'))
        os.remove(new_csv)
        
        
    def test_consolidate_single_file(self):
        """Consolidating a single file should NOT consolidate but should return the file"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'sensorS')
              
        self.assertEqual(new_csv, os.path.join(datafolder,'FL12345678_sensorS_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv'))
        
    def test_consolidate_day(self):
        """Consolidating 2 files for a single day and checking variable"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'sensorD',
                                             dt_day = dt.datetime(2014,1,7))
              
        ts1 = fluksoapi.load_file(os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertTrue(np.isnan(ts1['sensorD'].loc[dt.datetime(2014,1,8,8,0,0, tzinfo=pytz.UTC)]))       
        ts2 = fluksoapi.load_file(os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv'))

        ts = fluksoapi.load_file(new_csv)
        self.assertEqual(ts.index[0], ts1.index[0])
        self.assertEqual(ts.index[-1], dt.datetime(2014,1,8,0,0,0, tzinfo=pytz.UTC))
        
        os.remove(new_csv)
        
    def test_load_file(self):
        """load_file should return a pandas dataframe with localized index (UTC)"""
        
        datafolder = os.path.join(test_dir, 'data')          
        df = fluksoapi.load_file(os.path.join(datafolder, 'FL12345678_sensorD_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.index.tz, pytz.UTC, "the tz is {} instead of UTC".format(df.index.tz))
        self.assertListEqual(df.columns.tolist(), ['sensorD'])


    def test_parse_date_from_datetime(self):
        """Parsing a datetime into a pandas.Timestamp"""
        
        BXL = pytz.timezone('Europe/Brussels')
        dt_ = BXL.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = fluksoapi._parse_date(dt_)
        self.assertEqual(pts.value/1e9, epoch_expected)
        
    
    def test_parse_date_from_datetime_naive(self):
        """Parsing a naïve datetime into a pandas.Timestamp makes it UTC"""
        
        dt_ = pytz.UTC.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = fluksoapi._parse_date(dt.datetime(2014,11,23,1,2,3))
        self.assertEqual(pts.value/1e9, epoch_expected)
        
        
    def test_parse_date_from_posix(self):
        """Parsing a float"""
        
        pts = fluksoapi._parse_date(1416778251.460574)
        self.assertEqual(1416778251.460574, pts.value/1e9)
        
    def test_parse_date_from_string(self):
        """Parsing some commong types of strings"""
        
        dt_ = pytz.UTC.localize(dt.datetime(2014,11,23,1,2,3))
        epoch = pytz.UTC.localize(dt.datetime(1970,1,1,0,0,0))
        epoch_expected = (dt_ - epoch).total_seconds()
        
        pts = fluksoapi._parse_date('20141123 01:02:03')
        self.assertEqual(pts.value/1e9, epoch_expected)   
        
        pts = fluksoapi._parse_date('2014-11-23 01:02:03')
        self.assertEqual(pts.value/1e9, epoch_expected)   

        pts = fluksoapi._parse_date('2014-11-23T010203')
        self.assertEqual(pts.value/1e9, epoch_expected)   


if __name__ == '__main__':
    
    #http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python    
    ln = lambda f: getattr(FluksoapiTest, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    unittest.TestLoader.sortTestMethodsUsing = lncmp

    suite1 = unittest.TestLoader().loadTestsFromTestCase(FluksoapiTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
