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

import datetime
import logging
import pandas
from magi import Magi
from x_man import xMan
from utils.data_hub import DataHub


STOCKS_500 = ['ABT', 'ABBV', 'ACN', 'ACE', 'ADBE', 'ADT', 'AAP', 'AES', 'AET', 'AFL', 'AMG', 'A', 'GAS', 'APD', 'ARG', 'AKAM', 'AA', 'AGN', 'ALXN', 'ALLE', 'ADS', 'ALL', 'ALTR', 'MO', 'AMZN', 'AEE', 'AAL', 'AEP', 'AXP', 'AIG', 'AMT', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'APC', 'ADI', 'AON', 'APA', 'AIV', 'AMAT', 'ADM', 'AIZ', 'T', 'ADSK', 'ADP', 'AN', 'AZO', 'AVGO', 'AVB', 'AVY', 'BHI', 'BLL', 'BAC', 'BK', 'BCR', 'BXLT', 'BAX', 'BBT', 'BDX', 'BBBY', 'BRK-B', 'BBY', 'BLX', 'HRB', 'BA', 'BWA', 'BXP', 'BSK', 'BMY', 'BRCM', 'BF-B', 'CHRW', 'CA', 'CVC', 'COG', 'CAM', 'CPB', 'COF', 'CAH', 'HSIC', 'KMX', 'CCL', 'CAT', 'CBG', 'CBS', 'CELG', 'CNP', 'CTL', 'CERN', 'CF', 'SCHW', 'CHK', 'CVX', 'CMG', 'CB', 'CI', 'XEC', 'CINF', 'CTAS', 'CSCO', 'C', 'CTXS', 'CLX', 'CME', 'CMS', 'COH', 'KO', 'CCE', 'CTSH', 'CL', 'CMCSA', 'CMA', 'CSC', 'CAG', 'COP', 'CNX', 'ED', 'STZ', 'GLW', 'COST', 'CCI', 'CSX', 'CMI', 'CVS', 'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DLPH', 'DAL', 'XRAY', 'DVN', 'DO', 'DTV', 'DFS', 'DISCA', 'DISCK', 'DG', 'DLTR', 'D', 'DOV', 'DOW', 'DPS', 'DTE', 'DD', 'DUK', 'DNB', 'ETFC', 'EMN', 'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'EMC', 'EMR', 'ENDP', 'ESV', 'ETR', 'EOG', 'EQT', 'EFX', 'EQIX', 'EQR', 'ESS', 'EL', 'ES', 'EXC', 'EXPE', 'EXPD', 'ESRX', 'XOM', 'FFIV', 'FB', 'FAST', 'FDX', 'FIS', 'FITB', 'FSLR', 'FE', 'FSIV', 'FLIR', 'FLS', 'FLR', 'FMC', 'FTI', 'F', 'FOSL', 'BEN', 'FCX', 'FTR', 'GME', 'GPS', 'GRMN', 'GD', 'GE', 'GGP', 'GIS', 'GM', 'GPC', 'GNW', 'GILD', 'GS', 'GT', 'GOOGL', 'GOOG', 'GWW', 'HAL', 'HBI', 'HOG', 'HAR', 'HRS', 'HIG', 'HAS', 'HCA', 'HCP', 'HCN', 'HP', 'HES', 'HPQ', 'HD', 'HON', 'HRL', 'HSP', 'HST', 'HCBK', 'HUM', 'HBAN', 'ITW', 'IR', 'INTC', 'ICE', 'IBM', 'IP', 'IPG', 'IFF', 'INTU', 'ISRG', 'IVZ', 'IRM', 'JEC', 'JBHT', 'JNJ', 'JCI', 'JOY', 'JPM', 'JNPR', 'KSU', 'K', 'KEY', 'GMCR', 'KMB', 'KIM', 'KMI', 'KLAC', 'KSS', 'KRFT', 'KR', 'LB', 'LLL', 'LH', 'LRCX', 'LM', 'LEG', 'LEN', 'LVLT', 'LUK', 'LLY', 'LNC', 'LLTC', 'LMT', 'L', 'LOW', 'LYB', 'MTB', 'MAC', 'M', 'MNK', 'MRO', 'MPC', 'MAR', 'MMC', 'MLM', 'MAS', 'MA', 'MAT', 'MKC', 'MCD', 'MHFI', 'MCK', 'MJN', 'MMV', 'MDT', 'MRK', 'MET', 'KORS', 'MCHP', 'MU', 'MSFT', 'MHK', 'TAP', 'MDLZ', 'MON', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MUR', 'MYL', 'NDAQ', 'NOV', 'NAVI', 'NTAP', 'NFLX', 'NWL', 'NFX', 'NEM', 'NWSA', 'NEE', 'NLSN', 'NKE', 'NI', 'NE', 'NBL', 'JWN', 'NSC', 'NTRS', 'NOC', 'NRG', 'NUE', 'NVDA', 'ORLY', 'OXY', 'OMC', 'OKE', 'ORCL', 'OI', 'PCAR', 'PLL', 'PH', 'PDCO', 'PAYX', 'PNR', 'PBCT', 'POM', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PNW', 'PXD', 'PBI', 'PCL', 'PNC', 'RL', 'PPG', 'PPL', 'PX', 'PCP', 'PCLN', 'PFG', 'PG', 'PGR', 'PLD', 'PRU', 'PEG', 'PSA', 'PHM', 'PVH', 'QRVO', 'PWR', 'QCOM', 'DGX', 'RRC', 'RTN', 'O', 'RHT', 'REGN', 'RF', 'RSG', 'RAI', 'RHI', 'ROK', 'COL', 'ROP', 'ROST', 'RLC', 'R', 'CRM', 'SNDK', 'SCG', 'SLB', 'SNI', 'STX', 'SEE', 'SRE', 'SHW', 'SIAL', 'SPG', 'SWKS', 'SLG', 'SJM', 'SNA', 'SO', 'LUV', 'SWN', 'SE', 'STJ', 'SWK', 'SPLS', 'SBUX', 'HOT', 'STT', 'SRCL', 'SYK', 'STI', 'SYMC', 'SYY', 'TROW', 'TGT', 'TEL', 'TE', 'TGNA', 'THC', 'TDC', 'TSO', 'TXN', 'TXT', 'HSY', 'TRV', 'TMO', 'TIF', 'TWX', 'TWC', 'TJK', 'TMK', 'TSS', 'TSCO', 'RIG', 'TRIP', 'FOXA', 'TSN', 'TYC', 'UA', 'UNP', 'UNH', 'UPS', 'URI', 'UTX', 'UHS', 'UNM', 'URBN', 'VFC', 'VLO', 'VAR', 'VTR', 'VRSN', 'VZ', 'VRTX', 'VIAB', 'V', 'VNO', 'VMC', 'WMT', 'WBA', 'DIS', 'WM', 'WAT', 'ANTM', 'WFC', 'WDC', 'WU', 'WY', 'WHR', 'WFM', 'WMB', 'WEC', 'WYN', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XL', 'XYL', 'YHOO', 'YUM', 'ZBH', 'ZION', 'ZTS']
STOCKS_1JAN2014_1JAN2018_SUCCESS_RATE_60 = ['YUM', 'VRTX', 'GIS', 'GD', 'BRK-B', 'MAS', 'PKI', 'SNA', 'FOXA', 'XYL', 'TSN', 'BEN', 'CMI', 'CME', 'CMS', 'MAR', 'VLO', 'HUM', 'BLX', 'FFIV', 'BLL', 'HCA', 'HCN', 'NFX', 'MA', 'MO', 'MS', 'AMGN', 'FB', 'COST', 'DOV', 'SCHW', 'FCX', 'DFS', 'V', 'AVY', 'ALL', 'NTAP', 'MMV', 'RLC', 'SO', 'JNPR', 'CAT', 'BAC', 'GS', 'CAG', 'LH', 'PGR', 'HIG', 'CELG', 'ZION', 'STI', 'STZ', 'PNR', 'IVZ', 'PNC', 'AON', 'PRU', 'URBN', 'HRS', 'HRL', 'IPG', 'RHT', 'APC', 'APD', 'KSU', 'WFC', 'NVDA', 'PEG', 'AVGO', 'RTN', 'ED', 'JNJ', 'EW', 'STT', 'LUV', 'ADSK', 'ECL', 'NUE', 'EXPE', 'EXPD', 'ETFC', 'CLX', 'DTE', 'UNH', 'BBT', 'OMC', 'KO', 'LNC', 'KEY', 'KLAC', 'BF-B', 'SWK', 'RSG', 'AAL', 'TGT', 'HBAN', 'INTC', 'MLM', 'INTU', 'ALXN', 'DHR', 'JPM', 'R', 'NFLX', 'WM', 'WY', 'HST', 'THC', 'SYK', 'LEG', 'SYY', 'AET', 'GRMN', 'ESRX', 'SWKS', 'CTAS', 'EMR', 'FDX', 'PG', 'CTXS', 'PM', 'EFX', 'XRX', 'MCHP', 'DVA', 'ETN', 'ZBH', 'DG', 'CB', 'CA', 'CF', 'CHRW', 'SRE', 'GNW', 'BXP', 'AIV', 'DIS', 'PPG', 'MNST', 'NSC', 'OKE', 'IP', 'IR', 'URI', 'PWR', 'CSCO', 'BA', 'BK', 'DRI', 'CCL', 'CCI', 'CCE', 'DTV', 'MYL', 'D', 'PEP', 'T', 'WMB', 'VRSN', 'OI', 'NTRS', 'HP', 'HD', 'AMG', 'TMO', 'AMT', 'ICE', 'BDX', 'MPC', 'MDLZ', 'NEE', 'ACN', 'NI', 'TEL', 'NE', 'NBL', 'FLS', 'ADS', 'ADP', 'GILD', 'BSK', 'GME', 'ADM', 'XEC', 'XEL', 'LEN', 'EBAY', 'MET', 'TXN', 'DAL', 'ORCL', 'ESV', 'ESS', 'HON', 'ABBV', 'ISRG', 'PFG']
STOCKS_1JAN2015_1JAN2018_SUCCESS_RATE_60 = ['VRTX', 'GIS', 'GD', 'BRK-B', 'MAS', 'MAR', 'SNA', 'FOXA', 'XRAY', 'JNJ', 'TSN', 'BEN', 'CMI', 'EL', 'CME', 'DTE', 'CMS', 'GRMN', 'BLX', 'FFIV', 'BLL', 'HCA', 'NFX', 'MA', 'MO', 'MU', 'MS', 'AMGN', 'COST', 'DOV', 'MSFT', 'SCHW', 'FCX', 'BSK', 'V', 'MPC', 'ALL', 'NTAP', 'MMV', 'RLC', 'SO', 'JNPR', 'CTSH', 'SWKS', 'CAT', 'BAC', 'GS', 'CAG', 'LH', 'PGR', 'HIG', 'CELG', 'ZION', 'STI', 'STZ', 'RSG', 'IVZ', 'PNC', 'BXP', 'AMZN', 'AON', 'PRU', 'URI', 'HRS', 'HRL', 'IPG', 'NLSN', 'APH', 'APC', 'APD', 'WFC', 'NVDA', 'AVGO', 'RTN', 'PKI', 'DISCA', 'PAYX', 'OXY', 'ED', 'EW', 'STT', 'LUV', 'ECL', 'NUE', 'EXPE', 'EXPD', 'ETFC', 'R', 'CLX', 'UNH', 'OMC', 'KO', 'LNC', 'KEY', 'ITW', 'CTAS', 'BF-B', 'SWK', 'PNR', 'DG', 'DE', 'AKAM', 'INTC', 'MLM', 'INTU', 'ALXN', 'DHR', 'MCD', 'NFLX', 'WM', 'WY', 'HSY', 'FITB', 'EQT', 'THC', 'YUM', 'LEG', 'SYY', 'AES', 'AET', 'ESRX', 'KLAC', 'EMR', 'FDX', 'CRM', 'PG', 'PM', 'EFX', 'XRX', 'MON', 'KMB', 'PEP', 'COG', 'PEG', 'ETN', 'ZBH', 'AAL', 'SRE', 'CB', 'CA', 'CF', 'SBUX', 'GNW', 'AIV', 'DIS', 'PPG', 'MNST', 'NSC', 'OKE', 'IP', 'IR', 'MTB', 'PWR', 'CSCO', 'BA', 'DRI', 'CCL', 'CCI', 'CCE', 'DTV', 'MYL', 'D', 'DVA', 'T', 'WMB', 'VRSN', 'OI', 'CINF', 'NTRS', 'HD', 'TMK', 'AMG', 'TMO', 'AMT', 'BDX', 'AVY', 'MDLZ', 'NEE', 'ACN', 'NI', 'TEL', 'NE', 'HP', 'ADS', 'ADP', 'GILD', 'ADM', 'XEC', 'XEL', 'LEN', 'EBAY', 'MET', 'MSI', 'TWX', 'PCAR', 'TXN', 'DAL', 'ORCL', 'HON', 'ICE', 'ABBV', 'ROK', 'ISRG', 'PFG']
STOCKS_1JAN2016_1JAN2018_SUCCESS_RATE_60 = ['QRVO', 'JWN', 'EOG', 'VRTX', 'GIS', 'GD', 'VAR', 'BRK-B', 'MAS', 'MAR', 'MAT', 'SNA', 'FOXA', 'JNJ', 'TSN', 'BEN', 'CMI', 'CMG', 'CME', 'DTE', 'CMS', 'TSS', 'GRMN', 'BLX', 'FFIV', 'HCA', 'FTI', 'HCN', 'NFX', 'MO', 'MU', 'OKE', 'MS', 'AMGN', 'COST', 'DOV', 'MSFT', 'GLW', 'SCHW', 'FCX', 'MDT', 'V', 'MPC', 'ALL', 'NTAP', 'MMV', 'RLC', 'SO', 'JNPR', 'WEC', 'IBM', 'CAT', 'BAC', 'CAG', 'LM', 'LH', 'PGR', 'HIG', 'CELG', 'ZION', 'STI', 'STZ', 'RSG', 'PNC', 'BXP', 'GOOGL', 'AMZN', 'AON', 'PRU', 'URI', 'HRS', 'HRL', 'IPG', 'NLSN', 'RHI', 'APH', 'APC', 'APA', 'APD', 'WFC', 'NVDA', 'RTN', 'PAYX', 'ED', 'CSX', 'EW', 'STT', 'LUV', 'AES', 'ADSK', 'ECL', 'NUE', 'EXPE', 'EXPD', 'UNP', 'ETFC', 'R', 'CLX', 'BBY', 'UNH', 'OMC', 'KO', 'LNC', 'KEY', 'ITW', 'CTAS', 'SWK', 'WYNN', 'DG', 'AKAM', 'MLM', 'ALXN', 'SLG', 'DHR', 'NFLX', 'WY', 'HST', 'HSY', 'DLPH', 'CTSH', 'FITB', 'EQT', 'XLNX', 'HAS', 'THC', 'GPS', 'YUM', 'XEC', 'SYY', 'HCP', 'ESRX', 'AMAT', 'SWKS', 'KLAC', 'EMR', 'FDX', 'CRM', 'PX', 'PG', 'PH', 'PM', 'C', 'XRX', 'MON', 'MCHP', 'COP', 'KMB', 'BF-B', 'DVA', 'KMI', 'COG', 'ETN', 'ZBH', 'AAL', 'SRE', 'CB', 'CA', 'CF', 'ZTS', 'CHRW', 'SBUX', 'GNW', 'AIZ', 'EIX', 'AIV', 'LOW', 'MSI', 'DIS', 'PPG', 'NSC', 'GOOG', 'IP', 'IR', 'L', 'MTB', 'JCI', 'PWR', 'CSCO', 'BA', 'DRI', 'CCL', 'CCI', 'CCE', 'DTV', 'MYL', 'D', 'NAVI', 'PEP', 'T', 'WMB', 'VRSN', 'OI', 'CINF', 'NTRS', 'FLS', 'FLR', 'TMK', 'INTC', 'AMG', 'NWL', 'AMP', 'TMO', 'AMT', 'ICE', 'TRV', 'AVY', 'MDLZ', 'IVZ', 'NEE', 'ACN', 'NI', 'TEL', 'NE', 'NBL', 'HP', 'ADS', 'ADP', 'GILD', 'BSK', 'ADM', 'LEG', 'XEL', 'LEN', 'EBAY', 'MET', 'PDCO', 'TXN', 'DAL', 'ORCL', 'PXD', 'AA', 'PKI', 'CNP', 'HON', 'ABBV', 'ROK', 'ISRG', 'PFG']
STOCKS_1JAN2017_1JAN2018_SUCCESS_RATE_60 = ['EOG', 'YUM', 'JWN', 'VRTX', 'BWA', 'SPG', 'GT', 'GE', 'GD', 'MAS', 'MAR', 'SNA', 'XRAY', 'JNJ', 'TSN', 'BEN', 'CMI', 'CME', 'CMS', 'VLO', 'TGNA', 'FSLR', 'GRMN', 'BLX', 'FFIV', 'HCN', 'NFX', 'PRGO', 'MO', 'MS', 'AMGN', 'COST', 'FE', 'DOV', 'GLW', 'SCHW', 'FCX', 'BDX', 'WHR', 'BSK', 'MDT', 'F', 'NTAP', 'MMV', 'RLC', 'JNPR', 'CTSH', 'IBM', 'FIS', 'BAX', 'CAT', 'BAC', 'GIS', 'CAG', 'LM', 'LH', 'PGR', 'HIG', 'ABC', 'ZION', 'STI', 'STT', 'IVZ', 'PNC', 'GOOGL', 'VFC', 'AMZN', 'PRU', 'RL', 'URBN', 'CHK', 'URI', 'HRS', 'HRL', 'IPG', 'RHI', 'APC', 'APA', 'KSS', 'NVDA', 'RTN', 'EL', 'PAYX', 'OXY', 'ED', 'CSX', 'ADSK', 'ECL', 'SEE', 'NUE', 'EXPD', 'UNP', 'ETFC', 'R', 'CLX', 'UNH', 'OMC', 'KR', 'LNC', 'AEE', 'BF-B', 'WYNN', 'SWN', 'DG', 'AAP', 'WBA', 'TGT', 'DTV', 'DHI', 'MLM', 'ALXN', 'SLG', 'DHR', 'NFLX', 'WM', 'WY', 'VNO', 'HST', 'RIG', 'HSY', 'WEC', 'FITB', 'EQR', 'EQT', 'GPC', 'XLNX', 'HAS', 'GPS', 'XEC', 'SYY', 'AES', 'EMN', 'HCP', 'ESRX', 'AMAT', 'KLAC', 'FDX', 'PX', 'PG', 'MON', 'MCHP', 'COP', 'KMB', 'PEG', 'ETN', 'COL', 'TMO', 'DLTR', 'ZBH', 'SRE', 'CB', 'CA', 'CF', 'CHRW', 'GNW', 'AIZ', 'BXP', 'AIV', 'CVS', 'MSI', 'PPG', 'MNST', 'GOOG', 'IP', 'IR', 'MTB', 'VZ', 'JCI', 'CSCO', 'WDC', 'HBI', 'CCE', 'MYL', 'LYB', 'D', 'NAVI', 'DVA', 'T', 'OI', 'CINF', 'NTRS', 'HP', 'HD', 'LLY', 'TMK', 'AME', 'AMG', 'UPS', 'MPC', 'MDLZ', 'ACN', 'NI', 'TEL', 'FLS', 'ADS', 'ADP', 'DNB', 'GILD', 'ADM', 'LEG', 'EBAY', 'MET', 'TXN', 'ORCL', 'PXD', 'AA', 'ESS', 'HON', 'CNX', 'ABBV', 'ROK', 'TROW', 'ISRG', 'PFE']
STOCKS_FILTERED = ['ACN', 'MO', 'AMZN', 'AMT', 'AIV', 'AZO', 'AVGO', 'AVY', 'BLL', 'BCR', 'BDX', 'BF-B', 'CAH', 'CB', 'CI', 'CTAS', 'CLX', 'KO', 'CMCSA', 'STZ', 'CCI', 'CSX', 'DHR', 'DFS', 'DG', 'DPS', 'DTE', 'EBAY', 'EW', 'GGP', 'GIS', 'HBI', 'HOG', 'HAS', 'HCA', 'HD', 'HON', 'HRL', 'HUM', 'ITW', 'IPG', 'IFF', 'JPM', 'KSU', 'MTB', 'MAC', 'MAS', 'MA', 'KORS', 'MSFT', 'NEE', 'NLSN', 'NI', 'NOC', 'ORLY', 'PEP', 'PFE', 'PGR', 'RSG', 'ROP', 'SRE', 'SPG', 'SJM', 'SYY', 'FOXA', 'UNH', 'VFC', 'VRSN', 'XEL', 'XL', 'YUM']
STOCKS_SELECTED = ['NFLX', 'YUM', 'CCE', 'WY', 'VRTX', 'MYL', 'GIS', 'D', 'DHR', 'URI', 'HRS', 'AMGN', 'GD', 'T', 'MAS', 'MAR', 'IPG', 'OI', 'SNA', 'LEG', 'NTRS', 'DG', 'JNJ', 'SYY', 'TSN', 'BEN', 'CMI', 'CME', 'ESRX', 'NVDA', 'FDX', 'CMS', 'DTV', 'AVGO', 'ETN', 'RTN', 'AMG', 'PG', 'GRMN', 'BLX', 'SCHW', 'ED', 'FFIV', 'XRX', 'APC', 'UPS', 'NFX', 'MPC', 'MO', 'MDLZ', 'MS', 'IVZ', 'DVA', 'ACN', 'COST', 'DOV', 'TMO', 'NI', 'TEL', 'FCX', 'ECL', 'ZBH', 'BSK', 'NUE', 'HP', 'LNC', 'EXPD', 'ETFC', 'ADS', 'ADP', 'SRE', 'CB', 'CA', 'CF', 'R', 'CLX', 'UNH', 'ADM', 'OMC', 'NTAP', 'XEC', 'MMV', 'RLC', 'EBAY', 'MET', 'JNPR', 'SE', 'KLAC', 'BF-B', 'GNW', 'BXP', 'AIV', 'CAT', 'BAC', 'CAG', 'TXN', 'PPG', 'ISRG', 'LH', 'ORCL', 'PGR', 'HIG', 'ZION', 'HON', 'IP', 'IR', 'STI', 'MLM', 'STT', 'ABBV', 'ALXN', 'JCI', 'BDX', 'PRU', 'CSCO', 'PNC']
STOCKS_ERROR = ['ACE', 'ADT', 'GAS', 'ARG', 'BHI', 'BXLT', 'BRCM', 'CVC', 'CAM', 'COH', 'CSC', 'DOW', 'DD', 'EMC', 'FSIV', 'HAR', 'HON', 'HSP', 'HCBK', 'JOY', 'GMCR', 'KRFT', 'LLTC', 'MHFI', 'MJN', 'PLL', 'POM', 'PCL', 'PCP', 'RAI', 'SNDK', 'SIAL', 'STJ', 'SPLS', 'HOT', 'TE', 'TSO', 'TWC', 'TJK', 'TYC', 'WFM', 'YHOO']
SYMBOLS = list(set(STOCKS_1JAN2014_1JAN2018_SUCCESS_RATE_60) & set(STOCKS_1JAN2015_1JAN2018_SUCCESS_RATE_60) & set(STOCKS_1JAN2016_1JAN2018_SUCCESS_RATE_60) & set(STOCKS_1JAN2017_1JAN2018_SUCCESS_RATE_60))

START_DATE = datetime.date(2017, 1, 2)
END_DATE = datetime.date(2018, 1, 2)
CAPITAL = 10000


def main(
        symbols,
        start_date,
        end_date,
        capital,
):
    """Main function"""
    logging.basicConfig(filename='logs/Magi_{0}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), format='%(levelname)s: %(message)s', level=logging.INFO)

    # Prepare MarketTicks
    data_hub = DataHub()
    market_ticks_by_day = data_hub.getDailyMarketTicks(start_date, end_date, symbols)
    x_man = xMan(capital)
    magi = Magi(capital, x_man)

    for dt_idx in pandas.date_range(start_date, end_date, freq='B'):
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


if __name__ == '__main__':
    """Entry point"""
    main(
        SYMBOLS,
        START_DATE,
        END_DATE,
        CAPITAL,
    )
