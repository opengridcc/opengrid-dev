# -*- coding: utf-8 -*-
"""
This test is a combination of unit and integration test. 
It makes a connection with google spreadsheets to get a dummy test version of the
houseprint sheet. The sheet is called "unit and integration test houseprint"

Open that sheet to check some of the tests.

Created on Mon Dec 30 02:37:25 2013

@author: roel
"""

import os, sys
import unittest
import inspect

from opengrid.library.houseprint import houseprint

class HouseprintTest(unittest.TestCase):
    """
    Class for testing the class Houseprint
    """

    @classmethod    
    def setUpClass(cls):
        """
        Make the connection to the google drive spreadsheet only once.
        This makes the test rather an integration than a unitttest.
        
        All tests can use self.hp as the houseprint object
        """
        
        here = os.path.abspath(os.path.dirname(__file__))
        cls.hp = houseprint.load_houseprint_from_file(os.path.join(here, 'test_saved_hp.hp')
        
    @classmethod    
    def tearDownClass(cls):
        
        pass
    
    
    def test_parsing_sites(self):
        """Test parsing the sites"""
        
        # check the site keys
        sitekeys = [x.key for x in self.hp.sites]
        self.assertListEqual(sitekeys, list(range(1,8)))
        
        # some random attribute tests
        self.assertEqual(self.hp.sites[6].size, 180)
        self.assertEqual(self.hp.sites[5].inhabitants, 5)
        self.assertEqual(self.hp.sites[4].postcode, 5000)
        self.assertEqual(self.hp.sites[3].construction_year, 1950)
        self.assertEqual(self.hp.sites[2].epc_cert, 102.27)
        self.assertEqual(self.hp.sites[1].k_level, "")
        
        
    def test_parsing_devices(self):
        """Test parsing devices"""
        
        devicekeys = ["FL03001001","FL03001002","FL03001003a","FL03001003b","FL03001004","FL03001005","FL03001006","FL03001007"]
        self.assertEqual([x.key for x in self.hp.get_devices()], devicekeys)
        self.assertEqual(self.hp.get_devices()[1].site.key, 2)
        
    def test_parsing_sensors(self):
        """Test parsing of sensors"""
        
        sensorkeys = ['s'+ str(x) for x in range(1,21)]
        self.assertListEqual([x.key for x in self.hp.get_sensors()], sensorkeys)
        
        # test a specific sensor
        s12 = self.hp.get_sensors()[11]
        self.assertEqual(s12.key, 's12')
        self.assertEqual(s12.token, 't12')
        self.assertEqual(s12.device.key, 'FL03001002')
        self.assertEqual(s12.type, 'water')
        self.assertEqual(s12.description, 'Water house')
        
    def test_get_sensors_by_type(self):
        """Searching for sensors by type should return only concerned sensors"""

        watersensors = self.hp.get_sensors(sensortype='water')
        self.assertEqual([x.key for x in watersensors], ['s6', 's12', 's13'])        
    
    def test_search_sites(self):
        """Searching sites based on site attributes"""
        
        self.assertEqual(4, self.hp.search_sites(key=4)[0].key)
        sites_with_3_inhabitants = self.hp.search_sites(inhabitants=3)
        self.assertEqual([3,4], [x.key for x in sites_with_3_inhabitants])

    def test_search_sensors(self):
        """Searching sensors based on sensor attributes"""
        
        sensors = self.hp.search_sensors(system='grid')
        self.assertEqual(['s1', 's2'], [x.key for x in sensors])
        
        sensors = self.hp.search_sensors(type='electricity', direction='Import')
        self.assertEqual(['s2'], [x.key for x in sensors])


    def test_save_and_load(self):
        """Save a HP and load it back"""
        
        self.hp.init_tmpo()
        self.hp.save('test_saved_hp.hp')
        hp2 = houseprint.load_houseprint_from_file('test_saved_hp.hp')
        
        # Just comparing the old and new hp does not work: the sensors have the
        # same attributes, but are different objects (different location in memory)
        # As a solution, we check some of their attributes
        s1_old = self.hp.get_sensors()[0]
        s1_new = hp2.get_sensors()[0]

        self.assertEqual(s1_old.site.key, s1_new.site.key)        
        for x in ["key", "type", "description", "system", "quantity", "unit", "direction", "tariff"]:
            self.assertEqual(s1_old.__dict__[x], s1_new.__dict__[x])
            
        self.assertIsNotNone(self.hp.get_tmpos())
        self.hp.save('test_saved_hp.hp')
        self.assertIsNotNone(self.hp.get_tmpos())
                
        
if __name__ == '__main__':
    
    # http://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python
    if sys.version_info.major == 3: #compatibility python 3
        ln = lambda f: getattr(HouseprintTest, f).__code__.co_firstlineno #functions have renamed attributes
        lncmp = lambda _, a, b: (ln(a) > ln(b)) - (ln(a) < ln(b)) #cmp() was deprecated, see https://docs.python.org/3.0/whatsnew/3.0.html
    else:
        ln = lambda f: getattr(HouseprintTest, f).im_func.func_code.co_firstlineno
        lncmp = lambda _, a, b: cmp(ln(a), ln(b))

    unittest.TestLoader.sortTestMethodsUsing = lncmp
        
    #unittest.main()

    suite1 = unittest.TestLoader().loadTestsFromTestCase(HouseprintTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
