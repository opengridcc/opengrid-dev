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
from opengrid import config
cfg = config.Config()

class CacheTest(unittest.TestCase):
    
    def test_init(self):
        """Check if correct folder is used"""
        
        ch = caching.Cache('standby', folder=os.getcwd())
        self.assertEqual(ch.folder, os.getcwd())
        
        ch = caching.Cache('water_standby')
        self.assertEqual(ch.folder, os.path.join(os.getcwd(), 'data'))
        
        
    def test_load(self):
        ch = caching.Cache('elec_standby')
        df = ch._load('mysensor')
        
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=365)).all())
        self.assertEqual(df.columns, ['mysensor'])
        
        
    def test_get(self):
        
        ch = caching.Cache('elec_standby')
        df = ch.get('mysensor')
        
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=365)).all())
        self.assertEqual(df.columns, ['mysensor'])
        
        df = ch.get('mysensor', end='20160115')
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160101', freq='D', periods=15)).all())
        
        df = ch.get('mysensor', start = '20160707', end='20160708')
        self.assertTrue((df.index == pd.DatetimeIndex(start='20160707', freq='D', periods=2)).all())
                         
    def test_check_df(self):
        ch = caching.Cache('elec_standby')
        
        df = pd.DataFrame()
        self.assertFalse(ch.check_df(df))
        
        index = pd.DatetimeIndex(start='20160101', freq='D', periods=3)       
        df = pd.DataFrame(index=index, data=np.random.randn(3,2), columns=['A', 'B'])
        self.assertFalse(ch.check_df(df))
        
        index = pd.DatetimeIndex(['20160201', '20160202', '20160203'])       
        df = pd.DataFrame(index=index, data=np.random.randn(3), columns=['A'])
        self.assertTrue(ch.check_df(df))
        
        index = pd.DatetimeIndex(['20160201', '20160202', '20160204'])       
        df = pd.DataFrame(index=index, data=np.random.randn(3), columns=['A'])
        self.assertFalse(ch.check_df(df))
        
        
        


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
