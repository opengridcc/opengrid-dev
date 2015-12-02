# -*- coding: utf-8 -*-
"""
<author>
<Date>

Functions to fetch (historic, current or prognosed) weather data from wunderground weather stations.
Required: API key, to be added to opengrid.cfg.

"""

# import libraries specific to wunderground script
import datetime
import pytz
import pandas as pd
import pdb


import urllib2 
import json 
from pprint import pprint
import time


class Wunderground(object):
    """
    Class to manage api calls to fetch current and historic weather data from
    Wunderground weather stations
    
    This class avoids calling the api again for getting the current conditions
    if they have been obtained within time_delay_min. This is handled by the
    following attributes:
    
    * timestamp_current: timestamp when last call to fetch current conditions
      was succesfully launched
    * json_current : json object returned with the last call
    * time_delay : if timestamp_current is within this time_delay from the
      actual time, use the existing json_current.  Else, call Wunderground to 
      update json_current, and update timestamp_current accordingly.
    """

    def __init__(self, apikey, city, time_delay=20*60):
        """
        Parameters
        ----------
        * apikey : String
            Wunderground API key (can be obtained after subscription)
        * city : String
            Location of weather station
        * time_delay: float
            Time delay in seconds for calling api since last call for current conditions
        """
        
        self.apikey = apikey
        self.city = city
        self.time_delay = time_delay
        
        self.json_current = None
        self.timestamp_current = 0
        
    def reset(self):
        """
        Reset json_current and timestam_current
        """
        
        self.json_current = None
        self.timestamp_current = 0
        
    
    def _fetch_current(self):
        """
        Call Wunderground to get current conditions and overwrite
        json_current and timestamp_current
        """
        URL = ''.join(['http://api.wunderground.com/api/',self.apikey,'/geolookup/conditions/q/EU/',self.city,'.json'])
        f = urllib2.urlopen(URL) 
        json_string = f.read() 
        self.json_current = json.loads(json_string)
        self.timestamp_current = time.time()
        
        print("Obtained current conditions and saved json in self.json_current")
        
    def fetch_current(self):
        """
        Call Wunderground to get current conditions IF NEEDED based on current
        time, self.timestamp_current and self.time_delay.  
        If Wunderground is to be called, overwrite json_current and timestamp_current
        """        
        
        if time.time() < (self.timestamp_current + self.time_delay):
            print("No need to call Wunderground, using cached current conditions.")
        else:
            self._fetch_current()
            
    
    def show_properties(self):
        """
        Print all properties that can be obtained from the current conditions
        todo!!
        """
        
        try:
            print("These are the known current properties:\n")
            for prop in self.json_current['current_observation'].keys():
                print(prop)
        except:
            print("Problem reading self.json_current")
            

    def get_current(self, prop):
        """
        Extract current value for prop from self.json_current. 
        Fetch current conditions from Wunderground if needed, depending on 
        current time, self.timestamp_current and self.time_delay. 
        
        Parameters
        ----------
        * prop : String
            Type of weather property to look up.
            
        Returns
        -------
        value, timestamp : value and associated timestamp
        
        Note
        ----
        If prop cannot be found, print all possible properties and raise a 
        ValueError
        """
            
        self.fetch_current()
                
        try:
            curr_value = float(self.json_current['current_observation'][prop] )
        except:
            print("Property not found.")            
            self.show_properties()
            raise ValueError('Property {} not found.  See show_properties() to get a list with all possibilities'.format(prop))
        
    
        return curr_value, self.timestamp_current
        

#Script to obtain CURRENT weather detail readings
def fetch_curr_conditions(apikey, city, prop='temp_c'):
    '''
    Generic function for getting current weather conditions in a specified city.
        
    Parameters
    ----------
    * apikey : String
        Wunderground API key (can be obtained after subscription)
    * city : String
        location of weather station
    * prop : String
        Type of weather property to look up.  
        
    Returns
    -------
    
    
    Author: Ryton & comments from Saroele

    Output:  double return with value, date/time. If an error occurs, the json response will be printed.
    '''
    #
    
    URL = ''.join(['http://api.wunderground.com/api/',apikey,'/geolookup/conditions/q/EU/',city,'.json'])
    f = urllib2.urlopen(URL) 
    json_string = f.read() 
    parsed_json = json.loads(json_string) 
    #pprint(parsed_json)
    
    try:
        location = parsed_json['location']['city'] 
        curr_value = float(parsed_json['current_observation'][prop] )
        currdate = datetime.date.today()
    except:
        pprint(parsed_json)
        raise
    
    f.close()

    return curr_value, currdate

