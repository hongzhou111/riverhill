'''
GA Algorithm

gene:                               buy/sell decision models(m - 1. MACD crossover )
chromesome:                         stock(s)
Population:                         portfolio(p = stocks + cash)
fitness:                            growth return (g),  Sharpe Ratio(return / sigma), MACD
initialization:                     buy 9 stocks, each for 100k, keep 500k cash, total 1400k
generation:
    crossover                       if (s.g >= # && s.mr rank top 2 && cash > 2k & luck dice > (1 - 0.7)) buy 2k(10%) more of s
                                    #if (s.g <= # && s.mr rank bottom 2 && luck dice > (1 - 0.7))  sell 2k(10%) s
    crossover(Sharpe)               #if (s.SR >= # && s.mr rank top 2 && cash > 2k & luck dice > (1 - 0.7)) buy 10% of current position of s
                                    if (s.SR <= # && s.mr rank bottom 2 && luck dice > (1 - 0.7))  sell 10% (5k) s
    crossover(take short profit)    if (s.g >= # && s.mr rank top 2) sell 2k(10%) s
    mutate                          if (s.SR < # && luck dice > (1 - 0.1)) sell 100 % of s,  for the bottom 3 stocks
                                    buy 100k top scored stock, up to 3 stocks
    mutate(take long profit)        if (s.g >= # && s.mr rank top 2) sell 2k(10%) s - not implemented

    repeat generation,  crossover every 7 time tic(every week), mutate every 20 time tic (every month)
'''
#import time
import logging
from datetime import datetime
from datetime import timedelta
import pymongo
import json
import traceback
import math
from bson import json_util
import pandas as pd
import numpy as np

from test_g20 import StockScore
from test_mongo import MongoExplorer

