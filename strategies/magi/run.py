"""
Script to run Magi strategy.

xMan:
    - Receive and execute ORDERS.
    - Track POSITIONS per Symbol.
    - Track PORTFOLIO holding and performance.
    - Calculate PERFORMANCE at Symbol and Portfolio levels.

Magi:
    - Own and run strategy

MarketTick:
    - Feed to xMan for order execution / MTM
    - Feed to Magi for strategy

Flow:
1. Before SOD, xMan has existing orders from prior day strategy.
2. Today's MarketTick feeds to xMan, for order execution, EOD MTM, EOD performance etc.
3. After EOD, today's MarketTick feeds to Magi to run strategy, which send orders to xMan.
"""
import copy
import datetime
import logging
from strategies.magi.magi import Magi
from strategies.magi.x_man import xMan
from strategies.magi.config import Config
from utils.data_hub import DataHub
from utils.performance_evaluation import get_risk_free_rate_by_year

STOCKS_500 = ['ABT', 'ABBV', 'ACN', 'ACE', 'ADBE', 'ADT', 'AAP', 'AES', 'AET', 'AFL', 'AMG', 'A', 'GAS', 'APD', 'ARG', 'AKAM', 'AA', 'AGN', 'ALXN', 'ALLE', 'ADS', 'ALL', 'ALTR', 'MO', 'AMZN', 'AEE', 'AAL', 'AEP', 'AXP', 'AIG', 'AMT', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'APC', 'ADI', 'AON', 'APA', 'AIV', 'AMAT', 'ADM', 'AIZ', 'T', 'ADSK', 'ADP', 'AN', 'AZO', 'AVGO', 'AVB', 'AVY', 'BHI', 'BLL', 'BAC', 'BK', 'BCR', 'BXLT', 'BAX', 'BBT', 'BDX', 'BBBY', 'BRK-B', 'BBY', 'BLX', 'HRB', 'BA', 'BWA', 'BXP', 'BSK', 'BMY', 'BRCM', 'BF-B', 'CHRW', 'CA', 'CVC', 'COG', 'CAM', 'CPB', 'COF', 'CAH', 'HSIC', 'KMX', 'CCL', 'CAT', 'CBG', 'CBS', 'CELG', 'CNP', 'CTL', 'CERN', 'CF', 'SCHW', 'CHK', 'CVX', 'CMG', 'CB', 'CI', 'XEC', 'CINF', 'CTAS', 'CSCO', 'C', 'CTXS', 'CLX', 'CME', 'CMS', 'COH', 'KO', 'CCE', 'CTSH', 'CL', 'CMCSA', 'CMA', 'CSC', 'CAG', 'COP', 'CNX', 'ED', 'STZ', 'GLW', 'COST', 'CCI', 'CSX', 'CMI', 'CVS', 'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DLPH', 'DAL', 'XRAY', 'DVN', 'DO', 'DTV', 'DFS', 'DISCA', 'DISCK', 'DG', 'DLTR', 'D', 'DOV', 'DOW', 'DPS', 'DTE', 'DD', 'DUK', 'DNB', 'ETFC', 'EMN', 'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'EMC', 'EMR', 'ENDP', 'ESV', 'ETR', 'EOG', 'EQT', 'EFX', 'EQIX', 'EQR', 'ESS', 'EL', 'ES', 'EXC', 'EXPE', 'EXPD', 'ESRX', 'XOM', 'FFIV', 'FB', 'FAST', 'FDX', 'FIS', 'FITB', 'FSLR', 'FE', 'FSIV', 'FLIR', 'FLS', 'FLR', 'FMC', 'FTI', 'F', 'FOSL', 'BEN', 'FCX', 'FTR', 'GME', 'GPS', 'GRMN', 'GD', 'GE', 'GGP', 'GIS', 'GM', 'GPC', 'GNW', 'GILD', 'GS', 'GT', 'GOOGL', 'GOOG', 'GWW', 'HAL', 'HBI', 'HOG', 'HAR', 'HRS', 'HIG', 'HAS', 'HCA', 'HCP', 'HCN', 'HP', 'HES', 'HPQ', 'HD', 'HON', 'HRL', 'HSP', 'HST', 'HCBK', 'HUM', 'HBAN', 'ITW', 'IR', 'INTC', 'ICE', 'IBM', 'IP', 'IPG', 'IFF', 'INTU', 'ISRG', 'IVZ', 'IRM', 'JEC', 'JBHT', 'JNJ', 'JCI', 'JOY', 'JPM', 'JNPR', 'KSU', 'K', 'KEY', 'GMCR', 'KMB', 'KIM', 'KMI', 'KLAC', 'KSS', 'KRFT', 'KR', 'LB', 'LLL', 'LH', 'LRCX', 'LM', 'LEG', 'LEN', 'LVLT', 'LUK', 'LLY', 'LNC', 'LLTC', 'LMT', 'L', 'LOW', 'LYB', 'MTB', 'MAC', 'M', 'MNK', 'MRO', 'MPC', 'MAR', 'MMC', 'MLM', 'MAS', 'MA', 'MAT', 'MKC', 'MCD', 'MHFI', 'MCK', 'MJN', 'MMV', 'MDT', 'MRK', 'MET', 'KORS', 'MCHP', 'MU', 'MSFT', 'MHK', 'TAP', 'MDLZ', 'MON', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MUR', 'MYL', 'NDAQ', 'NOV', 'NAVI', 'NTAP', 'NFLX', 'NWL', 'NFX', 'NEM', 'NWSA', 'NEE', 'NLSN', 'NKE', 'NI', 'NE', 'NBL', 'JWN', 'NSC', 'NTRS', 'NOC', 'NRG', 'NUE', 'NVDA', 'ORLY', 'OXY', 'OMC', 'OKE', 'ORCL', 'OI', 'PCAR', 'PLL', 'PH', 'PDCO', 'PAYX', 'PNR', 'PBCT', 'POM', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PNW', 'PXD', 'PBI', 'PCL', 'PNC', 'RL', 'PPG', 'PPL', 'PX', 'PCP', 'PCLN', 'PFG', 'PG', 'PGR', 'PLD', 'PRU', 'PEG', 'PSA', 'PHM', 'PVH', 'QRVO', 'PWR', 'QCOM', 'DGX', 'RRC', 'RTN', 'O', 'RHT', 'REGN', 'RF', 'RSG', 'RAI', 'RHI', 'ROK', 'COL', 'ROP', 'ROST', 'RLC', 'R', 'CRM', 'SNDK', 'SCG', 'SLB', 'SNI', 'STX', 'SEE', 'SRE', 'SHW', 'SIAL', 'SPG', 'SWKS', 'SLG', 'SJM', 'SNA', 'SO', 'LUV', 'SWN', 'SE', 'STJ', 'SWK', 'SPLS', 'SBUX', 'HOT', 'STT', 'SRCL', 'SYK', 'STI', 'SYMC', 'SYY', 'TROW', 'TGT', 'TEL', 'TE', 'TGNA', 'THC', 'TDC', 'TSO', 'TXN', 'TXT', 'HSY', 'TRV', 'TMO', 'TIF', 'TWX', 'TWC', 'TJK', 'TMK', 'TSS', 'TSCO', 'RIG', 'TRIP', 'FOXA', 'TSN', 'TYC', 'UA', 'UNP', 'UNH', 'UPS', 'URI', 'UTX', 'UHS', 'UNM', 'URBN', 'VFC', 'VLO', 'VAR', 'VTR', 'VRSN', 'VZ', 'VRTX', 'VIAB', 'V', 'VNO', 'VMC', 'WMT', 'WBA', 'DIS', 'WM', 'WAT', 'ANTM', 'WFC', 'WDC', 'WU', 'WY', 'WHR', 'WFM', 'WMB', 'WEC', 'WYN', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XL', 'XYL', 'YHOO', 'YUM', 'ZBH', 'ZION', 'ZTS']
STOCKS_FOCUS = ['SPY', 'VXX']
START_DATE = datetime.date(2020, 1, 1)
END_DATE = datetime.date(2022, 12, 31)
CAPITAL = 10000
SUCCESS_THRESHOLD = 1


