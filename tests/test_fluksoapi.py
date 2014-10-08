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

    def test_find_csv(self):
        """test find_csv for the two possible results"""
        
        datafolder = os.path.join(test_dir, 'data')
        self.assertRaises(ValueError, fluksoapi.find_csv, datafolder, 'f81fb35a62f59a987d8eeaeffc845ed0')
        
        self.assertEqual('FL12345678_f81fb35a62f59a987d8eea3ffc845ed0_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv',
                         fluksoapi.find_csv(datafolder, 'f81fb35a62f59a987d8eea3ffc845ed0'))
                         
        
    def test_consolidate(self):
        """Consolidating 2 files and checking result"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'f81fb35a62f59a987d8eeaeffc845ed0')
              
        ts1 = fluksoapi.load_csv(os.path.join(datafolder, 'FL12345678_f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertTrue(np.isnan(ts1['f81fb35a62f59a987d8eeaeffc845ed0'].loc[dt.datetime(2014,1,8,8,0,0, tzinfo=pytz.UTC)]))       
        ts2 = fluksoapi.load_csv(os.path.join(datafolder, 'FL12345678_f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv'))    
        #ts = fluksoapi.load_csv(os.path.join(datafolder, 'f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_16-01-00.csv'))
        #pdb.set_trace()        

        ts = fluksoapi.load_csv(new_csv)        
        self.assertEqual(ts.index[0], ts1.index[0])
        self.assertEqual(ts.index[-1], ts2.index[-1])
        self.assertEqual(ts['f81fb35a62f59a987d8eeaeffc845ed0'].loc['2014-01-08 08:00:00'], 1120.0, "Last file should overwrite identical indices")
        os.remove(new_csv)
        
    def test_consolidate_day(self):
        """Consolidating 2 files for a single day and checking result"""
        
        datafolder = os.path.join(test_dir, 'data')        
        new_csv=fluksoapi.consolidate_sensor(folder = datafolder, 
                                             sensor = 'f81fb35a62f59a987d8eeaeffc845ed0',
                                             dt_day = dt.datetime(2014,1,7))
              
        ts1 = fluksoapi.load_csv(os.path.join(datafolder, 'FL12345678_f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertTrue(np.isnan(ts1['f81fb35a62f59a987d8eeaeffc845ed0'].loc[dt.datetime(2014,1,8,8,0,0, tzinfo=pytz.UTC)]))       
        ts2 = fluksoapi.load_csv(os.path.join(datafolder, 'FL12345678_f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_16-02-00_TO_2014-01-08_16-01-00.csv'))    
        #ts = fluksoapi.load_csv(os.path.join(datafolder, 'f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_16-01-00.csv'))
        #pdb.set_trace()        

        ts = fluksoapi.load_csv(new_csv)        
        self.assertEqual(ts.index[0], ts1.index[0])
        self.assertEqual(ts.index[-1], dt.datetime(2014,1,8,0,0,0, tzinfo=pytz.UTC))
        
        os.remove(new_csv)
        
    def test_consolidate_raises(self):
        """Consolidation for a sensor without files should raise a ValueError"""
        
        datafolder = os.path.join(test_dir, 'data')    
        self.assertRaises(ValueError, fluksoapi.consolidate_sensor, 
                          folder = datafolder, sensor = 'nonexistent')
                                        
    def test_load_csv(self):
        """load_csv should return a pandas dataframe with localized index (UTC)"""
        
        datafolder = os.path.join(test_dir, 'data')          
        df = fluksoapi.load_csv(os.path.join(datafolder, 'FL12345678_f81fb35a62f59a987d8eeaeffc845ed0_FROM_2014-01-07_08-02-00_TO_2014-01-08_08-01-00.csv'))
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.index.tz, pytz.UTC, "the tz is {} instead of UTC".format(df.index.tz))
        self.assertListEqual(df.columns.tolist(), ['f81fb35a62f59a987d8eeaeffc845ed0'])


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
