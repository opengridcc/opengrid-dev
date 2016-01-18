__author__ = 'Jan'

from scipy import stats
import matplotlib.pyplot as plt

from opengrid.library import analysis


class LinearRegression(analysis.Analysis):
    """
        Calculate a simple linear regression given a dataframe with X and Y values
    """
    def __init__(self, data, x_name='x', y_name='y'):
        """
            Parameters
            ----------
            data: Pandas Dataframe
                This dataframe has to be strictly formatted!
                One column must be named 'x', the other one 'y'
        """

        super(LinearRegression, self).__init__()

        self.data = data
        self.x_name = x_name
        self.y_name = y_name

        self.slope, self.intercept, self.r_value, self.p_value, self.std_err = stats.linregress(data[x_name], data[y_name])

    def get_y(self, x):
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

        # check if x is an iterable
        if not hasattr(x, '__iter__'):
            return self._get_y(x)
        else:
            return [self._get_y(val) for val in x]

    def _get_y(self, x):
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

    def get_x(self, y):
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

    def to_plt(self, force_origin=True):
        """
            Create scatterplot and plot trendline

            Parameters
            ----------
            force_origin: boolean, default True
                set the default values of the axis to 0,0

            Returns
            -------
            matplotlib figure
        """
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        ax1.scatter(self.data[self.x_name], self.data[self.y_name], alpha=1, s=20)

        function = "${s:.2f}x + {i:.2f}$".format(s=self.slope, i=self.intercept)
        r2 = "$R^2$: ${r:.2f}$".format(r=self.r_value)
        label = "{}\n{}".format(function,r2)

        x = self._get_plot_x()

        ax1.plot(x, self.get_y(x), '-', label=label)
        plt.legend(loc='upper left')

        if force_origin:
            x1, x2, y1, y2 = plt.axis()
            plt.axis((0, x2, 0, y2))

        return fig

    def _get_plot_x(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, the min and max since it's a single line
        """

        return [self.data[self.x_name].min(), self.data[self.x_name].max()]


class LinearRegression2(LinearRegression):
    """
        Calculate a linear regression that uses a predefined breakpoint to break between regression and baseload
    """
    def __init__(self, data, breakpoint, x_name='x', y_name='y'):
        """
            Parameters
            ----------
            data: Pandas Dataframe
                columns must be exactly named 'x' and 'y'
            breakpoint: number
                value on the x-axis where to break between regression and baseload
        """

        self.breakpoint = breakpoint
        self.x_name = x_name
        self.y_name = y_name

        # base_load is the mean of all y values where x is below the breakpoint
        self.base_load = data[data[x_name] <= self.breakpoint][y_name].mean()

        # calculate trendline by making a simple linear regression (superclass) on the right hand side data
        super(LinearRegression2, self).__init__(data=self._calculate_regression_data(data), x_name=x_name, y_name=y_name)

        # intersect is the intersection of the trendline and the baseload
        self.intersect = self.get_x(self.base_load)

        # the super init writes only right hand side data to self.data, so we have to overwrite it after initialisation
        self.data = data

    def _calculate_regression_data(self, data):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint
        """

        return data[data[self.x_name] > self.breakpoint]

    def _get_y(self, x):
        """
            Calculate a value on the trend line for a given x-value

            Parameters
            ----------
            x: number

            Returns
            -------
            float
        """
        # if the value is before the intersection, return the baseload
        if x <= self.intersect:
            return self.base_load
        else:
            # else return the normal value in the trendline
            return super(LinearRegression2, self)._get_y(x)

    def _get_plot_x(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, they are the same as the normal linear regression,
            but the intersection of the trend and the baseload need to be added
        """
        ret = super(LinearRegression2, self)._get_plot_x()
        ret.append(self.intersect)
        return sorted(ret)


class LinearRegression3(LinearRegression2):
    """
        Calculate a linear regression that uses a predefined breakpoint to break between baseload and regression,
        yet exclude values in a certain range (percentage of the baseload) from the regression
    """

    def __init__(self, data, breakpoint, percentage, include_end_of_base_load=True, x_name='x', y_name='y'):
        """
            Parameters
            ----------

            data: Pandas Dataframe
                columns must be named 'x' and 'y'
            breakpoint: number
                point on the x-axis where to break between baseload and regression
            percentage: float
                y-values that are in this range to the baseload are excluded from the regression
            include_end_of_base_load: boolean

        """

        self.percentage = percentage
        self.include_end_of_base_load = include_end_of_base_load

        super(LinearRegression3, self).__init__(data=data, breakpoint=breakpoint, x_name=x_name, y_name=y_name)

    def _calculate_regression_data(self, data):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint (from Linearregression2),
            but we iterate over them and drop values that are close to the baseline.
        """
        # make a list of indices of entries that are to be excluded from the regression
        to_drop = data[data[self.x_name] <= self.breakpoint].sort(self.x_name).index.tolist()

        # get the data from Regression 3
        res = super(LinearRegression3, self)._calculate_regression_data(data)

        # sort by x-value and iterate
        for entry in res.sort(self.x_name).iterrows():
            # if the y value is smaller than the percentage of the baseload
            if entry[1][self.y_name] < self.base_load * (1+self.percentage):
                # add the entry to the list to be dropped
                to_drop.append(entry[0])
            else:
                # if not, end the loop
                break

        # if we want to include the last value of the base load in the regression, remove it from the todrop list
        if self.include_end_of_base_load:
            to_drop.pop()

        # drop the to_drop list from the dataframe
        res = data.drop(to_drop)

        return res
