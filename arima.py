import pandas_datareader.data as web
import datetime
import pandas as pd
from matplotlib import pyplot
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf


TRAIN_SIZE = 0.2
FORECAST_STEPS = 20
STOCKS_PREDICT = ['SPY', 'AAPL']

"""
TODO:
1. Does model change significantly as time goes by? e.g. fit 3 month, vs fit 1 year
2. What is the optimal prediction horizon? e.g. 5 days
3. How frequently do we re-fit model?
"""


def download_data(tickers=['AAPL', 'SPY'], start_date=datetime.date(2022, 5, 1), end_date=datetime.date(2022, 8, 26)):
    """
    Downland stock historical data from Yahoo finance, histPanel is a Panel, already in ascending order, e.g:
    Dimensions: 6 (items) x 2 (major_axis) x 2 (minor_axis)
    Items axis: Open to Adj Close
    Major_axis axis: 2016-10-11 00:00:00 to 2016-10-12 00:00:00
    Minor_axis axis: SPY to ^N225
    """
    df = web.DataReader(tickers, 'yahoo', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    # Cleanse data: remove dates where there is NaN and 0
    for col_name, ts in df.iteritems():
        for row_name, value in ts.iteritems():
            if float(value) == 0:
                df[col_name][row_name] = 'NaN'

    df = df.dropna(axis=0, how='any')

    return df


def adf(ts):
    result = adfuller(ts.dropna())
    print('ADF Statistic: %f' % result[0])
    print('p-value: %f' % result[1])


def plot_acf_differencing(ts):
    # Reset index for plotting convenience
    ts = ts.reset_index()[ts.name]

    pyplot.rcParams.update({'figure.figsize': (9, 7), 'figure.dpi': 120})

    # Original Series
    fig, axes = pyplot.subplots(3, 2, sharex=True)

    ts0 = ts.dropna()
    axes[0, 0].plot(ts0)
    axes[0, 0].set_title('Original Series')
    plot_acf(ts0, lags=len(ts0)-1, ax=axes[0, 1])

    # 1st Differencing
    ts1 = ts.diff().dropna()
    axes[1, 0].plot(ts1)
    axes[1, 0].set_title('1st Order Differencing')
    plot_acf(ts1, lags=len(ts1)-1, ax=axes[1, 1])

    # 2nd Differencing
    ts2 = ts1.diff().dropna()
    axes[2, 0].plot(ts2)
    axes[2, 0].set_title('2nd Order Differencing')
    plot_acf(ts2, lags=len(ts2)-1, ax=axes[2, 1])

    pyplot.show()


def plot_pacf_ar(ts):
    # Reset index for plotting convenience
    ts = ts.reset_index()[ts.name]

    # PACF plot of 1st differenced series
    pyplot.rcParams.update({'figure.figsize': (9, 3), 'figure.dpi': 120})

    fig, axes = pyplot.subplots(1, 2, sharex=True)
    ts1 = ts.diff().dropna()
    axes[0].plot(ts1)
    axes[0].set_title('1st Differencing')
    axes[1].set(ylim=(0, 5))
    plot_pacf(ts1, ax=axes[1])

    pyplot.show()


def plot_acf_ma(ts):
    pyplot.rcParams.update({'figure.figsize': (9, 3), 'figure.dpi': 120})

    fig, axes = pyplot.subplots(1, 2, sharex=True)
    ts1 = ts.diff().dropna()
    axes[0].plot(ts1)
    axes[0].set_title('1st Differencing')
    axes[1].set(ylim=(0, 1.2))
    plot_acf(ts1, lags=len(ts1)-1, ax=axes[1])

    pyplot.show()


def fit_arima(ts):
    # 1,1,2 ARIMA Model
    model = ARIMA(ts, order=(1, 1, 2))
    model_fit = model.fit(disp=0)
    print(model_fit.summary())

    # Plot residual errors
    residuals = pd.DataFrame(model_fit.resid)
    fig, ax = pyplot.subplots(1, 2)
    residuals.plot(title="Residuals", ax=ax[0])
    residuals.plot(kind='kde', title='Density', ax=ax[1])
    pyplot.show()

    # Actual vs Fitted
    model_fit.plot_predict(dynamic=False)
    pyplot.show()


def run(ts, p, d, q):
    # Create Training and Test
    train = ts[:85]
    test = ts[85:]

    # Build Model
    model = ARIMA(train, order=(p, d, q))
    fitted = model.fit(disp=-1)
    print(fitted.summary())

    # Forecast
    fc, se, conf = fitted.forecast(15, alpha=0.05)  # 95% conf

    # Make as pandas series
    fc_series = pd.Series(fc, index=test.index)
    lower_series = pd.Series(conf[:, 0], index=test.index)
    upper_series = pd.Series(conf[:, 1], index=test.index)

    # Plot
    pyplot.figure(figsize=(12, 5), dpi=100)
    pyplot.plot(train, label='training')
    pyplot.plot(test, label='actual')
    pyplot.plot(fc_series, label='forecast')
    pyplot.fill_between(lower_series.index, lower_series, upper_series, color='k', alpha=.15)
    pyplot.title('Forecast vs Actuals')
    pyplot.legend(loc='upper left', fontsize=8)
    pyplot.show()


def main():
    LOOK_BACK_DAYS = 365

    date = datetime.date(2022, 8, 26)
    start_date = date - datetime.timedelta(days=LOOK_BACK_DAYS)

    df = download_data(tickers=['AAPL'], start_date=start_date, end_date=date)
    ts = df[('Adj Close', 'AAPL')]

    # 1. ADF test if original series is already stationary
    # p-value > 0.05, so cannot reject null hypothesis (non-stationary), thus original series is non-stationary
    adf(ts)

    # 2. Find d: Plot differencing series
    # 2nd diff shows ACF become negative quickly so tentatively fix d = 1
    plot_acf_differencing(ts)

    # 3. Find p: AR term
    plot_pacf_ar(ts)

    # 4. Find q: MA term
    plot_acf_ma(ts)

    return ts


if __name__ == '__main__':
    main()
