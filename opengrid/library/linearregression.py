from opengrid.library import analysis
import logging
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class LinearRegression(analysis.Analysis):
    """
    Calculate a simple linear regression given a dataframe with X and Y values
    """

    def __init__(self, independent, dependent, *args, **kwargs):
        """
        Parameters
        ----------
        independent : pandas.Series
        dependent : pandas.Series
        """
        df = pd.concat([independent, dependent], axis=1).dropna()
        df.columns = ['independent', 'dependent']
        self._check_df(df=df)
        super(LinearRegression, self).__init__(df=df, *args, **kwargs)

    def do_analysis(self, *args, **kwargs):
        df = self._calculate_regression_data()
        slope, self.intercept, r_value, self.p_value, self.std_err = stats.linregress(
            df.independent, df.dependent)
        self._set_slope(slope)
        self._set_r_value(r_value)
        #self.rsquared = self.r_value**2
        try:
            self.rsquared = self._r2()
        except AttributeError:
            # the subclass that gets this error will have to find another way to calculate rsquared
            pass

    def _check_df(self, df):
        """
        Check if dataframe has correct size etc.
        Throws error if dataframe is not good.
        """
        if not len(df) > 2:
            raise ValueError("Data set is too small")

    def _r2(self):
        """
            Calculate R Squared

            Returns
            -------
            float
        """
        res = np.corrcoef(self.df.dependent, self.get_y(self.df.independent))[0, 1] ** 2
        return res

    def _calculate_regression_data(self):
        """
            Decide what data to use for the linear regression.
            In this case all data.
        """
        return self.df

    def _set_slope(self, slope):
        """
        Sets slope attribute, but throws an error when it is negative

        Parameters
        ----------
        slope: float

        """
        self.slope = slope
        if slope < 0:
            raise ValueError("Negative slope!")

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

    def plot(self, force_origin=True):
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

        ax1.scatter(self.df.independent, self.df.dependent, alpha=1, s=20)

        function = "${s:.2f}x + {i:.2f}$".format(s=self.slope, i=self.intercept)
        r2 = "$R^2$: ${r:.2f}$".format(r=self.rsquared)
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

        ret = [self.df.independent.min(), self.df.independent.max()]
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

        diff_x = self.df.independent.max() - self.df.independent.min()
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

        return min(1, float(len(self.df)) / float(expected_observations))

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
        spacing = self.score_spacing(**kwargs)
        observations = self.score_observations(**kwargs)

        return (self.rsquared * self._weigh_score(spacing, weight) * self._weigh_score(observations, weight))

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

    def __init__(self, independent, dependent, breakpoint, *args, **kwargs):
        """
        Parameters
        ----------
        independent : pandas.Series
        dependent : pandas.Series
        breakpoint : int | float
            value on the x-axis where to break between regression and baseload
        """

        self.breakpoint = breakpoint
        super(LinearRegression2, self).__init__(independent=independent,
                                                dependent=dependent, *args,
                                                **kwargs)

    def do_analysis(self, *args, **kwargs):
        # base_load is the mean of all y values where x is below the breakpoint
        self._set_base_load(self.df[self.df.independent <= self.breakpoint].dependent.mean())
        super(LinearRegression2, self).do_analysis(*args, **kwargs)

        if self.base_load is not None:
            self._set_intersect(self.get_x(self.base_load))
        else:
            self._set_intersect(None)

        self.rsquared = self._r2()

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

    def _set_slope(self, slope):
        """
        Sets slope attribute, throws an error if it is negative

        Parameters
        ----------
        slope: float
        """
        if slope < 0:
            raise ValueError('Negative slope not possible for this type of regression Analysis')
        else:
            self.slope = slope

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

    def _calculate_regression_data(self):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint
        """

        return self.df[self.df.independent > self.breakpoint]

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

        num_points = len(self.df[self.df.independent <= breakpoint])  # number of points below the breakpoint

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

    def __init__(self, independent, dependent, breakpoint, percentage,
                 include_end_of_base_load=True, *args, **kwargs):
        """
        Parameters
        ----------
        independent : pandas.Series
        dependent : pandas.Series
        breakpoint : int | float
            point on the x-axis where to break between baseload and regression
        percentage: float
            y-values that are in this range to the baseload are excluded from the regression
        include_end_of_base_load : bool
        """

        self.percentage = percentage
        self.include_end_of_base_load = include_end_of_base_load
        super(LinearRegression3, self).__init__(independent=independent,
                                                dependent=dependent,
                                                breakpoint=breakpoint, *args,
                                                **kwargs)

    def _calculate_regression_data(self):
        """
            Decide what data to use for the linear regression.
            In this case all data past the breakpoint (from Linearregression2),
            but we iterate over them and drop values that are close to the base load.
        """
        # make a list of indices of entries that are to be excluded from the regression
        to_drop = self.df[self.df.independent <= self.breakpoint].sort_values(by='independent').index.tolist()

        # get the data from Regression 2
        res = super(LinearRegression3, self)._calculate_regression_data()

        if self.base_load is not None:
            # sort by x-value and iterate
            for entry in res.sort_values(by='independent').iterrows():
                # if the y value is smaller than the percentage of the baseload
                if entry[1].dependent < self.base_load * (1 + self.percentage):
                    # add the entry to the list to be dropped
                    to_drop.append(entry[0])
                else:
                    # if not, end the loop
                    break

            # if we want to include the last value of the base load in the regression, remove it from the todrop list
            if self.include_end_of_base_load and len(to_drop) > 0:
                to_drop.pop()

        # drop the to_drop list from the dataframe
        res = self.df.drop(to_drop)

        return res
