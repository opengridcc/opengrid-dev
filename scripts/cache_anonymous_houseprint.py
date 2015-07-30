# -*- coding: utf-8 -*-
"""
Script to cache anonymous houseprint data into hp_anonymous.pkl

Created on 05/07/2014 by Roel De Coninck
"""

import os, sys
import inspect


script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))
from opengrid.library import config
from opengrid.library.houseprint import houseprint

##############################################################################

c = config.Config()
gjson = c.get('houseprint','json')

hp = houseprint.Houseprint(gjson)
print('Sensor data fetched')

hp.save('new_houseprint.pkl')
 
