import bs4
import requests
import iso8601
import datetime as dt
import pandas as pd
from .misc import dayset


def get_belpex(start, end=None):
    """
    Fetches Belpex prices for given period between start and end

    Parameters
    ----------
    start : something datetime like
    end : something datetime like too
        optional, defaults to tomorrow, because Belpex values are available for 1 day in the future!

    Returns
    -------
    Pandas Series
    """
    if end is None:
        end = dt.date.today() + dt.timedelta(days=1)
    # Prices are fetched per day, so we'll create a set of days, download seperate dataframes per day and put them
    # together
    series = [get_belpex_day(date) for date in dayset(start, end)]
    return pd.concat(series)


def get_belpex_day(date):
    """
    Get Belpex prices for a given day

    Parameters
    ----------
    date: something datetime like

    Returns
    -------
    Pandas series
    """
    # start out by getting the html from the website
    html = fetch_website(date)
    # parse html into an array of timestamps and values
    try:
        index, data = parse_html(html)
    except KeyError:  # something goes wrong when parsing, probably meaning data is unavailable.
        print("No data found for {}".format(date.date()))
        return None

    series = pd.Series(index=index, data=data)
    series = series.tz_convert('Europe/Brussels')
    return series


def fetch_website(date):
    """
    Fetch the website containing the data from ENTSOE.EU

    Parameters
    ----------
    date: something datetime-like

    Returns
    -------
    str
    """
    # the date needs to look like 24.02.2016 for the url
    formatted_date = date.strftime("%d.%m.%Y")
    url = "https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime={}+00:00|CET|DAY&biddingZone.values=CTY|10YBE----------2!BZN|10YBE----------2&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)".format(
        formatted_date)

    r = requests.get(url)

    if r.status_code == 200:
        return r.text
    else:
        raise Exception("Seems like you got code {}".format(r.status_code))


def parse_html(html):
    """
    Searches the html-page for the elements we need

    Parameters
    ----------
    html : str

    Returns
    -------
    index : list of timestamps
    data : list of floats
    """
    index = []
    data = []

    # run the page through beautiful soup
    soup = bs4.BeautifulSoup(html, 'html.parser')

    # the elements we want are in a div with id dv-data-table
    data_table = soup.find(id='dv-data-table')
    # every element is in a span
    spans = data_table.findAll('span')
    for span in spans:
        # There is a iso8601 timestamp somewhere in an 'onclick' JavaScript call...
        # Luckily all arguments passed are of constant width so we can grab the stamp by index
        date = iso8601.parse_date(span['onclick'][128:152])
        index.append(date)
        # the value is right in the middle of the span
        value = float(span.text)
        data.append(value)

    return index, data
