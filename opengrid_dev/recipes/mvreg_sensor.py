# -*- coding: utf-8 -*-
"""
Script for generating a multivariable regression model for a single sensor.
The script will fetch the data, build a model and make graphs.

Created on 26/03/2017 by Roel De Coninck

"""

import sys, os
import matplotlib
matplotlib.use('Agg')

import pandas as pd
from opengrid_dev.library import houseprint, caching, regression, forecastwrapper
from opengrid_dev import config
c = config.Config()

import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = 10,5


def compute(sensorid, start_model, end_model):
    end = pd.Timestamp('now', tz='Europe/Brussels')
    # Create houseprint from saved file, if not available, parse the google spreadsheet
    try:
        hp_filename = os.path.join(c.get('data', 'folder'), 'hp_anonymous.pkl')
        hp = houseprint.load_houseprint_from_file(hp_filename)
        print("Houseprint loaded from {}".format(hp_filename))
    except Exception as e:
        print(e)
        print("Because of this error we try to build the houseprint from source")
        hp = houseprint.Houseprint()
    hp.init_tmpo()

    # Load the cached daily data
    sensor = hp.find_sensor(sensorid)
    cache = caching.Cache(variable='{}_daily_total'.format(sensor.type))
    df_day = cache.get(sensors=[sensor])
    df_day.rename(columns={sensorid: sensor.type}, inplace=True)

    # Load the cached weather data, clean up and compose a combined dataframe
    weather = forecastwrapper.Weather(location=(50.8024, 4.3407), start=start_model, end=end)
    irradiances = [
        (0, 90),  # north vertical
        (90, 90),  # east vertical
        (180, 90),  # south vertical
        (270, 90),  # west vertical
    ]
    orientations = [0, 90, 180, 270]
    weather_data = weather.days(irradiances=irradiances,
                                wind_orients=orientations,
                                heating_base_temperatures=[0, 6, 8, 10, 12, 14, 16, 18]).dropna(axis=1)
    weather_data.drop(['icon', 'summary', 'moonPhase', 'windBearing', 'temperatureMaxTime', 'temperatureMinTime',
                       'apparentTemperatureMaxTime', 'apparentTemperatureMinTime', 'uvIndexTime',
                       'sunsetTime', 'sunriseTime'],
                      axis=1, inplace=True)
    # Add columns for the day-of-week
    for i, d in zip(range(7), ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
        weather_data[d] = 0
        weather_data.loc[weather_data.index.weekday == i, d] = 1
    weather_data = weather_data.applymap(float)

    data = pd.concat([df_day, weather_data], axis=1).dropna()
    data = data.tz_convert('Europe/Brussels')

    df = data.resample(rule='MS').sum()
    if len(df) < 2:
        print("Not enough data for building a monthly reference model")
        sys.exit(1)

    # monthly model, statistical validation
    mv = regression.MVLinReg(df.ix[:end_model], sensor.type, p_max=0.03)
    figures = mv.plot(df=df)

    figures[0].savefig(os.path.join(c.get('data', 'folder'), 'figures', 'multivar_model_' + sensorid + '.png'), dpi=100)
    figures[1].savefig(os.path.join(c.get('data', 'folder'), 'figures', 'multivar_results_' + sensorid + '.png'),
                       dpi=100)

    # weekly model, statistical validation
    df = data.resample(rule='W').sum()
    if len(df.ix[:end_model]) < 4:
        print("Not enough data for building a weekly reference model")
        sys.exit(1)
    mv = regression.MVLinReg(df.ix[:end_model], sensor.type, p_max=0.02)
    if len(df.ix[end_model:]) > 0:
        figures = mv.plot(model=False, bar_chart=True, df=df.ix[end_model:])
        figures[0].savefig(
            os.path.join(c.get('data', 'folder'), 'figures', 'multivar_prediction_weekly_' + sensorid + '.png'),
            dpi=100)


if __name__ == '__main__':


    if not len(sys.argv) == 4:
        print("""
        Use of this script: python mreg_sensors.py sensorid from till

        sensorid: (string) sensortoken
        from: (string) starting date for the identification data of the model
        till: (string) end date for the identification data of the model
        """)
        exit(1)


    # parse arguments
    sensorid = sys.argv[1]
    start_model = pd.Timestamp(sys.argv[2], tz='Europe/Brussels')
    end_model = pd.Timestamp(sys.argv[3], tz='Europe/Brussels') #last day of the data period for the model

    compute(sensorid, start_model, end_model)


