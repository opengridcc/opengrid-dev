import unittest
from six import string_types
from pandas.core.series import Series

from opengrid.library.belpex import *


class BelpexTest(unittest.TestCase):
    """
    Class for testing the belpex web scraper
    """

    def setUp(self):
        self.website = fetch_website(date=dt.datetime.today())

    def test_fetch_website(self):
        self.assertIsInstance(self.website, string_types)

    def test_parse_html(self):
        parsed = parse_html(self.website)
        self.assertIsInstance(parsed, tuple)

        dates, values = parsed
        self.assertIsInstance(dates, list)
        self.assertIsInstance(values, list)
        self.assertEqual(len(dates), len(values))
        self.assertIsInstance(dates[0], dt.datetime)
        self.assertIsInstance(values[0], float)

        website_err = fetch_website(date=dt.datetime.today() + dt.timedelta(days=5))
        with self.assertRaises(KeyError):
            parse_html(website_err)

    def test_get_belpex_day(self):
        series = get_belpex_day(date=dt.datetime.today())
        self.assertIsInstance(series, Series)

        self.assertIsNone(get_belpex_day(date=dt.datetime.today() + dt.timedelta(days=5)))

    def test_get_belpex(self):
        series = get_belpex(start=dt.datetime.today() - dt.timedelta(days=1), end=dt.datetime.today())
        self.assertIsInstance(series, Series)


if __name__ == '__main__':
    unittest.main()
