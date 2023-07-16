
class MarketTick:
    """
    MarketTick is symbol specific, which simulates the real-time market data tick.
    In reality, different symbols may tick at different time.
    """
    def __init__(self, symbol, open, close, high, low, volume, dt_idx):
        self.symbol = symbol
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume
        self.dt_idx = dt_idx

    def __str__(self):
        return 'MarketTick<symbol={}, open={}, close={}, high={}, low={}, volume={}, dt_idx={}>'.format(
            self.symbol, self.open, self.close, self.high, self.low, self.volume, self.dt_idx)
