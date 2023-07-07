import numpy as np

# Static risk free rates, i.e. 4 week T Bill yields
# TODO: Source this programmatically
T_Bill_Yields = {
    2019: 2.08,
    2018: 1.81,
    2017: 0.83,
    2016: 0.25,
    2015: 0.03,
    2014: 0.03,
    2013: 0.05,
    2012: 0.07,
    2011: 0.04,
    2010: 0.11,
}
# Average 0.17625 %


def annualized_return(daily_values, n=255):
    """
    Calculate annualized return for given portfolio.
    :param daily_values: Daily portfolio values in Numpy.Series format.
    :param n: Day basis, i.e. number of trading days in a year.
    :return: Annualized return
    """
    daily_returns = daily_values.pct_change().dropna()
    annualized = daily_returns.mean() * n
    return annualized


def annualized_volatility(daily_values, n=255):
    """
    Calculate annualized volatility for given portfolio.
    :param daily_values: Daily portfolio values in Numpy.Series format.
    :param n: Day basis, i.e. number of trading days in a year.
    :return: Annualized volatility
    """
    daily_returns = daily_values.pct_change().dropna()
    annualized = daily_returns.std() * np.sqrt(n)
    return annualized


def sharpe_ratio(daily_values, n=255, risk_free=0.0017625):
    """
    Calculate sharpe ratio for given portfolio.
    :param daily_values: Daily portfolio values in Numpy.Series format.
    :param n: Day basis, i.e. number of trading days in a year.
    :param risk_free: Risk free rate.
    :return: Sharpe ratio.
    """
    daily_returns = daily_values.pct_change().dropna()
    mean = daily_returns.mean() * n - risk_free
    sigma = daily_returns.std() * np.sqrt(n)
    return mean / sigma
