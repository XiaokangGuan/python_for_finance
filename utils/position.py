import logging


class Position:
    def __init__(self, symbol):
        self.symbol = symbol
        # Can be short position, where quantity is negative
        self.quantity = 0
        self.cost = 0
        self.realized_pnl = 0
        self.mtm = 0

    def __str__(self):
        return 'Position<symbol={}, quantity={}, cost={}, mtm={}, realized_pnl={}>'.format(
            self.symbol, self.quantity, self.cost, self.mtm, self.realized_pnl)

    def change(self, price, quantity, commission):
        """Position change should ONLY be triggered by order execution"""
        logging.info('Position: BEFORE: position={} CHANGE: price={}, quantity={}, commission={}'.format(
            self, price, quantity, commission))
        if quantity == 0:
            logging.error('Position: change: symbol={} Invalid quantity is 0'.format(self.symbol))
            raise Exception()
        if self.quantity * quantity >= 0:
            # Increasing position, either short or long, commission is included in position cost
            self.quantity += quantity
            self.cost += (price * quantity + commission)
        else:
            # Reducing position, either short or long, commission is included in realized_pnl
            self.realized_pnl += ((self.cost/self.quantity - price)*quantity - commission)
            self.cost += self.cost/self.quantity*quantity
            self.quantity += quantity
        logging.info('Position: AFTER: position={} CHANGE: price={}, quantity={}, commission={}'.format(
            self, price, quantity, commission))

    def update_mtm(self, price):
        """Update Position mtm based on given price marker"""
        #logging.info('Position mtm: BEFORE: position={} price={}'.format(self, price))
        self.mtm = self.quantity * price
        #logging.info('Position mtm: AFTER: position={} price={}'.format(self, price))

