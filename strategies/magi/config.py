import logging
import yaml

SD_PERIOD = 66
# This is for trading signal logic
LOOK_BACK_PERIOD = 22
# This allows to trade on next day's open
LOOK_FORWARD_PERIOD = 0
MA_SHORT_PERIOD = 5
MA_LONG_PERIOD = SD_PERIOD
TRIGGER_DISTANCE = 3
STOP_ORDER_DISTANCE = 1
LIMIT_ORDER_DISTANCE = 1
ORDER_LIMIT = 1000
LIMIT_ORDER_PCT = 0.2
STOP_ORDER_PCT = -0.2


class Config:
    def __init__(self,
                 symbols=[],
                 sd_period=SD_PERIOD,
                 look_back_period=LOOK_BACK_PERIOD,
                 look_forward_period=LOOK_FORWARD_PERIOD,
                 ma_short_period=MA_SHORT_PERIOD,
                 ma_long_period=MA_LONG_PERIOD,
                 trigger_distance=TRIGGER_DISTANCE,
                 stop_order_distance=STOP_ORDER_DISTANCE,
                 limit_order_distance=LIMIT_ORDER_DISTANCE,
                 order_limit=ORDER_LIMIT,
                 limit_order_pct=LIMIT_ORDER_PCT,
                 stop_order_pct=STOP_ORDER_PCT):
        self.symbols = symbols
        self.sd_period = sd_period
        self.look_back_period = look_back_period
        self.look_forward_period = look_forward_period
        self.ma_short_period = ma_short_period
        self.ma_long_period = ma_long_period
        self.trigger_distance = trigger_distance
        self.stop_order_distance = stop_order_distance
        self.limit_order_distance = limit_order_distance
        self.order_limit = order_limit
        self.limit_order_pct = limit_order_pct
        self.stop_order_pct = stop_order_pct

    def log(self):
        logging.info('============================================================')
        logging.info('Magi strategy config:')
        logging.info('SYMBOLS: {}'.format(self.symbols))
        logging.info('SD_PERIOD: {}'.format(self.sd_period))
        logging.info('LOOK_BACK_PERIOD: {}'.format(self.look_back_period))
        logging.info('LOOK_FORWARD_PERIOD: {}'.format(self.look_forward_period))
        logging.info('MA_SHORT_PERIOD: {}'.format(self.ma_short_period))
        logging.info('MA_LONG_PERIOD: {}'.format(self.ma_long_period))
        logging.info('TRIGGER_DISTANCE: {}'.format(self.trigger_distance))
        logging.info('STOP_ORDER_DISTANCE: {}'.format(self.stop_order_distance))
        logging.info('LIMIT_ORDER_DISTANCE: {}'.format(self.limit_order_distance))
        logging.info('ORDER_LIMIT: {}'.format(self.order_limit))
        logging.info('LIMIT_ORDER_PCT: {}'.format(self.limit_order_pct))
        logging.info('STOP_ORDER_PCT: {}'.format(self.stop_order_pct))
        logging.info('============================================================')

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k in dir(self):
                setattr(self, k, v)

    def save(self, name):
        with open(f'models/{name}.yml', 'w') as file:
            yaml.dump(vars(self), file, default_flow_style=False)

    def load(self, name):
        with open(f'models/{name}.yml') as file:
            documents = yaml.full_load(file)
        self.update(**documents)
