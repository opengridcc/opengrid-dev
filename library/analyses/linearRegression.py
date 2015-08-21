__author__ = 'Jan'

from scipy import stats
import matplotlib.pyplot as plt

from analysis import Analysis

class LinearRegression(Analysis):
    """
        Calculate a simple linear regression given a dataframe with X and Y values
    """
    def __init__(self,data, xName='x', yName='y'):
        """
            Parameters
            ----------
            data: Pandas Dataframe
                This dataframe has to be strictly formatted!
                One column must be named 'x', the other one 'y'
        """

        super(LinearRegression, self).__init__()

        self.data = data
        self.xName = xName
        self.yName = yName

        self.slope, self.intercept, self.r_value, self.p_value, self.std_err = stats.linregress(data[xName],data[yName])

    def getY(self,x):
        """
            Calculate the value on the trend line for a given x-value or an array of x-values

            Parameters
            ----------
            x: single number (float or int)
                OR iterable (array) of numbers

            Returns
            -------
            float if x is a single number
            array of floats if x is an iterable
        """

        #check if x is an iterable
        if not hasattr(x, '__iter__'):
            return self._getY(x)
        else:
            return [self._getY(val) for val in x]

    def _getY(self,x):
        """
            Calculate a value on the trend line for a given x-value

            Parameters
            ----------
            x: number

            Returns
            -------
            float
        """

        # y = ax + b
        return self.slope * x + self.intercept

    def getX(self,y):
        """
            Calculate value on the trendline for given y-value

            Parameters
            ----------
            y: number

            Return
            ------
            float
        """

        # y = ax + b => x = (y-b)/a
        return (y - self.intercept)/self.slope

    def toPlt(self, forceOrigin=True):
        """
            Create scatterplot and plot trendline

            Parameters
            ----------
            forceOrigin: boolean, default True
                set the default values of the axis to 0,0

            Returns
            -------
            matplotlib figure
        """
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        ax1.scatter(self.data[self.xName], self.data[self.yName], alpha=1, s=20)

        function = "${s:.2f}x + {i:.2f}$".format(s = self.slope, i = self.intercept)
        r2 = "$R^2$: ${r:.2f}$".format(r = self.r_value)
        label = "{}\n{}".format(function,r2)

        x = self._getPlotX()

        ax1.plot(x, self.getY(x), '-', label=label)
        plt.legend()

        if forceOrigin:
            x1,x2,y1,y2 = plt.axis()
            plt.axis((0,x2,0,y2))

        return fig

    def _getPlotX(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, the min and max since it's a single line
        """

        return [self.data[self.xName].min(),self.data[self.xName].max()]

class LinearRegression2(LinearRegression):
    """
        Calculate a linear regression that uses a predefined breakpoint to break between regression and baseload
    """
    def __init__(self,data,breakpoint,xName='x', yName='y'):
        """
            Parameters
            ----------
            data: Pandas Dataframe
                columns must be exactly named 'x' and 'y'
            breakpoint: number
                value on the x-axis where to break between regression and baseload
        """

        self.breakpoint = breakpoint
        self.xName = xName
        self.yName = yName

        #baseLoad is the mean of all y values where x is below the breakpoint
        self.baseLoad = data[data[xName]<=self.breakpoint][yName].mean()

        #calculate trendline by making a simple linear regression (superclass) on the right hand side data
        super(LinearRegression2, self).__init__(data = self._calculateRegressionData(data), xName=xName, yName=yName)

        #intersect is the intersection of the trendline and the baseload
        self.intersect = self.getX(self.baseLoad)

        #the super init writes only right hand side data to self.data, so we have to overwrite it after initialisation
        self.data = data

    def _calculateRegressionData(self, data):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint
        """

        return data[data[self.xName]>self.breakpoint]

    def _getY(self,x):
        """
            Calculate a value on the trend line for a given x-value

            Parameters
            ----------
            x: number

            Returns
            -------
            float
        """
        #if the value is before the intersection, return the baseload
        if x <= self.intersect:
            return self.baseLoad
        else:
            #else return the normal value in the trendline
            return super(LinearRegression2, self)._getY(x)

    def _getPlotX(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, they are the same as the normal linear regression,
            but the intersection of the trend and the baseload need to be added
        """
        ret = super(LinearRegression2, self)._getPlotX()
        ret.append(self.intersect)
        return sorted(ret)

class LinearRegression3(LinearRegression2):
    """
        Calculate a linear regression that uses a predefined breakpoint to break between baseload and regression,
        yet exclude values in a certain range (percentage of the baseload) from the regression
    """

    def __init__(self, data, breakpoint, percentage, includeEndOfBaseLoadInRegression=True, xName='x', yName='y'):
        """
            Parameters
            ----------

            data: Pandas Dataframe
                columns must be named 'x' and 'y'
            breakpoint: number
                point on the x-axis where to break between baseload and regression
            percentage: float
                y-values that are in this range to the baseload are excluded from the regression
            includeEndOfBaseLoadInRegression: boolean

        """

        self.percentage = percentage
        self.includeEndOfBaseLoadInRegression = includeEndOfBaseLoadInRegression

        super(LinearRegression3, self).__init__(data=data, breakpoint=breakpoint, xName=xName, yName=yName)

    def _calculateRegressionData(self,data):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint (from Linearregression2),
            but we iterate over them and drop values that are close to the baseline.
        """
        #make a list of indices of entries that are to be excluded from the regression
        toDrop = data[data[self.xName]<=self.breakpoint].sort(self.xName).index.tolist()

        #get the data from Regression 3
        res = super(LinearRegression3, self)._calculateRegressionData(data)

        #sort by x-value and iterate
        for entry in res.sort(self.xName).iterrows():
            #if the y value is smaller than the percentage of the baseload
            if entry[1][self.yName] < self.baseLoad * (1+self.percentage):
                #add the entry to the list to be dropped
                toDrop.append(entry[0])
            else:
                #if not, end the loop
                break

        # if we want to include the last value of the base load in the regression, remove it from the todrop list
        if self.includeEndOfBaseLoadInRegression:
            toDrop.pop()

        #drop the toDrop list from the dataframe
        res = data.drop(toDrop)

        return res