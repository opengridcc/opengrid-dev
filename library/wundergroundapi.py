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


#Script to obtain CURRENT weather detail readings
def fetch_curr_conditions(apikey, city, prop='temp_c'):
    '''
    Generic function for getting current weather conditions in a specified city.
        
    Parameters
    ----------
    * apikey : String
        Wunderground API key (should be obtained after subscription)
    * city : String
        location of weather station
    * prop : String
        Type of weather property to look up.  
    
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

def Details_Temp_Xdaysago(key,city,x_days_ago = 5,prop = "temp_c",PDcolumnname ='T_out'):
#get more subhourly details for a single day, eg. day 5
    x_days_ago_date =  datetime.datetime.today()- datetime.timedelta(days=x_days_ago)   
    Temp_values = Fetch_historic_temp_ByDate(key,city,x_days_ago_date,prop,PDcolumnname)
    return Temp_values


#some scripts for HISTORIC data fetching

def Fetch_historic_tempYMD(key,city,year,month,day, prop = 'tempm',PDcolumnname= 'T_out' ):
    # example URL: http://api.wunderground.com/api/<key>/history_20140808/q/EU/Leuven.json
    # get temp df using year month day.
    
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
    Tout_h = pd.DataFrame(temp_c_list,columns = [PDcolumnname],index = time_list)
    return Tout_h
    f.close()
    
def Fetch_historic_temp_ByDate(key,city,date_object, prop = 'tempm',PDcolumnname= 'T_out' ):
#same as above, but with dateobject as input. hour / min are ignored
    year = date_object.year
    month = date_object.month
    day = date_object.day
    Tout_h = Fetch_historic_tempYMD(key,city,year,month,day, prop ,PDcolumnname)
    return Tout_h

#scripts for Historic day-AVERAGE weather fetching

def Fetch_historic_dayaverage(key,city,year,month,day,prop = "meantempm",PDcolumnname ='T_out'):
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
    Tout_h = pd.DataFrame([temp_c_list],columns = [PDcolumnname], index=time_list)
    #
    
    #Tout_h_T.set_index(time_list)
    f.close()
    return Tout_h
    
    
def Fetch_historic_dayaverage_By_date(key,city,date_object,prop = 'meantempm',PDcolumnname ='T_out'):
#same as above, but with dateobject as input. hour / min are ignored
    year = date_object.year
    month = date_object.month
    day = date_object.day
    Tout_h = Fetch_historic_dayaverage(key,city,year,month,day,prop,PDcolumnname);
    return Tout_h

def Average_Temp_Xdaysago(key,city,x_days_ago = 5,prop = 'meantempm',PDcolumnname ='T_out'):
#get more subhourly details for a single day, eg. day 5
    x_days_ago_date =  datetime.datetime.today()- datetime.timedelta(days=x_days_ago)   
    Temp_values = Fetch_historic_dayaverage_By_date(key,city,x_days_ago_date,prop,PDcolumnname)
    return Temp_values


	
