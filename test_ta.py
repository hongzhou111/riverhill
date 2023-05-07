import pandas as pd
import ta
from pandas_datareader import data as web
import datetime
import numpy as np
from ta.utils import dropna
import matplotlib.pyplot as plt

#stock = 'GPL'
stock = 'GPL'
start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%m-%d-%Y")
# end_date = datetime.datetime(2020,2,20)
df = web.DataReader(stock, data_source='yahoo', start=start_date)

df = dropna(df)
plt.plot(df['Close'])

#macd = ta.trend.MACD(close=df['Close'], n_slow=31, n_fast= 15,n_sign=9)
#df['MACD'] = macd.macd_diff()
#plt.plot(macd.macd())
#plt.plot(macd.macd_signal())
#plt.plot(macd.macd_diff())

df['CCI'] = ta.trend.cci(df['High'], df['Low'], df['Close'], n=31, c=0.015)
plt.plot(df['CCI'])
plt.axhline(y=0, color='r', linestyle='-')

#df['RSI'] = ta.momentum.RSIIndicator(df['Close'], n = 14).rsi()
#plt.plot(df['RSI'])

plt.show()
