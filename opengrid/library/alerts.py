"""
Create alerts

"""

import json

def get_threshold(analysis, sensor_key):
    """
    Return threshold value for a given sensor_key for a given analysis.
    The threshold is fetched from the alerts.cfg file.

    Parameters
    ----------
    analysis : str
        Name of the analysis
    sensor_key : str
        Sensor key for which the threshold has to be returned.
    """

    threshold = json.load(open("alerts.cfg", "r"))
    default = threshold[analysis]['default']

    return threshold[analysis].get(sensor_key, default)


def create_alerts(df, hp, analysis, slack, column='result'):
    """
    Create alerts for each sensor, if needed.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with specific structure:
            - sensor_keys as index
            - by default, needs a column called 'result' with the data to be compared to a threshold
            You can specify a different column
    analysis : str
        Name of the analysis
    slack : Slack object
        See library.slack.py
    column : str, default='result'
        Column name with the results to be used for the alerting
    """

    for sensor_key in df.index:
        tr = get_threshold(analysis, sensor_key=sensor_key)
        if df.loc[sensor_key, column] > tr:
            json_message = {
                "text": "",
                "attachments": [
                    {
                        "title": "High electricity consumption",
                        "text": """We found a strange (high) value for the analysis {}.
                        """.format(analysis),
                        "fallback": "OpenGrid alert",
                        "color": "warning",  # this will create a red line
                        "fields": [
                            {
                                "title": "Fluksometer",
                                "value": hp.find_sensor(sensor_key).device.key,
                                "short": True
                            },
                            {
                                "title": "Sensor key",
                                "value": sensor_key,
                                "short": True
                            },
                            {
                                "title": "Your result",
                                "value": df.loc[sensor_key, column],
                                "short": True
                            },
                            {
                                "title": "Your threshold value",
                                "value": tr,
                                "short": True
                            }
                        ]
                    }
                ]
            }
            slack.post_json(json_message)
