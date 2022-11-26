from utils.data_hub import DataHub
from x_man import Order, MarketTick, Position, xMan, ORDER_STATE_NEW, ORDER_STATE_PARTIALLY_FILLED, ORDER_STATE_FULLY_FILLED, ORDER_STATE_CANCELLED, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, ORDER_TYPE_STOP, ORDER_DIRECTION_BUY, ORDER_DIRECTION_SELL
import logging
import datetime
import math
import pandas

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
SD_PERIOD = 22
# This is for trading signal logic
LOOK_BACK_PERIOD = 22
# This allows to trade on next day's open
LOOK_FORWARD_PERIOD = 0
MA_SHORT_PERIOD = 5
MA_LONG_PERIOD = SD_PERIOD
TRIGGER_DISTANCE = 3
STOP_ORDER_DISTANCE = 2
LIMIT_ORDER_DISTANCE = 2
ORDER_LIMIT = 1000
CAPITAL = 10000


class Magi:
    def __init__(self):
        self.xMan = xMan(CAPITAL)
        self.dataHub = DataHub()
        self.symbolData = None
        # Strategy config
        self.symbols = SYMBOLS
        self.startDate = START_DATE
        self.endDate = END_DATE
        self.sdPeriod = SD_PERIOD
        self.lookBackPeriod = LOOK_BACK_PERIOD
        self.lookForwardPeriod = LOOK_FORWARD_PERIOD
        self.MAShortPeriod = MA_SHORT_PERIOD
        self.MALongPeriod = MA_LONG_PERIOD
        self.triggerDistance = TRIGGER_DISTANCE
        self.stopOrderDistance = STOP_ORDER_DISTANCE
        self.limitOrderDistance = LIMIT_ORDER_DISTANCE
        self.orderLimit = ORDER_LIMIT
        self.capital = CAPITAL

        self.logConfig()

    def __str__(self):
        return 'He is my shield!'

    def logConfig(self):
        logging.info('============================================================')
        logging.info('Magi strategy config:')
        logging.info('SYMBOLS; {}'.format(self.symbols))
        logging.info('START_DATE: {}'.format(self.startDate))
        logging.info('END_DATE: {}'.format(self.endDate))
        logging.info('SD_PERIOD: {}'.format(self.sdPeriod))
        logging.info('LOOK_BACK_PERIOD: {}'.format(self.lookBackPeriod))
        logging.info('LOOK_FORWARD_PERIOD: {}'.format(self.lookForwardPeriod))
        logging.info('MA_SHORT_PERIOD: {}'.format(self.MAShortPeriod))
        logging.info('MA_LONG_PERIOD: {}'.format(self.MALongPeriod))
        logging.info('TRIGGER_DISTANCE: {}'.format(self.triggerDistance))
        logging.info('STOP_ORDER_DISTANCE: {}'.format(self.stopOrderDistance))
        logging.info('LIMIT_ORDER_DISTANCE: {}'.format(self.limitOrderDistance))
        logging.info('ORDER_LIMIT: {}'.format(self.orderLimit))
        logging.info('CAPITAL: {}'.format(self.capital))
        logging.info('============================================================')

    def setUpConfig(self, symbols=SYMBOLS, startDate=START_DATE, endDate=END_DATE, sdPeriod=SD_PERIOD, lookBackPeriod=LOOK_BACK_PERIOD, lookForwardPeriod=LOOK_FORWARD_PERIOD, MAShortPeriod=MA_SHORT_PERIOD, MALongPeriod=MA_LONG_PERIOD, triggerDistance=TRIGGER_DISTANCE, stopOrderDistance=STOP_ORDER_DISTANCE, limitOrderDistance=LIMIT_ORDER_DISTANCE, orderLimit=ORDER_LIMIT, capital=CAPITAL):
        self.symbols = symbols
        self.startDate = startDate
        self.endDate = endDate
        self.sdPeriod = sdPeriod
        self.lookBackPeriod = lookBackPeriod
        self.lookForwardPeriod = lookForwardPeriod
        self.MAShortPeriod = MAShortPeriod
        self.MALongPeriod = MALongPeriod
        self.triggerDistance = triggerDistance
        self.stopOrderDistance = stopOrderDistance
        self.limitOrderDistance = limitOrderDistance
        self.orderLimit = orderLimit
        self.capital = capital
        self.logConfig()

    def prepareSymbolData(self):
        self.symbolData = self.dataHub.downloadDataFromYahoo(self.startDate, self.endDate, self.symbols)

    def getStartIndex(self):
        return max(self.sdPeriod, self.lookBackPeriod, self.MAShortPeriod, self.MALongPeriod)

    def getEndIndex(self):
        return -self.lookForwardPeriod

    def getOrderSize(self, price):
        """Esitmate the order size based on the current price and order limit"""
        #TODO: We need to improve the logic
        return math.floor(self.orderLimit / price)

    def runStrategyOnMarketTick(self, marketTick):
        """
        Run strategy for the marketTick given for a specific symbol.
        The strategy probably also depends on past marketTicks, which need to be looked up in self.symbolData
        Place orders based on strategy signals
        """
        # We do not execute strategy if we already have an open position.
        #position = self.xMan.getPositionBySymbol(marketTick.symbol)
        #if position and position.quantity != 0:
        #    return

        ts = self.symbolData[marketTick.symbol]['Close']
        sd = ts[:marketTick.dtIdx][-self.sdPeriod:].std()
        highest = ts[:marketTick.dtIdx][-self.lookBackPeriod:].max()
        lowest = ts[:marketTick.dtIdx][-self.lookBackPeriod:].min()
        MAShort = ts[:marketTick.dtIdx][-self.MAShortPeriod:].mean()
        MALong = ts[:marketTick.dtIdx][-self.MALongPeriod:].mean()
        currPrice = marketTick.close

        if currPrice < highest - sd * self.triggerDistance and currPrice >= MAShort:
            quantity = self.getOrderSize(currPrice)
            #TODO: Without knowledge of the next marketTick, we place orders based on current marketTick
            if quantity > 0:
                marketOrder = Order(marketTick.symbol, ORDER_DIRECTION_BUY, ORDER_TYPE_MARKET, float('nan'), quantity, marketTick.dtIdx)
                self.xMan.placeOrder(marketOrder)
                logging.info('Magi: runStrategyOnMarketTick: TRIGGER BUY: Placed marketOrder={}'.format(marketOrder))
                stopOrder = Order(marketTick.symbol, ORDER_DIRECTION_SELL, ORDER_TYPE_STOP, currPrice-sd*self.stopOrderDistance, quantity, marketTick.dtIdx)
                limitOrder = Order(marketTick.symbol, ORDER_DIRECTION_SELL, ORDER_TYPE_LIMIT, currPrice + sd * self.limitOrderDistance, quantity, marketTick.dtIdx)
                self.xMan.linkOrders([stopOrder, limitOrder])
                self.xMan.placeOrder(stopOrder)
                logging.info('Magi: runStrategyOnMarketTick: Placed stopOrder={}'.format(stopOrder))
                self.xMan.placeOrder(limitOrder)
                logging.info('Magi: runStrategyOnMarketTick: Placed limitOrder={}'.format(limitOrder))
            else:
                logging.info('Magi: runStrategyOnMarketTick: TRIGGER BUY, but cannot trade due to quantity=0, marketTick={}'.format(marketTick))

    def run(self):
        self.prepareSymbolData()

        # Determine trading range for running strategy. Exclude periods for strategy setup, endIdx Not inclusive
        dtIndexes = pandas.date_range(self.startDate, self.endDate, freq='B')
        startIdx = self.getStartIndex()
        endIdx = self.getEndIndex()
        logging.debug('Magi: run: startIdx={}, endIdx={}'.format(startIdx, endIdx))

        for dtIdx in dtIndexes:
            logging.info('============================================================')
            logging.info(dtIdx)
            logging.info('------------------------------------------------------------')
            logging.info('Execute existing orders and run strategy for today')
            logging.info('------------------------------------------------------------')
            for symbol in self.symbolData.keys():
                if dtIdx not in (self.symbolData[symbol].index[startIdx:] if endIdx == 0 else self.symbolData[symbol].index[startIdx: endIdx]):
                    logging.debug('Magi: run: dtIdx={}: Cannot trade, outside strategy running period'.format(dtIdx))
                    continue

                # Construct marketTick for this tradingDate
                open = self.symbolData[symbol].loc[dtIdx, 'Open']
                close = self.symbolData[symbol].loc[dtIdx, 'Close']
                high = self.symbolData[symbol].loc[dtIdx, 'High']
                low = self.symbolData[symbol].loc[dtIdx, 'Low']
                volume = self.symbolData[symbol].loc[dtIdx, 'Volume']
                marketTick = MarketTick(symbol, open, close, high, low, volume, dtIdx)

                # Execute existing orders from previous tradingPeriod. In reality, this happens during current tradingPeriod.
                self.xMan.executeOrdersOnMarketTick(marketTick)

                # Run strategy on current tradingPeriod. In reality, this happens immediately after current tradingPeriod.
                self.runStrategyOnMarketTick(marketTick)

            logging.info('------------------------------------------------------------')
            logging.info('Performance Summary for today')
            logging.info('------------------------------------------------------------')
            self.xMan.evaluatePerformance()
            logging.info('============================================================')

        self.xMan.describeTradesExecutedByDatetime()


def main():
    """Main function"""
    #logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.basicConfig(filename='Magi_{0}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), format='%(levelname)s: %(message)s', level=logging.INFO)
    magi = Magi()
    magi.run()


if __name__ == '__main__':
    """Entry point"""
    main()
