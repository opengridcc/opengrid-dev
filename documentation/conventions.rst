###############################
Some conventions and guidelines
###############################

Guidelines
##########

* **Always** remove the output of the ipython notebooks before comitting in order to avoid conflicts

As long as we have no configuration environment
===============================================
* create a folder for the data.  It is not obliged to create the subfolders *zip* and *csv*, they will be created automatically.  
* some scripts have a 'path_to_data' setting.  Always point to your data path created above.  Never point to *data/zip* or *data/csv*)
* 


Conventions
###########


* all time series data are pandas dataframes (pd.DataFrame).  Even single column dataframes are supposed to be converted back to dataframes. 
* the columns of the dataframes are always the sensor-IDs (like f886a33b7aa3145ba23c84eae1c0c5c8).  
* the index of the dataframes is always a DatetimeIndex
* the index is always at UTC
* scripts that are supposed to be scheduled with a cron job on the droplet have a filename starting with job_


 
