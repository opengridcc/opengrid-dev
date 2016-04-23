# -*- coding: utf-8 -*-
"""
Script to cache anonymous houseprint data into hp_anonymous.pkl

Created on 05/07/2014 by Roel De Coninck
"""

from opengrid.library.houseprint import houseprint

##############################################################################

hp = houseprint.Houseprint()
print('Sensor data fetched')

hp.save('hp_anonymous.pkl')
print('Houseprint saved to hp_anonymous.pkl')
