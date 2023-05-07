import yfinance as yf
import pandas as pd
from yahoofinancials import YahooFinancials

#stock = yf.Ticker("MSFT")
stock = yf.Ticker("TSLA")

# get stock info
print(stock.info)

# get historical market data
hist = stock.history(period="max")
print(hist)

# show actions (dividends, splits)
print(stock.actions)

# show dividends
stock.dividends

# show splits
stock.splits

# show financials
print('financials', stock.financials)
print(stock.quarterly_financials)

# show major holders
#stock.major_holders
print(stock.major_holders)

# show institutional holders
#stock.institutional_holders
stock.institutional_holders

# show balance heet
print(stock.balance_sheet)
print(stock.quarterly_balance_sheet)

# show cashflow
print(stock.cashflow)
print(stock.quarterly_cashflow)

# show earnings
print('earnings', stock.earnings)
print(stock.quarterly_earnings)

# show sustainability
stock.sustainability

# show analysts recommendations
print('recommendation', stock.recommendations)

# show next event (earnings, etc)
stock.calendar

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
stock.isin

# show options expirations
print(stock.options)

# get option chain for specific expiration
#opt = stock.option_chain('YYYY-MM-DD')
opt = stock.option_chain('2020-09-17')
# data available via: opt.calls, opt.puts

yahoo_financials = YahooFinancials('TSLA')

data = yahoo_financials.get_historical_price_data(start_date='2000-01-01',
                                                  end_date='2019-12-31',
                                                  time_interval='weekly')

tsla_df = pd.DataFrame(data['TSLA']['prices'])
tsla_df = tsla_df.drop('date', axis=1).set_index('formatted_date')
print(tsla_df.head())

#print(yahoo_financials.get_key_statistics_data())
#print(yahoo_financials.get_financial_stmts('quarterly', 'income'))
#print(yahoo_financials.get_stock_earnings_data())

'''
data = yf.download(  # or pdr.get_data_yahoo(...
        # tickers list or string as well
        tickers = "SPY AAPL stock",

        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "ytd",

        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval = "1m",

        # group by ticker (to access via data['SPY'])
        # (optional, default is 'column')
        group_by = 'ticker',

        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust = True,

        # download pre/post regular market hours data
        # (optional, default is False)
        prepost = True,

        # use threads for mass downloading? (True/False/Integer)
        # (optional, default is True)
        threads = True,

        # proxy URL scheme use use when downloading?
        # (optional, default is None)
        proxy = None
    )
'''