# -*- coding: utf-8 -*-
"""
Created by Filip Jorissen

The defined class can be interpreted as 'the object storing data for a sensor x'. 
For each sensor two files are created:
Sensor.meta contains metadata about the measurements. Sensor.float contains only the 
measurements: no timestamps. The location of the measurement in the file indicates 
the time at which it was measured. If there exists already stored data for the sensor, data 
is appended and/or overwritten.

Based on this object it is also possible to fetch timestamped data from these files using getAllData() 
and getSamplesStartingFrom().

TODO: improve documentation
"""
import os, json, struct, io, sys


class TimeSeriesData(object):
    """
    """
    
    def __init__(self, sensor, token, unit):
        self.sensor=sensor
        self.token=token
        self.unit=unit
    
        # set hardcoded paths
        self.resultpath="results-float"
        self.backuppath="backups"
        self.metapath=os.path.join(self.resultpath, sensor + ".meta")
        self.datapath=os.path.join(self.resultpath, sensor + ".float")
        self.dataformat = 'f'  #Format of the stored data: float

        #create results folder if it does not exist
        if not os.path.exists(self.resultpath):
            os.makedirs(self.resultpath)
        # create folder for backups if it does not exist
        if not os.path.exists(self.backuppath):
            os.makedirs(self.backuppath)
	    
	    # if exists: load existing metadata for sensor
        if os.path.exists(self.metapath):
            # load existing meta file
            with open(self.metapath, 'rb') as fp:
    		    self.metadata = json.load(fp)
            # set write mode to read and overwrite
            self.mode = 'r+b'
        #else: prepare metadata for new file
        else:
            #create new meta file
            self.metadata=dict()
            self.metadata['sensor']=sensor
            self.metadata['token']=token
            self.metadata['unit']=unit
            self.metadata['resolution']='minute' #add to getSecondsFromResolution !
            self.metadata['edittimes']=[]
            self.metadata['dataformat']=self.dataformat
            self.metadata['datalength']=struct.calcsize(self.dataformat)
            # set write mode to write
            self.mode='wb'
            
        #script for converting old data format to new one -> should be removed soon
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
            
                
    #store newdata in .float file and updata metadata file
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
        offset=(timestamp-self.metadata['starttime'])/self.getSecondsFromResolution()*entrylength
        storeData(newdata, self.datapath, self.metadata['dataformat'], offset)
        self.updateNumSamples()
        
        self.storeMetaData()
    
    #update the metadata entry stating how many samples the data file contains
    def updateNumSamples(self):
        with open(self.datapath, 'rb') as fp:
            fp.seek(0, os.SEEK_END)
            filesize = fp.tell()
        self.metadata['numSamples']=filesize/self.metadata['datalength']
    
    #check whether the given inputs are consistent with the pre-existing files
    def validateData(self, newdata, timestamp):
        #raise an exception when data measurements happened before the currently first measurement of the file
        if timestamp<self.metadata['starttime']:
            raise ValueError('The added data cannot be appended before the start of the file')
        #check for inconsistencies
        if self.metadata['sensor'] != self.sensor or self.metadata['token'] != self.token or self.metadata['unit'] != self.unit:
            raise ValueError('Argument is inconsistent with its stored value')
        if (timestamp- self.metadata['starttime']) % self.getSecondsFromResolution() != 0:
            raise ValueError("Timestamp does not have the correct spacing compared to the initial timestamp! Storage cancelled.")
    
    #perform the actual data storage
    def storeMetaData(self):
        # save (updated) meta data file
        with open(self.metapath, 'wb') as fp:
            json.dump(self.metadata, fp)
    
    #fetch all data from the current sensor and return it together with the timestamps
    def getAllData(self):
        data= self.getDataFromFile(0, -1)
        return self.dataToDict(data, self.metadata['starttime'])
    
    #fetch data from file and convert to correct format
    def getDataFromFile(self, offset, samples):
        with open(self.datapath, 'rb') as fp:
            fp.seek(offset)
            stringData=fp.read(samples*self.metadata['datalength'])
        return self.stringDataToData(stringData)
         
        
    
    #Fetch 'samples' data samples starting from timestamp 'firsttimestamp' and return it together with the timestamps
    #when 'samples' is omitted or negative, all data is read. A 'firsttimestamp' of zero (or empty) will return data starting from the first sample.
    #A negative 'firsttimestamp' value will read the _last_ 'samples' samples from the file.
    def getSamplesStartingFrom(self, firstTimeStamp=0, samples=-1):
        if firstTimeStamp==0:
            offset=0
        elif firstTimeStamp < 0:
            if samples < 0:
                offset=0
            else:
                offset=(self.metadata['numSamples']-samples)*self.metadata['datalength']
        else:
            offset=(firstTimeStamp-self.metadata['starttime'])*self.metadata['datalength']/self.getSecondsFromResolution()
        if offset<0:
            raise ValueError("Trying to fetch data before start of the file")
        
        data= self.getDataFromFile(offset, samples)
        return self.dataToDict(data, firstTimeStamp)
    
    #convert string data to 'formatted' data -> unpack data
    def stringDataToData(self, stringData):
        stringFormat=str(self.metadata['dataformat'])*(len(stringData)/self.metadata['datalength'])
        return struct.unpack_from(stringFormat,stringData)
    
    #add timestamps to the data and return them as a dictionary containing two lists, one with samples and one with timestamps
    def dataToDict(self,data, firstTimeStamp):
        result={}
        timeStamp=firstTimeStamp
        seconds=self.getSecondsFromResolution()
        timeStamps=[]
        samples=[]
        for row in data:
            timeStamps.append(timeStamp)
            samples.append(row)
            timeStamp=timeStamp+seconds
        result['timestamps']=timeStamps
        result['samples']=samples
        return result
    
    #returns the amount of seconds between each measurement
    def getSecondsFromResolution(self):
        if self.metadata['resolution']=='minute':
            return 60
        elif self.metadata['resolution']=='second':
            return 1
        else:
            raise ValueError("The given resolution is not supported yet")

#function for converting between data formats (float, string, ...) (untested)
def convertDataFormat(fromPath, toPath, toFormat):
    data=fetchDataFromFile(fromPath)
    storeData(data, toPath, toFormat)

#function for getting one row from a nested list
def nestedListToList(nestedList, index):
    newlist=[]
    for row in nestedList:
        newlist.append(row[index])
    return newlist

#fetch data from a file while fetching the format from the meta file
def fetchDataFromFile(filepath):
    if os.path.exists(filepath):
        with open(filepath.replace('.float','.meta'), 'rb') as fp:
		    metadata = json.load(fp)
        with open(filepath, 'rb') as fp:
            stringdata=fp.read()
            stringformat=str(metadata['dataformat'])*(len(stringdata)/metadata['datalength'])
            data= struct.unpack_from(stringformat,stringdata)
        
        return data

#store data in the specified format
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
