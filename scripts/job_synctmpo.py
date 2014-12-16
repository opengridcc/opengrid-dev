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

from opengrid.library import fluksoapi
from opengrid.library import houseprint
sys.path.append('/usr/local/src/tmpo-py')
import tmpo

tmpos = tmpo.Session()
tmpos.debug = True
hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')


tmpos = fluksoapi.update_tmpo(tmposession = tmpos, hp=hp)
tmpos.sync()
