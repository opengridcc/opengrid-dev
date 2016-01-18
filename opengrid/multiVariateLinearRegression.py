__author__ = 'Jan'

import statsmodels.formula.api as sm

from analysis import Analysis

class MultiVariateLinearRegression(Analysis):
    def __init__(self, data, dependentVariable):
        """
            Calculate an Ordinary Least Squares Regression on a dataset with multiple variables

            Parameters
            ----------
            data: Pandas Dataframe
            dependentVariable: String
                name of the dependent variable. This will be the y value, all other columns will be used as x values
        """
        self.data = data
        self.dependentVariable = dependentVariable

        #select all column names that are not the dependent variable
        variables = [name for name in data.columns.tolist() if name != dependentVariable][::-1]

        self.result = self._runOLS(data=self.data, dependentVariable=dependentVariable, otherVariables=variables)

    def _constructFormula(self, dependentVariable, variables):
        """
            Take a dependent variable y and list of variables and concatenate them into
            "y ~ var1 + var2 + var3"

            Parameters
            ----------
            dependentVariable: String
            variables: list of strings

            Returns
            -------
            string
        """
        rhs = variables.pop()
        while len(variables) > 0:
            rhs += " + {}".format(variables.pop())

        formula = "{} ~ {}".format(dependentVariable, rhs)

        return formula

    def _runOLS(self, data, dependentVariable, otherVariables):
        """
            Construct the formula and run the OLS

            Parameters
            ----------
            data: Pandas Dataframe
            dependentVariable: String
            otherVariables: list of strings
        """
        #The OLS calculation takes a formula of the form "y ~ x1 + x2"
        formula = self._constructFormula(dependentVariable,otherVariables)

        return sm.ols(formula=formula,data=data).fit()

    def getOLSWithSignificantVariables(self,pvalueLimit=0.05):
        """
            Re-run the OLS but only with the variables where the pValue is below the pvalueLimit (standard 0.05)
            which means that the variable is statistically significant

            Parameters
            ----------
            pvalueLimit: float

            Returns
            -------
            sm.ols.fit
        """
        #get variables that are significant
        variables = self.getSignificantVariables(pvalueLimit)

        return self._runOLS(data=self.data, dependentVariable=self.dependentVariable, otherVariables=variables)

    def getSignificantVariables(self,pvalueLimit=0.05):
        """
            Return the names of the columns where the pValue is below the pvalueLimit (standard 0.05),
            meaning that the variable is statiscally significant

            Parameters
            ----------
            pvalueLimit: float

            Returns
            -------
            list of strings
        """
        #iterate all pvalues, ignore intercept, return names where the value is smaller than pvaluelimit
        return [name for name,value in self.result.pvalues.iteritems() if name != 'Intercept' and value < pvalueLimit]