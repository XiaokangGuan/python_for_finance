import uuid
import logging

ORDER_STATE_NEW = 'ORDER_STATE_NEW'
ORDER_STATE_PARTIALLY_FILLED = 'ORDER_STATE_PARTIALLY_FILLED'
ORDER_STATE_FULLY_FILLED = 'ORDER_STATE_FULLY_FILLED'
ORDER_STATE_CANCELLED = 'ORDER_STATE_CANCELLED'
ORDER_TYPE_MARKET = 'ORDER_TYPE_MARKET'
ORDER_TYPE_LIMIT = 'ORDER_TYPE_LIMIT'
ORDER_TYPE_STOP = 'ORDER_TYPE_STOP'
ORDER_DIRECTION_BUY = 'ORDER_DIRECTION_BUY'
ORDER_DIRECTION_SELL = 'ORDER_DIRECTION_SELL'

MIN_COMMISSION_PER_ORDER = 1
MAX_COMMISSION_PER_ORDER_PER_TRADE_VALUE = 0.005
COMMISSION_PER_SHARE = 0.005


class Order:
    def __init__(self, symbol, direction, type, price, quantity, open_dt_idx, pct_from_market=None,
                 valid_from_dt_idx=None, valid_to_dt_idx=None):
        self.order_id = uuid.uuid4()
        self.symbol = symbol
        self.direction = direction
        self.type = type
        # this is the price submitted when placing order
        self.price = price
        # this is the limit / stop percentage from market order execution price
        self.pct_from_market = pct_from_market
        # this is the average price filling the order
        self.fill_price = 0
        # this quantity should be non-negative
        self.quantity_outstanding = quantity
        self.quantity_filled = 0
        self.state = ORDER_STATE_NEW
        self.commission = 0
        self.link_id = None
        # this is when the order is created
        self.open_dt_idx = open_dt_idx
        # this is when the order is fully filled or cancelled
        self.close_dt_idx = None
        # Order executable period (inclusive). None means no bound.
        self.valid_from_dt_idx = valid_from_dt_idx
        self.valid_to_dt_idx = valid_to_dt_idx

    def __str__(self):
        return 'Order<order_id={}, symbol={}, direction={}, type={}, price={}, pct_from_market={}, fill_price={}, ' \
               'quantity_outstanding={}, quantity_filled={}, state={}, commission={}, link_id={}, open_dt_idx={}, ' \
               'close_dt_idx={}>, valid_from_dt_idx={},valid_to_dt_idx={}'.format(
            self.order_id, self.symbol, self.direction, self.type, self.price, self.pct_from_market, self.fill_price,
            self.quantity_outstanding, self.quantity_filled, self.state, self.commission, self.link_id, self.open_dt_idx,
            self.close_dt_idx, self.valid_from_dt_idx, self.valid_to_dt_idx)

    def calculate_commission(self):
        """Calculate commission for this order, commission is only incurred on fully filled"""
        min_commission = MIN_COMMISSION_PER_ORDER
        maxCommission = MAX_COMMISSION_PER_ORDER_PER_TRADE_VALUE * (self.fill_price * self.quantity_filled)
        commission = COMMISSION_PER_SHARE * self.quantity_filled
        self.commission = max(min(commission, maxCommission), min_commission)

    def fill(self, fill_price, quantity, datetime):
        logging.info('Order: fill: BEFORE: order={} CHANGE: fill_price={}, quantity={}, datetime={}'.format(
            self, fill_price, quantity, datetime))
        if quantity > self.quantity_outstanding or quantity <= 0:
            logging.error('Order: fill: order_id={} Invalid quantity={}!'.format(self.order_id, quantity))
            raise Exception()
        self.fill_price = (self.fill_price * self.quantity_filled + fill_price * quantity) / (self.quantity_filled + quantity)
        self.quantity_filled += quantity
        self.quantity_outstanding -= quantity
        if self.quantity_outstanding > 0:
            self.state = ORDER_STATE_PARTIALLY_FILLED
        elif self.quantity_outstanding == 0:
            self.state = ORDER_STATE_FULLY_FILLED
            self.close_dt_idx = datetime
            self.calculate_commission()
        logging.info('Order: fill: AFTER: order={} CHANGE: fill_price={}, quantity={}, datetime={}'.format(
            self, fill_price, quantity, datetime))

    def cancel(self, datetime):
        logging.info('Order: cancel: BEFORE: order={} CHANGE: datetime={}'.format(self, datetime))
        self.state = ORDER_STATE_CANCELLED
        self.close_dt_idx = datetime
        logging.info('Order: cancel: AFTER: order={} CHANGE: datetime={}'.format(self, datetime))
