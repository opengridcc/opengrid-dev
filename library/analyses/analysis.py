__author__ = 'Jan'

class Analysis(object):
    """
        Abstract class for Open Grid Analyses
    """

    def __init__(self, id = None):
        self.id = id

    def toJson(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def toPlt(self):
        raise NotImplementedError("Subclass must implement abstract method")