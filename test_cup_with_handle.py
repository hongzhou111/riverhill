'''
Cuap with Handle using LOG filter
LOG - Laplacian of Gaussian
Parameters
1. sigma	        80	            10-100
2. Range Up Bound	x0 + 2*sigma	810
3. Scale Laplace	2050	        2000 - 3000
Laplace Base	    0
Range Lower Bound	x0-2*sigma	    490
x0	                x0 = Range Up Bound - 2 * sigma	650
Price Base	        p[x0+2*sigma]	810
Model Price	        Price Base * (1 + Scale * l[i])
l[i]	            "1/(sigma*sigma)
                     *(((i -x0)*(i-x0)/(sigma*sigma)-1)
                     *POWER(2.71828,(-1*(i-x0)*
                     (i-x0)/(2*sigma*sigma)))"

PearsonCorrelation



Change History:
2023/01/12 - create
'''

#import time
#import logging
#from datetime import datetime
#from datetime import timedelta
#import pymongo
#import json
#import traceback
import math
#import random
#from bson import json_util
from datetime import datetime
from datetime import timedelta
#import json
import numpy as np
from test_mongo import MongoExplorer
import pandas as pd
#from pandas import json_normalize
#from test_yahoo import QuoteExplorer
#from test_g20_v2 import StockScore
#from openpyxl import load_workbook
#from test_stockstats import StockStats
#from test_fundamentals import StockFundamentalsExplorer
import yfinance as yf
from stockstats import StockDataFrame as Sdf
#from test_yahoo import QuoteExplorer
#from test_stockstats import StockStats

