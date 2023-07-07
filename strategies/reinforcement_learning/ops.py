import os
import math
import logging
import numpy as np
import keras.backend as K
from utils.data_hub import DataHub

format_quantity = lambda x: '{0:,}'.format(x)
format_notional = lambda x: ('-$' if x < 0 else '+$') + '{0:,.2f}'.format(abs(x))
format_percentage = lambda x: ('-' if x < 0 else '+') + '{0:.2f}%'.format(abs(x) * 100)


def log_daily_flash(t, action_name, price, shares, mv, cash, next_shares, next_mv, next_cash, initial_portfolio):
    portfolio = mv + cash
    next_portfolio = next_mv + next_cash

    logging.debug(
        'T={} {} at: {} | Shares_T: {} | MV_T: {} | Cash_T: {} | Shares_T1: {} | MV_T1: {} | Cash_T1: {} | Daily PNL: {} | Accumulative PNL: {}'.format(
            t,
            action_name,
            format_notional(price),
            format_quantity(shares),
            format_notional(mv),
            format_notional(cash),
            format_quantity(next_shares),
            format_notional(next_mv),
            format_notional(next_cash),
            format_notional(next_portfolio - portfolio),
            format_notional(next_portfolio - initial_portfolio)
        ))


def show_train_result(result):
    """
    Displays training results
    """
    logging.info('### Train Model Result ###')
    logging.info('Episode {}/{}'.format(result[0], result[1]))
    logging.info('Total Profit: {}'.format(format_notional(result[2])))
    logging.info('Model Loss: {:.4f}'.format(result[3]))
    logging.info('##########################')


def show_eval_result(result):
    """
    Displays eval results
    """
    logging.info('### Evaluate Model Result ###')
    logging.info('Start: {}'.format(result[0]))
    logging.info('End: {}'.format(result[1]))
    logging.info('Total Profit: {}'.format(format_notional(result[2])))
    logging.info('Annualized Return: {}'.format(format_percentage(result[3])))
    logging.info('Annualized Volatility: {}'.format(format_percentage(result[4])))
    logging.info('Sharpe Ratio: {}'.format(result[5]))
    logging.info('#############################')


def get_stock_data(stock, start_date, end_date):
    """
    Reads stock data from csv file
    """
    data_hub = DataHub()
    dfs = data_hub.downloadDataFromYahoo(startDate=start_date, endDate=end_date, symbols=[stock])
    df = dfs[stock]
    return list(df['Adj Close'])


def switch_k_backend_device():
    """
    Switches `keras` backend from GPU to CPU if required.

    Faster computation on CPU (if using tensorflow-gpu).
    """
    if K.backend() == "tensorflow":
        logging.debug("switching to TensorFlow for CPU")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def sigmoid(x):
    """
    Performs sigmoid operation
    """
    try:
        if x < 0:
            return 1 - 1 / (1 + math.exp(x))
        return 1 / (1 + math.exp(-x))
    except Exception as err:
        print("Error in sigmoid: " + err)


def get_state(data, t, n_days, stock_percentage):
    """
    Returns state at t (n-day price representation, portfolio stock %)
    For each day of observation period, we take Sigmoid(Price_T - Price_T-1)
    """
    d = t - n_days + 1
    block = data[d: t + 1] if d >= 0 else -d * [data[0]] + data[0: t + 1]  # pad with t0
    res = []
    for i in range(n_days - 1):
        res.append(sigmoid(block[i + 1] - block[i]))

    res.append(stock_percentage)

    return np.array([res])


def get_state1(prices, t, n_days, holding, cash):
    """
    Returns state at t (n-day prices, stock holdings, cash)
    No standardization / normalization performed
    """
    d = t - n_days + 1
    res = prices[d: t + 1] if d >= 0 else -d * [prices[0]] + prices[0: t + 1]  # pad with t0

    res.append(holding)
    res.append(cash)

    return np.array([res])
