import numpy as np
import math


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
            return self.getBlackScholesPrice()
 
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
 
    def getBlackScholesPrice(self):
        """ Determine the option price using the exact Black-Scholes expression. """
        d1 = (np.log(self.spot/self.strike) + (self.rate + 0.5*self.sigma**2) * self.tenor) / (self.sigma * np.sqrt(self.tenor))
        d2 = d1 - self.sigma * np.sqrt(self.tenor)
 
        call = self.spot * self.ncdf(d1) - self.strike * np.exp(-self.rate * self.tenor) * self.ncdf(d2)
 
        if self.callPut == 'Call':
            return call
        elif self.callPut == 'Put':
            return self.applyPutCallParity(call)
 
    def ncdf(self, x):
        """ Cumulative distribution function for the standard normal distribution. """
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
 
    def applyPutCallParity(self, call):
        """ Make use of put-call parity to determine put price. """
        return self.strike * np.exp(-self.rate * self.tenor) - self.spot + call
