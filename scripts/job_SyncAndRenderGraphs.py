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
from opengrid.library.houseprint import Houseprint
from opengrid.library import config
c = config.Config()


# Sync houseprint ###################################################################

hp = Houseprint()
all_sensordata = hp.get_all_fluksosensors()
print('Sensor data fetched')

hp.save('/usr/local/src/opengrid/scripts/hp_anonymous.pkl')
hp.save('/var/www/private/hp_anonymous.pkl')

# Sync Tmpo ########################################################################

sys.path.append(c.get('tmpo', 'folder'))
from opengrid.library import fluksoapi
import tmpo

tmpos = tmpo.Session()
tmpos.debug = True

tmpos = fluksoapi.update_tmpo(tmposession = tmpos, hp=hp)
tmpos.sync()
