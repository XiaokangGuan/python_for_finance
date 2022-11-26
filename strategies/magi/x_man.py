import uuid
import logging
import datetime

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
    def __init__(self, symbol, direction, type, price, quantity, openDtIdx):
        self.orderId = uuid.uuid4()
        self.symbol = symbol
        self.direction = direction
        self.type = type
        # this is the price submitted when placing order
        self.price = price
        # this is the average price filling the order
        self.fillPrice = 0
        # this quantity should be non-negative
        self.quantityOutstanding = quantity
        self.quantityFilled = 0
        self.state = ORDER_STATE_NEW
        self.commission = 0
        self.linkId = None
        # this is when the order is created
        self.openDtIdx = openDtIdx
        # this is when the order is fully filled or cancelled
        self.closeDtIdx = None

    def __str__(self):
        return 'Order<orderId={}, symbol={}, direction={}, type={}, price={}, fillPrice={}, quantityOutstanding={}, quantityFilled={}, state={}, commission={}, linkId={}, openDtIdx={}, closeDtIdx={}>'.format(self.orderId, self.symbol, self.direction, self.type, self.price, self.fillPrice, self.quantityOutstanding, self.quantityFilled, self.state, self.commission, self.linkId, self.openDtIdx, self.closeDtIdx)

    def calculateCommission(self):
        """Calculate commission for this order, commission is only incurred on fully filled"""
        minCommission = MIN_COMMISSION_PER_ORDER
        maxCommission = MAX_COMMISSION_PER_ORDER_PER_TRADE_VALUE * (self.fillPrice * self.quantityFilled)
        commission = COMMISSION_PER_SHARE * self.quantityFilled
        self.commission = max(min(commission, maxCommission), minCommission)

    def fill(self, fillPrice, quantity, datetime):
        logging.info('Order: fill: BEFORE: order={} CHANGE: fillPrice={}, quantity={}, datetime={}'.format(self, fillPrice, quantity, datetime))
        if quantity > self.quantityOutstanding or quantity <= 0:
            logging.error('Order: fill: orderId={} Invalid quantity={}!'.format(self.orderId, quantity))
            raise Exception()
        self.fillPrice = (self.fillPrice * self.quantityFilled + fillPrice * quantity) / (self.quantityFilled + quantity)
        self.quantityFilled += quantity
        self.quantityOutstanding -= quantity
        if self.quantityOutstanding > 0:
            self.state = ORDER_STATE_PARTIALLY_FILLED
        elif self.quantityOutstanding == 0:
            self.state = ORDER_STATE_FULLY_FILLED
            self.closeDtIdx = datetime
            self.calculateCommission()
        logging.info('Order: fill: AFTER: order={} CHANGE: fillPrice={}, quantity={}, datetime={}'.format(self, fillPrice, quantity, datetime))

    def cancel(self, datetime):
        logging.info('Order: cancel: BEFORE: order={} CHANGE: datetime={}'.format(self, datetime))
        self.state = ORDER_STATE_CANCELLED
        self.closeDtIdx = datetime
        logging.info('Order: cancel: AFTER: order={} CHANGE: datetime={}'.format(self, datetime))


class Position:
    def __init__(self, symbol):
        self.symbol = symbol
        # Can be short position, where quantity is negative
        self.quantity = 0
        self.cost = 0
        self.realizedPNL = 0

    def __str__(self):
        return 'Position<symbol={}, quantity={}, cost={}, realizedPNL={}>'.format(self.symbol, self.quantity, self.cost, self.realizedPNL)

    def change(self, price, quantity, commission):
        """Position change should ONLY triggered by order execution"""
        logging.info('Position: BEFORE: position={} CHANGE: price={}, quantity={}, commission={}'.format(self, price, quantity, commission))
        if quantity == 0:
            logging.error('Position: change: symbol={} Invalid quantity is 0'.format(self.symbol))
            raise Exception()
        if self.quantity * quantity >= 0:
            # Increasing position, either short or long, commission is included in position cost
            self.quantity += quantity
            self.cost += (price * quantity + commission)
        else:
            # Reducing position, either short or long, commission is included in realizedPNL
            self.realizedPNL += ((self.cost/self.quantity - price)*quantity - commission)
            self.cost += self.cost/self.quantity*quantity
            self.quantity += quantity
        logging.info('Position: AFTER: position={} CHANGE: price={}, quantity={}, commission={}'.format(self, price, quantity, commission))


