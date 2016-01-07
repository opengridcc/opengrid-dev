# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 10:31:00 2016

@author: roel
"""

import pandas as pd

def parse_date(d):
    """
    Return a pandas.Timestamp if possible.  
    
    Parameters
    ----------
    d : Datetime, float, int, string or pandas Timestamp
        Anything that can be parsed into a pandas.Timestamp
        
    Returns
    -------
    pts : pandas.Timestamp
    
    Raises
    ------
    ValueError if it was not possible to create a pandas.Timestamp
    """
    
    if isinstance(d, float) or isinstance(d, int):
        # we have a POSIX timestamp IN SECONDS.
        pts = pd.Timestamp(d, unit='s')
        return pts
        
    try:
        pts = pd.Timestamp(d)
    except:
        raise ValueError("{} cannot be parsed into a pandas.Timestamp".format(d))
    else:
        return pts