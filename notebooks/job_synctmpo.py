# -*- coding: utf-8 -*-
"""
Synchronize the opengrid data to your computer.

Created on 16/12/2014 by Roel De Coninck
"""

import os, sys
import inspect


script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))

sys.path.append('/usr/local/src/tmpo-py')
import tmpo

from opengrid.library.houseprint import houseprint

try:
    if os.path.exists(c.get('tmpo', 'data')):
        path_to_tmpo_data = c.get('tmpo', 'data')
except:
    path_to_tmpo_data = None

tmpos = tmpo.Session()
tmpos.debug = True
hp = houseprint.load_houseprint_from_file('new_houseprint.pkl')
hp.init_tmpo(tmpos)
hp.sync_tmpo()
