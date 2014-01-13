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
from opengrid.library.houseprint import Houseprint

class HouseprintTest(unittest.TestCase):
    """
    Class for testing the class Houseprint
    """

    @classmethod    
    def setUpClass(cls):
        """
        Make the connection to the google drive spreadsheet only once.
        All tests can use self.hp as the houseprint object
        """
        
        cls.hp = Houseprint(houseprint = "test Opengrid houseprint (Responses)")
        
    @classmethod    
    def tearDownClass(cls):
        
        pass
    

    def test_get_sensor(self):
        """Test getting an individual sensor"""
        
        expected = {'Sensor':'53b1eb0479c83dee927fff10b0cb0fe6',
                    'Token': '8bf357390aa2c340075d9cf51e0c78e8',
                    'Type': 'electricity',
                    'Function': 'Main'}        
        
        s4=self.hp.get_sensor(4,2)
        self.assertDictEqual(s4, expected)
        

    def test_get_all_sensors(self):
        """Test getting all sensors for a given row"""
        
        allsensors = self.hp.get_all_sensors(7)
        
        self.assertListEqual(sorted(allsensors.keys()), range(1,7))
        self.assertIsNone(allsensors[5])


    def test_identify_fluksos(self):
        """Test the identify_flukso's method"""
        
        expected = {'FL03001552':4, 'FL03001561':5, 'FL02000449':6, 'FL03001566':7}        
        
        self.assertDictEqual(self.hp.flukso_ids, expected)


    def test_get_all_fluksosensors(self):
        """Getting all sensorinfo from all flukso's"""

        keys = sorted(['FL03001552', 'FL03001561', 'FL02000449', 'FL03001566'])  
        
        fl = self.hp.get_all_fluksosensors()
        self.assertListEqual(sorted(fl.keys()), keys)
        fl.pop('FL03001552')
        self.assertListEqual(sorted(self.hp.fluksosensors.keys()), keys)
        
        
    def test_get_sensors_by_type(self):
        """Get all sensors by type (gas, water electricity)"""
        
        expected = sorted(['a6028457292f1866b468b63adcc82ee3', '29ba25498c657eda0cdd34bf22d3f9e4',
                    '313b78fec4f845be91c328ee2f92c6d4', '051a928dd04ca55e0411bd6f07e05c04',
                    'd4b28740c7ee7a98f94a4d23d794af79'])
                    
        sensors = sorted(self.hp.get_sensors_by_type('gas'))
        self.assertListEqual(expected, sensors)
        
        
    def test_get_flukso_from_sensor(self):
        """get_flukso_from_sensor should return correct flukso or ValueError"""
        
        expected = 'FL03001552'
        fl = self.hp.get_flukso_from_sensor('53b1eb0479c83dee927fff10b0cb0fe6') 
        self.assertEqual(expected, fl)
        
        self.assertRaises(ValueError, self.hp.get_flukso_from_sensor, sensor = 'nonexistentsensor')        

if __name__ == '__main__':
    
    # http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python    
    ln = lambda f: getattr(HouseprintTest, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    unittest.TestLoader.sortTestMethodsUsing = lncmp
        
    #unittest.main()

    suite1 = unittest.TestLoader().loadTestsFromTestCase(HouseprintTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
