import uuid
import logging
import datetime
from utils.order import ORDER_STATE_NEW, ORDER_STATE_PARTIALLY_FILLED, ORDER_STATE_FULLY_FILLED, ORDER_STATE_CANCELLED, \
    ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, ORDER_TYPE_STOP, ORDER_DIRECTION_BUY, ORDER_DIRECTION_SELL
from utils.position import Position
from utils.portfolio import Portfolio
from utils.performance import Performance


class xMan:
    def __init__(self, initial_capital):
        self.orders = []
        self.positions = []
        self.portfolio = Portfolio(initial_capital)
        self.symbol_performances = []
        self.initial_capital = initial_capital
        self.portfolio_max_capital_required = 0
        self.portfolio_success = 0
        self.portfolio_failure = 0
        self.portfolio_total_trade_life = datetime.timedelta()

    def place_order(self, order):
        self.orders.append(order)

    def get_order_by_order_id(self, order_id):
        """Return a single order or None given the unique order_id"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        logging.debug('xMan: get_order_by_order_id: No order found for order_id={}'.format(order_id))

    def get_orders_by_link_id(self, link_id):
        """Return a list of orders given the link_id"""
        orders = []
        for order in self.orders:
            if order.link_id and order.link_id == link_id:
                orders.append(order)
        return orders

    def get_orders_by_symbol(self, symbol):
        """Return a list of orders given the symbol"""
        orders = []
        for order in self.orders:
            if order.symbol == symbol:
                orders.append(order)
        return orders

    def get_position_by_symbol(self, symbol):
        for position in self.positions:
            if position.symbol == symbol:
                return position
        logging.debug('xMan: get_position_by_symbol: No position found for symbol={}'.format(symbol))

    def get_performance_by_symbol(self, symbol):
        for performance in self.symbol_performances:
            if performance.symbol == symbol:
                return performance
        logging.debug('xMan: get_performance_by_symbol: No position found for symbol={}'.format(symbol))

    def execute_market_order(self, order, market_tick):
        """Execute market order, update position"""
        logging.debug('xMan: execute_market_order: Check order={}, market_tick={}'.format(order, market_tick))
        # We always fully fill market orders
        quantity_changed = order.quantity_outstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantity_outstanding
        order.fill(market_tick.open, order.quantity_outstanding, market_tick.dt_idx)
        if order.state == ORDER_STATE_FULLY_FILLED:
            self.cancel_linked_orders(order, market_tick.dt_idx)

        position = self.get_position_by_symbol(order.symbol)
        if not position:
            position = Position(order.symbol)
            self.positions.append(position)
        position.change(market_tick.open, quantity_changed, order.commission)

    def execute_limit_order(self, order, market_tick):
        """Execute limit order, update position"""
        logging.debug('xMan: execute_limit_order: Check order={}, market_tick={}'.format(order, market_tick))
        if (order.direction == ORDER_DIRECTION_BUY and order.price >= market_tick.low) or (
                order.direction == ORDER_DIRECTION_SELL and order.price <= market_tick.high):
            quantity_changed = order.quantity_outstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantity_outstanding
            order.fill(order.price, order.quantity_outstanding, market_tick.dt_idx)
            if order.state == ORDER_STATE_FULLY_FILLED:
                self.cancel_linked_orders(order, market_tick.dt_idx)

            position = self.get_position_by_symbol(order.symbol)
            if not position:
                position = Position(order.symbol)
                self.positions.append(position)
            position.change(order.price, quantity_changed, order.commission)

    def execute_stop_order(self, order, market_tick):
        """Execute stop order, update position"""
        logging.debug('xMan: execute_stop_order: Check order={}, market_tick={}'.format(order, market_tick))
        if (order.direction == ORDER_DIRECTION_BUY and order.price <= market_tick.high) or (
                order.direction == ORDER_DIRECTION_SELL and order.price >= market_tick.low):
            quantity_changed = order.quantity_outstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantity_outstanding
            order.fill(order.price, order.quantity_outstanding, market_tick.dt_idx)
            if order.state == ORDER_STATE_FULLY_FILLED:
                self.cancel_linked_orders(order, market_tick.dt_idx)

            position = self.get_position_by_symbol(order.symbol)
            if not position:
                position = Position(order.symbol)
                self.positions.append(position)
            position.change(order.price, quantity_changed, order.commission)

    def execute_orders_on_market_tick(self, market_tick):
        for order in self.get_orders_by_symbol(market_tick.symbol):
            if order.state in [ORDER_STATE_FULLY_FILLED, ORDER_STATE_CANCELLED]:
                continue
            if order.type == ORDER_TYPE_MARKET:
                self.execute_market_order(order, market_tick)
            # TODO: We execute stop order ahead of limit order, limit order can possibly be cancelled before filled
            elif order.type == ORDER_TYPE_STOP:
                self.execute_stop_order(order, market_tick)
            elif order.type == ORDER_TYPE_LIMIT:
                self.execute_limit_order(order, market_tick)
            else:
                logging.error('xMan: execute_orders_on_market_tick: Unsupported order type {}'.format(order))

    def update_mtm_on_market_tick(self, market_tick):
        position = self.get_position_by_symbol(market_tick.symbol)
        if not position:
            position = Position(market_tick.symbol)
            self.positions.append(position)
        position.update_mtm(market_tick.close)

    def run_on_market_ticks(self, market_ticks_by_symbol):
        for symbol, market_tick in market_ticks_by_symbol.items():
            # Execute existing orders from previous tradingPeriod. In reality, this happens during current tradingPeriod.
            self.execute_orders_on_market_tick(market_tick)
            # Update Position and Portfolio MTM using Close price. In reality, this happens at end of current trading Period.
            self.update_mtm_on_market_tick(market_tick)
            # Refresh portfolio
            self.portfolio.refresh(self.positions)

    def cancel_linked_orders(self, order, datetime):
        """If one order get fully filled, other linked orders will be cancelled"""
        linked_orders = self.get_orders_by_link_id(order.link_id)
        for linkedOrder in linked_orders:
            if linkedOrder.order_id != order.order_id:
                linkedOrder.cancel(datetime)

    def link_orders(self, orders):
        """If one order get fully filled, other linked orders will be cancelled"""
        link_id = uuid.uuid4()
        for order in orders:
            order.link_id = link_id
        logging.debug(
            'xMan: link_orders: Linked order_ids={}, link_id={}'.format([order.order_id for order in orders], link_id))

    def get_all_symbols(self):
        """Get all symbols ever executed"""
        order_symbols = [order.symbol for order in self.orders]
        position_symbols = [position.symbol for position in self.positions]
        return list(set(order_symbols + position_symbols))

    def evaluate_performance(self):
        self.portfolio_success = 0
        self.portfolio_failure = 0
        self.portfolio_total_trade_life = datetime.timedelta()
        for symbol in self.get_all_symbols():
            outstanding_market_orders, outstanding_stop_orders, outstanding_limit_orders, filled_market_orders, \
            filled_stop_orders, filled_limit_orders, cancelled_market_orders, cancelled_stop_orders, \
            cancelled_limit_orders = 0, 0, 0, 0, 0, 0, 0, 0, 0
            total_trade_life = datetime.timedelta()
            for order in self.get_orders_by_symbol(symbol):
                if order.state in [ORDER_STATE_PARTIALLY_FILLED, ORDER_STATE_NEW]:
                    if order.type == ORDER_TYPE_MARKET:
                        outstanding_market_orders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        outstanding_stop_orders += 1
                    elif order.type == ORDER_TYPE_LIMIT:
                        outstanding_limit_orders += 1
                elif order.state == ORDER_STATE_FULLY_FILLED:
                    if order.type == ORDER_TYPE_MARKET:
                        filled_market_orders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        filled_stop_orders += 1
                        total_trade_life += (order.close_dt_idx.to_pydatetime() - order.open_dt_idx.to_pydatetime())
                    elif order.type == ORDER_TYPE_LIMIT:
                        filled_limit_orders += 1
                        total_trade_life += (order.close_dt_idx.to_pydatetime() - order.open_dt_idx.to_pydatetime())
                elif order.state == ORDER_STATE_CANCELLED:
                    if order.type == ORDER_TYPE_MARKET:
                        cancelled_market_orders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        cancelled_stop_orders += 1
                    elif order.type == ORDER_TYPE_LIMIT:
                        cancelled_limit_orders += 1
            position = self.get_position_by_symbol(symbol)
            if not position:
                position = Position(symbol)
                self.positions.append(position)
            symbol_performance = self.get_performance_by_symbol(symbol)
            if not symbol_performance:
                symbol_performance = Performance(symbol)
                self.symbol_performances.append(symbol_performance)
            success = filled_limit_orders
            failure = filled_stop_orders
            max_capital_required = max(symbol_performance.max_capital_required, position.cost)
            symbol_performance.update_performance(
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
                position.realized_pnl,
                position.quantity,
                position.cost,
                position.mtm,
                total_trade_life)
            logging.info('xMan: evaluate_performance: Symbol performance={}'.format(symbol_performance))
            self.portfolio_success += success
            self.portfolio_failure += failure
            self.portfolio_total_trade_life += total_trade_life
        self.portfolio_max_capital_required = max(self.portfolio_max_capital_required, self.portfolio.position_cost)

        logging.info('xMan: evaluate_performance: Portfolio portfolio realized_pnl={}, portfolio cash_balance={}, \
        portfolio position_cost={}, portfolio position_mtm={}, portfolio_max_capital_required={}, portfolio_success={}, \
        portfolio_failure={}, portfolio_successRate={:.2f}%, portfolio_average_trade_ife={}'.format(
            self.portfolio.realized_pnl,
            self.portfolio.cash_balance,
            self.portfolio.position_cost,
            self.portfolio.position_mtm,
            self.portfolio_max_capital_required,
            self.portfolio_success,
            self.portfolio_failure,
            (float(self.portfolio_success) * 100) / (
                        self.portfolio_success + self.portfolio_failure) if self.portfolio_success + self.portfolio_failure else float(
                'nan'),
            self.portfolio_total_trade_life / (
                        self.portfolio_success + self.portfolio_failure) if self.portfolio_success + self.portfolio_failure > 0 else 'No Trades'))

    def describe_trades_executed_by_datetime(self):
        result = dict()
        for order in self.orders:
            if order.state == ORDER_STATE_FULLY_FILLED:
                daycounts = result.get(order.close_dt_idx, dict())
                count = daycounts.get(order.type, 0)
                daycounts[order.type] = count + 1
                result[order.close_dt_idx] = daycounts
        logging.info('============================================================')
        logging.info('Trades Execution Summary for all dates')
        logging.info('------------------------------------------------------------')
        keys = list(result.keys())
        keys.sort()
        for dt in keys:
            logging.info('xMan: describeTradesExecutedByDatetime: {}: {}'.format(dt, result.get(dt, 'ERROR')))
        logging.info('============================================================')
