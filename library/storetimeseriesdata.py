# -*- coding: utf-8 -*-
"""
Created by Filip Jorissen

This function stores sensor measurement data. For each sensor two files are created. 
Sensor.meta contains metadata about the measurements. Sensor.txt contains only the 
measurements: no timestamps. The location of the measurement in the file indicates 
the time at which it was measured. If there exists already stored data for the sensor, data 
is appended and/or overwritten.

TODO: new documentation
"""
import os, json, struct,io, sys


class TimeSeriesData(object):
    """
    """
    
    def __init__(self, sensor, token, unit):
        self.sensor=sensor
        self.token=token
        self.unit=unit
    
        self.resultpath="results-float"
        self.backuppath="backups"
        self.metapath=os.path.join(self.resultpath, sensor + ".meta")
        self.datapath=os.path.join(self.resultpath, sensor + ".float")
        self.dataformat = 'f'  #Format of the stored data: float

        #create results folder if it does not exist
        if not os.path.exists(self.resultpath):
            os.makedirs(self.resultpath)
        if not os.path.exists(self.backuppath):
            os.makedirs(self.backuppath)
	
        if os.path.exists(self.metapath):
            # load existing meta file
            with open(self.metapath, 'rb') as fp:
    		    self.metadata = json.load(fp)
            # set write mode to read and overwrite
            self.mode = 'r+b'

        else:
            #create new meta file
            self.metadata=dict()
            self.metadata['sensor']=sensor
            self.metadata['token']=token
            self.metadata['unit']=unit
            self.metadata['resolution']='minute' #need to edit factors '60' below when this is changed!
            self.metadata['edittimes']=[]
            self.metadata['dataformat']=self.dataformat
            self.metadata['datalength']=struct.calcsize(self.dataformat)
            # set write mode to write
            self.mode='wb'
            
        oldpath=os.path.join('results', sensor + ".meta")    
        backuppath=os.path.join(self.backuppath, sensor + ".txt")
        if os.path.exists(oldpath):
            with open(oldpath, 'rb') as fp:
    		    oldmetadata = json.load(fp)
            self.metadata=oldmetadata
            self.metadata['dataformat']=self.dataformat
            self.metadata['datalength']=struct.calcsize(self.dataformat)
                
            with open(oldpath.replace('meta','txt'), 'rb') as fp:
                olddata=fp.read()
            stringdata=olddata.replace('000???', 'nan')
            stringdata=stringdata.replace('000nan', 'nan')
            stringdata=stringdata.split(oldmetadata['separator'])
            floatdata=stringdata[0:-1]
            storeData(floatdata,self.datapath,self.metadata['dataformat'])
            self.storeMetaData()
            
            with open(backuppath,'wb') as fp:
                fp.write(olddata)
            os.rename(oldpath, backuppath)
            os.rename(oldpath.replace('meta','txt'), backuppath.replace('meta','txt'))
            
                
    
    def storeTimeSeriesData(self, newdata):
        timestamp=newdata[0][0]
        newdata=nestedListToList(newdata,1)
        
        #append the unix timestamp to indicate which values were overwritten/added
        if not 'starttime' in self.metadata.keys():
            self.metadata['starttime']=timestamp
        self.metadata['edittimes'].append(timestamp)
        
        # do some data consistency checks
        self.validateData(newdata, timestamp)

    	# insert new data at the correct point in the file
        entrylength=self.metadata['datalength']
        offset=(timestamp-self.metadata['starttime'])/60*entrylength
        storeData(newdata, self.datapath, self.metadata['dataformat'], offset)
    
        self.storeMetaData()
        
    def validateData(self, newdata, timestamp):
        #raise an exception when data measurements happened before the currently first measurement of the file
        if timestamp<self.metadata['starttime']:
            raise ValueError('The added data cannot be appended before the start of the file')
        #check for inconsistencies
        if self.metadata['sensor'] != self.sensor or self.metadata['token'] != self.token or self.metadata['unit'] != self.unit:
            raise ValueError('Argument is inconsistent with its stored value')
        if (timestamp- self.metadata['starttime']) % 60 != 0:
            print "Timestamp does not have the correct spacing compared to the initial timestamp! Storage cancelled."
            return
    
    def storeMetaData(self):
        # save (updated) meta data file
        with open(self.metapath, 'wb') as fp:
            json.dump(self.metadata, fp)

def convertDataFormat(fromPath, toPath, toFormat):
    data=fetchDataFromFile(fromPath)
    storeData(data, toPath, toFormat)

def nestedListToList(nestedList, index):
    newlist=[]
    for row in nestedList:
        newlist.append(row[index])
    return newlist

def fetchDataFromFile(filepath):
    if os.path.exists(filepath):
        with open(filepath.replace('.float','.meta'), 'rb') as fp:
		    metadata = json.load(fp)
        with open(filepath, 'rb') as fp:
            stringdata=fp.read()
            stringformat=str(metadata['dataformat'])*(len(stringdata)/metadata['datalength'])
            data= struct.unpack_from(stringformat,stringdata)
        
        return data

def storeData(data, path, dataformat, offset=0):
    if os.path.exists(path):
        mode="r+b"
    else:
        mode="wb"
    
    entrylength=struct.calcsize(dataformat)
    with open(path, mode) as fp:
        fp.seek(0, os.SEEK_END)
        filesize = fp.tell()
        #if the file has been untouched for too long: append dummy data
        if filesize < offset:
            fp.write((struct.pack(dataformat,float('nan')))*((offset - filesize)/entrylength))
        fp.seek(offset,0)
        for row in data:
            stringdata=struct.pack(dataformat,float(row))
            fp.write(stringdata)
