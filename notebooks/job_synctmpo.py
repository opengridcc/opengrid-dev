# -*- coding: utf-8 -*-
"""
Synchronize the opengrid data to your computer.

Created on 16/12/2014 by Roel De Coninck
"""

import os, sys
import inspect


#script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
#sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))

#sys.path.append('/usr/local/src/tmpo-py')
#import tmpo

from opengrid.library import houseprint

hp = houseprint.Houseprint()
hp.sync_tmpos()
print hp._tmpos.db
