from opengrid.library import analysis
import logging
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as fm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from copy import deepcopy


class MVLinReg(analysis.Analysis):
    """
    Multi-variable linear regression based on statsmodels and Ordinary Least Squares (ols)

    Pass a dataframe with the variable to be modelled (endogenous variable) and the possible independent (exogenous)
    variables.  Specify as string the name of the endogenous variable, and optionally pass a list with names of
    exogenous variables to try (by default all other columns will be tried as exogenous variables).

    The analysis is based on a forward-selection approach: starting from a simple model, the model is iteratively
    refined and verified until no statistical relevant improvements can be obtained.  Each model in the iteration loop
    is stored in the attribute self.list_of_fits.  The selected model is self.fit (=pointer to the last element of
    self.list_of_fits).

    The dataframe can contain daily, weekly, monthly, yearly ... values.  Each row is an instance.


    Examples
    --------

    >> mvlr = MVLinReg(df, 'gas', p_max=0.04)
    >> mvlr = MVLinReg(df, 'gas', list_of_exog=['heatingDegreeDays14', 'GlobalHorizontalIrradiance', 'WindSpeed'])


    """

    def __init__(self, df, endog, **kwargs):
        """

        Parameters
        ----------
        df : pd.DataFrame
            Datetimeindex and both endogenous and exogenous variables as columns
        endog : str
            Name of the endogeneous variable to model
        p_max : float (default=0.05)
            Acceptable p-value of the t-statistic for estimated parameters
        list_of_exog : list of str (default=None)
            If None (default), try to build a model with all columns in the dataframe
            If a list with column names is given, only try these columns as exogenous variables
        confint : float, default=0.05
            Two-sided confidence interval for predictions.
        cross_validation : bool, default=False
            If True, compute the model based on cross-validation (leave one out)
            Only possible if the df has less than 15 entries.
            Note : this will take much longer computation times!
        allow_negative_predictions : bool, default=False
            If True, allow predictions to be negative.
            For gas consumption or PV production, this is not physical so allow_negative_predictions should be False
        """
        self.df = df.copy()
        assert endog in self.df.columns, "The endogenous variable {} is not a column in the dataframe".format(endog)
        self.endog = endog

        self.p_max = kwargs.get('p_max', 0.05)
        self.list_of_exog = kwargs.get('list_of_kwargs', self.df.columns.tolist())
        self.confint = kwargs.get('confint', 0.05)
        self.cross_validation = kwargs.get('cross_validation', False)
        self.allow_negative_predictions = kwargs.get('allow_negative_predictions', False)
        try:
            self.list_of_exog.remove(self.endog)
        except:
            pass

        self.do_analysis()


    def do_analysis(self):
        """
        Find the best model (fit) and create self.list_of_fits and self.fit

        """
        if self.cross_validation:
            return self._do_analysis_cross_validation()
        else:
            return self._do_analysis_no_cross_validation()


    def _do_analysis_no_cross_validation(self):
        """
        Find the best model (fit) and create self.list_of_fits and self.fit

        """

        self.list_of_fits = []
        # first model is just the mean
        self.list_of_fits.append(fm.ols(formula='{} ~ 1'.format(self.endog), data=self.df).fit())
        # try to improve the model until no improvements can be found
        all_exog = self.list_of_exog[:]
        while all_exog:
            # try each x in all_exog and overwrite the best_fit if we find a better one
            # the first best_fit is the one from the previous round
            best_fit = deepcopy(self.list_of_fits[-1])
            for x in all_exog:
                # make new_fit, compare with best found so far
                formula = self.list_of_fits[-1].model.formula + '+{}'.format(x)
                fit = fm.ols(formula=formula, data=self.df).fit()
                best_fit = self.find_best_bic([best_fit, fit])

            # Sometimes, the obtained fit may be better, but contains unsignificant parameters.
            # Correct the fit by removing the unsignificant parameters and estimate again
            best_fit = self._prune(best_fit, p_max=self.p_max)

            # if best_fit does not contain more variables than last fit in self.list_of_fits, exit
            if best_fit.model.formula in self.list_of_fits[-1].model.formula:
                break
            else:
                self.list_of_fits.append(best_fit)
                all_exog.remove(x)
        self.fit = self.list_of_fits[-1]


    def _do_analysis_cross_validation(self):
        """
        Find the best model (fit) based on cross-valiation (leave one out)

        """
        assert len(self.df) < 15, "Cross-validation is not implemented if your sample contains more than 15 datapoints"

        # initialization: first model is the mean, but compute cv correctly.
        errors = []
        formula = '{} ~ 1'.format(self.endog)
        for i in self.df.index:
            # make new_fit, compute cross-validation and store error
            df_ = self.df.drop(i, axis=0)
            fit = fm.ols(formula=formula, data=df_).fit()
            cross_prediction = self._predict(fit=fit, df=self.df.loc[[i], :])
            errors.append(cross_prediction['predicted'] - cross_prediction[self.endog])

        self.list_of_fits = [fm.ols(formula=formula, data=self.df).fit()]
        self.list_of_cverrors = [np.mean(np.abs(np.array(errors)))]

        # try to improve the model until no improvements can be found
        all_exog = self.list_of_exog[:]
        while all_exog:
            #import pdb;pdb.set_trace()
            # try each x in all_exog and overwrite if we find a better one
            # at the end of iteration (and not earlier), save the best of the iteration
            better_model_found = False
            best = dict(fit=self.list_of_fits[-1], cverror=self.list_of_cverrors[-1])
            for x in all_exog:
                formula = self.list_of_fits[-1].model.formula + '+{}'.format(x)
                # cross_validation, currently only implemented for monthly data
                # compute the mean error for a given formula based on leave-one-out.
                errors = []
                for i in self.df.index:
                    # make new_fit, compute cross-validation and store error
                    df_ = self.df.drop(i, axis=0)
                    fit = fm.ols(formula=formula, data=df_).fit()
                    cross_prediction = self._predict(fit=fit, df=self.df.loc[[i], :])
                    errors.append(cross_prediction['predicted'] - cross_prediction[self.endog])
                cverror = np.mean(np.abs(np.array(errors)))
                # compare the model with the current fit
                if  cverror < best['cverror']:
                    # better model, keep it
                    # first, reidentify using all the datapoints
                    best['fit'] = fm.ols(formula=formula, data=self.df).fit()
                    best['cverror'] = cverror
                    better_model_found = True

            if better_model_found:
                self.list_of_fits.append(best['fit'])
                self.list_of_cverrors.append(best['cverror'])
            else:
                # if we did not find a better model, exit
                break

            # next iteration with the found exog removed
            all_exog.remove(x)

        self.fit = self.list_of_fits[-1]




    def _prune(self, fit, p_max):
        """
        If the fit contains statistically insignificant parameters, remove them.
        Returns a pruned fit where all parameters have p-values of the t-statistic below p_max

        Parameters
        ----------
        fit: fm.ols fit object
            Can contain insignificant parameters
        p_max : float
            Maximum allowed probability of the t-statistic

        Returns
        -------
        fit: fm.ols fit object
            Won't contain any insignificant parameters

        """

        for par in fit.pvalues.where(fit.pvalues > p_max).dropna().index:

            corrected_formula = fit.model.formula.replace('+{}'.format(par), '')
            fit = fm.ols(formula=corrected_formula, data=self.df).fit()
        return fit

    def find_best_rsquared(self, list_of_fits):
        """Return the best fit, based on rsquared"""
        res = sorted(list_of_fits, key=lambda x: x.rsquared)
        return res[-1]

    def find_best_akaike(self, list_of_fits):
        """Return the best fit, based on Akaike information criterion"""
        res = sorted(list_of_fits, key=lambda x: x.aic)
        return res[0]

    def find_best_bic(self, list_of_fits):
        """Return the best fit, based on Akaike information criterion"""
        res = sorted(list_of_fits, key=lambda x: x.bic)
        return res[0]


    def _predict(self, fit, df, **kwargs):
        """
        Return a df with predictions and confidence interval
        The df will contain the following columns:
        - 'predicted': the model output
        - 'interval_u', 'interval_l': upper and lower confidence bounds.

        Parameters
        ----------
        fit : Statsmodels fit
        df : pandas DataFrame or None (default)
            If None, use self.df
        confint : float (default=0.05)
            Confidence level for two-sided hypothesis, if given, overrides the default one.

        Returns
        -------
        df : pandas DataFrame
            same as df with additional columns 'predicted', 'interval_u' and 'interval_l'
        """


        confint = kwargs.get('confint', self.confint)

        # Add model results to data as column 'predictions'
        if 'Intercept' in fit.model.exog_names:
            df['Intercept'] = 1.0
        df['predicted'] = fit.predict(df)
        if not self.allow_negative_predictions:
            df.loc[df['predicted'] < 0, 'predicted'] = 0
        prstd, interval_l, interval_u = wls_prediction_std(fit, df[fit.model.exog_names])
        df['interval_l'] = interval_l
        df['interval_u'] = interval_u

        return df

    def predict(self, **kwargs):
        """
        Add predictions and confidence interval to self.df
        self.df will contain the following columns:
        - 'predicted': the model output
        - 'interval_u', 'interval_l': upper and lower confidence bounds.

        Parameters
        ----------
        confint : float (default=0.05)
            Confidence level for two-sided hypothesis, if given, overrides the default one.

        Returns
        -------
        Nothing, adds columns to self.df
        """
        self.df = self._predict(fit=self.fit, df=self.df, **kwargs)

    def plot(self, model=True, bar_chart=True, **kwargs):
        """
        Plot measurements and predictions.

        By default, use self.fit and self.df, but both can be overruled by the arguments df and fit
        This function will detect if the data has been used for the modelling or not and will
        visualize them differently.

        Parameters
        ----------
        model : boolean, default=True
            If True, show the modified energy signature
        bar_chart : boolean, default=True
            If True, make a bar chart with predicted and measured data
        df : pandas Dataframe, default=None
            The data to be plotted.  If None, use self.df
            If the dataframe does not have a column 'predicted', a prediction will be made
        fit : statsmodels fit, default=None
            The model to be used.  if None, use self.fit
        confint : float (default=0.05)
            Confidence level for two-sided hypothesis, if given, overrides the default one.

        Returns
        -------
        figures : List of plt.figure objects.

        """
        figures = []
        fit = kwargs.get('fit', self.fit)
        df = kwargs.get('df', self.df)

        if not 'predicted' in df.columns:
            df = self._predict(fit=fit, df=df, confint=kwargs.get('confint', 0.05))
        # split the df in the auto-validation and prognosis part
        try:
            df_auto = df.loc[self.df.index, :]
        except KeyError:
            # no overlap between self.df and df
            df_auto = pd.DataFrame()
            df_prog = df
        else:
            df_prog = df.drop(self.df.index)
            if len(df_prog) > 0:
                assert df_prog.index[0] > df_auto.index[-1], "Back-casting is currently not implemented"

        if model:
            # The first variable in the formula is the most significant.  Use it as abcis for the plot
            try:
                exog1 = fit.model.formula.split('+')[1].strip()
            except IndexError:
                exog1 = self.list_of_exog[0]

            # plot model as an adjusted trendline
            # get sorted model values
            dfmodel = df[[exog1, 'predicted', 'interval_u', 'interval_l']]
            dfmodel.index = dfmodel[exog1]
            dfmodel.sort(inplace=True)
            plt.plot(dfmodel.index, dfmodel['predicted'], '--', color='royalblue')
            plt.plot(dfmodel.index, dfmodel['interval_l'], ':',  color='royalblue')
            plt.plot(dfmodel.index, dfmodel['interval_u'], ':', color='royalblue')
            # plot dots for the measurements
            if len(df_auto) > 0:
                plt.plot(df_auto[exog1], df_auto[self.endog], 'o', mfc='orangered', mec='orangered', ms=8, label='Data used for model fitting')
            if len(df_prog) > 0:
                plt.plot(df_prog[exog1], df_prog[self.endog], 'o', mfc='seagreen', mec='seagreen', ms=8, label='Data not used for model fitting')
            plt.title('{} - rsquared={} - BIC={}'.format(fit.model.formula, fit.rsquared, fit.bic))
            figures.append(plt.gcf())

        if bar_chart:
            ind = np.arange(len(df.index))  # the x locations for the groups
            width = 0.35  # the width of the bars

            fig, ax = plt.subplots()
            title = 'Measured' # will be appended based on the available data
            if len(df_auto) > 0:
                model = ax.bar(ind[:len(df_auto)], df_auto['predicted'], width*2, color='#FDD787', ecolor='#FDD787',
                               yerr=df_auto['interval_u'] - df_auto['predicted'], label=self.endog + ' modelled')
                title = title + ', modelled'
            if len(df_prog) > 0:
                prog = ax.bar(ind[len(df_auto):], df_prog['predicted'], width * 2, color='#6CD5A1', ecolor='#6CD5A1',
                              yerr=df_prog['interval_u'] - df_prog['predicted'], label=self.endog + ' expected')
                title = title + ' and predicted'

            meas = ax.bar(ind+width/2., df[self.endog], width, label=self.endog + ' measured', color='#D5756C')
            # add some text for labels, title and axes ticks
            ax.set_ylabel(self.endog)
            ax.set_title('{} {}'.format(title, self.endog))
            ax.set_xticks(ind + width)
            ax.set_xticklabels([x.strftime('%d-%m-%Y') for x in df.index], rotation='vertical')
            ax.yaxis.grid(True)
            ax.xaxis.grid(False)


            plt.legend(ncol=3, loc='upper center')
            figures.append(plt.gcf())

        plt.show()

        return figures

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
