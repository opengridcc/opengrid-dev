# -*- coding: utf-8 -*-
"""
opengrid

The config module provides support for handling configuration
such as the location to store files, etc.

The configuration is composed from different sources in a
hierarchical fashion:
    * The defaults hard-coded in this file.
    * If it exists: the opengrid.cfg file in the directory
      of this module
    * If it exists: the opengrid.cfg file in the 'current'
      directory
    * If provided: the file given to the constructor
The lower a source is in the list, to more it has precedence.

Not all files must contain all configuration properties. A
configuration file can also overwrite only a subset of the
configuration properties.
"""
import os, sys

#configparser changed name in Python3
if sys.version_info[0] == 3:
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

import inspect


class Config(SafeConfigParser):
    """
    The config class implements the ConfigParser interface.
    More specifically, it inherits from SafeConfigParser.

    See the documentation of SafeConfigParser for the available
    methods.
    """

    def __init__(self, configfile=None):
        SafeConfigParser.__init__(self)
        self.__add_defaults()
        configfiles = []
        # Add the filename for the config file in the modules
        # directory
        self.opengrid_libdir = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))
        configfiles.append(os.path.join(self.opengrid_libdir, 'opengrid.cfg'))
        # Add the filename for the config file in the 'current' directory
        configfiles.append('opengrid.cfg')
        # Add the filename for the config file passed in
        if configfile:
            configfiles.append(configfile)
        self.read(configfiles)

    def __add_defaults(self):
        self.add_section('opengrid_server')
        self.set('opengrid_server', 'host', '95.85.34.168')
        self.set('opengrid_server', 'port', '8080')
        self.set('opengrid_server', 'user', 'opengrid')
        self.set('opengrid_server', 'password', 'CHANGE ME IN AN OPENGRID.CFG FILE')

        self.add_section('data')
        self.set('data', 'folder', os.path.expanduser("~/.opengrid/data"))

        self.add_section('houseprint')
        self.set('houseprint', 'password', 'CHANGE ME IN AN OPENGRID.CFG FILE')

        self.add_section('env')
        self.set('env', 'type', 'dev')
        self.set('env', 'plots', 'inline')






