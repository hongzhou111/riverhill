import time
from datetime import datetime
from datetime import timedelta
import pandas as pd
from test_mongo import MongoExplorer
from stockstats import StockDataFrame as Sdf
from test_stockstats_v2 import StockStats
from test_rl_macd_v3 import StockRL
import csv
import json
import numpy as np
import math
import pytz
#from pytz import utc
import robin_stocks.robinhood as rh
#import os.path
import copy
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

class TS_10Sec_Reader:
    def __init__(self, ticker):
        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        self.ticker = ticker

    def read_lvl1(self,aaod):
        start = f'{aaod}T13:30:00Z'
        end = f'{aaod}T20:01:00Z'

        collection = f"{self.ticker}_10sec_ts_lvl1"
        query = {'$and': [{'CurTime': {'$gte': start}}, {'CurTime': {'$lt': end}}]}
        return pd.DataFrame(list(self.mongoDB[collection].find(query)))

    def read_lvl2(self,aaod):
        start = f'{aaod}T13:30:00Z'
        end = f'{aaod}T20:01:00Z'

        collection = f"{self.ticker}_10sec_ts_lvl2"
        query = {'$and': [{'CurTime': {'$gte': start}}, {'CurTime': {'$lt': end}}]}
        return pd.DataFrame(list(self.mongoDB[collection].find(query)))

    def match(self, aaod):
        lvl1 = self.read_lvl1(aaod)
        # print(lvl1)
        lvl2 = self.read_lvl2(aaod)

        # ceiling lvl2 getTime to 10sec
        # lvl2['TradeTime'] = pd.to_datetime(lvl2['GetTime'])
        # lvl2['TradeTime'] += np.array(-lvl2['TradeTime'].dt.second % 10, dtype='<m8[s]')
        # lvl2['TradeTime'] = lvl2['TradeTime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        # print(lvl2['GetTime'].unique())
        # print(lvl2['TradeTime'].unique())
        # print(lvl2)

        df = pd.merge(lvl1, lvl2, on='CurTime', how='left')
        # print(df.head(100))

        # compute exp of price diff,  Bid and Ask are opposite formula
        df1 = df[df['Side'] == 'Bid']
        df1['g'] = np.exp(100*(df1['Price'] - df1['Last'])/df1['Last'])

        df2 = df[df['Side'] == 'Ask']
        df2['g'] = -np.exp(100*(df2['Last'] - df2['Price'])/df2['Last'])

        df3 = pd.concat([df1, df2])
        df3['lvl2'] = df3['g'] * df3['TotalSize']
        # print(df3.head(100))

        # compute sum
        df4 = pd.DataFrame(columns=['CurTime', 'lvl2'])
        df4['CurTime'] = df3['CurTime']
        df4['lvl2'] = df3['lvl2']

        s = df4.groupby('CurTime').sum().reset_index()
        # print(s)

        # merge the lvl2 impact index back to lvl1
        l = pd.merge(lvl1, s, on='CurTime', how='left')
        l['Close'] = l['Last']
        # l['Close'] = l['lvl2']
        l['Date'] = l['CurTime']

        ss = StockStats(self.ticker, interval='no')
        ss.stock = l
        ss.stock = Sdf.retype(ss.stock)
        ss.macd(6, 13, 9)
        ss.stock.reset_index()
        # print(ss.stock)

        csv_name = f'{self.ticker}_lvl1_lvl2.csv'
        ss.stock.to_csv(csv_name)

ticker = 'AAPL'     #'AMZN'     #'TSLA'     #'NVDA'
aaod = '2023-06-05'
ts = TS_10Sec_Reader(ticker)
ts.match(aaod)

