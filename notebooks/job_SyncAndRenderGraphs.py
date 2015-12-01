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
c = config.Config()

sys.path.append(c.get('tmpo', 'folder'))
import tmpo
from opengrid.library.houseprint import houseprint

try:
    if os.path.exists(c.get('tmpo', 'data')):
        path_to_tmpo_data = c.get('tmpo', 'data')
except:
    path_to_tmpo_data = None

# Sync houseprint ###################################################################

gjson = c.get('houseprint','json')
hp = houseprint.Houseprint(gjson)
print('Sensor data fetched')

hp.save('/usr/local/src/opengrid/scripts/hp_anonymous.pkl')
hp.save('/var/www/private/hp_anonymous.pkl')

# Sync Tmpo ########################################################################

tmpos = tmpo.Session(path_to_tmpo_data=path_to_tmpo_data)
tmpos.debug = True
hp.init_tmpo(tmpos)
hp.sync_tmpo()
