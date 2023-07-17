import datetime


class Performance:
    """Performance metrics for each symbol"""

    def __init__(self, symbol):
        self.symbol = symbol
        self.outstanding_market_orders = 0
        self.outstanding_stop_orders = 0
        self.outstanding_limit_orders = 0
        self.filled_market_orders = 0
        self.filled_stop_orders = 0
        self.filled_limit_orders = 0
        self.cancelled_market_orders = 0
        self.cancelled_stop_orders = 0
        self.cancelled_limit_orders = 0
        self.success = 0
        self.failure = 0
        self.max_capital_required = 0
        self.realized_pnl = 0
        self.position_quantity = 0
        self.position_cost = 0
        self.position_mtm = 0
        self.total_trade_life = datetime.timedelta()

    def __str__(self):
        return 'Performance<symbol={}, outstanding_market_orders={}, outstanding_stop_orders={}, ' \
               'outstanding_limit_orders={}, filled_market_orders={}, filled_stop_orders={}, filled_limit_orders={}, ' \
               'cancelled_market_orders={}, cancelled_stop_orders={}, cancelled_limit_orders={}, success={}, ' \
               'failure={}, successRate={:.2f}%, max_capital_required={}, realized_pnl={}, position_quantity={}, ' \
               'position_cost={}, position_mtm={}, total_trade_life={}, averageTradeLife={}>'.format(
            self.symbol,
            self.outstanding_market_orders,
            self.outstanding_stop_orders,
            self.outstanding_limit_orders,
            self.filled_market_orders,
            self.filled_stop_orders,
            self.filled_limit_orders,
            self.cancelled_market_orders,
            self.cancelled_stop_orders,
            self.cancelled_limit_orders,
            self.success, self.failure,
            float(self.success * 100) / (self.success + self.failure) if self.success + self.failure > 0 else float('nan'),
            self.max_capital_required,
            self.realized_pnl,
            self.position_quantity,
            self.position_cost,
            self.position_mtm,
            self.total_trade_life,
            self.total_trade_life / (self.success + self.failure) if self.success + self.failure > 0 else 'No Trades')

    def update_performance(self,
                           outstanding_market_orders,
                           outstanding_stop_orders,
                           outstanding_limit_orders,
                           filled_market_orders,
                           filled_stop_orders,
                           filled_limit_orders,
                           cancelled_market_orders,
                           cancelled_stop_orders,
                           cancelled_limit_orders,
                           success,
                           failure,
                           max_capital_required,
                           realized_pnl,
                           position_quantity,
                           position_cost,
                           position_mtm,
                           total_trade_life):
        self.outstanding_market_orders = outstanding_market_orders
        self.outstanding_stop_orders = outstanding_stop_orders
        self.outstanding_limit_orders = outstanding_limit_orders
        self.filled_market_orders = filled_market_orders
        self.filled_stop_orders = filled_stop_orders
        self.filled_limit_orders = filled_limit_orders
        self.cancelled_market_orders = cancelled_market_orders
        self.cancelled_stop_orders = cancelled_stop_orders
        self.cancelled_limit_orders = cancelled_limit_orders
        self.success = success
        self.failure = failure
        self.max_capital_required = max_capital_required
        self.realized_pnl = realized_pnl
        self.position_quantity = position_quantity
        self.position_cost = position_cost
        self.position_mtm = position_mtm
        self.total_trade_life = total_trade_life
