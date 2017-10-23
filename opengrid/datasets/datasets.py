import pandas as pd
import os

dir = os.path.dirname(__file__)

path = os.path.join(dir, 'elec_power_min_1sensor.pkl')
ELEC_POWER_MIN_1SENSOR = pd.read_pickle(path=path, compression='gzip')