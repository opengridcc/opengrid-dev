# -*- coding: utf-8 -*-
"""
Synchronize the opengrid data to your computer.

Created on 16/12/2014 by Roel De Coninck
"""

import os

from opengrid.library import houseprint
from opengrid import config

c = config.Config()

# Load houseprint from cache if possible, otherwise build it from source
try:
    hp_filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
    hp = houseprint.load_houseprint_from_file(hp_filename)
    print("Houseprint loaded from {}".format(hp_filename))
except Exception as e:
    print(e)
    print("Because of this error we try to build the houseprint from source")
    hp = houseprint.Houseprint()

hp.init_tmpo()
hp.sync_tmpos()