class MarketTick:
    """
    MarketTick is symbol specific, which simulates the real-time market data tick.
    In reality, different symbols may tick at different time.
    """
    def __init__(self, symbol, open, close, high, low, volume, dtIdx):
        self.symbol = symbol
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume
        self.dtIdx = dtIdx

    def __str__(self):
        return 'MarketTick<symbol={}, open={}, close={}, high={}, low={}, volume={}, dtIdx={}>'.format(self.symbol, self.open, self.close, self.high, self.low, self.volume, self.dtIdx)


class Performance:
    """Performance metrics for each symbol"""
    def __init__(self, symbol):
        self.symbol = symbol
        self.outstandingMarketOrders = 0
        self.outstandingStopOrders = 0
        self.outstandingLimitOrders = 0
        self.filledMarketOrders = 0
        self.filledStopOrders = 0
        self.filledLimitOrders = 0
        self.cancelledMarketOrders = 0
        self.cancelledStopOrders = 0
        self.cancelledLimitOrders = 0
        self.success = 0
        self.failure = 0
        self.maxCapitalRequired = 0
        self.realizedPNL = 0
        self.positionQuantity = 0
        self.positionCost = 0
        self.totalTradeLife = datetime.timedelta()

    def __str__(self):
        return 'Performance<symbol={}, outstandingMarketOrders={}, outstandingStopOrders={}, outstandingLimitOrders={}, filledMarketOrders={}, filledStopOrders={}, filledLimitOrders={}, cancelledMarketOrders={}, cancelledStopOrders={}, cancelledLimitOrders={}, success={}, failure={}, successRate={:.2f}%, maxCapitalRequired={}, realizedPNL={}, positionQuantity={}, positionCost={}, totalTradeLife={}, averageTradeLife={}>'.format(self.symbol, self.outstandingMarketOrders, self.outstandingStopOrders, self.outstandingLimitOrders, self.filledMarketOrders, self.filledStopOrders, self.filledLimitOrders, self.cancelledMarketOrders, self.cancelledStopOrders, self.cancelledLimitOrders, self.success, self.failure, float(self.success*100)/(self.success+self.failure) if self.success+self.failure > 0 else float('nan'), self.maxCapitalRequired, self.realizedPNL, self.positionQuantity, self.positionCost, self.totalTradeLife, self.totalTradeLife/(self.success+self.failure) if self.success+self.failure > 0 else 'No Trades')

    def updatePerformance(self, outstandingMarketOrders, outstandingStopOrders, outstandingLimitOrders, filledMarketOrders, filledStopOrders, filledLimitOrders, cancelledMarketOrders, cancelledStopOrders, cancelledLimitOrders, success, failure, maxCapitalRequired, realizedPNL, positionQuantity, positionCost, totalTradeLife):
        self.outstandingMarketOrders = outstandingMarketOrders
        self.outstandingStopOrders = outstandingStopOrders
        self.outstandingLimitOrders = outstandingLimitOrders
        self.filledMarketOrders = filledMarketOrders
        self.filledStopOrders = filledStopOrders
        self.filledLimitOrders = filledLimitOrders
        self.cancelledMarketOrders = cancelledMarketOrders
        self.cancelledStopOrders = cancelledStopOrders
        self.cancelledLimitOrders = cancelledLimitOrders
        self.success = success
        self.failure = failure
        self.maxCapitalRequired = maxCapitalRequired
        self.realizedPNL = realizedPNL
        self.positionQuantity = positionQuantity
        self.positionCost = positionCost
        self.totalTradeLife = totalTradeLife


