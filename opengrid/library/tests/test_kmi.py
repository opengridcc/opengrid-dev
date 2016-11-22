import unittest
from six import string_types
from pandas.core.frame import DataFrame

from opengrid.library.kmi import *


class KMITest(unittest.TestCase):
    """
    Class for testing the kmi web scraper
    """

    def test_fetch_website(self):
        """
        Check if the URL works
        """
        self.assertIsInstance(fetch_website(), string_types)

    def test_get_kmi_current_month(self):
        """
        Check if the top function returns a dataframe
        """
        self.assertIsInstance(get_kmi_current_month(), DataFrame)


if __name__ == '__main__':
    unittest.main()
