__author__ = 'Jan'

from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
import logging
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

        self._set_data(data)
        self.x_name = x_name
        self.y_name = y_name

        slope, self.intercept, r_value, self.p_value, self.std_err = stats.linregress(
                self.data[self.x_name], self.data[self.y_name])
        self._set_slope(slope)
        self._set_r_value(r_value)

    def _set_data(self, data):
        """
        Set data attribute, but check if dataframe has correct size etc.
        Throws error if dataframe is not good.

        Parameters
        ----------
        data: Pandas Data Frame

        """
        if len(data) > 2:
            self.data = data
        else:
            raise ValueError("Data set is too small")

    def _set_slope(self, slope):
        """
        Sets slope attribute, but throws a warning when it is negative

        Parameters
        ----------
        slope: float

        """
        self.slope = slope
        if slope < 0:
            logging.warning("Negative slope")

    def _set_r_value(self, r_value):
        """
        Sets r_value attribute, but throws a warning when it is negative

        Parameters
        ----------
        r_value: float


        """
        self.r_value = r_value
        if r_value < 0:
            logging.warning("Negative r_value")

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
        return (y - self.intercept) / self.slope

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
        r2 = "$R^2$: ${r:.2f}$".format(r=self.r_value**2)
        label = "{}\n{}".format(function, r2)

        x = self.get_trend_x()

        ax1.plot(x, self.get_y(x), '-', label=label)
        plt.legend(loc='upper left')

        if force_origin:
            x1, x2, y1, y2 = plt.axis()
            plt.axis((0, x2, 0, y2))

        return fig

    def get_trend_x(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, the min and max since it's a single line
        """

        ret = [self.data[self.x_name].min(), self.data[self.x_name].max()]
        return ret

    def score_spacing(self, max_spacing, min_spacing=0.0, spacing_tolerance=0.1, **kwargs):
        """
        Assign a score between 0 and 1 to the spacing of the x-values.
        We need a nominal spacing, between a miniumum and maximum.
        The spacing of this regression will be given as a percentage of that nominal.

        A spacing_tolerance can be set to allow values that lie close to the nominal spacing to get a value of 1.

        Parameters
        ----------
        max_spacing : float
        min_spacing : float (default 0)
        spacing_tolerance : float (default 0.1)
            percentage: only values between 0 and 1 allowed

        Returns
        -------
        float (percentage between 0 and 1)

        """
        margin = 1 - spacing_tolerance  # eg. if the spacing_tolerance is 5%, we will lower the nominal to 95% of it's value

        diff_x = self.data[self.x_name].max() - self.data[self.x_name].min()
        nominal_diff_x = (max_spacing - min_spacing) * margin

        return min(1, float(diff_x) / float(nominal_diff_x))

    def score_observations(self, expected_observations, **kwargs):
        """
        Assign a score between 0 and 1 to the number of observations.

        eg. If the analysis runs on monthly values for a year, the expected_observations number of observations is 12.
        If the dataframe only has 6 observations, the score will be 0.5

        Parameters
        ----------
        expected_observations: int

        Returns
        -------
        float (between 0 and 1)
        """

        return min(1, float(len(self.data)) / float(expected_observations))

    def score_total(self, weight=0.5, **kwargs):
        """
        Assign a score between 0 and 1 to the quality of the regression data as a whole

        This is done by multiplying the R Squared value with the the other scores.
        The other scores are weighted in to limit their influence on the final score.

        Parameters
        ----------
        weight: float

        Returns
        -------
        float (between 0 and 1)
        """
        r_squared = self.r_value ** 2
        spacing = self.score_spacing(**kwargs)
        observations = self.score_observations(**kwargs)

        return (r_squared * self._weigh_score(spacing, weight) * self._weigh_score(observations, weight))

    @staticmethod
    def _weigh_score(score, weight):
        """
        Adjusts a score to a weight.

        eg. If a score is 0.5 but you only want it to have an impact of 30% (weight = 0.3),
        the score will be redistributed between 0.7 and 1, resulting to 0.85.

        Parameters
        ----------
        score: float
        weight: float

        Returns
        -------
        float
        """
        return 1 - weight + (score * weight)


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
        self._set_base_load(data[data[x_name] <= self.breakpoint][y_name].mean())

        # calculate trendline by making a simple linear regression (superclass) on the right hand side data
        super(LinearRegression2, self).__init__(
                data=self._calculate_regression_data(data), x_name=x_name, y_name=y_name)

        if self.slope < 0:
            raise Exception("Negative slope detected, this is not possible for this type of regression")

        # intersect is the intersection of the trendline and the baseload
        if self.base_load is not None:
            self._set_intersect(self.get_x(self.base_load))
        else:
            self._set_intersect(None)

        # the super init writes only right hand side data to self.data, so we have to overwrite it after initialisation
        self._set_data(data)

    def _set_intersect(self, intersect):
        """
        Sets intersect attribute, checks for validity
        It has to be positive

        Parameters
        ----------
        intersect: float

        """
        if intersect is not None and intersect > 0:
            self.intersect = intersect
        else:
            self.intersect = None

    def _set_base_load(self, base_load):
        """
        Sets base load attribute, checks for validity

        Parameters
        ----------
        base_load: float

        """
        if not np.isnan(base_load):
            self.base_load = base_load
        else:
            self.base_load = None

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
        # if there is an intersection and the value is before the intersection, return the baseload
        if self.intersect is not None and x <= self.intersect:
            return self.base_load
        else:
            # else return the normal value in the trendline
            return super(LinearRegression2, self)._get_y(x)

    def get_trend_x(self):
        """
            Return the values that are needed to draw the trendline.
            In this case, they are the same as the normal linear regression,
            but the intersection of the trend and the baseload need to be added
        """
        ret = super(LinearRegression2, self).get_trend_x()
        if self.intersect is not None:
            ret.append(self.intersect)
        return sorted(ret)

    def score_baseload(self, baseload_threshold=3, **kwargs):
        """
        Asign a score between 0 and 1 to the baseload, based on the number of points below the breakpoint.

        Parameters
        ----------
        baseload_threshold: int
            number of points below the breakpoint that make the baseline qualitative

        Returns
        -------
        float (between 0 and 1)
        """

        if self.intersect is not None and self.intersect > self.breakpoint:
            breakpoint = self.intersect
        else:
            breakpoint = self.breakpoint

        num_points = len(self.data[self.data[self.x_name] <= breakpoint])  # number of points below the breakpoint

        return min(1, float(num_points) / float(baseload_threshold))

    def score_total(self, weight=0.5, **kwargs):
        """
        Calculate score between 0 and 1 by combining all sub-scores

        Parameters
        ----------
        weight: float

        Returns
        -------
        float
        """
        score = super(LinearRegression2, self).score_total(weight=weight, **kwargs)
        baseload_score = self.score_baseload(**kwargs)

        return score * self._weigh_score(baseload_score, weight)

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
            but we iterate over them and drop values that are close to the base load.
        """
        # make a list of indices of entries that are to be excluded from the regression
        to_drop = data[data[self.x_name] <= self.breakpoint].sort(self.x_name).index.tolist()

        # get the data from Regression 3
        res = super(LinearRegression3, self)._calculate_regression_data(data)

        if self.base_load is not None:
            # sort by x-value and iterate
            for entry in res.sort(self.x_name).iterrows():
                # if the y value is smaller than the percentage of the baseload
                if entry[1][self.y_name] < self.base_load * (1 + self.percentage):
                    # add the entry to the list to be dropped
                    to_drop.append(entry[0])
                else:
                    # if not, end the loop
                    break

            # if we want to include the last value of the base load in the regression, remove it from the todrop list
            if self.include_end_of_base_load and len(to_drop) > 0:
                to_drop.pop()

        # drop the to_drop list from the dataframe
        res = data.drop(to_drop)

        return res