class xMan:
    def __init__(self, initialCapital):
        self.orders = []
        self.positions = []
        self.performances = []
        self.portfolioRealizedPNL = 0
        self.portfolioCashBalance = initialCapital
        self.initialCapital = initialCapital
        self.portfolioPositionCost = 0
        self.portfolioMaxCapitalRequired = 0
        self.portfolioSuccess = 0
        self.portfolioFailure = 0

    def placeOrder(self, order):
        self.orders.append(order)

    def getOrderByOrderId(self, orderId):
        """Return a single order or None given the unique orderId"""
        for order in self.orders:
            if order.orderId == orderId:
                return order
        logging.debug('xMan: getOrderByOrderId: No order found for orderId={}'.format(orderId))

    def getOrdersByLinkId(self, linkId):
        """Return a list of orders given the linkId"""
        orders = []
        for order in self.orders:
            if order.linkId and order.linkId == linkId:
                orders.append(order)
        return orders

    def getOrdersBySymbol(self, symbol):
        """Return a list of orders given the symbol"""
        orders = []
        for order in self.orders:
            if order.symbol == symbol:
                orders.append(order)
        return orders

    def getPositionBySymbol(self, symbol):
        for position in self.positions:
            if position.symbol == symbol:
                return position
        logging.debug('xMan: getPositionBySymbol: No position found for symbol={}'.format(symbol))

    def getPerformanceBySymbol(self, symbol):
        for performance in self.performances:
            if performance.symbol == symbol:
                return performance
        logging.debug('xMan: getPerformanceBySymbol: No position found for symbol={}'.format(symbol))

    def executeMarketOrder(self, order, marketTick):
        """Execute market order, update position"""
        logging.debug('xMan: executeMarketOrder: Check order={}, marketTick={}'.format(order, marketTick))
        # We always fully fill market orders
        quantityChanged = order.quantityOutstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantityOutstanding
        order.fill(marketTick.open, order.quantityOutstanding, marketTick.dtIdx)
        if order.state == ORDER_STATE_FULLY_FILLED:
            self.cancelLinkedOrders(order, marketTick.dtIdx)

        position = self.getPositionBySymbol(order.symbol)
        if not position:
            position = Position(order.symbol)
            self.positions.append(position)
        position.change(marketTick.open, quantityChanged, order.commission)

    def executeLimitOrder(self, order, marketTick):
        """Execute limit order, update position"""
        logging.debug('xMan: executeLimitOrder: Check order={}, marketTick={}'.format(order, marketTick))
        if (order.direction == ORDER_DIRECTION_BUY and order.price >= marketTick.low) or (order.direction == ORDER_DIRECTION_SELL and order.price <= marketTick.high):
            quantityChanged = order.quantityOutstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantityOutstanding
            order.fill(order.price, order.quantityOutstanding, marketTick.dtIdx)
            if order.state == ORDER_STATE_FULLY_FILLED:
                self.cancelLinkedOrders(order, marketTick.dtIdx)

            position = self.getPositionBySymbol(order.symbol)
            if not position:
                position = Position(order.symbol)
                self.positions.append(position)
            position.change(order.price, quantityChanged, order.commission)

    def executeStopOrder(self, order, marketTick):
        """Execute stop order, update position"""
        logging.debug('xMan: executeStopOrder: Check order={}, marketTick={}'.format(order, marketTick))
        if (order.direction == ORDER_DIRECTION_BUY and order.price <= marketTick.high) or (order.direction == ORDER_DIRECTION_SELL and order.price >= marketTick.low):
            quantityChanged = order.quantityOutstanding if order.direction == ORDER_DIRECTION_BUY else -order.quantityOutstanding
            order.fill(order.price, order.quantityOutstanding, marketTick.dtIdx)
            if order.state == ORDER_STATE_FULLY_FILLED:
                self.cancelLinkedOrders(order, marketTick.dtIdx)

            position = self.getPositionBySymbol(order.symbol)
            if not position:
                position = Position(order.symbol)
                self.positions.append(position)
            position.change(order.price, quantityChanged, order.commission)

    def executeOrdersOnMarketTick(self, marketTick):
        for order in self.getOrdersBySymbol(marketTick.symbol):
            if order.state in [ORDER_STATE_FULLY_FILLED, ORDER_STATE_CANCELLED]:
                continue
            if order.type == ORDER_TYPE_MARKET:
                self.executeMarketOrder(order, marketTick)
            #TODO: We execute stop order ahead of limit order, limit order can possibly be cancelled before filled
            elif order.type == ORDER_TYPE_STOP:
                self.executeStopOrder(order, marketTick)
            elif order.type == ORDER_TYPE_LIMIT:
                self.executeLimitOrder(order, marketTick)
            else:
                logging.error('xMan: executeOrdersOnMarketTick: Unsupported order type {}'.format(order))

    def cancelLinkedOrders(self, order, datetime):
        """If one order get fully filled, other linked orders will be cancelled"""
        linkedOrders = self.getOrdersByLinkId(order.linkId)
        for linkedOrder in linkedOrders:
            if linkedOrder.orderId != order.orderId:
                linkedOrder.cancel(datetime)

    def linkOrders(self, orders):
        """If one order get fully filled, other linked orders will be cancelled"""
        linkId = uuid.uuid4()
        for order in orders:
            order.linkId = linkId
        logging.debug('xMan: linkOrders: Linked orderIds={}, linkId={}'.format([order.orderId for order in orders], linkId))

    def getAllSymbols(self):
        """Get all symbols ever executed"""
        orderSymbols = [order.symbol for order in self.orders]
        positionSymbols = [position.symbol for position in self.positions]
        return list(set(orderSymbols + positionSymbols))

    def evaluatePerformance(self):
        self.portfolioRealizedPNL = 0
        self.portfolioCashBalance = self.initialCapital
        self.portfolioPositionCost = 0
        self.portfolioSuccess = 0
        self.portfolioFailure = 0
        self.portfolioTotalTradeLife = datetime.timedelta()
        for symbol in self.getAllSymbols():
            outstandingMarketOrders, outstandingStopOrders, outstandingLimitOrders, filledMarketOrders, filledStopOrders, filledLimitOrders, cancelledMarketOrders, cancelledStopOrders, cancelledLimitOrders = 0, 0, 0, 0, 0, 0, 0, 0, 0
            totalTradeLife = datetime.timedelta()
            for order in self.getOrdersBySymbol(symbol):
                if order.state in [ORDER_STATE_PARTIALLY_FILLED, ORDER_STATE_NEW]:
                    if order.type == ORDER_TYPE_MARKET:
                        outstandingMarketOrders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        outstandingStopOrders += 1
                    elif order.type == ORDER_TYPE_LIMIT:
                        outstandingLimitOrders += 1
                elif order.state == ORDER_STATE_FULLY_FILLED:
                    if order.type == ORDER_TYPE_MARKET:
                        filledMarketOrders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        filledStopOrders += 1
                        totalTradeLife += (order.closeDtIdx.to_pydatetime() - order.openDtIdx.to_pydatetime())
                    elif order.type == ORDER_TYPE_LIMIT:
                        filledLimitOrders += 1
                        totalTradeLife += (order.closeDtIdx.to_pydatetime() - order.openDtIdx.to_pydatetime())
                elif order.state == ORDER_STATE_CANCELLED:
                    if order.type == ORDER_TYPE_MARKET:
                        cancelledMarketOrders += 1
                    elif order.type == ORDER_TYPE_STOP:
                        cancelledStopOrders += 1
                    elif order.type == ORDER_TYPE_LIMIT:
                        cancelledLimitOrders += 1
            position = self.getPositionBySymbol(symbol)
            if not position:
                position = Position(symbol)
                self.positions.append(position)
            performance = self.getPerformanceBySymbol(symbol)
            if not performance:
                performance = Performance(symbol)
                self.performances.append(performance)
            success = filledLimitOrders
            failure = filledStopOrders
            maxCapitalRequired = max(performance.maxCapitalRequired, position.cost)
            performance.updatePerformance(outstandingMarketOrders, outstandingStopOrders, outstandingLimitOrders, filledMarketOrders, filledStopOrders, filledLimitOrders, cancelledMarketOrders, cancelledStopOrders, cancelledLimitOrders, success, failure, maxCapitalRequired, position.realizedPNL, position.quantity, position.cost, totalTradeLife)
            logging.info('xMan: evaluatePerformance: performance={}'.format(performance))
            self.portfolioSuccess += success
            self.portfolioFailure += failure
            self.portfolioTotalTradeLife += totalTradeLife
            self.portfolioRealizedPNL += position.realizedPNL
            self.portfolioCashBalance += (position.realizedPNL - position.cost)
            self.portfolioPositionCost += position.cost
        self.portfolioMaxCapitalRequired = max(self.portfolioMaxCapitalRequired, self.portfolioPositionCost)

        logging.info('xMan: evaluatePerformance: Portfolio portfolioRealizedPNL={}, portfolioCashBalance={}, portfolioPositionCost={}, portfolioMaxCapitalRequired={}, portfolioSuccess={}, portfolioFailure={}, portfolioSuccessRate={:.2f}%, portfolioAverageTradeLife={}'.format(self.portfolioRealizedPNL, self.portfolioCashBalance, self.portfolioPositionCost, self.portfolioMaxCapitalRequired, self.portfolioSuccess, self.portfolioFailure, (float(self.portfolioSuccess)*100)/(self.portfolioSuccess+self.portfolioFailure) if self.portfolioSuccess+self.portfolioFailure else float('nan'), self.portfolioTotalTradeLife/(self.portfolioSuccess+self.portfolioFailure) if self.portfolioSuccess+self.portfolioFailure > 0 else 'No Trades'))

    def describeTradesExecutedByDatetime(self):
        result = dict()
        for order in self.orders:
            if order.state == ORDER_STATE_FULLY_FILLED:
                daycounts = result.get(order.closeDtIdx, dict())
                count = daycounts.get(order.type, 0)
                daycounts[order.type] = count + 1
                result[order.closeDtIdx] = daycounts
        logging.info('============================================================')
        logging.info('Trades Execution Summary for all dates')
        logging.info('------------------------------------------------------------')
        keys = list(result.keys())
        keys.sort()
        for dt in keys:
            logging.info('xMan: describeTradesExecutedByDatetime: {}: {}'.format(dt, result.get(dt, 'ERROR')))
        logging.info('============================================================')
