import pandas as pd
import os

class DatasetContainer:
    """
    This class contains the names and paths to the data sets,
    and has the ability to unpack them.
    """
    def __init__(self, paths=None):
        """
        You can initialise empty and add the paths later,
        or you can initialise with a list of paths to data sets

        NOTE: all data sets are assumed to be pickled
        and gzip compressed Pandas DataFrames

        Parameters
        ----------
        paths : [str]
        """
        self.list = {}
        for path in paths:
            self.add(path)

    def add(self, path):
        """
        Add the path of a data set to the list of available sets

        NOTE: a data set is assumed to be a pickled
        and gzip compressed Pandas DataFrame

        Parameters
        ----------
        path : str
        """
        name_with_ext = os.path.split(path)[1]  # split directory and filename
        name = name_with_ext.split('.')[0]  # remove extension
        self.list.update({name: path})  # add to list

    def unpack(self, name):
        """
        Unpacks a data set to a Pandas DataFrame

        Parameters
        ----------
        name : str
            call `.list` to see all availble datasets

        Returns
        -------
        pd.DataFrame
        """
        path = self.list[name]
        df = pd.read_pickle(path, compression='gzip')
        return df

directory = os.path.dirname(__file__)  # get the path to the `datasets` directory
# list all filenames in this directory that have the extension `pkl`
pickles = [filename for filename in os.listdir(directory) if filename.lower().endswith('.pkl')]
# join directory and filenames to get full paths
paths = [os.path.join(directory, filename) for filename in pickles]
sets = DatasetContainer(paths)  # init container object

def list_available():
    return sets.list

def get(name):
    return sets.unpack(name)