class Rule_Cup_with_Handle:
    def __init__(self, aaod = datetime.now().strftime("%Y-%m-%d")):
        mongo_client = MongoExplorer()
        self.mongoDB = mongo_client.mongoDB
        self.aaod = aaod

    def getdf(self, ticker):
        self.ticker = ticker

        y = yf.Ticker(self.ticker)
        h = y.history(start="1970-01-01", end=self.aaod)
        df = Sdf.retype(h)
        df = df.reset_index()
        self.df = df
        return df

    #def save_result(self):
    #    self.mongoDB['stock_cup_with_handle_results'].replace_one(
    #        {"symbol": self.symbol},
    #        self.result,
    #        upsert=True)

    def log(self, sigma):
        laplacian = []
        l0 = 2 * sigma
        #l = 0
        e = 2.71828
        for i in range(math.floor(4 * sigma)):
            l = (1 / (sigma * sigma)) * (((i - l0) * (i - l0) / (sigma * sigma)) - 1) * math.pow(e, (-1 * (i - l0) * (i - l0) / (2 * sigma * sigma)))
            laplacian.append(l)
        return laplacian

    def log_negative(self, sigma):
        l_n = [(-1) * x for x in self.log(sigma)]
        return l_n

    # Calculate the person correlation score between two items in a dataset.
    # @param  {object}  prefs The dataset containing data about both items that are being compared.
    # @param  {string}  p1 Item one for comparison.
    # @param  {string}  p2 Item two for comparison.
    # @return {float}  The pearson correlation score.
    def pearsonCorrelation(self, prefs, p1, p2):
        si = []
        for key in range(len(prefs[p1])):
            si.append(key)
        n = len(si)
        if n == 0: return 0
        sum1 = 0
        for i in range(len(si)):
            sum1 += prefs[p1][si[i]]
        sum2 = 0
        for i in range(len(si)):
            sum2 += prefs[p2][si[i]]
        sum1Sq = 0
        for i in range(len(si)):
            sum1Sq += math.pow(prefs[p1][si[i]], 2)
        sum2Sq = 0
        for i in range(len(si)):
            sum2Sq += math.pow(prefs[p2][si[i]], 2)
        pSum = 0
        for i in range(len(si)):
            pSum += prefs[p1][si[i]] * prefs[p2][si[i]]

        num = pSum - (sum1 * sum2 / n)
        try:
            den = math.sqrt((sum1Sq - math.pow(sum1, 2) / n) * (sum2Sq - math.pow(sum2, 2) / n))
        except:
            den = 0

        if den == 0: return 0

        return num / den

    def getPerf(self, aaod, log_sign=1):
        i = self.df.loc[self.df['Date'] == aaod].index[0]
        base_price  = self.df['close'][i]

        # find the best price in next 100 - 300 days
        forward = 10
        best_price = self.df['close'][i]
        best_i = i
        for ii in range(300):
            if (i + forward + ii > len(self.df['close']) - 1):
                break
            p = self.df['close'][i + forward + ii]
            if log_sign == 1:
                if p > best_price:
                    best_price = p
                    best_i = i + forward + ii
            else:
                if p < best_price:
                    best_price = p
                    best_i = i + forward + ii
        perf = best_price / base_price
        return perf, best_i

    def fit(self, ticker, df=pd.DataFrame(), threshold=0.8, log_sign=1, find_all=1, look_back=100, save_cwh=False):           # log_sing:  1 - normail log;  2 - negative log
        if df.empty:
            self.getdf(ticker)
        else:
            self.df = df
        result = pd.DataFrame(columns=['symbol', 'cwh_sign', 'cwh_end', 'pearson', 'sigma', 'end_date', 'perf', 'perf_date'])

        #finalPearson = 0
        # 1. Range Up Bound: minDate - AAOD, increment by 7 calendar days
        endI = len(self.df['close']) - 1
        fit_one = 0
        while endI > look_back:
            #2. sigma:   40 - 100, increament by 10
            for i in range(9):
                sigma = 10 + 10 * (9-i)

                data0 = np.array(self.df['close'][endI + 1 - 4 * sigma: endI + 1])
                if log_sign == 1:
                    data1 = np.array(self.log(sigma))
                else:
                    data1 = np.array(self.log_negative(sigma))
                if len(data0) == len(data1):
                    data = np.stack((data0, data1), axis=0)
                    pearson = self.pearsonCorrelation(data, 0, 1)
                    if pearson > threshold and endI > look_back:
                        # loof for local best fit
                        local_endi = endI
                        #local_p = 0
                        local_besti = local_endi
                        local_p = pearson
                        localSigma = sigma
                        localAAOD = self.df['Date'][endI].strftime("%Y-%m-%d")
                        while local_endi > endI - 4 * sigma and local_endi > look_back:
                            for li in range(9):
                                sigma2 = 10 + 10 * (9 - li)

                                data02 = np.array(self.df['close'][local_endi + 1 - 4 * sigma2: local_endi + 1])
                                if log_sign == 1:
                                    data12 = np.array(self.log(sigma2))
                                else:
                                    data12 = np.array(self.log_negative(sigma2))

                                if len(data02) == len(data12):
                                    data2 = np.stack((data02, data12), axis=0)
                                    p2 = self.pearsonCorrelation(data2, 0, 1)
                                    if p2 > local_p and local_endi > look_back:
                                        local_besti = local_endi
                                        local_p = p2
                                        localSigma = sigma2
                                        localAAOD = self.df['Date'][local_endi].strftime("%Y-%m-%d")
                            local_endi = local_endi - 1

                        # check price performance in the next year
                        perf, best_i = self.getPerf(localAAOD, log_sign)
                        perf_date = self.df['Date'][best_i].strftime("%Y-%m-%d")
                        #print(endI, local_besti, local_p, localSigma, localAAOD, perf, perf_date)

                        r = [self.ticker, log_sign, local_besti, local_p, localSigma, localAAOD, perf, perf_date]
                        result.loc[len(result.index)] = r

                        if save_cwh == True:
                            r2 = {
                                'symbol': self.ticker,
                                'cwh_sign': log_sign,
                                'cwh_end': local_besti,
                                'pearson': local_p,
                                'sigma': localSigma,
                                'end_date': localAAOD,
                                'perf': perf,
                                'perf_date': perf_date
                            }
                            #print(r2)

                            self.mongoDB['stock_cwh_results'].delete_many({"$and": [{'symbol': self.ticker},
                                {"cwh_end": {"$lte": local_besti + localSigma}}, {"cwh_end": {"$gte": (local_besti - localSigma)}}]})
                            self.mongoDB['stock_cwh_results'].insert_one(r2)

                        endI = local_besti - 4 * sigma + 5
                        fit_one += 1
                        break
            if find_all == 0 and fit_one > 0: break
            endI = endI - 5

        return result

    def fit_all(self, threshold=0.8):
        result = pd.DataFrame(columns=['symbol', 'cwh_sign', 'cwh_end', 'pearson', 'sigma', 'end_date', 'perf', 'perf_date'])

        mongo_col = self.mongoDB['etrade_companies']
        mongo_query = {'status': 'active'}
        com = mongo_col.find(mongo_query, no_cursor_timeout=True)

        #aaod = datetime.now().strftime("%Y-%m-%d")
        #today = datetime.now()

        index = 1
        restartIndex = 6843        #3991
        stopIndex = 7000            #1000000
        for i in com:
            print(str(index) + "	" + i['Yahoo_Symbol'])
            if index > stopIndex:
                break
            if index >= restartIndex:
                ticker = i['Yahoo_Symbol']

                last_cwh1 = self.mongoDB['stock_cwh_results'].find_one({'symbol': ticker, 'cwh_sign': 1}, sort=[{"cwh_end", -1}])
                last_cwh_count1 = self.mongoDB['stock_cwh_results'].count_documents({'symbol': ticker, 'cwh_sign': 1})
                if last_cwh_count1 > 0 and last_cwh1['cwh_end'] > (4 * last_cwh1['sigma'] + 100):
                    look_back1 = last_cwh1['cwh_end'] - 4 * last_cwh1['sigma']
                else:
                    look_back1 = 100
                #print(last_cwh1, look_back1)

                last_cwh2 = self.mongoDB['stock_cwh_results'].find_one({'symbol': ticker, 'cwh_sign': 2}, sort=[{'cwh_end', -1}])
                last_cwh_count2 = self.mongoDB['stock_cwh_results'].count_documents({'symbol': ticker, 'cwh_sign': 2})
                if last_cwh_count2 > 0 and last_cwh2['cwh_end'] > (4 * last_cwh2['sigma'] + 180):
                    look_back2 = last_cwh2['cwh_end'] - 4 * last_cwh2['sigma']
                else:
                    look_back2 = 100
                #print(last_cwh2, look_back2)

                df = self.getdf(ticker)
                rr = self.fit(ticker=ticker, df=df, threshold=threshold, log_sign=1, look_back=look_back1, save_cwh=True)
                #rr.to_csv('cwh_results.csv', mode='a', header=False)
                rr2 = self.fit(ticker=ticker, df=df, threshold=threshold, log_sign=2, look_back=look_back2, save_cwh=True)
                #rr2.to_csv('cwh_results.csv', mode='a', header=False)
                result = pd.concat([result, rr, rr2])
            index += 1
        return result

    def trade_with_cwh(self, ticker, aaod, df=pd.DataFrame(), look_back=120, cwh_back=150, db_look_back=20):
        result = pd.DataFrame(columns=['symbol', 'cwh_sign', 'cwh_end', 'pearson', 'sigma', 'end_date', 'perf', 'perf_date'])
        if df.empty:
            self.getdf(ticker)
        else:
            self.df = df
        if self.df.empty: return result

        aaod_date = datetime(*(int(s) for s in aaod.split('-')))
        df2 = self.df.loc[self.df['Date'] <= aaod]
        new_i = len(df2['Date']) - 1 - look_back

        # check stock_cwh_results
        aaod_i = len(df2['Date']) - 1
        query1 = {'$and': [{'symbol': self.ticker}, {'cwh_sign': 1}, {'cwh_end': {'$lte': aaod_i}}, {'cwh_end': {'$gte': (aaod_i - db_look_back)}}]}
        cwh1 = self.mongoDB['stock_cwh_results'].find(query1).sort('cwh_end', -1)
        cwh_c1 = self.mongoDB['stock_cwh_results'].count_documents(query1)
        #print(aaod, new_i, aaod_i, cwh_c1, query1)

        query2 = {'$and': [{'symbol': self.ticker}, {'cwh_sign': 2}, {'cwh_end': {'"$lte': aaod_i}}, {"cwh_end": {"$gte": (aaod_i - db_look_back)}}]}
        cwh2 = self.mongoDB['stock_cwh_results'].find(query2).sort('cwh_end', -1)
        cwh_c2 = self.mongoDB['stock_cwh_results'].count_documents(query2)

        if cwh_c2 > 0:
            result = pd.DataFrame(list(cwh2))
        elif cwh_c1 > 0:
            result = pd.DataFrame(list(cwh1))
        elif new_i > 40:
            rr = self.fit(ticker, df=self.df, threshold=0.8, log_sign=1, find_all=0, look_back=new_i, save_cwh=True)
            rr2 = self.fit(ticker, df=self.df, threshold=0.8, log_sign=2, find_all=0, look_back=new_i, save_cwh=True)
            if not rr.empty:
                cwh_end_date = datetime(*(int(s) for s in rr['end_date'][0].split('-')))
                cwh_start_date = cwh_end_date + timedelta(days=(-1) * 4 * rr['sigma'][0])
                date_diff = aaod_date - cwh_end_date
            else:
                cwh_end_date = aaod_date
                cwh_start_date = aaod_date
                date_diff = timedelta(days=200)

            if not rr2.empty:
                cwh_end_date2 = datetime(*(int(s) for s in rr2['end_date'][0].split('-')))
                cwh_start_date2 = cwh_end_date2 + timedelta(days=(-1) * 4 * rr2['sigma'][0])
                date_diff2 = (aaod_date - cwh_end_date2)
            else:
                cwh_end_date2 = aaod_date
                cwh_start_date2 = aaod_date
                date_diff2 = timedelta(days=200)

            if (not rr2.empty) and date_diff2.days < cwh_back and cwh_end_date2 > cwh_end_date:
                #    not (
                #(cwh_end_date2 >= cwh_start_date and cwh_end_date2 <= cwh_end_date) or
                #(cwh_start_date2 >= cwh_start_date and cwh_start_date2 <= cwh_end_date)):  # if cwh2 is within 20 days,  and no cwh overlaping after, sell
                result = pd.concat([result, rr2])
            elif (not rr.empty) and date_diff.days < cwh_back and cwh_end_date > cwh_end_date2:
                #not (
                #    (cwh_end_date >= cwh_start_date2 and cwh_end_date <= cwh_end_date2) or
                #    (cwh_start_date >= cwh_start_date2 and cwh_start_date <= cwh_end_date2)):  # if cwh is within 20 days,  and no cwh2 oerlaping and after, buy
                result = pd.concat([result, rr])

        return result

if __name__ == '__main__':
    aaod = datetime.now().strftime("%Y-%m-%d")

    cwh = Rule_Cup_with_Handle(aaod)
    rr = cwh.fit_all(0.8)
    print(rr)
