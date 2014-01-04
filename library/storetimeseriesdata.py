# -*- coding: utf-8 -*-
"""
Created by Filip Jorissen

This function stores sensor measurement data. For each sensor two files are created. Sensor.meta contains metadata about the measurements. Sensor.txt contains the actual measurements: only the measurements. The location of the measurement in the file indicates the time at which it was measured. If an existing measurement is already stored, data is appended and overwritten.

TODO: add conditions to check for illegal operations: too long file, ...
"""
import os, io
import json

def storeTimeSeriesData(data, sensor, token, unit):
    resultpath="results"
    metapath=resultpath +"/"+ sensor + ".meta"
    datapath=resultpath +"/"+ sensor + ".txt"

    #create results folder if it does not exist
    if not os.path.exists(resultpath):
        os.makedirs(resultpath)
	
    if os.path.exists(metapath):
        # load existing meta file
        with open(metapath, 'rb') as fp:
		    metadata = json.load(fp)
        # set write mode to read and overwrite
        mode = 'r+b'
        #check for inconsistencies
        if metadata['sensor'] != sensor or metadata['token'] != token or metadata['unit'] != unit:
            raise ValueError('Argument is inconsistent with its stored value')
    else:
        #create new meta file
        metadata=dict()
        metadata['starttime']=data[0][0]
        metadata['sensor']=sensor
        metadata['token']=token
        metadata['unit']=unit
        metadata['resolution']='minute' #need to edit factor '60' below when this is changed!
        metadata['datalength']=6
        metadata['separator']=' '
        metadata['edittimes']=[]
        # set write mode to write
        mode='wb'

    #append the unix timestamp to indicate which values were overwritten/added
    metadata['edittimes'].append(data[0][0])

    #raise an exception when data measurements happened before the currently first measurement of the file
    if data[0][0]<metadata['starttime']:
        raise ValueError('The added data cannot be appended before the start of the file')

	# insert new data at the correct point in the file
    entrylength=metadata['datalength'] + len(metadata['separator'])
    with open(datapath, mode) as fp:
        startIndex=(data[0][0]-metadata['starttime'])/60*entrylength
        fp.seek(0, os.SEEK_END)
        filesize = fp.tell()
        #if the file has been untouched for too long: append dummy data
        if filesize < startIndex:
            fp.write(("???".zfill(metadata['datalength']) + metadata['separator'])*((startIndex - filesize)/entrylength))
        fp.seek(startIndex,0)
        for row in data:
            fp.write(str(row[1]).zfill(metadata['datalength'])+ metadata['separator'])
    
    # save (updated) meta data file
    with open(metapath, 'wb') as fp:
        json.dump(metadata, fp)

	    