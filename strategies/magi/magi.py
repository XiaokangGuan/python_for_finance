from utils.order import Order, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, ORDER_TYPE_STOP, ORDER_DIRECTION_BUY, ORDER_DIRECTION_SELL
import logging
import math
import pandas


class Magi:
    def __init__(self,
                 capital,
                 x_man,
                 config,
                 trading_calendar,
                 model_name):
        self.capital = capital
        self.x_man = x_man
        self.symbol_data = dict()
        self.capital_used = 0
        self.trading_calendar = trading_calendar
        self.model_name = model_name

        # Strategy config
        self.config = config
        self.config.log()

        # Model map
        self.MODEL_MAP = {
            'focus_stock': self._run_mispricing,
            'price_mean_reversion': self._run_price_mean_reversion,
        }

    def __str__(self):
        return 'He is my shield!'

    def get_start_index(self):
        return max(self.config.sd_period,
                   self.config.look_back_period,
                   self.config.ma_short_period,
                   self.config.ma_long_period)

    def get_order_size(self, price):
        """Estimate the order size based on the current price and order limit"""
        # Limit the max allowed portfolio exposure (i.e. MTM) by initialCapital and available cash and manual limit.
        # TODO: Need smarter way of allocating to stocks, i.e. order_limit
        limit = max(0, 
                    min(self.capital - self.x_man.portfolio.position_mtm - self.capital_used,
                        self.x_man.portfolio.cash_balance - self.capital_used,
                        self.config.order_limit))
        return math.floor(limit / price)

    def get_stop_pct_from_market(self, ma, sd):
        """
        If stop_order_pct is manually set, then take it.
        Otherwise calculate from stop_order_distance.
        """
        if self.config.stop_order_pct is not None:
            return self.config.stop_order_pct
        else:
            return - self.config.stop_order_distance * sd / ma

    def get_limit_pct_from_market(self, ma, sd):
        """
        If limit_order_pct is manually set, then take it.
        Otherwise calculate from limit_order_distance.
        """
        if self.config.limit_order_pct is not None:
            return self.config.limit_order_pct
        else:
            return self.config.limit_order_distance * sd / ma

    def _run_mispricing(self, market_tick):
        """
        Run strategy for the market_tick given for a specific symbol.
        Signal is based on daily price returns.
        The strategy probably also depends on past market_ticks, which need to be looked up in self.symbol_data
        Place orders based on strategy signals
        """
        # Update timeseries on daily market_tick Close
        ts = pandas.Series(data=[market_tick.close_return], index=[market_tick.dt_idx])
        if self.symbol_data.get(market_tick.symbol, None) is None:
            self.symbol_data[market_tick.symbol] = ts
        else:
            ts_new = pandas.concat([self.symbol_data[market_tick.symbol], ts])
            self.symbol_data[market_tick.symbol] = ts_new

        # Check if enough data for running strategy
        ts = self.symbol_data[market_tick.symbol]
        if len(ts) < self.get_start_index() + 1:
            logging.debug('Magi: run: dt_idx={}: Not enough data to run Magi.'.format(market_tick.dt_idx))
            return

        # Calculate signal metrics
        sd = ts[:market_tick.dt_idx][-self.config.sd_period:].std()
        highest = ts[:market_tick.dt_idx][-self.config.look_back_period:].max()
        lowest = ts[:market_tick.dt_idx][-self.config.look_back_period:].min()
        ma_short = ts[:market_tick.dt_idx][-self.config.ma_short_period:].mean()
        ma_long = ts[:market_tick.dt_idx][-self.config.ma_long_period:].mean()
        curr_price = market_tick.close
        curr_return = market_tick.close_return

        logging.info('Magi: run_strategy_on_market_tick: curr_price={}, curr_return={}, ma_long={}, sd={}, distance={}, ma_short={}'.format(curr_price, curr_return, ma_long, sd, (curr_return - ma_long) / sd, ma_short))
        if curr_return < ma_long - sd * self.config.trigger_distance:
            quantity = self.get_order_size(curr_price)

            # TODO: Without knowledge of the next market_tick, we place orders based on current market_tick
            if quantity > 0:
                market_order = Order(market_tick.symbol,
                                     ORDER_DIRECTION_BUY,
                                     ORDER_TYPE_MARKET,
                                     float('nan'),
                                     quantity,
                                     market_tick.dt_idx)
                self.x_man.place_order(market_order)
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY: Placed marketOrder={}'.format(market_order))

                # Idea is to manually close position next day, instead of replying on Limit / Stop orders
                close_market_order = Order(market_tick.symbol,
                                           ORDER_DIRECTION_SELL,
                                           ORDER_TYPE_MARKET,
                                           float('nan'),
                                           quantity,
                                           market_tick.dt_idx,
                                           valid_from_dt_idx=self.trading_calendar[self.trading_calendar.index(market_tick.dt_idx)+2],
                                           valid_to_dt_idx=None)
                self.x_man.place_order(close_market_order)
                logging.info('Magi: run_strategy_on_market_tick: Placed close_market_order={}'.format(close_market_order))

                self.x_man.link_orders([market_order, close_market_order])

                # Update daily capital used
                self.capital_used += quantity * curr_price
            else:
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY, but cannot trade due to quantity=0, market_tick={}'.format(market_tick))

    def _run_price_mean_reversion(self, market_tick):
        """
        Run strategy for the market_tick given for a specific symbol.
        Signal is based on daily stock price.
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
            return

        # Calculate signal metrics
        sd = ts[:market_tick.dt_idx][-self.config.sd_period:].std()
        highest = ts[:market_tick.dt_idx][-self.config.look_back_period:].max()
        lowest = ts[:market_tick.dt_idx][-self.config.look_back_period:].min()
        ma_short = ts[:market_tick.dt_idx][-self.config.ma_short_period:].mean()
        ma_long = ts[:market_tick.dt_idx][-self.config.ma_long_period:].mean()
        curr_price = market_tick.close
        curr_return = market_tick.close_return

        logging.info('Magi: run_strategy_on_market_tick: curr_price={}, curr_return={}, ma_long={}, sd={}, distance={}, ma_short={}'.format(curr_price, curr_return, ma_long, sd, (curr_price - ma_long) / sd, ma_short))
        if curr_price < ma_long - sd * self.config.trigger_distance:
            quantity = self.get_order_size(curr_price)

            # TODO: Without knowledge of the next market_tick, we place orders based on current market_tick
            if quantity > 0:
                market_order = Order(market_tick.symbol,
                                     ORDER_DIRECTION_BUY,
                                     ORDER_TYPE_MARKET,
                                     float('nan'),
                                     quantity,
                                     market_tick.dt_idx)
                self.x_man.place_order(market_order)
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY: Placed marketOrder={}'.format(market_order))

                stop_order = Order(market_tick.symbol,
                                   ORDER_DIRECTION_SELL,
                                   ORDER_TYPE_STOP,
                                   float('nan'),
                                   quantity,
                                   market_tick.dt_idx,
                                   pct_from_market=self.get_stop_pct_from_market(ma_long, sd))
                self.x_man.place_order(stop_order)
                logging.info('Magi: run_strategy_on_market_tick: Placed stop_order={}'.format(stop_order))

                limit_order = Order(market_tick.symbol,
                                    ORDER_DIRECTION_SELL,
                                    ORDER_TYPE_LIMIT,
                                    float('nan'),
                                    quantity,
                                    market_tick.dt_idx,
                                    pct_from_market=self.get_limit_pct_from_market(ma_long, sd))
                self.x_man.place_order(limit_order)
                logging.info('Magi: run_strategy_on_market_tick: Placed limit_order={}'.format(limit_order))

                self.x_man.link_orders([market_order, stop_order, limit_order])

                # Update daily capital used
                self.capital_used += quantity * curr_price
            else:
                logging.info('Magi: run_strategy_on_market_tick: TRIGGER BUY, but cannot trade due to quantity=0, market_tick={}'.format(market_tick))

    def run_on_market_ticks(self, market_ticks_by_symbol):
        self.capital_used = 0
        for symbol, market_tick in market_ticks_by_symbol.items():
            if symbol in self.config.symbols:
                self.MODEL_MAP[self.model_name](market_tick)
