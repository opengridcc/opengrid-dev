# -*- coding: utf-8 -*-
import sys
if sys.version_info.major == 3:
	from .config import Config
else:
    from config import Config