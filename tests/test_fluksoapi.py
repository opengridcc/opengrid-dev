# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 02:37:25 2013

@author: roel
"""

import os, sys
import unittest
import inspect

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(test_dir, os.pardir, os.pardir))
from opengrid.library import fluksoapi

class FluksoapiTest(unittest.TestCase):
    """
    Class for testing the module fluksoapi
    """

    def test_something(self):
        self.assertTrue(True)
        

if __name__ == '__main__':
    
    # http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python    
#    ln = lambda f: getattr(HouseprintTest, f).im_func.func_code.co_firstlineno
#    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
#    unittest.TestLoader.sortTestMethodsUsing = lncmp
#        
    unittest.main()
#
#    suite1 = unittest.TestLoader().loadTestsFromTestCase(HouseprintTest)
#    alltests = unittest.TestSuite([suite1])
#    
#    #selection = unittest.TestSuite()
#    #selection.addTest(HouseprintTest('test_get_sensor'))
#        
#    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
