# -*- coding: utf-8 -*-
"""
Synchronize the opengrid data to your computer.

Created on 16/12/2014 by Roel De Coninck
"""

from opengrid.library import houseprint

hp = houseprint.Houseprint()
hp.sync_tmpos()