def execute(market_ticks_by_day, x_man, magi):
    dt_indices = sorted(list(market_ticks_by_day.keys()), reverse=False)
    for dt_idx in dt_indices:
        logging.info('============================================================')
        logging.info(dt_idx)

        market_ticks_by_symbol = market_ticks_by_day.get(dt_idx, dict())

        logging.info('------------------------------------------------------------')
        logging.info('Execute existing orders and update MTM')
        logging.info('------------------------------------------------------------')

        x_man.run_on_market_ticks(market_ticks_by_symbol)

        logging.info('------------------------------------------------------------')
        logging.info('Performance Summary for today')
        logging.info('------------------------------------------------------------')

        x_man.evaluate_performance()

        logging.info('------------------------------------------------------------')
        logging.info('Run strategy for today')
        logging.info('------------------------------------------------------------')

        magi.run_on_market_ticks(market_ticks_by_symbol)

        logging.info('============================================================')

    x_man.describe_trades_executed_by_datetime()


def train(
        symbol_universe,
        start_date,
        end_date,
        capital,
        success_threshold,
        model_name,
):
    logging.basicConfig(
        filename='logs/train_{}_{}.log'.format(model_name, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')),
        format='%(levelname)s: %(message)s',
        level=logging.INFO)

    # Prepare components
    data_hub = DataHub()
    market_ticks_by_day = data_hub.getDailyMarketTicks(start_date, end_date, symbol_universe)
    # TODO: Need better pick of risk free rate
    risk_free = get_risk_free_rate_by_year(start_date.year)
    x_man = xMan(capital, risk_free)
    config = Config(symbols=symbol_universe)
    magi = Magi(capital, x_man, config)

    # Execute daily
    execute(market_ticks_by_day, x_man, magi)

    # Calibrate parameters and persist
    config_symbols = []
    for p in x_man.symbol_performances:
        if p.success + p.failure > 0 and p.success / (p.success + p.failure) >= success_threshold:
            config_symbols.append(p.symbol)
    config_trained = copy.deepcopy(config)
    config_trained.update(symbols=config_symbols)
    config_trained.log()
    config_trained.save(model_name)

    return magi


def test(
        start_date,
        end_date,
        capital,
        model_name,
):
    logging.basicConfig(
        filename='logs/test_{}_{}.log'.format(model_name, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')),
        format='%(levelname)s: %(message)s',
        level=logging.INFO)

    # Prepare components
    config = Config()
    config.load(model_name)
    data_hub = DataHub()
    market_ticks_by_day = data_hub.getDailyMarketTicks(start_date, end_date, config.symbols)
    # Some strategies need to know trading calendar
    trading_calendar = sorted(list(market_ticks_by_day.keys()), reverse=False)
    # TODO: Need better pick of risk free rate
    risk_free = get_risk_free_rate_by_year(start_date.year)
    x_man = xMan(capital, risk_free)
    magi = Magi(capital, x_man, config, trading_calendar, model_name)

    # Execute daily
    execute(market_ticks_by_day, x_man, magi)

    return magi


if __name__ == '__main__':
    """Entry point"""
    # train(
    #     STOCKS_500,
    #     START_DATE,
    #     END_DATE,
    #     CAPITAL,
    #     SUCCESS_THRESHOLD,
    #     '20200101_20221231_100_Mean_Rev'
    # )
    test(
        datetime.date(2015, 1, 1),
        datetime.date.today(),
        CAPITAL,
        'price_mean_reversion'
    )
