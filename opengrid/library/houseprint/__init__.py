__author__ = 'Jan Pecinovsky'

import sys
if sys.version_info.major == 3:
	from .houseprint import *
else:
    from houseprint import *