def details_xdaysago(key,city,x_days_ago = 5,prop = "temp_c",columnname ='T_out'):
    """
    Get more subhourly details for a single day, x days ago
    
    todo: complete docstring
    """
    x_days_ago_date =  datetime.datetime.today()- datetime.timedelta(days=x_days_ago)   
    temp_values = fetch_historic_temp_bydate(key,city,x_days_ago_date,prop,columnname)
    return temp_values


#some scripts for HISTORIC data fetching

def fetch_historic_tempYMD(key,city,year,month,day, prop = 'tempm',columnname= 'T_out' ):
    """
    Get temp df using year month day.

    
    Example URL: http://api.wunderground.com/api/<key>/history_20140808/q/EU/Leuven.json
    
    todo: complete docstring    
    """    
    d = datetime.datetime(year,month,day,0,0)
    datestr = '{:%Y%m%d}'.format(d)
    
    URL = ''.join(['http://api.wunderground.com/api/',key,'/history_',datestr,'/q/BE/',city,'.json'])
    f = urllib2.urlopen(URL) 
    json_string = f.read() 
    parsed_json = json.loads(json_string) 
    #print json_string
    #pprint(parsed_json["history"]['dailysummary'])
    hr = "hour"
    minu = "min"
    time_list=[]
    temp_c_list= []

    for  entry in parsed_json["history"]["observations"]:
        #pprint(entry)
        hour_value = entry["date"][hr]
        min_value = entry["date"][minu]
        temp_c = entry[prop]
        temp_c_list.append(float(temp_c))
        concattime = datetime.datetime(year,month, day,int(hour_value),int(min_value))
        time_list.append(concattime)
        
        
        #print concattime, temp_c
    # print shape(temp_c_list), shape(time_list)
    Tout_h = pd.DataFrame(temp_c_list,columns = [columnname],index = time_list)
    return Tout_h
    f.close()
    
def fetch_historic_temp_bydate(key,city,date_object, prop = 'tempm',columnname= 'T_out' ):
#same as above, but with dateobject as input. hour / min are ignored
    year = date_object.year
    month = date_object.month
    day = date_object.day
    Tout_h = fetch_historic_tempYMD(key,city,year,month,day, prop ,columnname)
    return Tout_h

#scripts for Historic day-AVERAGE weather fetching

def fetch_historic_dayaverage(key,city,year,month,day,prop = "meantempm",columnname ='T_out'):
    # example URL: http://api.wunderground.com/api/<key>/history_20140808/q/EU/Leuven.json
    # get temp df using year month day.
    #city = 'Geel'   
    d = datetime.datetime(year,month,day,0,0)
    datestr = '{:%Y%m%d}'.format(d)
    
    URL = ''.join(['http://api.wunderground.com/api/',key,'/history_',datestr,'/q/BE/',city,'.json'])
    f = urllib2.urlopen(URL) 
    json_string = f.read() 
    parsed_json = json.loads(json_string) 
    
    #print json_string
    #pprint(parsed_json["history"]['dailysummary'])
    hr = "hour"
    minu = "min"
    
    time_list=[]
    temp_c_list= []
    
    for  entry in parsed_json["history"]['dailysummary']:
        #"pprint(entry)
        hour_value = entry["date"][hr]
        min_value = entry["date"][minu]
        temp_c = entry[prop]
        temp_c_list.append(temp_c)
        concattime = datetime.datetime(year,month, day,int(hour_value),int(min_value))
        time_list.append(concattime)
        #print concattime, temp_c
    #Tout_h = pd.DataFrame([temp_c_list],columns = ['T_out'],index = time_list)
    #parse_dates=['Date'], dayfirst=True, index_col='Date'
    Tout_h = pd.DataFrame([temp_c_list],columns = [columnname], index=time_list)
    #
    
    #Tout_h_T.set_index(time_list)
    f.close()
    return Tout_h
    
    
def fetch_historic_dayaverage_by_date(key,city,date_object,prop = 'meantempm',columnname ='T_out'):
#same as above, but with dateobject as input. hour / min are ignored
    year = date_object.year
    month = date_object.month
    day = date_object.day
    Tout_h = fetch_historic_dayaverage(key,city,year,month,day,prop,columnname);
    return Tout_h

def average_temp_xdaysago(key,city,x_days_ago = 5,prop = 'meantempm',columnname ='T_out'):
#get more subhourly details for a single day, eg. day 5
    x_days_ago_date =  datetime.datetime.today()- datetime.timedelta(days=x_days_ago)   
    temp_values = fetch_historic_dayaverage_by_date(key,city,x_days_ago_date,prop,columnname)
    return temp_values


	
