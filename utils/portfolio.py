
class Portfolio:
    """
    Aggregation of Positions
    """
    def __init__(self, capital):
        self.initial_capital = capital
        self.realized_pnl = 0
        self.cash_balance = 0
        self.position_cost = 0
        self.position_mtm = 0

    def reset(self):
        self.realized_pnl = 0
        self.cash_balance = self.initial_capital
        self.position_cost = 0
        self.position_mtm = 0

    def refresh(self, positions):
        """
        Refresh portfolio based on given positions
        :param positions:
        :return:
        """
        self.reset()

        for position in positions:
            self.realized_pnl += position.realized_pnl
            self.cash_balance += (position.realized_pnl - position.cost)
            self.position_cost += position.cost
            self.position_mtm += position.mtm
