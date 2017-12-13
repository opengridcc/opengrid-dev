import unittest

from opengrid_dev import datasets

class DatasetTest(unittest.TestCase):
    def test_datasets(self):
        """
        Test if all pickle files in the folder `datasets`
        can be unpacked successfully
        """
        list = datasets.list_available()
        for dataset in list:
            datasets.get(dataset)


if __name__ == '__main__':
    unittest.main()