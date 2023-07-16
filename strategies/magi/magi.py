from utils.order import Order, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, ORDER_TYPE_STOP, ORDER_DIRECTION_BUY, ORDER_DIRECTION_SELL
import logging
import math
import pandas

SD_PERIOD = 22
# This is for trading signal logic
LOOK_BACK_PERIOD = 22
# This allows to trade on next day's open
LOOK_FORWARD_PERIOD = 0
MA_SHORT_PERIOD = 5
MA_LONG_PERIOD = SD_PERIOD
TRIGGER_DISTANCE = 3
STOP_ORDER_DISTANCE = 2
LIMIT_ORDER_DISTANCE = 2
ORDER_LIMIT = 1000


class Magi:
    def __init__(self,
                 capital,
                 x_man,
                 sd_period=SD_PERIOD,
                 look_back_period=LOOK_BACK_PERIOD,
                 look_forward_period=LOOK_FORWARD_PERIOD,
                 ma_short_period=MA_SHORT_PERIOD,
                 ma_long_period=MA_LONG_PERIOD,
                 trigger_distance=TRIGGER_DISTANCE,
                 stop_order_distance=STOP_ORDER_DISTANCE,
                 limit_order_distance=LIMIT_ORDER_DISTANCE,
                 order_limit=ORDER_LIMIT,):
        self.capital = capital
        self.x_man = x_man
        self.symbol_data = dict()
        self.capital_used = 0
        # Strategy config
        self.sd_period = sd_period
        self.look_back_period = look_back_period
        self.look_forward_period = look_forward_period
        self.ma_short_period = ma_short_period
        self.ma_long_period = ma_long_period
        self.trigger_distance = trigger_distance
        self.stop_order_distance = stop_order_distance
        self.limit_order_distance = limit_order_distance
        self.order_limit = order_limit

        self.log_config()

    def __str__(self):
        return 'He is my shield!'

    def log_config(self):
        logging.info('============================================================')
        logging.info('Magi strategy config:')
        logging.info('SD_PERIOD: {}'.format(self.sd_period))
        logging.info('LOOK_BACK_PERIOD: {}'.format(self.look_back_period))
        logging.info('LOOK_FORWARD_PERIOD: {}'.format(self.look_forward_period))
        logging.info('MA_SHORT_PERIOD: {}'.format(self.ma_short_period))
        logging.info('MA_LONG_PERIOD: {}'.format(self.ma_long_period))
        logging.info('TRIGGER_DISTANCE: {}'.format(self.trigger_distance))
        logging.info('STOP_ORDER_DISTANCE: {}'.format(self.stop_order_distance))
        logging.info('LIMIT_ORDER_DISTANCE: {}'.format(self.limit_order_distance))
        logging.info('ORDER_LIMIT: {}'.format(self.order_limit))
        logging.info('============================================================')

    def get_start_index(self):
        return max(self.sd_period, self.look_back_period, self.ma_short_period, self.ma_long_period)

    def get_order_size(self, price):
        """Estimate the order size based on the current price and order limit"""
        # Limit the max allowed portfolio exposure (i.e. MTM) by initialCapital and available cash and manual limit.
        # TODO: Need smarter way of allocating to stocks, i.e. order_limit
        limit = max(0, 
                    min(self.capital - self.x_man.portfolio.position_mtm - self.capital_used,
                        self.x_man.portfolio.cash_balance - self.capital_used,
                        self.order_limit))
        return math.floor(limit / price)

    def run_strategy_on_market_tick(self, market_tick):
        """
        Run strategy for the market_tick given for a specific symbol.
        The strategy probably also depends on past market_ticks, which need to be looked up in self.symbol_data
        Place orders based on strategy signals
        """
        # Update timeseries on daily market_tick Close
        ts = pandas.Series(data=[market_tick.close], index=[market_tick.dt_idx])
        if self.symbol_data.get(market_tick.symbol, None) is None:
            self.symbol_data[market_tick.symbol] = ts
        else:
            ts_new = pandas.concat([self.symbol_data[market_tick.symbol], ts])
            self.symbol_data[market_tick.symbol] = ts_new

        # Check if enough data for running strategy
        ts = self.symbol_data[market_tick.symbol]
        if len(ts) < self.get_start_index() + 1:
            logging.debug('Magi: run: dt_idx={}: Not enough data to run Magi.'.format(market_tick.dt_idx))

        # Calculate signal metrics
        sd = ts[:market_tick.dt_idx][-self.sd_period:].std()
        highest = ts[:market_tick.dt_idx][-self.look_back_period:].max()
        lowest = ts[:market_tick.dt_idx][-self.look_back_period:].min()
        ma_short = ts[:market_tick.dt_idx][-self.ma_short_period:].mean()
        ma_long = ts[:market_tick.dt_idx][-self.ma_long_period:].mean()
        curr_price = market_tick.close

        if curr_price < highest - sd * self.trigger_distance and curr_price >= ma_short:
            quantity = self.get_order_size(curr_price)
            #TODO: Without knowledge of the next market_tick, we place orders based on current market_tick
            if quantity > 0:
                market_order = Order(market_tick.symbol, ORDER_DIRECTION_BUY, ORDER_TYPE_MARKET, float('nan'), quantity, market_tick.dt_idx)
                self.x_man.place_order(market_order)
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY: Placed marketOrder={}'.format(market_order))
                stop_order = Order(market_tick.symbol, ORDER_DIRECTION_SELL, ORDER_TYPE_STOP, curr_price-sd*self.stop_order_distance, quantity, market_tick.dt_idx)
                limit_order = Order(market_tick.symbol, ORDER_DIRECTION_SELL, ORDER_TYPE_LIMIT, curr_price + sd * self.limit_order_distance, quantity, market_tick.dt_idx)
                self.x_man.link_orders([stop_order, limit_order])
                self.x_man.place_order(stop_order)
                logging.info('Magi: run_strategy_on_market_tick: Placed stop_order={}'.format(stop_order))
                self.x_man.place_order(limit_order)
                logging.info('Magi: run_strategy_on_market_tick: Placed limit_order={}'.format(limit_order))
                
                # Update daily capital used
                self.capital_used += quantity * curr_price
            else:
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY, but cannot trade due to quantity=0, market_tick={}'.format(market_tick))

    def run_on_market_ticks(self, market_ticks_by_symbol):
        self.capital_used = 0
        for symbol, market_tick in market_ticks_by_symbol.items():
            self.run_strategy_on_market_tick(market_tick)