class RuleGA:
    def __init__(self, save_p_flag):
        mongo_client = MongoExplorer()
        self.mongoDB = mongo_client.mongoDB
        #mongo_client = pymongo.MongoClient('mongodb://192.168.1.10:27017/')
        mongo = MongoExplorer()
        #self.mongoDB = mongo_client['riverhill']
        self.save_p_flag = save_p_flag

    def getDate(self, d):   #convert '2009-12-11' to a datetime
        return datetime(*(int(s) for s in d.split('-')))

    def getDateDiff(self, d1, d2):
        return (self.getDate(d2) - self.getDate(d1)).days

    def getWednesday(self, d):      # d = '2009-12-10'
        oldDate = self.getDate(d)
        newDate = oldDate + timedelta(2 - oldDate.weekday())
        return newDate

    def fitness(self, symbol, startDate, endDate):
        #startTime = datetime.now()
        l = (self.getDate(endDate) - self.getDate(startDate)).days / 365
        g20 = StockScore({"AAOD": endDate, "symbol": symbol})
        #print('g20 init run time:', datetime.now()-startTime)

        #startTime = datetime.now()
        sr = g20.get_sr(l)
        #print('sr run time:', datetime.now()-startTime)
        #startTime = datetime.now()
        g = g20.growthRate(l)
        #print('g run time:', datetime.now()-startTime)
        #print('fitness run time:', datetime.now()-startTime)
        return {
            #'sr':   sr,
            #'g':    g
            'Symbol':   symbol,
            'SR':       sr['SR'],
            'G':        g['G']
        }

    def fitness2(self, symbol, startDate, endDate):
        #startTime = datetime.now()
        mongo_query = {"$and": [{"Date": {"$lte": endDate}}, {"Date": {"$gte": startDate}}]}
        mongo_col_q = self.mongoDB.get_collection(symbol)
        q = list(mongo_col_q.find(mongo_query).sort("Date", -1))
        #print(len(q), q)
        if len(q) > 0:
            start = q[0]['Close']
            startDate = q[0]['Date']
            end = q[-1]['Close']
            endDate = q[-1]['Date']
            sr_df = pd.DataFrame(q)
            #print(sr_df['Close'])
            #r1 = sr_df['Close'].diff()
            #print(r1)
            #r2 = (sr_df['Close'].shift(1)-sr_df['Close'])/sr_df['Close'].shift(1)
            #print(r2)
            r = (sr_df['Close'].shift(1)-sr_df['Close'])/sr_df['Close']
            #print(r)
            sr = np.sqrt(252) * r.mean() / r.std()

            #print(startDate, endDate)
            #G20 Year = Days(G20 Date - AAOD) / 365
            #G20 Price = close @20
            #Total G20 = (today close / G20 Price) - 1
            #G20 = POWER(10, LOG10(1+Total G20) / G20 Year) - 1
            #G20 Weight = 100
            gYear = (datetime(*(int(s) for s in startDate.split('-'))) - datetime(*(int(s) for s in endDate.split('-')))).days / 365
            #print(gYear)
            weight = 100
            if start != 'null' and end != 'null':
                totalG = start / end - 1
            else:
                totalG = 0
            g = weight * (10 ** (np.log10(1 + totalG) / gYear) - 1)
            result = {
                #'sr':   sr,
                #'g':    g
                'Symbol':   symbol,
                'SR':       sr,
                'G':        g
            }
        else:
            result = {
                #'sr':   sr,
                #'g':    g
                'Symbol':   symbol,
                'SR':       0,
                'G':        0
            }
        #print('fitness2 run time:', datetime.now()-startTime)
        return result

    def getG(self, option):
        g = self.mongoDB['stock_g_score'].find_one({'symbol': option['symbol'], 'runDate': option['AAOD']})
        if self.mongoDB['stock_g_score'].count_documents({'symbol': option['symbol'], 'runDate': option['AAOD']}) == 0:
            g20 = StockScore(option)
            g = g20.run()
            g20.save_g20()
        return g

    def getAllG(self, d):
        #g = self.mongoDB['stock_g_list'].find_one({'date': d})
        gList  = list(self.mongoDB['stock_g_score'].find({"$and": [{'runDate': d}, {'Recommendation': ''}]}))
        #if self.mongoDB['stock_g_list'].count_documents({'date': d}) > 0:
        #    return g['gList']
        if len(gList) < 100:
            #gList = []
            com = self.mongoDB['etrade_companies'].find(no_cursor_timeout=True)
            dbList = self.mongoDB.list_collection_names()
            for c in com:
                if c['Yahoo_Symbol'] in dbList:
                    try:
                        g20 = StockScore({'AAOD': d, 'symbol': c['Symbol']})
                        g = g20.run()
                        if g['Recommendation'] == '' and g['CAP'] > 0:
                            #gList.append(g)
                            g20.save_g20()
                            #print(json_util.dumps(g, indent=4))
                    except Exception as error:
                        continue
            #gList = sorted(gList, key=lambda k: k['Score'], reverse=True)
            #self.mongoDB['stock_g_list'].replace_one(
            #    {'date': d},
            #    {'date': d, 'gList': gList},
            #    upsert=True)

            gList = list(self.mongoDB['stock_g_score'].find({"$and": [{'runDate': d}, {'Recommendation': ''}]}))
        return gList

    def getPrice(self, s, d):
        col = self.mongoDB.get_collection(s)
        query = {'Date': d}
        quote = col.find_one(query)
        if quote != None :
            return quote['Close']
        else:
            return 0

    def getTotal(self, d):
        total = self.p['cash']
        price = 0
        for s in self.p['stocks']:
            price = self.getPrice(s['symbol'], d)
            total = total + price * s['share']
        return total

    def init(self, pn, date, endDate, init_cash, ss):           # pn - portfolio name;  d = start date,  10 years back; endDate = last date for the evaluation; ss = initial stock list
        #init_cash = 500000
        stocks = []
        #get stock price
        #AMZN, ANTM, TSLA, COST, ISRG, CRM, ATVI, AAPL, GS, GE
        if ss == []:
            ss = ['AMZN', 'ANTM', 'TSLA', 'COST', 'ISRG', 'CRM', 'ATVI', 'AAPL', 'GS', 'GE']
            for symbol in ss:
                price = self.getPrice(symbol, date)
                if price > 0:
                    share = math.floor(100000 / price)
                    position = price * share
                    g = self.getG({'AAOD': date, 'symbol': symbol})
                    stock = {
                        "symbol":   symbol,
                        "share":    share,
                        "actions":
                            [
                                {
                                    "date": date,
                                    "action_type": "buy",
                                    "reason": "initial_buy",
                                    "fitness": {'Symbol': g['symbol'], 'SR': g['SR20'], 'G': g['Score']},
                                    "price": price,
                                    "share": share,
                                    "commission": 9,
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
                    g = self.getG({'AAOD': date, 'symbol': s['symbol']})
                    stock = {
                        "symbol":   s['symbol'],
                        "share":    share,
                        "actions":
                            [
                                {
                                    "date": date,
                                    "action_type": "buy",
                                    "reason": "initial_buy",
                                    "fitness": {'Symbol': g['symbol'], 'SR': g['SR20'], 'G': g['Score']},
                                    "price": price,
                                    "share": share,
                                    "commission": 9,
                                    "value": position
                                }
                            ]
                    }
                    stocks.append(stock)

        self.p = {
            "name": pn,
            "init_date": date,
            'end_date': endDate,
            "last_update_date": date,
            "last_cross_sell_date": date,
            "last_cross_profit_sell_date": date,
            "last_cross_buy_date": date,
            "last_mutate_sell_date": date,
            "last_mutate_perf_sell_date": date,
            "last_mutate_buy_date": date,
            "crossover_sell_flag": 1, # 1 execute;  0 skip
            "crossover_sell_period": 7, # 7 = weekly;  30 = monthly
            "crossover_sr_sell_threshold": -50,
            "crossover_sell_no": 1,
            "crossover_profit_sell_flag": 1, # 1 execute;  0 skip
            "crossover_profit_sell_period": 30, # 7 = weekly;  30 = monthly
            "crossover_profit_sell_threshold": 1000,
            "crossover_profit_sell_no": 1,
            "crossover_buy_flag": 1, # 1 execute;  0 skip
            "crossover_buy_period": 7, # 7 = weekly;  30 = monthly
            "crossover_g_buy_threshold": 6000,
            "crossover_g_buy_up_limit": 10000,
            "crossover_buy_no": 1,
            "mutate_sell_flag": 1, # 1 execute;  0 skip
            "mutate_sell_period": 30, # 30 = monthly;  365 = yearly
            "mutate_sell_sr_threshold": -10,  # sr < -10; g < -93
            "mutate_sell_no": 2,
            "mutate_perf_sell_flag": 1, # 1 execute;  0 skip
            "mutate_perf_sell_period": 90, # 30 = monthly;  90 = quarterly; 365 = yearly
            "mutate_perf_sell_lookback_period": 1825, # 30 = monthly;  365 = yearly; 730 = two years
            "mutate_perf_sell_g_threshold": -10,  # g <= 10%
            "mutate_perf_sell_no": 1,
            "mutate_buy_flag": 1, # 1 execute;  0 skip
            "mutate_buy_period": 30, # 30 = monthly;  365 = yearly
            "mutate_buy_g_threshold":  20,
            "mutate_buy_g_up_limit":  100,
            "mutate_buy_sr_threshold":  0.5,
            "mutate_buy_no": 1,
            "cash": init_cash,
            'total': init_cash,
            "total_history": [],
            "stocks": stocks
        }
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
            if 'last_cross_profit_sell_date' not in self.p:
                self.p['last_cross_profit_sell_date'] = self.p['end_date']
            if 'last_cross_buy_date' not in self.p:
                self.p['last_cross_buy_date'] = self.p['end_date']
            if 'last_mutate_sell_date' not in self.p:
                self.p['last_mutate_sell_date'] = self.p['end_date']
            if 'last_mutate_perf_sell_date' not in self.p:
                self.p['last_mutate_perf_sell_date'] = self.p['end_date']
            if 'last_mutate_buy_date' not in self.p:
                self.p['last_mutate_buy_date'] = self.p['end_date']
            self.p['end_date'] = newEndDate

            return self.p
        else:
            return None

    def crossover_buy(self, startDate, endDate, crossBuyFlag):
        #print('crossover_buy:', startDate, endDate)
        execute_flag = 0
        if crossBuyFlag > 0:
            fList = []
            for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                f = self.fitness2(s['symbol'], startDate, endDate)
                f['sIndex'] = i
                fList.append(f)
            fList = sorted(fList, key=lambda k: k['G'], reverse=True)
            crossover_buy_no = 0
            for s in fList:
                if crossover_buy_no >= self.p['crossover_buy_no']:
                    break
                ss = self.p['stocks'][s['sIndex']]['share']
                #for i, s in enumerate(self.p['stocks']):
                # f = self.fitness(s['symbol'], startDate, endDate)
                # f = self.fitness2(s['symbol'], startDate, endDate)
                # buy self.p['crossover_g_buy_threshold']
                #if f['G'] > self.p['crossover_g_buy_threshold'] and f['G'] <= self.p['crossover_g_buy_up_limit'] and s['share'] >= 10:
                    #buy_share = math.floor(s['share'] * 0.1)
                if s['G'] > self.p['crossover_g_buy_threshold'] and s['G'] <= self.p['crossover_g_buy_up_limit'] and ss >= 10 and crossover_buy_no < self.p['crossover_buy_no']:
                    buy_share = math.floor(ss * 0.1)
                    buy_price = self.getPrice(s['Symbol'], endDate)
                    buy_position = buy_price * buy_share
                    if buy_price > 0 and buy_position < self.p['cash'] - 9:
                        buy_action = {
                            "date": endDate,
                            "action_type": "buy",
                            "reason": "crossover_buy",
                            "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                            "price": buy_price,
                            "share": buy_share,
                            "commission": 9,
                            "value": buy_position
                        }

                        remaining_share = ss + buy_share
                        # update p
                        self.p['last_update_date'] = endDate
                        self.p['stocks'][s['sIndex']]['share'] = remaining_share
                        self.p['stocks'][s['sIndex']]['actions'].append(buy_action)
                        self.p['cash'] = self.p['cash'] - buy_position - 9
                        crossover_buy_no = crossover_buy_no + 1
                        # print(self.p)
                        execute_flag = 1
            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
        return execute_flag

    def crossover_sell(self, startDate, endDate, crossSellFlag):
        #print('crossover_sell:', startDate, endDate)
        execute_flag = 0
        if crossSellFlag > 0:
            fList = []
            for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                f = self.fitness2(s['symbol'], startDate, endDate)
                f['sIndex'] = i
                fList.append(f)
            fList = sorted(fList, key=lambda k: k['SR'], reverse=False)
            #print(fList)
            crossover_sell_no = 0
            for s in fList:
                if crossover_sell_no >= self.p['crossover_sell_no']:
                    break
                ss = self.p['stocks'][s['sIndex']]['share']
                #for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                #f = self.fitness2(s['symbol'], startDate, endDate)
                #sell if f.SR < crossover_sr_sell_threshold
                #if f['SR'] < self.p['crossover_sr_sell_threshold'] and s['share'] > 0:
                if s['SR'] < self.p['crossover_sr_sell_threshold'] and ss > 0 and crossover_sell_no < self.p['crossover_sell_no']:
                    sell_share = (-1) * math.floor(ss * 0.1)
                    sell_price = self.getPrice(s['Symbol'], endDate)
                    sell_position = sell_price * sell_share
                    if sell_price > 0 and sell_position > -5000: # minimum sell 5k
                        sell_position = -5000
                        sell_share = (-1) * math.floor((-1) * sell_position / sell_price)
                        if (-1) * sell_share > ss:
                            sell_share = (-1) * ss
                            sell_position = sell_price * sell_share
                    sell_action = {
                        "date": endDate,
                        "action_type": "sell",
                        "reason": "crossover_sell",
                        "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                        "price": sell_price,
                        "share": sell_share,
                        "commission": 9,
                        "value": sell_position
                    }
                    #print(sell_action)

                    remaining_share = ss + sell_share
                    # update p
                    self.p['last_update_date'] = endDate
                    self.p['stocks'][s['sIndex']]['share'] = remaining_share
                    self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                    self.p['cash'] = self.p['cash'] - sell_position - 9
                    crossover_sell_no = crossover_sell_no + 1
                    #print(self.p)
                    execute_flag = 1

            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
        return execute_flag

    def crossover_profit_sell(self, startDate, endDate, crossProfitSellFlag):
        #print('crossover_profit_sell:', startDate, endDate)
        execute_flag = 0
        if crossProfitSellFlag > 0:
            fList = []
            sList = []
            for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                f = self.fitness2(s['symbol'], startDate, endDate)
                f['sIndex'] = i
                fList.append(f)
                sList.append(s['symbol'])

            fList = sorted(fList, key=lambda k: k['G'], reverse=True)
            crossover_profit_sell_no = 0
            for s in fList:
                if crossover_profit_sell_no >= self.p['crossover_profit_sell_no']:
                    break
                ss = self.p['stocks'][s['sIndex']]['share']
                #for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                #f = self.fitness2(s['symbol'], startDate, endDate)
                # profit sell if f.SR > crossover_profit_threshold
                if s['G'] > self.p['crossover_profit_sell_threshold'] and ss > 0 and crossover_profit_sell_no < self.p['crossover_profit_sell_no']:
                    sell_share = (-1) * math.floor(ss * 0.1)
                    sell_price = self.getPrice(s['Symbol'], endDate)
                    sell_position = sell_price * sell_share
                    if sell_price > 0 and sell_position > -5000: # minimum sell 5k
                        sell_position = -5000
                        sell_share = (-1) * math.floor((-1) * sell_position / sell_price)
                        if (-1) * sell_share > ss:
                            sell_share = (-1) * ss
                            sell_position = sell_price * sell_share
                    sell_action = {
                        "date": endDate,
                        "action_type": "sell",
                        "reason": "crossover_profit_sell",
                        "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                        "price": sell_price,
                        "share": sell_share,
                        "commission": 9,
                        "value": sell_position
                    }

                    remaining_share = ss + sell_share
                    # update p
                    self.p['last_update_date'] = endDate
                    self.p['stocks'][s['sIndex']]['share'] = remaining_share
                    self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                    self.p['cash'] = self.p['cash'] - sell_position - 9
                    crossover_profit_sell_no = crossover_profit_sell_no + 1
                    #print(self.p)
                    execute_flag = 1

            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
        return execute_flag

    def mutate_sell(self, startDate, endDate, mutateSellFlag):
        #print('mutate_sell:', startDate, endDate)
        execute_flag = 0
        if mutateSellFlag > 0:
            fList = []
            sList = []
            for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], startDate, endDate)
                f = self.fitness2(s['symbol'], startDate, endDate)
                f['sIndex'] = i
                fList.append(f)
                sList.append(s['symbol'])

            # mutate_sell
            fList = sorted(fList, key=lambda k: k['SR'], reverse=False)
            mutate_sell_no = 0
            for s in fList:
                if mutate_sell_no >= self.p['mutate_sell_no']:
                    break
                ss = self.p['stocks'][s['sIndex']]['share']
                if s['SR'] <= self.p['mutate_sell_sr_threshold'] and mutate_sell_no < self.p['mutate_sell_no'] and ss > 0:
                    sell_share = (-1) * ss
                    #print(s['Symbol'])
                    sell_price = self.getPrice(s['Symbol'], endDate)
                    if sell_price > 0:
                        sell_position = sell_price * sell_share
                        sell_action = {
                            "date": endDate,
                            "action_type": "sell",
                            "reason": "mutate_sell",
                            "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                            "price": sell_price,
                            "share": sell_share,
                            "commission": 9,
                            "value": sell_position
                        }

                        remaining_share = self.p['stocks'][s['sIndex']]['share'] + sell_share
                        # update p
                        self.p['last_update_date'] = endDate
                        self.p['stocks'][s['sIndex']]['share'] = remaining_share
                        self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                        self.p['cash'] = self.p['cash'] - sell_position - 9
                        mutate_sell_no = mutate_sell_no + 1
                        execute_flag = 1

            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
        return execute_flag

    def mutate_perf_sell(self, startDate, endDate, mutatePerfSellFlag):
        #print('mutate_sell:', startDate, endDate)
        execute_flag = 0
        if mutatePerfSellFlag > 0:
            fList = []
            sList = []

            sDate = (self.getDate(endDate) + timedelta((-1) * self.p['mutate_perf_sell_lookback_period'])).strftime('%Y-%m-%d')
            #print(sDate)
            for i, s in enumerate(self.p['stocks']):
                #f = self.fitness(s['symbol'], sDate, endDate)
                f = self.fitness2(s['symbol'], sDate, endDate)
                f['sIndex'] = i
                fList.append(f)
                sList.append(s['symbol'])

            # mutate_sell
            fList = sorted(fList, key=lambda k: k['G'], reverse=False)
            #print(fList)
            mutate_perf_sell_no = 0
            for s in fList:
                if mutate_perf_sell_no >= self.p['mutate_perf_sell_no']:
                    break
                ss = self.p['stocks'][s['sIndex']]['share']
                if s['G'] <= self.p['mutate_perf_sell_g_threshold'] and mutate_perf_sell_no < self.p['mutate_perf_sell_no'] and ss > 0:
                    sell_share = (-1) * ss
                    #print(s['Symbol'])
                    sell_price = self.getPrice(s['Symbol'], endDate)
                    if sell_price > 0:
                        sell_position = sell_price * sell_share
                        sell_action = {
                            "date": endDate,
                            "action_type": "sell",
                            "reason": "mutate_perf_sell",
                            "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                            "price": sell_price,
                            "share": sell_share,
                            "commission": 9,
                            "value": sell_position
                        }

                        remaining_share = self.p['stocks'][s['sIndex']]['share'] + sell_share
                        # update p
                        self.p['last_update_date'] = endDate
                        self.p['stocks'][s['sIndex']]['share'] = remaining_share
                        self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                        self.p['cash'] = self.p['cash'] - sell_position - 9
                        mutate_perf_sell_no = mutate_perf_sell_no + 1
                        execute_flag = 1

            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
            #print(json_util.dumps(self.p['stocks'], indent=4))
        return execute_flag

    def mutate_buy(self, startDate, endDate, mutateBuyFlag):
        #print('mutate_buy:', startDate, endDate)
        exclusionList = ['GOOG', 'JMDA', 'QRHC', 'CCGN', 'BRVO', 'PIC', 'ELLI', 'HMTA', 'EIC', 'PUODY', 'PEER', 'BLMT', 'GOLD', 'TRCK', 'ATPT', 'VALE']
        execute_flag = 0
        if mutateBuyFlag > 0 and self.p['cash'] >= 10000:
            sList = []
            for i, s in enumerate(self.p['stocks']):
                sList.append(s['symbol'])

            # mutate_buy
            gList = self.getAllG(endDate)
            #gList = sorted(gList, key=lambda k: k['Score'], reverse=True)
            #gList = sorted(gList, key=lambda k: k['SR20'], reverse=True)
            #gList = sorted(gList, key=lambda k: k['SR1'], reverse=True)
            gList = sorted(gList, key=lambda k: k['CAP'], reverse=True)
            mutate_buy_no = 0
            for s in gList:
                if mutate_buy_no >= self.p['mutate_buy_no']:
                    break
                if s['symbol'] not in exclusionList and s['symbol'] not in sList and s['Score'] >= self.p['mutate_buy_g_threshold']\
                        and mutate_buy_no < self.p['mutate_buy_no']\
                        and s['Score'] <= self.p['mutate_buy_g_up_limit']\
                        and s['SR1'] >= self.p['mutate_buy_sr_threshold']\
                        and (s['CAP'] == 0 or s['CAP'] > 5):
                    # and s['SR20'] >= self.p['mutate_buy_sr_threshold']:
                    buy_price = self.getPrice(s['symbol'], endDate)
                    if buy_price > 0:
                        buy_share = math.floor(100000 / buy_price)
                        buy_position = buy_price * buy_share
                        if self.p['cash'] > buy_position:
                            stock = {
                                "symbol": s['symbol'],
                                "share": buy_share,
                                "actions":
                                    [
                                        {
                                            "date": endDate,
                                            "action_type": "buy",
                                            "reason": "mutate_buy",
                                            "fitness": {'Symbol': s['symbol'], 'SR': s['SR1'], 'G': s['Score']},
                                            #"gScore": s['Score'],
                                            "price": buy_price,
                                            "share": buy_share,
                                            "commission": 9,
                                            "value": buy_position
                                        }
                                    ]
                            }

                            # update p
                            self.p['last_update_date'] = endDate
                            self.p['stocks'].append(stock)
                            self.p['cash'] = self.p['cash'] - buy_position - 9
                            mutate_buy_no = mutate_buy_no + 1
                            execute_flag = 1

            #total = self.getTotal(endDate)
            #self.p['total'] = total
            #self.p['total_history'].append({"date": endDate, "cash": self.p['cash'], "total": total})
        return execute_flag

    def generation(self):
        mongo_query = {'$and': [{'Date': {'$gte': self.p['last_update_date']}}, {'Date': {'$lte': self.p['end_date']}}]}
        mongo_col_q = self.mongoDB.get_collection('AMZN')
        qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))

        index = 1
        #stopIndex = len(qDates) - 7
        stopIndex = 1500000
        for q in qDates:
            if index > stopIndex:
                break
            d = q['Date']
            dd = self.getDate(d)
            #print(index, d)

            execute_count = 0
            crossover_sell_execute = 0
            crossover_profit_sell_execute = 0
            crossover_buy_execute = 0
            mutate_sell_execute = 0
            mutate_perf_sell_execute = 0
            mutate_buy_execute = 0
            if self.getDateDiff(self.p['last_mutate_perf_sell_date'], d) >= self.p['mutate_perf_sell_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                mutate_perf_sell_execute = self.mutate_perf_sell(self.p['last_mutate_perf_sell_date'], d, self.p['mutate_perf_sell_flag'])
                self.p['last_mutate_perf_sell_date'] = d
            if self.getDateDiff(self.p['last_mutate_sell_date'], d) >= self.p['mutate_sell_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                mutate_sell_execute = self.mutate_sell(self.p['last_mutate_sell_date'], d, self.p['mutate_sell_flag'])
                self.p['last_mutate_sell_date'] = d
            if self.getDateDiff(self.p['last_cross_sell_date'], d) >= self.p['crossover_sell_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                crossover_sell_execute = self.crossover_sell(self.p['last_cross_sell_date'], d, self.p['crossover_sell_flag'])
                self.p['last_cross_sell_date'] = d
            if self.getDateDiff(self.p['last_cross_profit_sell_date'], d) >= self.p['crossover_profit_sell_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                crossover_profit_sell_execute = self.crossover_profit_sell(self.p['last_cross_profit_sell_date'], d, self.p['crossover_profit_sell_flag'])
                self.p['last_cross_profit_sell_date'] = d
            if self.getDateDiff(self.p['last_mutate_buy_date'], d) >= self.p['mutate_buy_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                mutate_buy_execute = self.mutate_buy(self.p['last_mutate_buy_date'], d, self.p['mutate_buy_flag'])
                self.p['last_mutate_buy_date'] = d
            if self.getDateDiff(self.p['last_cross_buy_date'], d) >= self.p['crossover_buy_period'] and dd.weekday() != 0 and dd.weekday() != 4:
                crossover_buy_execute = self.crossover_buy(self.p['last_cross_buy_date'], d, self.p['crossover_buy_flag'])
                self.p['last_cross_buy_date'] = d

            execute_count = crossover_sell_execute + crossover_profit_sell_execute + crossover_buy_execute + mutate_perf_sell_execute + mutate_sell_execute + mutate_buy_execute
            if execute_count > 0 or index == stopIndex or index == len(qDates):
                total = self.getTotal(d)
                self.p['total'] = total
                action = []
                if crossover_sell_execute == 1:
                    action.append("Crossover_Sell")
                if crossover_profit_sell_execute == 1:
                    action.append("Crossover_Profit_Sell")
                if crossover_buy_execute == 1:
                    action.append("Crossover_Buy")
                if mutate_perf_sell_execute == 1:
                    action.append("Mutate_Perf__Sell")
                if mutate_sell_execute == 1:
                    action.append("Mutate_Sell")
                if mutate_buy_execute == 1:
                    action.append("Mutate_Buy")
                self.p['total_history'].append({"date": d, "cash": self.p['cash'], "total": total, "action": action})

                if index == stopIndex or index == len(qDates):
                    self.p['last_update_date'] = d

                if self.save_p_flag > 0:
                    self.save_p()
                #print(json_util.dumps(self.p, indent=4))
            index = index + 1

    def save_p(self):
        self.mongoDB['stock_ga_results'].replace_one(
            {"name": self.p['name']},
            self.p,
            upsert=True)


if __name__ == '__main__':

    init_date = '2009-12-09'
    end_date = '2020-01-10'
    init_cash = 500000
    init_list = []
    save_p_flag = 0

    csList = [-80]
    cpsList = [1000]
    cbList = [1000]
    # msList = [-10, -20, -40]
    msList = [-10]
    #mpsList = [-50]
    mpsList = [10]   #-10
    #mbList = [1]
    mbList = [5]
    mbgList = [20]

    i = 97
    restart = 1
    stop = 150000
    ga = RuleGA(save_p_flag)
    #print(ga.fitness('AMZN', '2009-12-09', '2009-12-16'))
    #print(ga.fitness2('AMZN', '2009-12-09', '2009-12-16'))

    bestG = {}
    bestTotal = 0
    for cs in csList:
        for cps in cpsList:
            for cb in cbList:
                for ms in msList:
                    for mps in mpsList:
                        for mb in mbList:
                            for mbg in mbgList:
                                if i >= restart and i <= stop:
                                    startTime = datetime.now()

                                    ga_name = 'testG3_' + format(i,'02d')
                                    print(i, ga_name)
                                    #print('mutate_sell_sr_threshold', ms)
                                    ga.init(ga_name, init_date, end_date, init_cash, init_list)
                                    ga.p['crossover_sr_sell_threshold'] = cs
                                    ga.p['crossover_profit_sell_threshold'] = cps
                                    ga.p['crossover_g_buy_threshold'] = cb
                                    ga.p['mutate_sell_sr_threshold'] = ms
                                    ga.p['mutate_perf_sell_g_threshold'] = mps
                                    ga.p['mutate_buy_sr_threshold'] = mb
                                    ga.p['mutate_buy_g_threshold'] = mbg

                                    #print(ga.p)
                                    ga.generation()
                                    if bestTotal < ga.p['total']:
                                        bestG = ga.p
                                        bestTotal = ga.p['total']
                                    print(json_util.dumps(ga.p, indent=4))

                                    endTime = datetime.now()
                                    runTime = endTime - startTime
                                    print('run time', runTime)
                                i = i + 1
    '''
    #test reload
    save_p_flag = 0
    new_end_date = '2020-01-31'
    ga = RuleGA(save_p_flag)
    ga.reload('testG3_96', new_end_date)
    #print(ga.getTotal('2020-01-10'))
    print(json_util.dumps(ga.p, indent=4))

    ga.generation()
    print(json_util.dumps(ga.p, indent=4))
    '''
    '''
    init_date = '2019-05-16'
    init_list = [
        {'symbol': 'LYFT',
         'shares': 909},
        {'symbol': 'TTD',
         'shares': 250},
        {'symbol': 'AYX',
         'shares': 550},
        {'symbol': 'ISRG',
         'shares': 180},
        {'symbol': 'CRM',
         'shares': 600},
        {'symbol': 'ATVI',
         'shares': 700},
        {'symbol': 'MDB',
         'shares': 664},
        {'symbol': 'SQ',
         'shares': 1350},
        {'symbol': 'BABA',
         'shares': 400},
        {'symbol': 'AAPL',
         'shares': 200},
        #{'symbol': 'TCEHY',
        # 'shares': 1600},
        {'symbol': 'FB',
         'shares': 333},
        {'symbol': 'AMZN',
         'shares': 40},
        {'symbol': 'TSLA',
         'shares': 300},
        {'symbol': 'ANTM',
         'shares': 5430},
        {'symbol': 'COST',
         'shares': 49},
        {'symbol': 'GS',
         'shares': 37},
        {'symbol': 'GE',
         'shares': 126}
    ]

    csList = [-80]
    cpsList = [1000]
    cbList = [1000]
    # msList = [-10, -20, -40]
    msList = [-10]
    mpsList = [-50]
    mbList = [3]

    i = 94
    restart = 1
    stop = 150000
    ga = RuleGA()
    #print(ga.fitness('AMZN', '2009-12-09', '2009-12-16'))
    #print(ga.fitness2('AMZN', '2009-12-09', '2009-12-16'))

    #bestG = {}
    #bestTotal = 0
    for cs in csList:
        for cps in cpsList:
            for cb in cbList:
                for ms in msList:
                    for mps in mpsList:
                        for mb in mbList:
                            if i >= restart and i <= stop:
                                startTime = datetime.now()

                                ga_name = 'testG3_' + format(i,'02d')
                                print(i, ga_name)
                                ga.init(ga_name, init_date, init_list)
                                ga.p['crossover_sr_sell_threshold'] = cs
                                ga.p['crossover_profit_sell_threshold'] = cps
                                ga.p['crossover_g_buy_threshold'] = cb
                                ga.p['mutate_sell_sr_threshold'] = ms
                                ga.p['mutate_perf_sell_g_threshold'] = mps
                                ga.p['mutate_buy_sr_threshold'] = mb
                                #print(ga.p)
                                ga.generation()
                                #if bestTotal < ga.p['total']:
                                #    bestG = ga.p
                                #    bestTotal = ga.p['total']
                                print(json_util.dumps(ga.p, indent=4))

                                endTime = datetime.now()
                                runTime = endTime - startTime
                                print('run time', runTime)
                            i = i + 1

    '''
'''
    #for mb in mbList:
    #    if i >= restart and i <= stop:
    #        startTime = datetime.now()

    #        ga_name = 'testG3_' + format(i, '02d')
    #        print(i, ga_name)
    #        ga.init(ga_name, '2009-12-09', [])
    #        ga.p['mutate_buy_sr_threshold'] = mb
    #        ga.generation()
    #        if bestTotal < ga.p['total']:
    #            bestG = ga.p
    #            bestTotal = ga.p['total']
    #        print(json_util.dumps(ga.p, indent=4))

    #        endTime = datetime.now()
    #        runTime = endTime - startTime
    #        print('run time', runTime)
    #    i = i + 1

    #print('best ga:')
    #print(json_util.dumps(bestG, indent=4))
    #ga = RuleGA()
    #ga.init('ga_1', '2009-12-09', [])
    #ga.init('ga_2', '2009-12-09', [])
    #ga.init('ga_3', '2009-12-09', [])
    #ga.init('ga_4', '2009-12-09', [])
    #ga.init('ga_5', '2009-12-09', [])
    #ga.init('ga_6', '2009-12-09', [])
    #ga.init('ga_7', '2009-12-09', [])
    #ga.reload('ga_3')
    #print(json.dumps(ga.reload('ga_1'), indent=4))
    #print(ga.getWednesday('2018-12-09'))
    #print(ga.fitness('ANTM', '2009-12-02', '2009-12-09'))
    #print(ga.getPrice('ANTM', '2009-12-09'))
    #print(ga.getG({"AAOD": '2009-12-09', "symbol": 'AMZN'}))
    #print(json.dumps(ga.init('ga_1', '2009-12-09'), indent=4))
    #ga.getTotal('2019-12-09')
    #ga.mutate('2009-12-09', '2010-01-08')
    #for g in ga.getAllG('2010-01-12'):
    #    print(json.dumps(g, indent=4))
    #ga.generation()
    #print(json_util.dumps(ga.p, indent=4))

    # get baseline with no crossover and mutate
    #ga = RuleGA()
    #ga.init('ga_0', '2009-12-09')
    #ga.generation(0, 0)
    #print(json_util.dumps(ga.p, indent=4))
'''
'''
                #mutate profit sell
                if s['G'] > self.p['mutate_sell_profit_threshold'] and ss > 0:
                    sell_share = (-1) * math.floor(ss * 0.1)
                    sell_price = self.getPrice(s['Symbol'], endDate)
                    sell_position = sell_price * sell_share
                    if sell_position > -5000: # minimum sell 5k
                        sell_position = -5000
                        sell_share = (-1) * math.floor((-1) * sell_position / sell_price)
                        if (-1) * sell_share > ss:
                            sell_share = (-1) * ss
                            sell_position = sell_price * sell_share
                    sell_action = {
                        "date": endDate,
                        "action_type": "sell",
                        "reason": "mutate_profit_sell",
                        "fitness": {'Symbol': s['Symbol'], 'SR': s['SR'], 'G': s['G']},
                        "price": sell_price,
                        "share": sell_share,
                        "commission": 9,
                        "value": sell_position
                    }

                    remaining_share = ss + sell_share
                    # update p
                    self.p['last_update_date'] = endDate
                    self.p['stocks'][s['sIndex']]['share'] = remaining_share
                    self.p['stocks'][s['sIndex']]['actions'].append(sell_action)
                    self.p['cash'] = self.p['cash'] - sell_position - 9
'''
