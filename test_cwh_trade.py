'''
Change History:
2023/01/16 - create
2023/02/08 - remove cash for each stock,  when sell add cash back to self.p_cash
'''

from test_cup_with_handle import Rule_Cup_with_Handle
#import time
#import logging
#import pymongo
#import json
#import traceback
import math
import random
from bson import json_util
from datetime import datetime
#from datetime import timedelta
#import json
#import numpy as np
from test_mongo import MongoExplorer
import pandas as pd
#from pandas import json_normalize
#from test_yahoo import QuoteExplorer
#from test_g20_v2 import StockScore
#from openpyxl import load_workbook
#from test_stockstats import StockStats
from test_fundamentals import StockFundamentalsExplorer
import yfinance as yf
from stockstats import StockDataFrame as Sdf
#from test_yahoo import QuoteExplorer
#from test_stockstats import StockStats

class Rule_CWH:
    def __init__(self, save_p_flag=0):
        mongo_client = MongoExplorer()
        self.mongoDB = mongo_client.mongoDB
        self.save_p_flag = save_p_flag

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

    def getQuote(self, s):
        q = pd.DataFrame()
        try:
            y = yf.Ticker(s)
            df = y.history(period="max")
            df = df.reset_index()
            q = Sdf.retype(df)
            q = q.reset_index()
        except Exception as error:
            #print(error)
            pass
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
            #print(error)
            pass
        return close

    def getNextQuote(self, s, d):
        nq = pd.DataFrame()
        q = self.getQuote(s)
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i+1]
        except Exception as error:
            #print(error)
            pass
        return nq

    def getCAP(self, s, d):
        f = StockFundamentalsExplorer()
        f.get_fund(s, d)
        shares = f.get_shares()
        price = self.getPrice(s,d)
        return shares * price

    def getSellPrice(self, s, d):
        #nq = pd.DataFrame()
        q = self.getQuote(s)
        c = 0
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i+1]
            c = random.uniform(nq['open'], nq['high'])
            #c = nq['open']
        except Exception as error:
            #print(error)
            pass
        return c

    def getBuyPrice(self, s, d):
        #nq = pd.DataFrame()
        q = self.getQuote(s)
        c = 0
        try:
            i = q.loc[q['date'] == d].index[0]
            nq = q.iloc[i+1]
            c = random.uniform(nq['open'], nq['low'])
            #c = nq['open']
        except Exception as error:
            #print(error)
            pass
        return c

    def getTotal(self, d):
        total = self.p['p_cash']
        for s in self.p['stocks']:
            price = self.getPrice(s['symbol'], d)
            total = total + price * s['share']      #+ s['cash']
        return total

    def getPerf(self, ticker, aaod):
        perf = 0
        for i, s in enumerate(self.p['stocks']):
            if s['symbol'] == ticker:
                ss = self.p['stocks'][i]
                price = self.getPrice(ticker, aaod)
                if ss['init_investment'] > 0 :
                    perf = (ss['share'] * price) / ss['init_investment']        #ss['cash'] +
        return perf

    def getHoldingDuration(self, action_list, action_type, aaod):
        result = 0
        action_list.reverse()
        for a in action_list:
            if a['action_type'] == action_type:
                result = (datetime(*(int(s) for s in aaod.split('-'))) - datetime(*(int(s) for s in a['date'].split('-')))).days
                break
        return result

    def getLastAction(self, action_list, action_type):
        result = None

        #action_list.reverse()
        i = len(action_list) - 1
        while i >= 0:
            if action_list[i]['action_type'] == action_type:
                result = action_list[i]
                break
            i = i -1

        return result

    def getTotalPerf(self):
        #total_perf = self.p['total_history'][len(self.p['total_history']) - 1]['total'] / self.p['total_history'][0]['total']     # / self.p['total_history'][0]['total']
        total_perf = self.p['total_history'][len(self.p['total_history']) - 1]['total'] / self.p['investment']
        if self.p['investment'] - self.p['p_cash'] > 0:
            total_perf2 = (self.p['total_history'][len(self.p['total_history']) - 1]['total'] - self.p['p_cash']) / (self.p['investment'] - self.p['p_cash'])
        else:
            total_perf2 = 0

        amzn_init = self.getPrice('AMZN', self.p['total_history'][0]['date'])
        amzn_end = self.getPrice('AMZN', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        amzn_perf = amzn_end / amzn_init

        spy_init = self.getPrice('SPY', self.p['total_history'][0]['date'])
        spy_end = self.getPrice('SPY', self.p['total_history'][len(self.p['total_history']) - 1]['date'])
        spy_perf = spy_end / spy_init

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

        return total_perf, total_perf2, spy_perf, amzn_perf, msft_perf, tsla_perf, self.p['total_history'][len(self.p['total_history']) - 1]['date'], self.p['total_history'][0]['date']

    def init(self, pn, date, endDate, ss=[]):           # pn - portfolio name;  d = start date,  10 years back; endDate = last date for the evaluation; ss = initial stock list
        self.plist = []
        self.p = {
            "name": pn,
            "init_date": date,
            'end_date': endDate,
            "last_update_date": date,
            "last_cross_sell_date": date,
            "last_cross_buy_date": date,
            "last_mutate_buy_date": date,
            "last_mutate_sell_date": date,
            "mutate_sell_threshold": 0.8,
            "hold_time": 30,
            "investment": 0,
            "p_cash": 0,
            'total': 0,
            "total_history": []
        }
        stocks = []
        for s in ss:
            price = self.getPrice(s['symbol'], date)
            if price > 0:
                #share = math.floor(100000 / price)
                position = price * s['share']
                stock = {
                    "symbol":   s['symbol'],
                    "share":    s['share'],
                    #"cash":     0,
                    "init_investment": position,
                    "actions":
                        [
                            {
                                "date": date,
                                "action_type": "buy",
                                "reason": "initial_buy",
                                "price": price,
                                "share": s['share'],
                                "value": position
                            }
                        ]
                }
                stocks.append(stock)
                self.p['investment'] = self.p['investment'] + position
                self.plist.append(s['symbol'])

        self.p['stocks'] = stocks
        total = self.getTotal(date)
        self.p['total'] = total
        self.p['total_history'].append({"date": date, "total": total})

        if self.save_p_flag > 0:
            self.save_p()

        print(self.p)
        return self.p

    def reload(self, pn, newEndDate, **params):
        self.plist = []
        if self.mongoDB['stock_ga_results'].count_documents({'name': pn}) > 0:
            self.p = self.mongoDB['stock_ga_results'].find_one({'name': pn})
            if 'last_cross_sell_date' not in self.p:
                self.p['last_cross_sell_date'] = self.p['end_date']
            if 'last_cross_buy_date' not in self.p:
                self.p['last_cross_buy_date'] = self.p['end_date']
            if 'last_mutate_buy_date' not in self.p:
                self.p['last_mutate_buy_date'] = self.p['end_date']
            if 'last_mutate_sell_date' not in self.p:
                self.p['last_mutate_sell_date'] = self.p['end_date']
            self.p['end_date'] = newEndDate

            mst = params.get('mutate_sell_threshold')
            if mst is not None:
                self.p['mutate_sell_threshold'] = mst

            ht = params.get('hold_time')
            if ht is not None:
                self.p['hold_time'] = ht

            for s in self.p['stocks']:
                if s['share'] > 0 or s['init_investment'] > 0:
                    self.plist.append(s['symbol'])

            return self.p
        else:
            return None

    def run_portfolio(self, aaod):
        #startTime = datetime.now()

        execute_cross_sell_flag = 0
        execute_cross_buy_flag = 0
        execute_mutate_sell_flag = 0

        for i, s in enumerate(self.p['stocks']):
            #print(s['symbol'], aaod)
            #if s['cash'] > 0 or s['share'] > 0:
            if s['share'] > 0 or s['init_investment'] > 0:  #s['cash'] > 0 or
                self.plist.append(s['symbol'])

            reason = ''
            fitness = ''
            perf = self.getPerf(s['symbol'], aaod)
            last_buy_days = self.getHoldingDuration(self.p['stocks'][i]['actions'], 'buy', aaod)
            print(s['symbol'], s['share'], s['init_investment'], aaod, perf, last_buy_days)
            # cross sell when perf >= 1.5
            if s['share'] > 0 and last_buy_days > 365 and perf < 1.2:
                reason = 'cross_sell'
                fitness = {"perf": perf}
            elif s['share'] > 0 and last_buy_days > 730 and perf < 1.5:
                reason = 'cross_sell'
                fitness = {"perf": perf}
                # mutate sell when perf < 0.8
            #if perf < self.p['mutate_sell_threshold'] and s['share'] > 0:
            elif perf < self.p['mutate_sell_threshold'] and s['share'] > 0:
                reason = 'mutate_sell'
                fitness = {"perf": perf}
            elif s['share'] > 0 and last_buy_days > self.p['hold_time'] and perf < 1:  # if holding 90 days and no gain mutate sell
                reason = 'mutate_sell'
                fitness = {"perf": perf}

            if reason == '' and (s['share'] > 0 or s['init_investment'] > 0):
                cwh = Rule_Cup_with_Handle(aaod)
                cwh_rr = cwh.trade_with_cwh(ticker=s['symbol'], aaod=aaod, look_back=120, cwh_back=20)
                for ii, rr in cwh_rr.iterrows():
                    if ii > 0: break
                    if rr['cwh_sign'] == 2:     # cross sell
                        reason = 'cross_sell'
                        fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'], "end_date": rr['end_date'], "perf": perf}
                    if rr['cwh_sign'] == 1:  # cross buy
                        reason = 'cross_buy'
                        fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'], "end_date": rr['end_date']}

            if reason == 'cross_sell' or reason == 'mutate_sell':
                sell_share = (-1) * s['share']
                sell_price = self.getSellPrice(s['symbol'], aaod)
                if sell_share < 0 and sell_price > 0:
                    sell_position = sell_price * sell_share
                else:
                    sell_position = 0

                if sell_position < 0:
                    # update p
                    self.p['last_update_date'] = aaod
                    self.p['stocks'][i]['share'] = 0
                    #self.p['stocks'][i]['cash'] = self.p['stocks'][i]['cash'] - sell_position
                    self.p['p_cash'] = self.p['p_cash'] - sell_position

                    if reason == 'cross_sell':
                        execute_cross_sell_flag = 1
                    if reason == 'mutate_sell':
                        self.p['stocks'][i]['init_investment'] = 0
                        execute_mutate_sell_flag = 1

                    sell_action = {
                        "date": aaod,
                        "action_type": "sell",
                        "reason": reason,
                        "fitness": fitness,
                        "price": sell_price,
                        "share": sell_share,
                        "value": sell_position
                    }
                    print(sell_action)
                    self.p['stocks'][i]['actions'].append(sell_action)

            elif reason == 'cross_buy' and s['share'] == 0 and s['init_investment'] > 0:
                last_sell_action = self.getLastAction(s['actions'], 'sell')

                if last_sell_action != None and last_sell_action['reason'] == 'cross_sell':
                    buy_price = self.getBuyPrice(s['symbol'], aaod)
                    if buy_price > 0:
                        buy_share = math.floor(((-1) * last_sell_action['value']) / buy_price)
                        buy_position = buy_price * buy_share
                        if buy_position > 0:
                            buy_action = {
                                "date": aaod,
                                "action_type": "buy",
                                "reason": reason,
                                "fitness": fitness,
                                "price": buy_price,
                                "share": buy_share,
                                "value": buy_position
                            }
                            print(buy_action)

                            new_share = s['share'] + buy_share
                            # update p
                            self.p['last_update_date'] = aaod
                            self.p['stocks'][i]['share'] = new_share
                            self.p['stocks'][i]['actions'].append(buy_action)
                            if self.p['p_cash'] >= buy_position:
                                self.p['p_cash'] = self.p['p_cash'] - buy_position
                            else:
                                self.p['investment'] = self.p['investment'] + buy_position - self.p['p_cash']
                                self.p['p_cash'] = 0
                            execute_cross_buy_flag = 1

            #if execute_mutate_sell_flag == 0:
            #    self.plist.append(s['symbol'])

        return execute_cross_sell_flag, execute_mutate_sell_flag, execute_cross_buy_flag


    def run_all(self, aaod):
        execute_mutate_buy_flag = 0
        clist = self.mongoDB['stock_g20'].find({'AAOD': aaod, 'Recommendation': ''})
        clen = self.mongoDB['stock_g20'].count_documents({'AAOD': aaod, 'Recommendation': ''})
        if clen < 100:
            mongo_col = self.mongoDB['etrade_companies']
            mongo_query = {'status': 'active'}
            clist = mongo_col.find(mongo_query, no_cursor_timeout=True)
            source = 'etrade_companies'
        else:
            source = 'stock_g20'
        print(source)

        s = ''
        for i in clist:
            if source == 'etrade_companies':
                s = i['Yahoo_Symbol']
            elif source == 'stock_g20':
                s = i['symbol']

            reason = ''
            fitness = ''
            if s != '' and s not in self.plist:      # and i['Yahoo_Symbol'] not in self.exclusionList:
                print(s, aaod)
                cwh = Rule_Cup_with_Handle(aaod)
                cwh_rr = cwh.trade_with_cwh(ticker=s, aaod=aaod, look_back=120, cwh_back=20)
                for ii, rr in cwh_rr.iterrows():
                    if ii > 0: break
                    if rr['cwh_sign'] == 1:  # cross buy
                        reason = 'mutate_buy'
                        fitness = {"cwh_sign": rr['cwh_sign'], "pearson": rr['pearson'], "sigma": rr['sigma'], "end_date": rr['end_date']}

                if reason == 'mutate_buy':
                    buy_price = self.getPrice(s, aaod)
                    if buy_price > 0:
                        buy_share = math.floor(100000 / buy_price)
                        buy_position = buy_price * buy_share
                        if buy_position > 0:
                            existing_stock = 0
                            for pi, ps in enumerate(self.p['stocks']):
                                if ps['symbol'] == s:
                                    if ps['init_investment'] == 0 and ps['share'] == 0:
                                        buy_action = {
                                            "date": aaod,
                                            "action_type": "buy",
                                            "reason": reason,
                                            "fitness": fitness,
                                            "price": buy_price,
                                            "share": buy_share,
                                            "value": buy_position
                                        }
                                        print(buy_action)

                                        new_share = ps['share'] + buy_share
                                        # update p
                                        self.p['last_update_date'] = aaod
                                        self.p['stocks'][pi]['share'] = new_share
                                        self.p['stocks'][pi]['actions'].append(buy_action)
                                        self.p['stocks'][pi]['init_investment'] = self.p['stocks'][pi]['init_investment'] + buy_position
                                        execute_mutate_buy_flag = 1

                                    existing_stock = 1
                                    break
                            if existing_stock == 0:
                                stock = {
                                    "symbol": s,
                                    "share": buy_share,
                                    "init_investment": buy_position,
                                    "actions":
                                        [
                                            {
                                                "date": aaod,
                                                "action_type": "buy",
                                                "reason": reason,
                                                "fitness": fitness,
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

                            if self.p['p_cash'] >= buy_position:
                                self.p['p_cash'] = self.p['p_cash'] - buy_position
                            else:
                                self.p['investment'] = self.p['investment'] + buy_position - self.p['p_cash']
                                self.p['p_cash'] = 0
                            execute_mutate_buy_flag = 1

        return execute_mutate_buy_flag

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
            if index >= restartIndex and index % 19 == 0:
                startTime = datetime.now()
                d = q['Date']
                #dd = self.getDate(d)
                print(index, d)

                #execute_count = 0
                #crossover_sell_execute = 0
                #crossover_buy_execute = 0
                #mutate_buy_execute = 0
                crossover_sell_execute, mutate_sell_execute, crossover_buy_execute = self.run_portfolio(d)
                #crossover_sell_execute = self.crossover_sell(d, self.p['crossover_sell_flag'])
                mutate_buy_execute = self.run_all(d)

                #execute_count = crossover_sell_execute + mutate_buy_execute
                execute_count = crossover_sell_execute + mutate_sell_execute + crossover_buy_execute + mutate_buy_execute
                if execute_count > 0 or index == stopIndex or index == len(qDates):
                    total = self.getTotal(d)
                    self.p['total'] = total
                    action = []
                    if crossover_sell_execute == 1:
                        action.append("Crossover_Sell")
                        self.p['last_cross_sell_date'] = d
                    if mutate_sell_execute == 1:
                        action.append("Mutate_Sell")
                        self.p['last_mutate_sell_date'] = d
                    if crossover_buy_execute == 1:
                        action.append("Crossover_Buy")
                        self.p['last_cross_buy_date'] = d
                    if mutate_buy_execute == 1:
                        action.append("Mutate_Buy")
                        self.p['last_mutate_buy_date'] = d
                    self.p['total_history'].append({"date": d, "total": total, "action": action})

                    if index == stopIndex or index == len(qDates):
                        self.p['last_update_date'] = d

                    if self.save_p_flag > 0:
                        self.save_p()
                    #print(json_util.dumps(self.p, indent=4))
                    self.render(d)
                    print(self.getTotalPerf())

                endTime = datetime.now()
                runTime = endTime - startTime
                print('run time: ', runTime)

            index = index + 1

    def save_p(self):
        self.mongoDB['stock_ga_results'].replace_one(
            {"name": self.p['name']},
            self.p,
            upsert=True)

    def render(self, d):
        #history = self.p['total_history']

        stock_list = []
        for s in self.p['stocks']:
            if s['share'] > 0:
                price = self.getPrice(s['symbol'], d)
                value = price * s['share']
                stock_list.append({'symbol': s['symbol'], 'share': s['share'], 'price': price, 'value': value})

        print(self.p['investment'], self.p['p_cash'])
        print(self.p['total_history'])
        print(stock_list)

        #print(json_util.dumps(ga.p, indent=4))


if __name__ == '__main__':
    startTime = datetime.now()

    init_date = '2010-10-01'  # '05-31'

    #end_date = '2021-06-10'
    end_date = '2023-01-10'
    #init_list = [{'symbol': 'TSLA', 'shares': 250000}]
    save_p_flag = 1

    ga = Rule_CWH(save_p_flag)
    #ga_name = 'test_CWH_1'          # no cross_sell by duration
    ga_name = 'test_CWH_2'          # add 1 year 1.2, and 2 year 1.5 cross_sell


    #if ga.reload(ga_name, end_date, hold_time=90) is None:
    if ga.reload(ga_name, end_date) is None:
        ga.init(ga_name, init_date, end_date)
    #ga.init(ga_name, init_date, end_date)

    #print(json_util.dumps(ga.p, indent=4))
    print(ga.plist)

    ga.generation()
    print(json_util.dumps(ga.p, indent=4))

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time', runTime)

