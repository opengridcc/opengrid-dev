# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 09:36:16 2016

@author: roel
"""

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
import pandas as pd
import pytz

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
os.chdir(test_dir)
# add the path to opengrid to sys.path
sys.path.insert(1, os.path.join(test_dir, os.pardir, os.pardir, os.pardir))
from opengrid.library import caching
from opengrid.library.houseprint import Sensor

# Note: there is a opengrid.cfg in the test_dir which is loaded here!!
from opengrid import config
cfg = config.Config()

class CacheTest(unittest.TestCase):
    
    def test_init(self):
        """Check if correct folder is used"""
        
        ch = caching.Cache('standby', folder=os.getcwd())
        self.assertEqual(ch.folder, os.getcwd())
        
        ch = caching.Cache('water_standby')
        self.assertEqual(ch.folder, os.path.join(os.getcwd(), 'data', 'cache_day'))
        
        
    def test_load(self):
        """Load and parse a cached object correctly"""
        ch = caching.Cache('elec_standby')
        df = ch._load('mysensor')
        
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=365, tz='UTC')).all())
        self.assertEqual(df.columns, ['mysensor'])
        
        
    def test_get_raises(self):
        """Raise TypeError when argument sensors is not a list"""
        ch = caching.Cache('elec_standby')
        mysensor = Sensor(key='mysensor', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)
        self.assertRaises(TypeError, ch.get, mysensor)

    def test_get_single(self):
        """Obtain cached results and return a correct dataframe"""
        ch = caching.Cache('elec_standby')
        mysensor = Sensor(key='mysensor', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)
        df = ch.get([mysensor])
        
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=365, tz='UTC')).all())
        self.assertEqual(df.columns, ['mysensor'])
        
        df = ch.get([mysensor], end='20160115')
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=15, tz='UTC')).all())
        
        df = ch.get([mysensor], start = '20160707', end='20160708')
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160707', freq='D', periods=2, tz='UTC')).all())
        # self.assertFalse(df.index.tz is None, "Returned dataframe is tz-naive") #Removed this test on 21/04/16 after pull request #136 and discussion in #135.
        # However, we need to finalise the discussion: a date is also timezone dependent...


                         
    def test_get_multiple(self):
        """Obtain cached results and return a correct dataframe"""
        ch = caching.Cache('elec_standby')
        mysensor = Sensor(key='mysensor', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)
        mysensor2 = Sensor(key='mysensor2', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)
        df = ch.get([mysensor, mysensor2], end='20160104')

        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=4, tz='UTC')).all())
        self.assertListEqual(df.columns.tolist(), ['mysensor', 'mysensor2'])
        self.assertEqual(df.ix[1, 'mysensor2'], 5)
        self.assertTrue(np.isnan(df.ix[3, 'mysensor2']))


    def test_check_df_series(self):
        """check if series is not empty and has daily frequency"""
        ch = caching.Cache('elec_standby')

        df = pd.Series()
        self.assertFalse(ch.check_df(df))

        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        ts = pd.Series(index=index, data=np.random.randn(3), name='A')
        self.assertTrue(ch.check_df(ts))

    def test_check_df(self):
        """check if dataframe is not empty and has daily frequency"""
        ch = caching.Cache('elec_standby')

        df = pd.DataFrame()
        self.assertFalse(ch.check_df(df))

        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        df = pd.DataFrame(index=index, data=np.random.randn(3,2), columns=['A', 'B'])
        self.assertTrue(ch.check_df(df))
        
        index = pd.DatetimeIndex(['20160201', '20160202', '20160203'], tz='UTC')
        df = pd.DataFrame(index=index, data=np.random.randn(3), columns=['A'])
        self.assertTrue(ch.check_df(df))
        
        index = pd.DatetimeIndex(['20160201', '20160202', '20160204'], tz='UTC')
        df = pd.DataFrame(index=index, data=np.random.randn(3), columns=['A'])
        self.assertFalse(ch.check_df(df))

    def test_write_single1(self):
        """Write dataframe with single columns only"""
        ch = caching.Cache('elec_temp')

        # write a dataframe with single column
        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        df = pd.DataFrame(index=index, data=np.random.randn(3), columns=['testsensor'])
        expected_path = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor.csv')
        self.assertFalse(os.path.exists(expected_path))
        try:
            ch._write_single(df)
            self.assertTrue(os.path.exists(expected_path))
        except:
            raise
        finally:
            os.remove(expected_path)

        # raise ValueError on dataframe with multiple columns
        df = pd.DataFrame(index=index, data=np.random.randn(3,2), columns=['testsensor1', 'testsensor2'])
        self.assertRaises(ValueError, ch._write_single, df)
        
    def test_write_single2(self):
        """Write timeseries """
        ch = caching.Cache('elec_temp')

        # write a dataframe with single column
        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        df = pd.Series(index=index, data=np.random.randn(3), name='testsensor_series')
        expected_path = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor_series.csv')
        self.assertFalse(os.path.exists(expected_path))
        try:
            ch._write_single(df)
            self.assertTrue(os.path.exists(expected_path))
        except:
            raise
        finally:
            os.remove(expected_path)

        # raise ValueError on series without name
        df = pd.Series(index=index, data=np.random.randn(3))
        self.assertRaises(ValueError, ch._write_single, df)

    def test_write(self):
        """Write dataframe with multiple columns"""
        ch = caching.Cache('elec_temp')

        # write a dataframe with single column
        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        df = pd.DataFrame(index=index, data=np.random.randn(3,2), columns=['testsensor1', 'testsensor2'])
        expected_path1 = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor1.csv')
        expected_path2 = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor2.csv')
        self.assertFalse(os.path.exists(expected_path1))
        self.assertFalse(os.path.exists(expected_path2))

        try:
            ch._write(df)
            self.assertTrue(os.path.exists(expected_path1))
            self.assertTrue(os.path.exists(expected_path2))
        except:
            raise
        finally:
            os.remove(expected_path1)
            os.remove(expected_path2)

    def test_update_single(self):
        """Update an existing cached sensor with new information"""

        ch = caching.Cache('elec_temp')
        testsensor = Sensor(key='testsensor', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)

        try:
            # write a dataframe with single column
            index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
            df = pd.DataFrame(index=index, data=[0,1,2], columns=['testsensor'])
            expected_path = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor.csv')
            self.assertFalse(os.path.exists(expected_path))
            ch._write_single(df)

            index = pd.DatetimeIndex(start='20160103', freq='D', periods=3, tz='UTC')
            df_new = pd.DataFrame(index=index, data=[100,200,300], columns=['testsensor'])
            ch.update(df_new)
            df_res = ch.get([testsensor])
            
            self.assertEqual(df_res.iloc[1,0], 1)
            self.assertEqual(df_res.iloc[2,0], 100)
            self.assertEqual(df_res.iloc[4,0], 300)
        except:
            raise
        finally:
            os.remove(os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor.csv'))

    def test_update_multiple(self):
        """Update an existing cached sensor with new information"""

        ch = caching.Cache('elec_temp')
        testsensor2 = Sensor(key='testsensor2', device=None, site='None', type=None, description=None,system=None,
                                quantity=None,unit=None,direction=None,tariff=None,cumulative=None)

        # write a dataframe with two columns
        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3, tz='UTC')
        df = pd.DataFrame(index=index, data=dict(testsensor1=[0,1,2], testsensor2= [0,1,2]))
        expected_path1 = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor1.csv')
        expected_path2 = os.path.join(test_dir, cfg.get('data', 'folder'), 'cache_day', 'elec_temp_testsensor2.csv')
        self.assertFalse(os.path.exists(expected_path1))
        self.assertFalse(os.path.exists(expected_path2))
        try:
            ch.update(df)
            self.assertTrue(os.path.exists(expected_path1))
            self.assertTrue(os.path.exists(expected_path2))

            index = pd.DatetimeIndex(start='20160103', freq='D', periods=3, tz='UTC')
            df_new = pd.DataFrame(index=index, data=dict(testsensor1=[100,200,300], testsensor2=[100,200,300]))
            ch.update(df_new)
            df_res = ch.get([testsensor2])

            self.assertEqual(df_res.iloc[1,0], 1)
            self.assertEqual(df_res.iloc[2,0], 100)
            self.assertEqual(df_res.iloc[4,0], 300)
        except:
            raise
        finally:
            os.remove(expected_path1)
            os.remove(expected_path2)



if __name__ == '__main__':
    
    #http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python    
    ln = lambda f: getattr(CacheTest, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    unittest.TestLoader.sortTestMethodsUsing = lncmp

    suite1 = unittest.TestLoader().loadTestsFromTestCase(CacheTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
