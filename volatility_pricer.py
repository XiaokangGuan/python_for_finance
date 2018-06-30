import numpy as np
from data_hub import DataHub
import datetime

class VolatilityPricer():
    """
    Realized vol:
    Same as Black-Scholes, we assume the underlying follows a Geometric Brownian Motion.
    Then its log return follows a Normal distribution, with mean as 0.
    We take as input the historical daily underlying prices.
    Annualization factor is 252.
    Degree of Freedom is 0 as we are calculating the exact realized vol for the given historical period.

    Implied vol:


    """

    def __init__(self):
        self.historicalDataBySymbol = dict()
        self.dataHub = DataHub()
        self.realizedVolBySymbol = dict()
        self.impliedVolBySymbol = dict()

    def _loadHistoricalUnderlyingData(self, startDate, endDate, symbols):
        self.historicalDataBySymbol = self.dataHub.downloadDataFromYahoo(startDate, endDate, symbols)

    def _calculateRealizedVol(self, ts):
        """ Calculate the realized vol from given time series """
        pctChange = ts.pct_change().dropna()
        logReturns = np.log(1+pctChange)
        vol = np.sqrt(np.sum(np.square(logReturns)) / logReturns.size)
        annualizedVol = vol * np.sqrt(252)

        return annualizedVol

    def getRealizedVol(self, startDate=datetime.date.today()-datetime.timedelta(days=30), endDate=datetime.date.today(), symbols=['SPY']):
        """ Calculate the realized volatility from historical market data """
        self._loadHistoricalUnderlyingData(startDate, endDate, symbols)

        for symbol, df in self.historicalDataBySymbol.iteritems():
            # Use daily Close to calculate realized vols
            realizedVol = self._calculateRealizedVol(df.loc[:, 'Close'])
            self.realizedVolBySymbol[symbol] = realizedVol

        return self.realizedVolBySymbol

    def getImpliedVol(self):
        """ Calculate the implied volatility from option market price """
        pass