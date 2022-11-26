from utils.mortgage import calculate_monthly_payment
import pandas
from functools import reduce

AVG_INFLATION_RATE = 0.02
PROPERTY_AVG_INFLATION_RATE = 0.03
INVESTMENT_AVG_ANNUAL_RETURN = 0.06

INITIAL_CAPITAL = 1e7 # 10,000,000 HKD
INITIAL_MONTHLY_SALARY = 2e5 # 200,000 HKD
SALARY_INCREASE_RATE = AVG_INFLATION_RATE

INITIAL_PROPERTY_PRICE = 1.7e7 # 17,000,000 HKD
MORTGAGE_INTEREST_RATE = 0.02
TENOR_YEARS = 30

INITIAL_MONTHLY_RENT = 2.8e4 # 28,000 HKD
RENT_INCREASE_RATE = 0.03


pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)


def get_total_month_periods():
    """
    Assume all cashflows occur at end of each period.
    Period 0: Starting point. We have initial capital, pay downpayment, reset property price.
              (original property price - downpayment) is the starting liability.
              (initial cap - downpayment) goes to investiment.
    Period 1: At end of period 1, we receive 1st salary, pay 1st rent or installment.
              Remainder goes to investiment.
              Property appreciates for 1st time.
              Investment (from previous period) accrues the 1st return.
              Liability (from previous period) accrues the 1st interest.
    ...
    Period 12 * TENOR_YEARS: Receive last salary, pay last rent or installment.
              Remainder goes to investment, but no accurred returns.
    :return:
    """
    return 12 * TENOR_YEARS + 1


def get_cash_inflows():
    periods = get_total_month_periods()
    months, caps, salaries = [], [], []

    for i in range(periods):
        months.append(i)
        caps.append(INITIAL_CAPITAL if i == 0 else 0)
        salaries.append(0 if i == 0 else INITIAL_MONTHLY_SALARY * ((1+SALARY_INCREASE_RATE) ** (int((i-1)/12))))

    inflows = pandas.DataFrame({'Month': months,
                                'InitialCapital': caps,
                                'Salary': salaries})
    return inflows


def get_property_prices():
    periods = get_total_month_periods()
    months, prices = [], []

    for i in range(periods):
        months.append(i)
        prices.append(INITIAL_PROPERTY_PRICE * ((1+PROPERTY_AVG_INFLATION_RATE/12) ** i))

    property_prices = pandas.DataFrame({'Month': months,
                                        'PropertyPrice': prices})
    return property_prices


def get_down_payment_ratio():
    if INITIAL_PROPERTY_PRICE < 8e6:
        return 0.1
    elif INITIAL_PROPERTY_PRICE < 1e7:
        return 0.2
    else:
        return 0.5


def get_cash_outflows_stay_property():
    periods = get_total_month_periods()
    down_pmt_ratio = get_down_payment_ratio()
    down_pmt = INITIAL_PROPERTY_PRICE * down_pmt_ratio
    loan = INITIAL_PROPERTY_PRICE * (1 - down_pmt_ratio)
    monthly_pmt = calculate_monthly_payment(loan, MORTGAGE_INTEREST_RATE, 12 * TENOR_YEARS)

    months, down_pmts, installments = [], [], []

    for i in range(periods):
        months.append(i)
        down_pmts.append(down_pmt if i == 0 else 0)
        installments.append(0 if i == 0 else monthly_pmt)

    outflows = pandas.DataFrame({'Month': months,
                                 'DownPayment': down_pmts,
                                 'MonthlyInstallment': installments})
    return outflows


def get_cash_outflows_no_property():
    periods = get_total_month_periods()
    months, rents = [], []

    for i in range(periods):
        months.append(i)
        rents.append(0 if i == 0 else INITIAL_MONTHLY_RENT * ((1+RENT_INCREASE_RATE) ** (int((i-1)/12))))

    outflows = pandas.DataFrame({'Month': months,
                                 'MonthlyRent': rents})
    return outflows


def calc_nav_stay_property():
    """
    Buy a property for own stay.
    We spend salary on monthly installment, remainder to invest.
    :return:
    """
    # Gather all input data
    inflows = get_cash_inflows()
    outflows = get_cash_outflows_stay_property()
    property_prices = get_property_prices()
    nav = reduce(lambda left, right: pandas.merge(left, right, on=['Month'], how='outer'), [inflows, outflows, property_prices])

    # Calculate NAV
    property_assets, liabilities, investments = [], [], []
    investment = 0
    for idx, row in nav.iterrows():
        property_price = row['PropertyPrice']
        installment = row['MonthlyInstallment']
        down_pmt = row['DownPayment']
        init_cap = row['InitialCapital']
        salary = row['Salary']

        # Property asset
        property_assets.append(property_price)

        # Property liability
        liability = property_price - down_pmt if idx == 0 else liability * (1 + MORTGAGE_INTEREST_RATE/12) - installment
        liabilities.append(liability)

        # Investment
        remainder = init_cap + salary - down_pmt - installment
        investment = investment * (1 + INVESTMENT_AVG_ANNUAL_RETURN/12) + remainder
        investments.append(investment)

    nav['PropertyAsset'] = property_assets
    nav['PropertyLiability'] = liabilities
    nav['Investment'] = investments
    nav['NAV'] = nav['PropertyAsset'] - nav['PropertyLiability'] + nav['Investment']

    return nav


def calc_nav_no_property():
    """
    Do not buy a property. Stay in rented place.
    We spend salary on monthly rent, remainder to invest.
    :return:
    """
    # Gather all input data
    inflows = get_cash_inflows()
    outflows = get_cash_outflows_no_property()
    nav = reduce(lambda left, right: pandas.merge(left, right, on=['Month'], how='outer'), [inflows, outflows])

    # Calculate NAV
    property_assets, liabilities, investments = [], [], []
    investment = 0
    for idx, row in nav.iterrows():
        # Investment
        init_cap = row['InitialCapital']
        salary = row['Salary']
        rent = row['MonthlyRent']
        remainder = init_cap + salary - rent
        investment = investment * (1 + INVESTMENT_AVG_ANNUAL_RETURN/12) + remainder
        investments.append(investment)

    nav['Investment'] = investments
    nav['NAV'] = nav['Investment']

    return nav


def run():
    nav1 = calc_nav_stay_property()
    nav1.rename(columns={'NAV': 'NAV_StayProperty', 'Investment': 'Investment_StayProperty'}, inplace=True)
    nav2 = calc_nav_no_property()
    nav2.rename(columns={'NAV': 'NAV_NoProperty', 'Investment': 'Investment_NoProperty'}, inplace=True)
    res = pandas.merge(nav1, nav2[['Month', 'MonthlyRent', 'Investment_NoProperty', 'NAV_NoProperty']], on=['Month'], how='outer')
    return res
