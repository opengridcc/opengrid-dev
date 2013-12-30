# -*- coding: utf-8 -*-
"""
opengrid

The houseprint class defines an interface to the houseprint we collect for 
each opengrid participant.


Created on Mon Dec 30 00:51:49 2013 by saroele

"""

import os, sys
import gspread
import inspect

class Houseprint(object):
    """
    Interface to the houseprints of all opengrid participants.
    
    The houseprints are currently saved in a google drive spreadsheet.  This
    may change later.    
    
    """
    
    def __init__(self):
        """Create a connection with the google drive spreadsheet"""
        
        # Get the path of this current file 
        self.sourcedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        
        pwdfile = file(os.path.join(self.sourcedir, 'og.txt'))
        pwd = pwdfile.read().rstrip()
        
        # open spreadsheet, store main sheet in self.sheet
        gc = gspread.login('opengridcc@gmail.com', pwd)
        self.sheet = gc.open("Opengrid houseprint (Responses)").sheet1
                
        print "Opengrid houseprint (Responses) successfully opened"
        
    
    
        
    
if __name__ == '__main__':
    
    hp = Houseprint()