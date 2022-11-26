def calculate_future_value(payment, tenor=30, disc_rate=0.01, monthly=False):
    """
    Calculate FV for the given payment
    :param payment:
    :param tenor: in years
    :param disc_rate: discount rate
    :param monthly: if True, monthly payment; Otherwise just one initial payment
    :return: the Future value
    """
    monthly_rate = disc_rate / 12.0

    fv = payment
    for month in range(12 * tenor):
        fv = fv * (1 + monthly_rate)
        if monthly:
            fv = fv + payment

    return fv


def calculate_monthly_payment(loan, r, n):
    """
    Calculate the monthly payment.
    Formula: monthly payment = loan((r/12)*(1 + r/12) ** n) / ((1 + r/12) ** n - 1)
    :param loan: Total amount loaned
    :param r: annual interest rate
    :param n: number of monthly payments
    :return: monthly payment
    """
    return loan*((r/12)*(1 + r/12) ** n) / ((1 + r/12) ** n - 1)
