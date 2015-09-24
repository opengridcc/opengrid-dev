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

test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(test_dir, os.pardir, os.pardir))
from opengrid.library import config
c = config.Config()
sys.path.append(c.get('tmpo', 'folder'))
from opengrid.library.houseprint import houseprint

try:
    if os.path.exists(c.get('tmpo', 'data')):
        path_to_tmpo_data = c.get('tmpo', 'data')
except:
    path_to_tmpo_data = None

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
        
        cls.hp = houseprint.Houseprint(gjson=c.get('houseprint','json'), 
                                       spreadsheet="unit and integration test houseprint")
        
    @classmethod    
    def tearDownClass(cls):
        
        pass
    
    
    def test_parsing_sites(self):
        """Test parsing the sites"""
        
        # check the site keys
        sitekeys = [x.key for x in self.hp.sites]
        self.assertListEqual(sitekeys, range(1,8))
        
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
        
#==============================================================================
#     def test_saving_with_tmpo(self):
#         """Saving a houseprint should keep the tmpo session alive"""
#         
#         self.hp.init_tmpo(path_to_tmpo_data=path_to_tmpo_data)
#         
#         self.assertIsNotNone(self.hp.get_tmpos())
#         self.hp.save('test_saved_hp.hp')
#         self.assertIsNotNone(self.hp.get_tmpos())
#==============================================================================
        
    def test_get_sensors_by_type(self):
        """Searching for sensors by type should return only concerned sensors"""

        watersensors = self.hp.get_sensors(sensortype='water')
        self.assertEqual([x.key for x in watersensors], ['s6', 's12', 's13'])        
    

#==============================================================================
#     def test_anonymize(self):
#         """Test if the hp is truly anonymous after anyonimizing"""
#         
#         ### ATTENTION ###
#         # This test will remove e-mail addresses from the self.hp object.
#         # If other tests require this information, put them BEFORE this one
#         # as the tests are executed in order of appearance
#         #################
#         
#         self.hp.anonymize()
#         # test if there is still an e-mail address somewhere
#         email = False
#         for i in self.hp.cellvalues:
#             for j in i:
#                 try:
#                     email = j.find(u'@') > 0
#                 except:
#                     pass
#                 if email:
#                     self.assertFalse(email, msg=u"'@' found in cell {}".format(j))
#         for attr in ['gc', 'sheet', 'sourcedir']:
#             self.assertFalse(hasattr(self.hp, attr), msg="hp should NOT have attribute {}".format(attr))
#==============================================================================
            
    def test_save_and_load(self):
        """Save a HP and load it back"""
        
        self.hp.init_tmpo(path_to_tmpo_data=path_to_tmpo_data)
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
    ln = lambda f: getattr(HouseprintTest, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    unittest.TestLoader.sortTestMethodsUsing = lncmp
        
    #unittest.main()

    suite1 = unittest.TestLoader().loadTestsFromTestCase(HouseprintTest)
    alltests = unittest.TestSuite([suite1])
    
    #selection = unittest.TestSuite()
    #selection.addTest(HouseprintTest('test_get_sensor'))
        
    unittest.TextTestRunner(verbosity=1, failfast=False).run(alltests)
