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
import numpy as np
import pandas as pd
import datetime as dt
import pytz

from opengrid_dev.library import analysis
from opengrid_dev.library.exceptions import EmptyDataFrameError

class AnalysisTest(unittest.TestCase):
    
    def test_standby(self):

        from opengrid_dev import datasets
        df = datasets.get('elec_power_min_1sensor')
        res = analysis.standby(df, 'D')
        self.assertEqual(res.index.tz.zone, 'Europe/Brussels')

        self.assertRaises(EmptyDataFrameError, analysis.standby, pd.DataFrame)



if __name__ == '__main__':
    
    unittest.main()