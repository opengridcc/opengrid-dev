# -*- coding: utf-8 -*-
"""
Synchronize the opengrid data to your computer & cache the houseprint

Created on 16/12/2014 by Roel De Coninck
"""

import os
from opengrid.library import houseprint
from opengrid import config

c = config.Config()

hp = houseprint.Houseprint()
print('Sensor data fetched')

filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
hp.save(filename)

hp.init_tmpo()
hp.sync_tmpos()
