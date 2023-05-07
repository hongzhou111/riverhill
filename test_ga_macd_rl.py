'''
GA Algorithm with RL MACD

gene:                               buy/sell decision models(m - 2. RL and MACD crossover )
chromesome:                         stock(s)
Population:                         portfolio(p = stocks + cash)
fitness:                            MACD, RL, CAP
initialization:                     buy 9 stocks, each for 100k, keep 100k cash, total 1000k
generation:
    crossover                       sell if 2 > rl >= 1
    mutate                          buy 100k (or 10% of total) for rl < 1, sorted by
                                        1. CAP
                                        2. model_perf

    repeat generation               daily
'''
#import time
#import logging
from datetime import datetime
from datetime import timedelta
#import pymongo
#import json
#import traceback
import math
import random
from bson import json_util
from datetime import datetime
from datetime import timedelta
#import json
#import numpy as np
from test_mongo import MongoExplorer
import pandas as pd
#from pandas import json_normalize
#from test_yahoo import QuoteExplorer
from test_g20_v2 import StockScore
#from openpyxl import load_workbook
#from test_stockstats import StockStats
from test_fundamentals import StockFundamentalsExplorer
import yfinance as yf
from stockstats import StockDataFrame as Sdf


class RuleGA_MACD_RL:
    def __init__(self, save_p_flag=0):
        mongo_client = MongoExplorer()
        self.mongoDB = mongo_client.mongoDB
        self.save_p_flag = save_p_flag
        self.long = 6
        self.short = 13
        self.signal = 9

        #self.preferList = ['AMZN', 'AAPL', 'TSLA', 'SHOP', 'FB', 'MSFT', 'GOOGL', 'NFLX', 'NVDA', 'SQ', 'TTD']
        #self.preferList = ['AMZN', 'AAPL', 'TSLA', 'SHOP']
        #self.preferList = ['TSLA']
        #self.preferList = ['AMZN']
        #self.preferList = ['GOOGL']
        #self.preferList = ['SHOP']
        #self.preferList = ['AMZN', 'TSLA', 'BKNG']
        #self.preferList = ['AMZN', 'TSLA', 'MSFT']
        #self.preferList = ['AMZN', 'TSLA']
        #self.preferList = []
        self.protectList = ['AMZN', 'TSLA', 'SHOP', 'SQ', 'MBD', 'OKTA']

    def getDate(self, d):   #convert '2009-12-11' to a datetime
        return datetime(*(int(s) for s in d.split('-')))

    def getPreDate(self, s, d):
        q = self.getQuote(s)
        try:
            i = q.index[(q['date'] == d)].tolist()[0] - 1
        except Exception as error:
            print(error)
            i = -1
        if i >= 0:
            return q.iloc[i]['date'].strftime('%Y-%m-%d')
        else:
            return '1900-01-01'

    def fitness(self, ticker, aaod, always_run_rl=False):
        #startTime = datetime.now()
        result = None
        existing_ga = 0
        #ss = StockStats(ticker, aaod)
        #m = ss.macd_by_date_with_threshold(aaod, self.short, self.long, self.signal)
        ##print(m)
        #aaod1 = (datetime(*(int(s) for s in aaod.split('-'))) + timedelta(days=-1)).strftime('%Y-%m-%d')
        aaod1 = self.getPreDate(ticker, aaod)
        #query = {'$and': [{'symbol': ticker}, {'$or': [{'date': aaod}, {'date': aaod1}]}]}
        #query = {'$and': [{'symbol': ticker}, {'$or': [{'date': aaod, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}}, {'date': aaod1, 'r': {'$lt': 0.2}, 'len': {'$lt': 5}}, {'date': aaod1, 'r': {'$gte': 0.2}}]}]}
        query = {'$and': [{'symbol': ticker}, {'$or': [{'date': aaod, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}}, {'date': aaod1, 'r': {'$lt': 0.2}, 'len': {'$lt': 5}}, {'date': aaod1, 'r': {'$gte': 0.2}}]}]}
        #query = {'$and': [{'symbol': ticker}, {'$or': [{'date': aaod, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}}, {'date': aaod1, 'r': {'$gte': 0.2},'len': {'$gte': 5}}]}]}
        #query = {'symbol': ticker, 'date': aaod}
        #print(query)
        #crossing = self.mongoDB['macd_crossings'].find_one(query)
        #print(crossing)
        if self.mongoDB['macd_crossings'].count_documents(query) > 0:
        #if m['post_threshold_flag'] == 0 and ((m['r'] < 0.2 and m['len'] >= 5) or (m['len'] == 1 and m['pre_len'] >= 5)):
            print(ticker, 'check g20', aaod)
            #endTime = datetime.now()
            #runTime = endTime - startTime
            #print('fitness run time', runTime)

        #query2 = {'symbol': ticker, 'runDate': aaod}
            #if self.mongoDB['stock_g_score'].count_documents(query2) > 0:
                #result = self.mongoDB['stock_g_score'].find_one(query2)
                #if result.get('rl_result') is None:
                    #existing_ga = 0
                    #print('fitness:', result)
                    #result = None
                #else:
                    #existing_ga = 1
            #else:
            if existing_ga == 0:
                try:
                        g20 = StockScore({'AAOD': aaod, 'symbol': ticker, 'rl_save_loc': './ga_macd_rl/test_rl_'})
                        #g20.run(save_rl=True, always_run_rl=always_run_rl, retrain_rl=False)
                        g20.run(save_rl=True, always_run_rl=always_run_rl, retrain_rl=True)
                        g20.save_g20()
                        #print(g20.result)
                        if g20.result.get('rl_result') is not None:
                            #print(self.c2)
                            #print(json.dumps(g20.result, indent=4))
                            result = g20.result
                except Exception as error:
                    print(error)
                    result = None
        #3print('fitness:', result)
        return result

    def getQuote(self, s):
        q = pd.DataFrame()
        try:
            y = yf.Ticker(s)
            df = y.history(period="max")
            df = df.reset_index()
            q = Sdf.retype(df)
            q = q.reset_index()
        except Exception as error:
            print(error)
            #continue
        return q

    def getPrice(self, s, d):
        #col = self.mongoDB.get_collection(s)
        #query = {'Date': d}
        #quote = col.find_one(query)
        #if quote != None :
        #    return quote['Close']
        #else:
        #    return 0
        close = 0
        q = self.getQuote(s)
        try:
            close = q.loc[q['date'] == d]['close'].values[0]
            #print(close)
        except Exception as error:
            print(error)
            #continue
        return close

    def getNextQuote(self, s, d):
        nq = pd.DataFrame()
        q = self.getQuote(s)
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i+1]
        except Exception as error:
            print(error)
            #continue
        return nq

    def getCAP(self, s, d):
        f = StockFundamentalsExplorer()
        f.get_fund(s, d)
        shares = f.get_shares()
        price = self.getPrice(s,d)
        return shares * price

    def getCAPList(self, d):
        exclusionList = ['GOOG', 'JMDA', 'QRHC', 'CCGN', 'BRVO', 'PIC', 'ELLI', 'HMTA', 'EIC', 'PUODY', 'PEER',
                         'BLMT', 'GOLD', 'TRCK', 'ATPT', 'VALE', 'TS', 'CLB', 'ITUB', 'PBR', 'RHHBY', 'JAGGF',
                         'CEO', 'BBL', 'MDT', 'ENB', 'LUKOY', 'SU', 'CNQ', 'BB', 'MFC', 'ZURVY', 'LFC', 'EEM',
                         'GG', 'SGTZY', 'GLD', 'TS', 'ACN', 'PTR', 'SSL', 'HDB', 'CNI', 'MBT', 'WFT', 'SNP', 'AABA',
                         'RCI', 'YARIY', 'SYMC', 'AUY', 'PHI', 'BVN', 'EGO', 'SNN', 'SJR', 'FRFHF', 'LLL',
                         'CHA', 'BCH', 'CHKP', 'QGEN', 'SQM', 'SBS', 'ACH', 'CEL', 'PAAS', 'RE', 'OTEX', 'ESLT',
                         'CLB', 'NAK', 'LOGI', 'STE', 'ILF', 'RNR', 'RBYCF', 'CPA', 'CMPR', 'SA', 'STN', 'ESGR',
                         'ATU', 'CPL', 'GSIH', 'MFCB', 'NICE', 'PUODY', 'SEDG', 'LULU', 'HOKCY', 'APTV', 'BGNE',
                         'XMEX', 'GSX', 'GRWG', 'MNST', 'GDS', 'SE', 'MELI', 'DQ', 'SWET', 'INFO', 'TT', 'GBTC',
                         'HZNP', 'OCFT'' GOOG', 'YY', 'BCEI', 'SFUN', 'NBRI', 'PTRC', 'FET', 'NBRI', 'BASX', 'LPI',
                         'TS', 'CLB', 'ITUB', 'PBR', 'RHHBY', 'JAGGF', 'CEO', 'BBL', 'MDT', 'ENB',
                         'LUKOY', 'SU', 'CNQ', 'BB', 'MFC', 'ZURVY', 'LFC', 'EEM', 'GG', 'SGTZY',
                         'GLD', 'TS', 'ACN', 'PTR', 'SSL', 'HDB', 'CNI', 'MBT', 'WFT', 'SNP', 'AABA',
                         'RCI', 'YARIY', 'SYMC', 'AUY', 'PHI', 'BVN', 'EGO', 'SNN', 'SJR', 'FRFHF', 'LLL',
                         'CHA', 'BCH', 'CHKP', 'QGEN', 'SQM', 'SBS', 'ACH', 'CEL', 'PAAS', 'RE', 'OTEX', 'ESLT',
                         'CLB', 'NAK', 'LOGI', 'STE', 'ILF', 'RNR', 'RBYCF', 'CPA', 'CMPR', 'SA', 'STN', 'ESGR',
                         'ATU', 'CPL', 'GSIH', 'MFCB', 'NICE', 'PUODY', 'SEDG', 'LULU', 'HOKCY', 'APTV', 'BGNE',
                         'XMEX', 'GSX', 'GRWG', 'MNST', 'GDS', 'SE', 'MELI', 'DQ', 'SWET', 'INFO', 'TT', 'GBTC',
                         'HZNP', 'OCFT', 'GOOG', 'YY', 'BCEI', 'NPSNY', 'BRDCY', 'CPRI', 'BOTY', 'NXPI', 'XFLS',
                          'BBD', 'GPH', 'PAGS', 'PHIL', 'GFKSY', 'CNNA', 'DLOC', 'SEII', 'WWR', 'MT', 'DB', 'OIBRQ',
                         'BIEI', 'RMSL', 'KMI', 'NAKD', 'NSPX', 'BHP', 'TNXP', 'SBFM', 'SHIP', 'SEEL', 'FANH',
                         'LSXMK', 'EC', 'COTY', 'CLR', 'HWM', 'PENN', 'FSLR', 'IAU', 'ALXN', 'WLL','LNVGY']

        cList = []
        #d1 = (datetime(*(int(s) for s in d.split('-'))) + timedelta(days=-1)).strftime('%Y-%m-%d')
        d1 = self.getPreDate('AMZN', d)
        #query = {'$and': [{'accum': {'$lt': 0}}, {'symbol': {'"$nin': exclusionList}}, {'$or': [{'date': d}, {'date': d1}]}]}
        #query = {'$and': [{'accum': {'$lt': 0}}, {'$or': [{'date': d}, {'date': d1}]}]}
        #query = {'$and': [{'accum': {'$lt': 0}}, {'$or': [{'date': d, 'r': {'$lt': 0.2}}, {'date': d1, 'r': {'$gte': 0.2}}]}]}
        #query = {'$and': [{'accum': {'$lt': 0}}, {'$or': [{'date': d, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}}, {'date': d1, 'r': {'$lt': 0.2}, 'len': {'$lt': 5}}, {'date': d1, 'r': {'$gte': 0.2}}]}]}
        #query = {'$and': [{'accum': {'$lt': 0}}, {'$or': [{'date': d, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}}, {'date': d1, 'r': {'$gte': 0.2}, 'len': {'$gte': 5}}]}]}
        query = {'$or': [{'date': d, 'r': {'$lt': 0.2}, 'len': {'$gte': 5}},
                         {'date': d1, 'r': {'$lt': 0.2}, 'len': {'$lt': 5}},
                         {'date': d1, 'r': {'$gte': 0.2}}]}
        #print(query)
        #com = self.mongoDB['etrade_companies'].find(no_cursor_timeout=True)
        com = self.mongoDB['macd_crossings'].find(query, no_cursor_timeout=True)
        #print(self.mongoDB['macd_crossings'].count_documents(query))
        #dbList = self.mongoDB.list_collection_names()
        index = 1
        for c in com:
            #print(index, c['symbol'])
            #if c['Yahoo_Symbol'] in dbList:
            try:
                #ss = StockStats(c['Yahoo_Symbol'], d)
                #m = ss.macd_by_date_with_threshold(d, self.short, self.long, self.signal)
                #if m['post_threshold_flag'] == 0 and ((m['r'] < 0.2 and m['len'] >= 5) or (m['len'] == 1 and m['pre_len'] >= 5)):
                #cap = self.getCAP(c['symbol'], d)
                #cap = c['CAP']
                price = self.getPrice(c['symbol'], d)
                #if c['symbol'] not in exclusionList and c['CAP'] >= 10000:
                if c['symbol'] not in exclusionList and c['CAP'] >= 5000 and price < 5000:
                    #if c['symbol'] in self.p['prefer_list']:
                        #c['CAP'] = c['CAP'] * 10
                    cList.append({'symbol': c['symbol'], 'CAP': c['CAP']})
            except Exception as error:
                print(error)
                #continue
            index = index + 1
        cList = sorted(cList, key=lambda k: k['CAP'], reverse=True)
        print('cList', cList)
        return cList

    def getSellPrice(self, s, d):
        #nq = pd.DataFrame()
        q = self.getQuote(s)
        c = 0
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i]
            c = random.uniform(nq['open'], nq['high'])
        except Exception as error:
            print(error)
            #continue
        return c

    def getBuyPrice(self, s, d):
        #nq = pd.DataFrame()
        q = self.getQuote(s)
        c = 0
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i]
            c = random.uniform(nq['open'], nq['low'])
        except Exception as error:
            print(error)
            #continue
        return c

    def getTotal(self, d):
        total = self.p['cash']
        for s in self.p['stocks']:
            price = self.getPrice(s['symbol'], d)
            total = total + price * s['share']
        return total

    def getPerf(self, ticker):
        cost = 0
        worth = 0
        index = 0
        for i, s in enumerate(self.p['stocks']):
            if s['symbol'] == ticker:
                ss = self.p['stocks'][i]
                for j, a in enumerate(ss['actions']):
                    index += 1
                    if a['action_type'] == 'buy':
                        cost += a['value']
                    elif a['action_type'] == 'sell':
                        worth -= a['value']
                break
        #gain = worth - cost + s['share'] * self.getPrice(ticker, d)
        #perf = (worth / cost) ** (index / 2)
        perf = worth / cost
        return cost, worth, perf, index

    def getTotalPerf(self):
        total_perf = self.p['total_history'][len(self.p['total_history']) - 1]['total'] / self.p['total_history'][0]['total']     # / self.p['total_history'][0]['total']

        amzn_init = self.getPrice('AMZN', self.p['total_history'][0]['date'])
        amzn_end = self.getPrice('AMZN', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        amzn_perf = amzn_end / amzn_init

        #aapl_init = self.getPrice('AAPL', self.p['total_history'][0]['date'])
        #aapl_end = self.getPrice('AAPL', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        #aapl_perf = aapl_end / aapl_init

        #shop_init = self.getPrice('SHOP', self.p['total_history'][0]['date'])
        #shop_end = self.getPrice('SHOP', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        #if shop_init != 0:
        #    shop_perf = shop_end / shop_init
        #else:
        #    shop_perf = 0

        bkng_init = self.getPrice('BKNG', self.p['total_history'][0]['date'])
        bkng_end = self.getPrice('BKNG', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        if bkng_init != 0:
            bkng_perf = bkng_end / bkng_init
        else:
            bkng_perf = 0

        msft_init = self.getPrice('MSFT', self.p['total_history'][0]['date'])
        msft_end = self.getPrice('MSFT', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        if msft_init != 0:
            msft_perf = msft_end / msft_init
        else:
            msft_perf = 0

        tsla_init = self.getPrice('TSLA', self.p['total_history'][0]['date'])
        tsla_end = self.getPrice('TSLA', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        if tsla_init != 0:
            tsla_perf = tsla_end / tsla_init
        else:
            tsla_perf = 0

        return total_perf, amzn_perf, msft_perf, tsla_perf, self.p['total_history'][len(self.p['total_history']) - 1]['date'], self.p['total_history'][0]['date']

    def getBuyAmt(self):
        #n = len(self.p['prefer_list'])
        i = len(self.p['prefer_list'])
        #if n < 5:
        #    i = n
        #else:
        #    i = 5

        if i > 0:
            buy_amt = self.p['cash']
        else:
            j = int(self.p['cash'] / 100000)
            if j > 0:
                buy_amt = self.p['cash'] / j
            else:
                buy_amt = self.p['cash']
        while i > 1:
            if self.p['cash'] > (i - 1) * 100000:
                buy_amt = self.p['cash'] / i
                break
            i -= 1
        return buy_amt

    def init(self, pn, date, endDate, init_cash, ss):           # pn - portfolio name;  d = start date,  10 years back; endDate = last date for the evaluation; ss = initial stock list
        preferList = ['BLK', 'NTES', 'NVDA', 'ISRG', 'BFAM', 'NFLX', 'TSLA', 'WDAY', 'W', 'MTCH', 'CPRT', 'SHOP', 'GWRE',
                      'MKTX', 'ROKU', 'ALNY', 'ZS', 'COUP', 'TEAM', 'VEEV', 'GNRC', 'PFPT', 'EPAM', 'SQ', 'NVR',
                      'AMZN', 'NIO', 'BIO', 'BL', 'OKTA', 'CMG', 'DG', 'MCHP', 'DLTR', 'MA', 'ROST', 'ASML', 'BIIB',
                      'CME', 'GILD', 'CHTR', 'CTSH', 'REGN', 'NOW', 'FBHS', 'HII', 'DELL', 'ANET', 'FB', 'YUMC',
                      'SHOP', 'ISRG', 'ORLY', 'ZTS', 'SPOT', 'W', 'EW', 'NVR', 'GOOGL']
                      #'FLT'
        self.p = {
            "name": pn,
            "init_date": date,
            'end_date': endDate,
            "last_update_date": date,
            "last_cross_sell_date": date,
            "last_cross_buy_date": date,
            "last_mutate_buy_date": date,
            "crossover_sell_flag": 1, # 1 execute;  0 skip
            "crossover_sell_no": 100,
            "crossover_buy_no": 100,
            "mutate_buy_flag": 1, # 1 execute;  0 skip
            "mutate_buy_no": 1,
            "mutate_buy_threshold": 0.80,
            "cash": init_cash,
            'total': init_cash,
            "total_history": [],
            "prefer_list": preferList
        }
        #init_cash = 500000
        stocks = []
        #get stock price
        #AMZN, ANTM, TSLA, COST, ISRG, CRM, ATVI, AAPL, GS, GE
        if ss == []:
            #ss = ['AMZN', 'ANTM', 'TSLA', 'COST', 'ISRG', 'CRM', 'FB', 'AAPL', 'GS', 'GOOGL']
            #ss = self.p['prefer_list'][0:10]
            ss = self.p['prefer_list']
            for symbol in ss:
                price = self.getPrice(symbol, date)
                if price > 0:
                    share = math.floor(100000 / price)
                    position = price * share
                    #g = self.fitness(symbol, date, always_run_rl=True)
                    g = None
                    stock = {
                        "symbol":   symbol,
                        "share":    share,
                        "actions":
                            [
                                {
                                    "date": date,
                                    "action_type": "buy",
                                    "reason": "initial_buy",
                                    "fitness": g,
                                    "price": price,
                                    "share": share,
                                    "value": position
                                }
                            ]
                    }
                    stocks.append(stock)
        else:
            #print(ss)
            for s in ss:
                price = self.getPrice(s['symbol'], date)
                if price > 0:
                    #share = math.floor(100000 / price)
                    share = s['shares']
                    position = price * share
                    g = self.fitness(s['symbol'], date, always_run_rl=True)
                    stock = {
                        "symbol":   s['symbol'],
                        "share":    share,
                        "actions":
                            [
                                {
                                    "date": date,
                                    "action_type": "buy",
                                    "reason": "initial_buy",
                                    "fitness": g,
                                    "price": price,
                                    "share": share,
                                    "value": position
                                }
                            ]
                    }
                    stocks.append(stock)

        self.p['stocks'] = stocks
        total = self.getTotal(date)
        self.p['total'] = total
        self.p['total_history'].append({"date": date, "cash": self.p['cash'], "total": total})
        if self.save_p_flag > 0:
            self.save_p()
        return self.p

    def reload(self, pn, newEndDate):
        if self.mongoDB['stock_ga_results'].count_documents({'name': pn}) > 0:
            self.p = self.mongoDB['stock_ga_results'].find_one({'name': pn})
            if 'last_cross_sell_date' not in self.p:
                self.p['last_cross_sell_date'] = self.p['end_date']
            if 'last_cross_buy_date' not in self.p:
                self.p['last_cross_buy_date'] = self.p['end_date']
            if 'last_mutate_buy_date' not in self.p:
                self.p['last_mutate_buy_date'] = self.p['end_date']
            self.p['end_date'] = newEndDate
            if 'prefer_list' not in self.p:
                self.p['prefer_list'] = []

            return self.p
        else:
            return None

    def crossover_sell(self, aaod, crossSellFlag):
        #print('crossover_sell:', startDate, endDate)
        execute_flag = 0
        if crossSellFlag > 0:
            fList = []
            for i, s in enumerate(self.p['stocks']):
                if s['share'] > 0:
                    f = self.fitness(s['symbol'], aaod, always_run_rl=True)
                    #if f is not None and f['Reason'] == 'predict_action >= 1':
                    if f is not None and f['rl_result']['predict_action'] >= 1 and f['rl_result']['predict_vol'] > 0 and f['rl_result']['predict_action'] < 2:      # and f['Reason'] != 'len < 5':
                        f['sIndex'] = i
                        fList.append(f)
            fList = sorted(fList, key=lambda k: k['CAP'], reverse=False)
            #print(fList)
            crossover_sell_no = 0
            for s in fList:
                if crossover_sell_no >= self.p['crossover_sell_no']:
                    break
                print('crossover_sell')
                ss = self.p['stocks'][s['sIndex']]['share']
                sell_share = (-1) * math.floor(ss * s['rl_result']['predict_vol'])
                sell_price = self.getPrice(s['symbol'], aaod)
                #print(s['symbol'], sell_share, sell_price)
                if sell_share < 0 and sell_price > 0:
                    #sell_price = self.getNextQuote(s['symbol'], aaod)['close']
                    sell_position = sell_price * sell_share
                    sell_action = {
                        "date": aaod,
                        "action_type": "sell",
                        "reason": "crossover_sell",
                        "fitness": s,
                        "price": sell_price,
                        "share": sell_share,
                        "value": sell_position
                    }
                    print(sell_action)

                    remaining_share = ss + sell_share
                    # update p
                    self.p['last_update_date'] = aaod
                    self.p['stocks'][s['sIndex']]['share'] = remaining_share
                    self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                    self.p['cash'] = self.p['cash'] - sell_position
                    crossover_sell_no = crossover_sell_no + 1
                    #print(self.p)
                    execute_flag = 1

                    cost, worth, perf, trans_couunt  = self.getPerf(s['symbol'])
                    print(cost, worth, perf, trans_couunt)
                    #if perf >= 10 and s['symbol'] not in self.p['prefer_list']:
                    #    self.p['prefer_list'].append(s['symbol'])
                    #if perf < 1 and s['symbol'] in self.p['prefer_list']:
                    #    self.p['prefer_list'].remove(s['symbol'])

        return execute_flag

    def crossover(self, aaod):
        #startTime = datetime.now()

        execute_sell_flag = 0
        execute_buy_flag = 0
        existing_stock = []
        sell_list = []
        buy_list = []
        for i, s in enumerate(self.p['stocks']):
            if s['share'] > 0:
                existing_stock.append(s['symbol'])
                f = self.fitness(s['symbol'], aaod, always_run_rl=True)
                #sell
                if f is not None and f['rl_result']['predict_action'] >= 1 and f['rl_result']['predict_vol'] > 0 and f['rl_result']['predict_action'] < 2:      # and f['Reason'] != 'len < 5':
                    f['sIndex'] = i
                    sell_list.append(f)
                #buy
                elif f is not None and f['rl_result']['predict_action'] >= 0 and f['rl_result']['predict_vol'] > 0 and f['rl_result']['predict_action'] < 1:  # and f['Reason'] != 'len < 5':
                    f['sIndex'] = i
                    buy_list.append(f)
        #print(existing_stock)
        #endTime = datetime.now()
        #runTime = endTime - startTime
        #print('stocks run time', runTime)

        #startTime = datetime.now()
        #for p in self.p['prefer_list']:
        for p in self.p['prefer_list']:
            #print(p)
            if p not in existing_stock:
                f = self.fitness(p, aaod, always_run_rl=True)
                #buy
                if f is not None and f['rl_result']['predict_action'] >= 0 and f['rl_result']['predict_vol'] > 0 and f['rl_result']['predict_action'] < 1:  # and f['Reason'] != 'len < 5':
                    buy_list.append(f)
        #endTime = datetime.now()
        #runTime = endTime - startTime
        #print('p['prefer_list'] run time', runTime)

        #startTime = datetime.now()
        sell_list = sorted(sell_list, key=lambda k: k['CAP'], reverse=False)
        crossover_sell_no = 0
        for s in sell_list:
            if crossover_sell_no >= self.p['crossover_sell_no']:
                break
            print('crossover_sell')
            ss = self.p['stocks'][s['sIndex']]['share']
            sell_share = (-1) * math.floor(ss * s['rl_result']['predict_vol'])
            #sell_price = self.getPrice(s['symbol'], aaod)
            sell_price = self.getSellPrice(s['symbol'], aaod)
            #print(s['symbol'], sell_share, sell_price)
            if sell_share < 0 and sell_price > 0:
                # sell_price = self.getNextQuote(s['symbol'], aaod)['close']
                sell_position = sell_price * sell_share
                sell_action = {
                    "date": aaod,
                    "action_type": "sell",
                    "reason": "crossover_sell",
                    "fitness": s,
                    "price": sell_price,
                    "share": sell_share,
                    "value": sell_position
                }
                print(sell_action)

                remaining_share = ss + sell_share
                # update p
                self.p['last_update_date'] = aaod
                self.p['stocks'][s['sIndex']]['share'] = remaining_share
                self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                self.p['cash'] = self.p['cash'] - sell_position
                crossover_sell_no = crossover_sell_no + 1
                # print(self.p)
                execute_sell_flag = 1

                cost, worth, perf, trans_count = self.getPerf(s['symbol'])
                #print(cost, worth, perf, trans_count)
                if perf >= 1.05 and s['symbol'] not in self.p['prefer_list']:
                    self.p['prefer_list'].append(s['symbol'])
                elif perf < 1.02 and s['symbol'] in self.p['prefer_list'] and s['symbol'] not in self.protectList:
                   self.p['prefer_list'].remove(s['symbol'])

        #endTime = datetime.now()
        #runTime = endTime - startTime
        #print('sell run time', runTime)

        #startTime = datetime.now()
        buy_list = sorted(buy_list, key=lambda k: k['CAP'], reverse=False)
        crossover_buy_no = 0
        existing_stock = 0
        buy_amt = self.getBuyAmt()

        print('buy_amt', buy_amt, 'cash', self.p['cash'])
        for b in buy_list:
            if crossover_buy_no >= self.p['crossover_buy_no']:
                break
            if self.p['cash'] >= buy_amt:
                print('crossover_buy')
                #buy_price = self.getPrice(b['symbol'], aaod)
                buy_price = self.getBuyPrice(b['symbol'], aaod)
                if buy_price > 0:
                    buy_share = math.floor(buy_amt * b['rl_result']['predict_vol'] / buy_price)
                    buy_position = buy_price * buy_share
                    if buy_position > 0 and self.p['cash'] >= buy_position:
                        for pi, ps in enumerate(self.p['stocks']):
                            if ps['symbol'] == b['symbol']:
                                buy_action = {
                                    "date": aaod,
                                    "action_type": "buy",
                                    "reason": "crossover_buy",
                                    "fitness": b,
                                    "price": buy_price,
                                    "share": buy_share,
                                    "value": buy_position
                                }
                                print(buy_action)

                                remaining_share = ps['share'] + buy_share
                                # update p
                                self.p['last_update_date'] = aaod
                                self.p['stocks'][pi]['share'] = remaining_share
                                self.p['stocks'][pi]['actions'].append(buy_action)
                                self.p['cash'] = self.p['cash'] - buy_position
                                crossover_buy_no = crossover_buy_no + 1
                                execute_buy_flag = 1

                                existing_stock = 1
                                break
                        if existing_stock == 0:
                            stock = {
                                "symbol": b['symbol'],
                                "share": buy_share,
                                "actions":
                                    [
                                        {
                                            "date": aaod,
                                            "action_type": "buy",
                                            "reason": "crossover_buy",
                                            "fitness": b,
                                            "price": buy_price,
                                            "share": buy_share,
                                            "value": buy_position
                                        }
                                    ]
                            }
                            print(stock)
                            # update p
                            self.p['last_update_date'] = aaod
                            self.p['stocks'].append(stock)
                            self.p['cash'] = self.p['cash'] - buy_position
                            crossover_buy_no = crossover_buy_no + 1
                            execute_buy_flag = 1
        #endTime = datetime.now()
        #runTime = endTime - startTime
        #print('buy run time', runTime)

        return execute_sell_flag, execute_buy_flag

    def mutate_buy(self, aaod, mutateBuyFlag):
        execute_flag = 0
        if mutateBuyFlag > 0:
            existing_stock = 0

            buy_amt = self.getBuyAmt()

            #print('buy_amt', buy_amt, 'cash', self.p['cash'])
            mutateBuyChance = random.uniform(0, 1)
            print('buy chance', mutateBuyChance)

            if mutateBuyChance > self.p['mutate_buy_threshold'] and self.p['cash'] >= buy_amt and buy_amt > 10000:
                #sList = []
                #for i, s in enumerate(self.p['stocks']):
                #    sList.append(s['symbol'])

                # mutate_buy
                cList = self.getCAPList(aaod)
                mutate_buy_no = 0
                for s in cList:
                    if mutate_buy_no >= self.p['mutate_buy_no']:
                        break
                    if self.p['cash'] < buy_amt:
                        break
                    #print(s)
                    #if s['symbol'] not in exclusionList and s['symbol'] not in sList and mutate_buy_no < self.p['mutate_buy_no']:
                    #if s['symbol'] not in exclusionList and mutate_buy_no < self.p['mutate_buy_no']:
                    buy_price = self.getPrice(s['symbol'], aaod)
                    if buy_price > 0:
                        f = self.fitness(s['symbol'], aaod)
                        if f is not None and f['Reason'] == 'predict_action < 1' and f['rl_result']['predict_macd_accum'] < 0:
                        #if f is not None and f['rl_result']['predict_action'] < 1 and f['rl_result']['predict_vol'] > 0 and f['Recommendation'] == '':      # and f['Reason'] != 'len < 5':
                            buy_share = math.floor(buy_amt * f['rl_result']['predict_vol'] / buy_price)
                            buy_position = buy_price * buy_share
                            if buy_position > 0 and self.p['cash'] >= buy_position:
                                for pi, ps in enumerate(self.p['stocks']):
                                    if ps['symbol'] == s['symbol']:
                                        buy_action = {
                                            "date": aaod,
                                            "action_type": "buy",
                                            "reason": "mutate_buy",
                                            "fitness": f,
                                            "price": buy_price,
                                            "share": buy_share,
                                            "value": buy_position
                                        }
                                        print(buy_action)

                                        remaining_share = ps['share'] + buy_share
                                        # update p
                                        self.p['last_update_date'] = aaod
                                        self.p['stocks'][pi]['share'] = remaining_share
                                        self.p['stocks'][pi]['actions'].append(buy_action)
                                        self.p['cash'] = self.p['cash'] - buy_position
                                        #mutate_buy_no = mutate_buy_no + 1
                                        execute_flag = 1

                                        existing_stock = 1
                                        break
                                if existing_stock == 0:
                                    stock = {
                                        "symbol": s['symbol'],
                                        "share": buy_share,
                                        "actions":
                                            [
                                                {
                                                    "date": aaod,
                                                    "action_type": "buy",
                                                    "reason": "mutate_buy",
                                                    "fitness": f,
                                                    "price": buy_price,
                                                    "share": buy_share,
                                                    "value": buy_position
                                                }
                                            ]
                                    }
                                    print(stock)
                                    # update p
                                    self.p['last_update_date'] = aaod
                                    self.p['stocks'].append(stock)
                                    self.p['cash'] = self.p['cash'] - buy_position
                                    mutate_buy_no = mutate_buy_no + 1
                                    execute_flag = 1
                                #if s['symbol'] not in self.p['prefer_list']:
                                #    mutate_buy_no = mutate_buy_no + 1

        return execute_flag

    def generation(self):
        mongo_query = {'$and': [{'Date': {'$gt': self.p['last_update_date']}}, {'Date': {'$lte': self.p['end_date']}}]}
        mongo_col_q = self.mongoDB.get_collection('AMZN')
        qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))

        index = 1
        restartIndex = 1
        stopIndex = 1500000
        for q in qDates:
            if index > stopIndex:
                break
            if index >= restartIndex:
                d = q['Date']
                #dd = self.getDate(d)
                print(index, d)

                #execute_count = 0
                #crossover_sell_execute = 0
                #crossover_buy_execute = 0
                #mutate_buy_execute = 0
                crossover_sell_execute, crossover_buy_execute = self.crossover(d)
                #crossover_sell_execute = self.crossover_sell(d, self.p['crossover_sell_flag'])
                mutate_buy_execute = self.mutate_buy(d, self.p['mutate_buy_flag'])

                #execute_count = crossover_sell_execute + mutate_buy_execute
                execute_count = crossover_sell_execute + crossover_buy_execute + mutate_buy_execute
                if execute_count > 0 or index == stopIndex or index == len(qDates):
                    total = self.getTotal(d)
                    self.p['total'] = total
                    action = []
                    if crossover_sell_execute == 1:
                        action.append("Crossover_Sell")
                        self.p['last_cross_sell_date'] = d
                    if crossover_buy_execute == 1:
                        action.append("Crossover_Buy")
                        self.p['last_cross_buy_date'] = d
                    if mutate_buy_execute == 1:
                        action.append("Mutate_Buy")
                        self.p['last_mutate_buy_date'] = d
                    self.p['total_history'].append({"date": d, "cash": self.p['cash'], "total": total, "action": action})

                    if index == stopIndex or index == len(qDates):
                        self.p['last_update_date'] = d

                    if self.save_p_flag > 0:
                        self.save_p()
                    #print(json_util.dumps(self.p, indent=4))
                    self.render(d)
                    print(self.getTotalPerf())
            index = index + 1

    def save_p(self):
        self.mongoDB['stock_ga_results'].replace_one(
            {"name": self.p['name']},
            self.p,
            upsert=True)

    def render(self, d):
        history = self.p['total_history']

        stock_list = []
        for s in self.p['stocks']:
            if s['share'] > 0:
                stock_list.append({'symbol': s['symbol'], 'share': s['share']})

        print(history)
        print(stock_list)
        print(self.p['prefer_list'])

        #print(json_util.dumps(ga.p, indent=4))


if __name__ == '__main__':
    startTime = datetime.now()

    #init_date = '2013-06-14'        #'05-31'
    init_date = '2010-10-01'  # '05-31'
    #init_date = '2015-12-01'  # '05-31'

    end_date = '2021-06-10'
    init_cash = 200000
    #init_cash = 0
    init_list = []
    save_p_flag = 1

    ga = RuleGA_MACD_RL(save_p_flag)
    #ga_name = 'test_GA_MACD_RL_1'
    #ga_name = 'test_GA_MACD_RL_2'
    #ga_name = 'test_GA_MACD_RL_3'
    #ga_name = 'test_GA_MACD_RL_4'
    #ga_name = 'test_GA_MACD_RL_5'
    #ga_name = 'test_GA_MACD_RL_6'
    #ga_name = 'test_GA_MACD_RL_7'
    #ga_name = 'test_GA_MACD_RL_8'
    #ga_name = 'test_GA_MACD_RL_9'
    #ga_name = 'test_GA_MACD_RL_10'
    #ga_name = 'test_GA_MACD_RL_11'
    #ga_name = 'test_GA_MACD_RL_12'
    #ga_name = 'test_GA_MACD_RL_13'
    #ga_name = 'test_GA_MACD_RL_14'
    ga_name = 'test_GA_MACD_RL_15'
    p = ga.reload(ga_name, end_date)
    if p is None:
        ga.init(ga_name, init_date, end_date, init_cash, init_list)

    print(json_util.dumps(ga.p, indent=4))

    ga.generation()
    #print(json_util.dumps(ga.p, indent=4))
    #print(ga.getTotalPerf())

    #print(ga.getCAPList('2013-06-14'))

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time', runTime)


'''
(102.65078811892232, 9.142085219504287, 0.0, 0, '2018-04-06', '2010-10-01')
'''