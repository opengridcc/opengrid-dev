__author__ = 'Jan'

import statsmodels.formula.api as sm

from opengrid.library import analysis


class MultiVariateLinearRegression(analysis.Analysis):
    def __init__(self, data, dependent_variable):
        """
            Calculate an Ordinary Least Squares Regression on a dataset with multiple variables

            Parameters
            ----------
            data: Pandas Dataframe
            dependent_variable: String
                name of the dependent variable. This will be the y value, all other columns will be used as x values
        """
        self.data = data
        self.dependent_variable = dependent_variable

        # select all column names that are not the dependent variable
        variables = [name for name in data.columns.tolist() if name != dependent_variable][::-1]

        self.result = self._run_ols(data=self.data, dependent_variable=dependent_variable, other_variables=variables)

    def _construct_formula(self, dependent_variable, variables):
        """
            Take a dependent variable y and list of variables and concatenate them into
            "y ~ var1 + var2 + var3"

            Parameters
            ----------
            dependent_variable: String
            variables: list of strings

            Returns
            -------
            string
        """
        rhs = variables.pop()
        while len(variables) > 0:
            rhs += " + {}".format(variables.pop())

        formula = "{} ~ {}".format(dependent_variable, rhs)

        return formula

    def _run_ols(self, data, dependent_variable, other_variables):
        """
            Construct the formula and run the OLS

            Parameters
            ----------
            data: Pandas Dataframe
            dependent_variable: String
            other_variables: list of strings
        """
        # The OLS calculation takes a formula of the form "y ~ x1 + x2"
        formula = self._construct_formula(dependent_variable, other_variables)

        return sm.ols(formula=formula, data=data).fit()

    def get_ols_with_significant_variables(self, p_value_limit=0.05):
        """
            Re-run the OLS but only with the variables where the pValue is below the p_value_limit (standard 0.05)
            which means that the variable is statistically significant

            Parameters
            ----------
            p_value_limit: float

            Returns
            -------
            sm.ols.fit
        """
        # get variables that are significant
        variables = self.get_significant_variables(p_value_limit)

        return self._run_ols(data=self.data, dependent_variable=self.dependent_variable, other_variables=variables)

    def get_significant_variables(self, p_value_limit=0.05):
        """
            Return the names of the columns where the pValue is below the p_value_limit (standard 0.05),
            meaning that the variable is statiscally significant

            Parameters
            ----------
            p_value_limit: float

            Returns
            -------
            list of strings
        """
        # iterate all pvalues, ignore intercept, return names where the value is smaller than pvaluelimit
        return [name for name,value in self.result.pvalues.iteritems() if name != 'Intercept' and value < p_value_limit]