import os, sys
import inspect
import numpy as np
import pylab as plt


script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir))

from opengrid.library.storetimeseriesdata import fetchDataFromFile, TimeSeriesData

tsd=TimeSeriesData("0fb0f4af3c2b95158fba7977f42dacd8","04c5081d44ff178394aad3ae7e4f7777", "watt")
data= tsd.getSamplesStartingFrom(0,-1)

pargs = {"lw":5, "alpha":.6}
timestamps=data['timestamps']
samples=data['samples']
samples = [x for x in samples if str(x) != 'nan']
samples=sorted(samples,reverse=True)
timestamps = [(x-timestamps[0])/60 for x in timestamps]
samples=samples[::10]
plt.plot(range(0,len(samples)),samples, 'r', **pargs) 
plt.show()
