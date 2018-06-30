import numpy as np
import math
import logging


def ncdf(x):
    """
    Cumulative distribution function for the standard normal distribution.
    Alternatively, we can use below:
    from scipy.stats import norm
    norm.cdf(x)
    """
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def npdf(x):
    """
    Probability distribution function for the standard normal distribution.
    Alternatively, we can use below:
    from scipy.stats import norm
    norm.pdf(x)
    """
    return np.exp(-np.square(x) / 2) / np.sqrt(2 * np.pi)


def blackScholesOptionPrice(callPut, spot, strike, tenor, rate, sigma):
    """
    Black-Scholes option pricing
    tenor is float in years. e.g. tenor for 6 month is 0.5
    """
    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * tenor) / (sigma * np.sqrt(tenor))
    d2 = d1 - sigma * np.sqrt(tenor)

    if callPut == 'Call':
        return spot * ncdf(d1) - strike * np.exp(-rate * tenor) * ncdf(d2)
    elif callPut == 'Put':
        return -spot * ncdf(-d1) + strike * np.exp(-rate * tenor) * ncdf(-d2)


def blackScholesVega(callPut, spot, strike, tenor, rate, sigma):
    """ Black-Scholes vega """
    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * tenor) / (sigma * np.sqrt(tenor))
    return spot * np.sqrt(tenor) * npdf(d1)


def blackScholesDelta(callPut, spot, strike, tenor, rate, sigma):
    """ Black-Scholes delta """
    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * tenor) / (sigma * np.sqrt(tenor))
    if callPut == 'Call':
        return ncdf(d1)
    elif callPut == 'Put':
        return ncdf(d1) - 1


def blackScholesGamma(callPut, spot, strike, tenor, rate, sigma):
    """" Black-Scholes gamma """
    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * tenor) / (sigma * np.sqrt(tenor))
    return npdf(d1) / (spot * sigma * np.sqrt(tenor))


def blackScholesSolveImpliedVol(targetPrice, callPut, spot, strike, tenor, rate):
    """" Solve for implied volatility using Black-Scholes """
    MAX_ITERATIONS = 100
    PRECISION = 1.0e-5

    sigma = 0.5
    i = 0
    while i < MAX_ITERATIONS:
        optionPrice = blackScholesOptionPrice(callPut, spot, strike, tenor, rate, sigma)
        vega = blackScholesVega(callPut, spot, strike, tenor, rate, sigma)
        diff = targetPrice - optionPrice
        logging.debug('blackScholesSolveImpliedVol: iteration={}, sigma={}, diff={}'.format(i, sigma, diff))

        if abs(diff) < PRECISION:
            return sigma

        sigma = sigma + diff/vega
        i = i + 1

    logging.debug('blackScholesSolveImpliedVol: After MAX_ITERATIONS={}, best sigma={}'.format(MAX_ITERATIONS, sigma))
    return sigma


class EuropeanVanillaPricer:

    def __init__(self, method='MC', callPut='Call', spot=100.0, strike=120, tenor=1.0, rate=0.0014, sigma=0.20, iterations=1e6):
        self.method = method
        self.callPut = callPut
        self.spot = spot
        self.strike = strike
        self.tenor = tenor
        self.rate = rate
        self.sigma = sigma
        self.iterations = iterations
 
    def getPrice(self):
        """ Calculate price using given method. """
        if self.method == 'MC':
            return self.getMCPrice()
        elif self.method == 'BS':
            return self.getBSPrice()
 
    def getMCPrice(self):
        """
        Determine the option price using a Monte Carlo approach.
        The log return of underlying follow Normal distribution.
        s_T = s_t * exp((r - 1/2 * sig^2) * (T-t) + sig * sqrt(T-t) * sig_Normal)
        """
        calc = np.zeros([self.iterations, 2])
        rand = np.random.normal(0, 1, [1, self.iterations])
        mult = self.spot * np.exp(self.tenor * (self.rate - 0.5 * self.sigma**2))
 
        if self.callPut == 'Call':
            calc[:,1] = mult * np.exp(np.sqrt((self.sigma**2)*self.tenor) * rand) - self.strike
        elif self.callPut == 'Put':
            calc[:,1] = self.strike - mult*np.exp(np.sqrt((self.sigma**2) * self.tenor) * rand)
 
        avgPayOff = np.sum(np.amax(calc, axis=1)) / float(self.iterations)
  
        return np.exp(-self.rate * self.tenor) * avgPayOff
 
    def getBSPrice(self):
        """ Determine the option price using the exact Black-Scholes expression. """
        return blackScholesOptionPrice(self.callPut, self.spot, self.strike, self.tenor, self.rate, self.sigma)
 
    def applyPutCallParity(self, call):
        """ Make use of put-call parity to determine put price. """
        return self.strike * np.exp(-self.rate * self.tenor) - self.spot + call
