# -*- coding: utf-8 -*-
"""
Script to cache anonymous houseprint data into hp_anonymous.pkl

Created on 05/07/2014 by Roel De Coninck
"""
import os

from opengrid.library.houseprint import houseprint
from opengrid import config
c = config.Config()


##############################################################################

hp = houseprint.Houseprint()
print('Sensor data fetched')

filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
hp.save(filename)
