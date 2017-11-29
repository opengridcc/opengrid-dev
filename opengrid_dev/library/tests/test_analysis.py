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
import pandas as pd
import datetime as dt

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
os.chdir(test_dir)
# add the path to opengrid to sys.path
sys.path.insert(1, os.path.join(test_dir, os.pardir, os.pardir, os.pardir))
from opengrid.library import analysis

# Note: there is a opengrid.cfg in the test_dir which is loaded here!!
from opengrid import config
cfg = config.Config()

class AnalysisTest(unittest.TestCase):
    


    def test_init_DailyAgg(self):
        "Initialize a DailyAgg, check attributes of result"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data=np.arange(0, 80, 1), columns=['A'])

        anls = analysis.DailyAgg(df, agg='min')
        self.assertTrue(hasattr(anls, 'result'))

    def test_DailyAgg_analysis(self):
        "Verify result of analyses"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data={'A':np.arange(0, 80, 1), 'B':np.zeros(80)})

        anls = analysis.DailyAgg(df, agg='min')
        dayindex = pd.DatetimeIndex(start='20160101', freq='D', periods=4)
        self.assertTrue((anls.result.index==dayindex).all())
        self.assertTrue((anls.result['A'] == pd.Series(data=[0,24,48,72], index=dayindex)).all())

    def test_DailyAgg_analysis_with_timelimits(self):
        "Check results when limiting the hours for the analysis"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data={'A':np.arange(0, 80, 1), 'B':np.zeros(80)})

        anls = analysis.DailyAgg(df, agg='min', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55))
        dayindex = pd.DatetimeIndex(start='20160101', freq='D', periods=4)
        self.assertTrue((anls.result.index==dayindex).all())
        self.assertTrue((anls.result['A'] == pd.Series(data=[3,27,51,75], index=dayindex)).all())

    def test_json(self):
        "Verify the to_json method"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data={'A':np.arange(0, 80, 1), 'B':np.zeros(80)})

        js = analysis.DailyAgg(df, agg='min', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55)).to_json()
        self.assertIsInstance(pd.read_json(js), pd.DataFrame)

    def test_analysis_with_empty_df(self):
        "Empty dataframes should not raise errors"

        anls = analysis.DailyAgg(df=pd.DataFrame(), agg='max')
        self.assertIsInstance(anls.result, pd.DataFrame)

        js = anls.to_json()
        self.assertIsInstance(pd.read_json(js), pd.DataFrame)

    def test_run_analysis_twice(self):
        "Running an analysis twice should give same result"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data={'A':np.arange(0, 80, 1), 'B':np.zeros(80)})

        anls = analysis.DailyAgg(df, agg='min', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55))
        result1 = anls.result.copy()
        anls.do_analysis(agg='min', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55))
        result2 = anls.result.copy()
        self.assertTrue((result1==result2).all().all())

    def test_run_analysis_twice_different_args(self):
        "Running an analysis twice should give same result"
        index = pd.DatetimeIndex(start='20160101 00:51:15', freq='h', periods=80)
        df = pd.DataFrame(index=index, data={'A':np.arange(0, 80, 1), 'B':np.zeros(80)})

        anls = analysis.DailyAgg(df, agg='min', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55))
        result1 = anls.result.copy()
        anls.do_analysis(agg='max', starttime=dt.time(hour=3, minute=34), endtime=dt.time(hour=22, minute=55))
        result2 = anls.result.copy()
        self.assertFalse((result1==result2).all().all())



if __name__ == '__main__':
    
    unittest.main()