'''
Algorithm
Goal: Compute G20 score
Pattern:
Rating = Mkt Cap Score + History Average Annual Gain(G20) * Weight + PE Score + Dividend Score + Industry Rating * Industry Ranking
1. Mkt Cap Score:
    If cap > 10B, score = -0.001 * cap
    If cap <= 10B, score = (cap - 10) / (10 * cap)
2. G20:
    G20 Year = Days(G20 Date - AAOD) / 365
    G20 Price = close @20
    Total G20 = (today close / G20 Price) - 1
    G20 = POWER(10, LOG10(1 + Total G20) / G20 Year) - 1
    G20 Weight = 100
3. PE Score = PE Weight * (PE - Industry Average PE) / Industry Average PE
    PE Weight = 1
4. Dividend Score = Dividend Weight * (Dividend - Industry Average Dividend) / Industry Average Dividend
    Dividend Weight = 1
Not implemented because quarterly dividend and partial data
5. Industry Ranking = Sector Rating * Industry Rating
    Sector                                          Rating
    Industrials                                     1
    Non - Cyclical Consumer Goods & Services        1
    Healthcare                                      5
    Energy                                          2
    Financial                                       5
    Utilities                                       1
    Basic Material                                  1
    Technology                                      10
    Cyclical Consumer Goods & Services              1
    Telecommunication Services                      5

    Industry Rating: 0, .25, .5, 1

    Cap                 Industry Rating
    <= 10               0
    10 - 20             .25
    20 - 100            .5
    >= 100              1
6. Checks:
    1. G20Year < 1 - just note
    2. G20Close <= 1 -- just noted
    3. G1 < 0
    4. Industry = Tobacco
    5. Non USA
    6. G20 / G1 > 2 -- just noted
    7. Healthcare & G20Year < 5
    8. G20 / G1 < 0.25 -- just noted
    9. Stop
    10. if at least 1 of the following 4 > .2 -- just noted
        QuarterRevScore
        YearlyRevScore
        QuarterlyEPSScore
        YearlyEPSScore
    11. CAP < 1 -- just noted
    12. G20 < 10
    13. RL Checks:
            1. model_score < 1.1
            2. predict_date > 5
            3. len < 5
            4. predict_vol = 0
            5. predict_action < 1 -- buy
            6. predict_action >= 1 -- sell
            7. predict_action >= 2 -- hold
    14. Price < 1 ?
    15. Price / History Highest < 0.1
7. EPS Score
    1. current yearly eps increase
        early_eps_rate = (early_eps(today) - early_eps(today - 365)) / early_eps(today - 365)
    2. average yearly eps increase
        yearly_eps_rate(i) = (yearly_eps(i) - yearly_eps(i - 365)) / yearly_eps(i - 365)

    ave_early_eps_rate = Sum(early_eps_rate(i)) / sum(i)
    3. EPS Score
        3.1 if ave_early_eps_rate <> 0
            eps_score = 100 * (yearly_eps_rate + abs(yearly_eps_rate) * (yearly_eps_rate - ave_yearly_eps_rate) / abs(ave_yearly_eps_rate)))
        3.2 if ave_early_eps_rate = 0
            eps_score = 100 * yearly_eps_rate
8. Sharpe Ratio

Change History
2022/12/13 - change RL run param to run_rl:  0 - no run as default; 1 - run per condition; 2 - always run
2022/12/19 - updage averagePE, limit to active companies
2023/02/10 - relax CAP < 1,  G20Year < 1;  add Price < 1 ?,  Price / History Highest < 0.1
2023/03/06 - add cap < 0.2 B
'''
# Import Matplotlib's `pyplot` module as `plt`
# import matplotlib.pyplot as plt
# from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
#                               AutoMinorLocator)
# import sys
# import os
# import logging
#import warnings
#warnings.filterwarnings("ignore")
#import os
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
#import tensorflow as tf
#tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

#from datetime import date
from datetime import datetime
from datetime import timedelta
# import datetime
# import pymongo
# import json
#import re
#import pandas as pd
import numpy as np
import json
import traceback
from test_fundamentals import StockFundamentalsExplorer
from test_mongo import MongoExplorer
from test_stockstats import StockStats
import pandas as pd
#from pandas import json_normalize
from test_rl_macd_v2 import StockRL
import os.path
from test_yahoo import QuoteExplorer

class StockScore:
    def __init__(self, options):
        self.runDate = options['AAOD']
        self.AAOD = options['AAOD']
        self.symbol = options['symbol']
        if 'rl_save_loc' in options:
            self.rl_save_loc = options['rl_save_loc']
        else:
            self.rl_save_loc = './rl/test_rl_'

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        query_date = datetime(*(int(s) for s in self.AAOD.split('-')))
        mongo_query1 = {"symbol": self.symbol, "date": {"$lte": query_date}}
        mongo_query11 = {"symbol": self.symbol}
        mongo_query2 = {"Date": {"$lte": self.AAOD}}
        self.company = self.mongoDB['etrade_companies'].find_one({"Symbol": self.symbol})
        # print(self.symbol, self.company)
        #self.fundamentals = list(self.mongoDB['etrade_fundamentals'].find(mongo_query1).sort("date", -1))
        #if len(self.fundamentals) == 0:
        #    self.fundamentals = list(self.mongoDB['etrade_fundamentals'].find(mongo_query11).sort("date", 1))
        mongo_col_q = self.mongoDB.get_collection(self.company['Yahoo_Symbol'])
        self.q = list(mongo_col_q.find(mongo_query2).sort("Date", -1))
        if len(self.q) > 0:
            self.AAOD = self.q[0]['Date']
            #print(query_date, mongo_query2, self.AAOD, self.q[0])

        self.f = StockFundamentalsExplorer()
        self.f.get_fund(self.symbol, self.AAOD)
        #print(self.AAOD)

    def get_sr(self, length):
        start = self.q[0]['Close']
        startDate = self.q[0]['Date']
        endDate = None
        sr_length = 0
        newDate = datetime(*(int(s) for s in startDate.split('-'))) + timedelta(days=-365 * length)
        # print(length, startDate, newDate)
        targetEndDate = newDate.strftime('%Y-%m-%d')
        # print(startDate, targetEndDate)

        for i in range(len(self.q)):
            if self.q[i]['Date'] <= targetEndDate:
                end = self.q[i]['Close']
                endDate = self.q[i]['Date']
                sr_length = i + 1
                break

        if endDate is None:
            end = self.q[-1]['Close']
            endDate = self.q[-1]['Date']
            sr_length = len(self.q)

        # print(sr_length, self.q[0:sr_length])
        sr_df = pd.DataFrame(self.q[0:sr_length])
        # print(sr_df['Close'])
        # r1 = sr_df['Close'].diff()
        # print(r1)
        # r2 = (sr_df['Close'].shift(1)-sr_df['Close'])/sr_df['Close'].shift(1)
        # print(r2)
        r = (sr_df['Close'].shift(1) - sr_df['Close']) / sr_df['Close']
        # print(r)
        sr = np.sqrt(252) * r.mean() / r.std()

        result = {
            "StartDate": startDate,
            "StartClose": start,
            "EndDate": endDate,
            "EndClose": end,
            "Length": sr_length,
            "SR": sr
        }
        # print(result)
        return result

    def get_rev_eps_score(self, df, score_type):
        max_year = 5
        if score_type == 'rev':
            col1 = 'rev'
            col2 = 'quarter'
        elif score_type == 'eps':
            col1 = 'eps'
            col2 = 'quarter'

        current_rate = 0
        ave_rate = 0
        score = 0

        sum_rate = 0
        sum_num = 0
        for i, r in df.iterrows():
            if i < df.shape[0]:
                current_rev = float(r[col1])
                current_quarter = r[col2]
                current_year = current_quarter[0:4]
                current_q = current_quarter[-2:]

                # print(current_quarter, rate)
                if i == 0:
                    start_year = current_year

                base_year = str(int(current_year) - 1)
                # limit to 5 years
                # print(current_year, base_year)
                if int(base_year) < int(start_year) - max_year:
                    break
                base_quarter = base_year + current_q

                base_rev = 0
                base_df = df[df[col2] == base_quarter]
                if not base_df.empty:
                    base_rev = float(base_df.iloc[0][col1])
                if base_rev != 0:
                    rate = (current_rev - base_rev) / abs(base_rev)
                else:
                    rate = 0
                if rate != 0:
                    sum_rate = sum_rate + rate
                    sum_num = sum_num + 1
                if i == 0:
                    current_rate = rate

            if i == 0:
                current_rate = rate
        if sum_num > 0:
            ave_rate = sum_rate / sum_num

        if ave_rate != 0:
            score = current_rate + abs(current_rate) * (current_rate - ave_rate) / abs(ave_rate)
        else:
            score = current_rate

        return {
            'current_rate': current_rate,
            'ave_rate': ave_rate,
            'score': score
        }

    def get_history_high(self):
        hh= 0
        for p in self.q:
            if hh < p['Close']:
                hh = p['Close']
        return hh

    def checkRec_fundamentals(self):
        rec = ''
        reason = ''
        #nonUSAList = ['TS', 'CLB', 'ITUB', 'PBR', 'RHHBY', 'JAGGF', 'CEO', 'BBL', 'MDT', 'ENB', \
        #              'LUKOY', 'SU', 'CNQ', 'BB', 'MFC', 'ZURVY', 'LFC', 'EEM', 'GG', 'SGTZY', \
        #              'GLD', 'TS', 'ACN', 'PTR', 'SSL', 'HDB', 'CNI', 'MBT', 'WFT', 'SNP', 'AABA', \
        #              'RCI', 'YARIY', 'SYMC', 'AUY', 'PHI', 'BVN', 'EGO', 'SNN', 'SJR', 'FRFHF', 'LLL', \
        #              'CHA', 'BCH', 'CHKP', 'QGEN', 'SQM', 'SBS', 'ACH', 'CEL', 'PAAS', 'RE', 'OTEX', 'ESLT', \
        #              'CLB', 'NAK', 'LOGI', 'STE', 'ILF', 'RNR', 'RBYCF', 'CPA', 'CMPR', 'SA', 'STN', 'ESGR', \
        #              'ATU', 'CPL', 'GSIH', 'MFCB', 'NICE', 'PUODY', 'SEDG', 'LULU', 'HOKCY', 'APTV', 'BGNE',
        #              'XMEX', 'GSX', 'GRWG', 'MNST', 'GDS', 'SE', 'MELI', 'DQ', 'SWET', 'INFO', 'TT', 'GBTC',
        #              'HZNP', 'OCFT', 'GOOG', 'YY', 'BCEI', 'NPSNY', 'BRDCY', 'CPRI', 'BOTY', 'NXPI', 'XFLS',
        #              'BBD', 'GPH', 'PAGS', 'PHIL', 'GFKSY', 'CNNA', 'DLOC', 'SEII', 'WWR', 'MT', 'DB', 'OIBRQ',
        #              'BIEI', 'RMSL', 'KMI', 'NAKD', 'NSPX', 'BHP', 'TNXP']

        nonUSAList = ['GOOG', 'JMDA', 'QRHC', 'CCGN', 'BRVO', 'PIC', 'ELLI', 'HMTA', 'EIC', 'PUODY', 'PEER',
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
                     'BIEI', 'RMSL', 'KMI', 'NAKD', 'NSPX', 'BHP', 'TNXP', 'MLYBY', 'SIM','AMOV', 'GRDZF']

        # 4. Industry = Tobacco
        if self.company['industry'] == "Food & Tobacco":
            rec = "n"
            reason = "Tobacco"
        # 5. Non USA
        elif self.symbol in nonUSAList:
            rec = "n"
            reason = "None USA"
        # 14. price > 1
        #elif self.q[0]['Close'] < 1:
        #    rec = "n"
        #    reason = "Close < 1"
        #15. Price / History Highest < 0.1
        elif self.q[0]['Close'] / self.get_history_high() < 0.1:
            rec = "n"
            reason = "Clsoe/Highest < 0.1"
        # 11. CAP < 1
        #elif self.result['CAP'] < 10:
        #elif self.result['CAP'] < 1:     #5:
        elif self.result['CAP'] < 0.2:     #5:
        #elif self.result['CAP'] < 10 and self.result['CAP'] >= 0:
        #elif self.result['CAP'] < 1 and self.result['CAP'] > 0:
            #rec = "n"
            reason = "CAP < 0.2 B"
        # 12. G20 < 10

        return {
            "Recommendation": rec,
            "Reason": reason
        }

    def checkRec(self, g20_threshold=10):
        rec = ''
        reason = ''
        # 3. G1 < 0
        if self.result['G1'] < 0:
            rec = "n"
            reason = "G1 < 0"
        # 12. G20 < 20
        #elif self.result['G20'] < 20:
        elif self.result['G20'] < g20_threshold:
            rec = "n"
            reason = "G20 < " + str(g20_threshold)
        # 7. Healthcare & G20Year < 5
        elif (self.company['industry'] == "Pharmaceuticals" or self.company[
            'industry'] == "Healthcare Equipment & Supplies" or self.company[
                  'industry'] == "Healthcare Providers & Services" \
              or self.company['industry'] == "Biotechnology & Medical Research") and self.result['G20Year'] < 5:
            rec = "n"
            reason = "Healthcare & G20Year < 5"
        # 2. G20Close <= 1
        elif self.result['G20Close'] != 'null' and self.result['G20Close'] <= 1:
            # rec = "n"
            reason = "G20Close <= 1"
        # 6. G20 / G1 > 2
        elif self.result['G20'] / self.result['G1'] > 2:
            # rec = "n"
            reason = "G20/G1 > 2"
        # 1. G20Year < 3
        #if self.result['G20Year'] < 3:
        elif self.result['G20Year'] < 1:
            #rec = "n"
            reason = "G20Year < 1"
        # 8. G20 / G1 < 0.25
        elif self.result['G20'] / self.result['G1'] < 0.25:
            # rec = "n"
            reason = "G20/G1 < 0.25"
        # 9. Stop
        # 10. if at least 1 of the following 4 > .2
        #       QuarterRevScore
        #       YearlyRevScore
        #       QuarterlyEPSScore
        #       YearlyEPSScore
        elif "QuarterlyRevScore" in self.result and self.result['QuarterlyRevScore'] != '' \
                and "YearlyRevScore" in self.result and self.result['YearlyRevScore'] != '' \
                and "QuarterlyEPSScore" in self.result and self.result['QuarterlyEPSScore'] != '' \
                and "YearlyEPSScore" in self.result and self.result['YearlyEPSScore'] != '':
            rev_eps_count = 0
            if self.result['QuarterlyRevScore'] > 0.2:
                rev_eps_count += 1
            if self.result['YearlyRevScore'] > 0.2:
                rev_eps_count += 1
            if self.result['QuarterlyEPSScore'] > 0.2:
                rev_eps_count += 1
            if self.result['YearlyEPSScore'] > 0.2:
                rev_eps_count += 1

            if rev_eps_count < 1:
                # rec = "n"
                reason = "Rev_EPS_Score < 0.2"

        return {
            "Recommendation": rec,
            "Reason": reason
        }

    def checkRL(self):
        '''
        13. RL Checks:
            1. model_score < 1.1
            2. predict_date > 5
            3. len < 5
            4. predict_vol = 0
            5. predict_action < 1 -- buy
            6. predict_action >= 1 -- sell
            7. predict_action >= 2 -- hold
            8. buy_and_hold_perf < 1
        '''
        rec = ''
        reason = ''
        # 8. buy_and_hold_perf < 1.0
        if self.result['rl_result']['buy_and_hold_perf'] < 1:
            rec = "n"
            reason = "buy_and_hold_perf < 1"
        # 1. model_score < 1.1
        elif self.result['rl_result']['model_score'] < 1.05 or np.isnan(self.result['rl_result']['model_score']) is True:
            rec = "n"
            reason = "model_score < 1.05"
        else:
            predict_date = (datetime(*(int(s) for s in self.AAOD.split('-'))) - datetime(*(int(s) for s in self.result['rl_result']['predict_date'].split('-')))).days
            # 3. len < 5
            #if self.result['rl_result']['predict_macd_len'] < 5:
                #rec = "n"
                #reason = "len < 5"
            # 2. predict_date > 5
            #elif predict_date > 7:
            if predict_date > 7:
                #rec = "n"
                reason = "predict_date > 5"
            # 4. predict_vol = 0
            #elif self.result['rl_result']['predict_vol'] == 0:
                # rec = "n"
            #    reason = "predict_vol = 0"
            # 5. predict_action < 1 -- buy
            elif self.result['rl_result']['predict_action'] < 1:
                # rec = ""
                reason = "predict_action < 1"
            # 6. predict_action >= 1 -- sell
            elif self.result['rl_result']['predict_action'] >= 1 and self.result['rl_result']['predict_action'] < 2:
                # rec = ""
                reason = "predict_action >= 1"
            # 7. predict_action > 2 -- hold
            elif self.result['rl_result']['predict_action'] > 2:
                # rec = ""
                reason = "predict_action >= 2"

        return {
            "Recommendation": rec,
            "Reason": reason
        }

    def ranking(self):
        ind = self.company['industry']
        indRank = self.mongoDB['industry_ranking'].find_one({'Industry': ind})

        sharesNum = self.f.get_shares()
        # shares = self.fundamentals[0]['shares']
        # if shares != '--':
        #    sharesNum = float(shares[:-1].replace(' ', ''))
        #    shareBase = shares[:-1]
        # else:
        #    sharesNum = 0
        #    shareBase = "B"

        # if shareBase == "B":
        #    sharesNum = sharesNum * 1000
        # elif shareBase == "K":
        #    sharesNum = sharesNum / 1000

        cap = self.q[0]['Close'] * sharesNum / 1000
        # Cap Industry Rating
        #   <= 10      0
        # 10 - 20      .25
        # 20 - 100      .5
        #  >= 100      1
        if indRank is not None:
            if cap <= 10:
                result = 0
            elif cap > 10 and cap <= 20:
                result = 0.25 * indRank['Rank']
            elif cap > 20 and cap <= 100:
                result = 0.5 * indRank['Rank']
            else:
                result = indRank['Rank']
        else:
            result = 1

        return result

    def growthRate(self, length):
        start = self.q[0]['Close']
        startDate = self.q[0]['Date']
        end = 0
        endDate = None
        newDate = datetime(*(int(s) for s in startDate.split('-'))) + timedelta(days=-365 * length)
        targetEndDate = newDate.strftime('%Y-%m-%d')

        for i in range(len(self.q)):
            if self.q[i]['Date'] <= targetEndDate:
                end = self.q[i]['Close']
                endDate = self.q[i]['Date']
                sr_length = i + 1
                break

        if endDate is None:
            end = self.q[-1]['Close']
            endDate = self.q[-1]['Date']
            sr_length = len(self.q)

        # print(startDate, endDate)
        # G20 Year = Days(G20 Date - AAOD) / 365
        # G20 Price = close @20
        # Total G20 = (today close / G20 Price) - 1
        # G20 = POWER(10, LOG10(1+Total G20) / G20 Year) - 1
        # G20 Weight = 100
        gYear = (datetime(*(int(s) for s in startDate.split('-'))) - datetime(
            *(int(s) for s in endDate.split('-')))).days / 365
        weight = 100
        if start != 'null' and end != 'null':
            totalG = start / end - 1
        else:
            totalG = 0
        g = weight * (10 ** (np.log10(1 + totalG) / gYear) - 1)

        # print(sr_length, self.q[0:sr_length])
        sr_df = pd.DataFrame(self.q[0:sr_length])
        # print(sr_df['Close'])
        # r1 = sr_df['Close'].diff()
        # print(r1)
        # r2 = (sr_df['Close'].shift(1)-sr_df['Close'])/sr_df['Close'].shift(1)
        # print(r2)
        r = (sr_df['Close'].shift(1) - sr_df['Close']) / sr_df['Close']
        # print(r)
        sr = np.sqrt(252) * r.mean() / r.std()

        result = {
            "StartDate": startDate,
            "StartClose": start,
            "EndDate": endDate,
            "EndClose": end,
            "TotalYears": gYear,
            "GWeight": weight,
            "TotalG": totalG,
            "G": g,
            "Length": sr_length,
            "SR": sr
        }
        # print(result)
        return result

    def targetGrowthRate(self, lookforward):
        end = self.q[0]['Close']
        endDate = self.q[0]['Date']
        newDate = datetime(*(int(s) for s in endDate.split('-'))) + timedelta(days=365 * lookforward)
        targetDate = newDate.strftime('%Y-%m-%d')
        # print(endDate, targetDate)
        mongo_query = {"$and": [{"Date": {"$lte": targetDate}}, {"Date": {"$gte": endDate}}]}
        mongo_col_q = self.mongoDB.get_collection(self.company['Yahoo_Symbol'])
        q = list(mongo_col_q.find(mongo_query).sort("Date", -1))

        if len(q) > 0:
            start = q[0]['Close']
            startDate = q[0]['Date']
            end = q[-1]['Close']
            endDate = q[-1]['Date']

            # print(startDate, endDate)
            tYear = (datetime(*(int(s) for s in startDate.split('-'))) - datetime(
                *(int(s) for s in endDate.split('-')))).days / 365
            weight = 100
            totalT = start / end - 1
            if tYear != 0:
                t = weight * (10 ** (np.log10(1 + totalT) / tYear) - 1)
            else:
                t = 0

            # print(sr_length, self.q[0:sr_length])
            sr_df = pd.DataFrame(q)
            r = (sr_df['Close'].shift(1) - sr_df['Close']) / sr_df['Close']
            # print(r)
            sr = np.sqrt(252) * r.mean() / r.std()
        else:
            start = None
            startDate = None
            tYear = 0
            totalT = 0
            t = 0
            sr = 0

        result = {
            "StartDate": endDate,
            "StartClose": end,
            "EndDate": startDate,
            "EndClose": start,
            "TotalYears": tYear,
            "GWeight": weight,
            "TotalT": totalT,
            "T": t,
            "Length": len(q),
            "SR": sr
        }
        # print(result)
        return result

    # def averagePE(self, AAOD):
    def averagePE(self):
        # endDate = datetime(*(int(s) for s in AAOD.split('-')))
        # startDate = endDate + timedelta(days = -365)

        # compute the Industry Average PE
        ind = self.mongoDB['etrade_companies'].find().distinct("industry")
        for i in ind:
            # finalAAOD = AAOD
            finalAAOD = self.AAOD
            comCount = 0
            totalPE = 0
            avePE = 0
            # pe = 0

            com = list(self.mongoDB['etrade_companies'].find({"industry": i, "status": "active"}))
            for j in com:
                # get eps
                f = StockFundamentalsExplorer()
                f.get_fund(j['Yahoo_Symbol'], self.AAOD)
                eps = f.get_eps()
                # eps = self.mongoDB['etrade_fundamentals'].find_one({"$and": [{"symbol": j['Symbol']},\
                #        {"date": {"$lte": endDate}}, {"date": {"$gte": startDate}}]}, sort=[("date", -1)])
                # get close
                mongo_col_close = self.mongoDB.get_collection(j['Yahoo_Symbol'])
                # close = mongo_col_close.find_one({"Date": {"$lte": AAOD}}, sort=[("Date", -1)])
                close = mongo_col_close.find_one({"Date": {"$lte": self.AAOD}}, sort=[("Date", -1)])
                # compute pe
                # if eps is not None and not re.match('[a-zA-Z]', eps['EPS']) and eps['EPS'] != '' and float(eps['EPS'].replace(',', '')) > 0 and close is not None and close['Close'] != 'null':
                if eps > 0 and close is not None and close['Close'] != 'null':
                    # print(close['Close'], eps['EPS'])
                    # pe = close['Close'] / float(eps['EPS'].replace(',', ''))
                    # print(j['Symbol'], close['Close'], eps, self.f.fund['source'])
                    pe = close['Close'] / eps
                    if finalAAOD == self.AAOD and finalAAOD > close['Date']:
                        finalAAOD = close['Date']
                    if finalAAOD != self.AAOD and finalAAOD < close['Date']:
                        finalAAOD = close['Date']
                else:
                    pe = 0
                # add to total, increment count
                if pe > 0:
                    totalPE = totalPE + pe
                    comCount += 1
            if comCount > 0:
                avePE = totalPE / comCount
                result = {
                    "Date": finalAAOD,
                    "Industry": i,
                    "AveragePE": avePE,
                    "Count": comCount
                }
                print(json.dumps(result, indent=4))
                #self.mongoDB['average_pe'].insert_one(result)
                self.mongoDB['average_pe'].replace_one({'Date': finalAAOD, 'Industry': i}, result, upsert=True)

    def PEScore(self):
        peWeight = 1
        # eps = self.fundamentals[0]['EPS']
        # if eps != '' and float(eps.replace(',', '')) > 0:
        #    pe = self.q[0]['Close'] / float(eps.replace(',', ''))
        eps = self.f.get_eps()
        if eps > 0:
            pe = self.q[0]['Close'] / eps
        else:
            pe = 0

        # get the industry
        ind = self.company['industry']
        # get the Industry Average PE
        avePE = self.mongoDB['average_pe'].find_one({"Industry": ind, "Date": {"$lte": self.AAOD}}, sort=[("Date", -1)])
        if pe == 0:
            peScore = -1
        else:
            if avePE is not None and avePE['AveragePE'] > 0:
                peScore = peWeight * (avePE['AveragePE'] - pe) / avePE['AveragePE']
            else:
                peScore = 0

        if avePE is not None:
            result = {
                "PE": pe,
                "AveragePE": avePE['AveragePE'],
                "PEWeight": peWeight,
                "PEScore": peScore
            }
        else:
            result = {
                "PE": pe,
                "AveragePE": "",
                "PEWeight": peWeight,
                "PEScore": peScore
            }
        return result

    def capScore(self):
        # shares = self.fundamentals[0]['shares']
        # sharesNum = float(shares[:-1].replace(' ', ''))
        # shareBase = shares[-1:]
        # if shareBase == "B":
        #    sharesNum = sharesNum * 1000
        # elif shareBase == "K":
        #    sharesNum = sharesNum / 1000
        sharesNum = self.f.get_shares()
        score = 0
        cap = self.q[0]['Close'] * sharesNum / 1000
        if cap > 10:
            score = -0.001 * cap
        else:
            score = (cap - 10) / (cap * 10)
        result = {
            'CAP': cap,
            'capScore': score
        }
        return result

    #def run(self, save_rl=False, always_run_rl=False, retrain_rl=True):
    #def run(self, save_rl=False, run_rl=0, retrain_rl=True, g20_threshold=10):
    def run(self, save_rl=False, run_rl=0, retrain_rl=False, g20_threshold=10):
    # run_rl - 0 - no run as default; 1 - run per condition; 2 - always run
        if hasattr(self, 'result') is False or 'CAP' not in self.result:
            self.run_fundamentals()

        if self.result['Recommendation'] == '' and self.q is not None and len(self.q) > 0 and self.q[0] is not None:
            # compute g20
            g20 = self.growthRate(20)

            # compute g10
            g10 = self.growthRate(10)

            # compute g5
            g5 = self.growthRate(5)

            # compute g1
            g1 = self.growthRate(1)

            # compute final score
            s = self.result['CapScore'] + self.result['PEScore'] + g20['G'] + self.result['IndustryRank']

            # compute target
            t1 = self.targetGrowthRate(1)

            # compute sr20
            # sr20 = self.get_sr(20)

            # compute sr10
            # sr10 = self.get_sr(10)

            # compute sr5
            # sr5 = self.get_sr(5)

            # compute sr1
            # sr1 = self.get_sr(1)

            self.result["close"] = self.q[0]['Close']
            self.result["G20Date"] = g20['EndDate']
            self.result["G20Close"] = g20['EndClose']
            self.result["G20Year"] = g20['TotalYears']
            self.result["G20Total"] = g20['TotalG']
            self.result["G20"] = g20['G']
            self.result["SR20_Length"] = g20['Length']
            self.result["SR20"] = g20['SR']
            self.result["G10Date"] = g10['EndDate']
            self.result["G10Close"] = g10['EndClose']
            self.result["G10Year"] = g10['TotalYears']
            self.result["G10Total"] = g10['TotalG']
            self.result["G10"] = g10['G']
            self.result["SR10_Length"] = g10['Length']
            self.result["SR10"] = g10['SR']
            self.result["G5Date"] = g5['EndDate']
            self.result["G5Close"] = g5['EndClose']
            self.result["G5Year"] = g5['TotalYears']
            self.result["G5Total"] = g5['TotalG']
            self.result["G5"] = g5['G']
            self.result["SR5_Length"] = g5['Length']
            self.result["SR5"] = g5['SR']
            self.result["G1Date"] = g1['EndDate']
            self.result["G1Close"] = g1['EndClose']
            self.result["G1Year"] = g1['TotalYears']
            self.result["G1Total"] = g1['TotalG']
            self.result["G1"] = g1['G']
            self.result["SR1_Length"] = g1['Length']
            self.result["SR1"] = g1['SR']
            self.result["Score"] = s
            self.result["T1Date"] = t1['EndDate']
            self.result["T1Close"] = t1['EndClose']
            self.result["T1Year"] = t1['TotalYears']
            self.result["T1Total"] = t1['TotalT']
            self.result["T1"] = t1['T']
            self.result["TSR1_Length"] = t1['Length']
            self.result["TSR1"] = t1['SR']

            '''
            # compute rev and eps scores
            type1 = 'Quarter'
            type2 = 'Year'
            mongo_col1 = self.mongoDB['sec_rev']
            mongo_col2 = self.mongoDB['sec_eps']

            mongo_query1 = {"symbol": self.symbol, "type": type1}
            quotes1 = mongo_col1.find(mongo_query1).sort("quarter", -1)
            if mongo_col1.count_documents(mongo_query1) > 0:
                df1 = pd.DataFrame(list(quotes1))
                # df1['rev'] = df1['rev'].astype(float)
                rev_score1 = self.get_rev_eps_score(df1, 'rev')
                # print(self.symbol, 'Revenue Quarterly', rev_score1)
                self.result["QuarterlyRevScore_CurrentRate"] = rev_score1['current_rate']
                self.result["QuarterlyRevScore_AveRate"] = rev_score1['ave_rate']
                self.result["QuarterlyRevScore"] = rev_score1['score']

            mongo_query2 = {"symbol": self.symbol, "type": type2}
            quotes2 = mongo_col1.find(mongo_query2).sort("quarter", -1)
            if mongo_col1.count_documents(mongo_query2) > 0:
                df2 = pd.DataFrame(list(quotes2))
                # df2['rev'] = df2['rev'].astype(float)
                rev_score2 = self.get_rev_eps_score(df2, 'rev')
                # print(self.symbol, 'Revenue Yearly', rev_score2)
                self.result["YearlyRevScore_CurrentRate"] = rev_score2['current_rate']
                self.result["YearlyRevScore_AveRate"] = rev_score2['ave_rate']
                self.result["YearlyRevScore"] = rev_score2['score']

            mongo_query3 = {"symbol": self.symbol, "type": type1}
            quotes3 = mongo_col2.find(mongo_query3).sort("quarter", -1)
            if mongo_col2.count_documents(mongo_query3) > 0:
                df3 = pd.DataFrame(list(quotes3))
                # df3['eps'] = df3['eps'].astype(float)
                eps_score3 = self.get_rev_eps_score(df3, 'eps')
                # print(self.symbol, 'EPS Quarterly', eps_score3)
                self.result["QuarterlyEPSScore_CurrentRate"] = eps_score3['current_rate']
                self.result["QuarterlyEPScore_AveRate"] = eps_score3['ave_rate']
                self.result["QuarterlyEPSScore"] = eps_score3['score']

            mongo_query4 = {"symbol": self.symbol, "type": type2}
            quotes4 = mongo_col2.find(mongo_query4).sort("quarter", -1)
            if mongo_col2.count_documents(mongo_query4) > 0:
                df4 = pd.DataFrame(list(quotes4))
                # df4['eps'] = df4['eps'].astype(float)
                eps_score4 = self.get_rev_eps_score(df4, 'eps')
                # print(self.symbol, 'EPS Yearly', eps_score4)
                self.result["YearlyEPSScore_CurrentRate"] = eps_score4['current_rate']
                self.result["YearlyEPSScore_AveRate"] = eps_score4['ave_rate']
                self.result["YearlyEPSScore"] = eps_score4['score']
            '''

            cc = self.checkRec(g20_threshold)
            self.result['Recommendation'] = cc['Recommendation']
            self.result['Reason'] = cc['Reason']

        #if self.result['Recommendation'] == '' or always_run_rl is True:
        if run_rl == 2 or (run_rl == 1 and self.result['Recommendation'] == ''):
            # get rl params (short, long, signal, macd_threshold, macd_min_len)
            # default
            short = 3
            long = 7
            signal = 19
            macd_threshold = 0
            macd_min_len = 0

            mongo_rl_param = self.mongoDB['test_rl_macd_param']
            mongo_query_param = {"symbol": self.symbol}
            quote_param = mongo_rl_param.find(mongo_query_param)
            if mongo_rl_param.count_documents(mongo_query_param) > 0:
                short = quote_param[0]['short']
                long = quote_param[0]['long']
                signal = quote_param[0]['signal']
                macd_threshold = quote_param[0]['macd_threshold']
                macd_min_len = quote_param[0]['macd_min_len']

            ss = StockStats(self.symbol, self.AAOD)
            self.result['MACD'] = ss.macd_by_date(self.AAOD, short, long, signal)
            # print(ss.stock)

            # get StockRL
            # file_path = './rl/test_rl_' + self.symbol + '.zip'
            file_path = self.rl_save_loc + self.symbol + '.zip'
            if retrain_rl is True:
                rl = StockRL(self.symbol, 0, short, long, signal, aaod=self.AAOD, save_loc=self.rl_save_loc, macd_threshold=macd_threshold, macd_min_len=macd_min_len)
                rl.retrain(save=save_rl) if os.path.exists(file_path) else rl.train(save=save_rl)
            else:
                if os.path.exists(file_path) is False:
                    aaod_today = datetime.now().strftime("%Y-%m-%d")
                    rl = StockRL(self.symbol, 0, short, long, signal, aaod=aaod_today, save_loc=self.rl_save_loc, macd_threshold=macd_threshold, macd_min_len=macd_min_len)
                    rl.train(save=save_rl)
                else:
                    rl = StockRL(self.symbol, 0, short, long, signal, aaod=self.AAOD, save_loc=self.rl_save_loc, macd_threshold=macd_threshold, macd_min_len=macd_min_len)
                    rl.reload()
            self.result['rl_result'] = rl.run()
            cc = self.checkRL()
            if self.result['Recommendation'] == '':
                self.result['Recommendation'] = cc['Recommendation']
            if self.result['Reason'] == '':
                self.result['Reason'] = cc['Reason']
            else:
                self.result['Reason'] = self.result['Reason'] + ',' + cc['Reason']

        # print(self.result)
        return self.result

    def save_g20(self):
        # self.mongoDB['stock_g_score'].insert_one(self.result)
        self.mongoDB['stock_g_score'].replace_one({'symbol': self.symbol, 'AAOD': self.AAOD}, self.result, upsert=True)

    def run_fundamentals(self):
        # if self.fundamentals is not None and len(self.fundamentals) > 0 and self.fundamentals[0] is not None:
        if self.f.fund is not None:
            # compute cap score
            cap = self.capScore()

            # compute PE score
            peScore = self.PEScore()
            # eps = self.fundamentals[0]['EPS']
            eps = self.f.get_eps()
            # compute industry ranking
            rank = self.ranking()

            rev_growth, gross_margin = self.f.get_rocket_data()
        else:
            # compute cap score
            cap = {
                'CAP': 0,
                'capScore': 0
            }

            # compute PE score
            peScore = {
                "PE": '',
                "AveragePE": '',
                "PEWeight": 1,
                "PEScore": 0
            }
            eps = 0

            # compute industry ranking
            rank = 0

            rev_growth, gross_margin = (0, 0)

        self.result = {
            "symbol": self.symbol,
            "runDate": self.runDate,
            "AAOD": self.AAOD,
            "rule": "G20",
            'CAP': cap['CAP'],
            "CapScore": cap['capScore'],
            "IndustryRank": rank,
            "EPS": eps,
            "PE": peScore['PE'],
            "AveragePE": peScore['AveragePE'],
            "PEWeight": peScore['PEWeight'],
            "PEScore": peScore['PEScore'],
            "Rev Growth": rev_growth,
            "Gross Margin": gross_margin
            # "comment": "G20 Score"
        }

        cc = self.checkRec_fundamentals()
        self.result['Recommendation'] = cc['Recommendation']
        self.result['Reason'] = cc['Reason']
        if cc['Recommendation'] == '':
            return True
        else:
            return False

if __name__ == '__main__':
    '''
    aaod = datetime.now().strftime("%Y-%m-%d")
    g20 = StockScore({'AAOD': aaod, 'symbol': 'AAPL'})
    g20.averagePE()
    '''
    '''
    startTime = datetime.now()
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "CMIMD"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "LFC"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "GOOGL"})
    #g20 = StockScore({"AAOD": "2019-03-12", "symbol": "MSFT"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "CLB"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "ADRE"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "ATPT"})
    #g20 = StockScore({"AAOD": "2010-01-12", "symbol": "AIM"})
    #g20 = StockScore({"AAOD": "2009-12-01", "symbol": "AMZN"})
    #g20 = StockScore({"AAOD": "2019-03-29", "symbol": "AMZN"})
    #g20 = StockScore({"AAOD": "2019-12-01", "symbol": "HLAN"})
    #g20 = StockScore({"AAOD": "2019-10-28", "symbol": "CSWI"})
    #g20 = StockScore({"AAOD": "2019-07-14", "symbol": "AMZN"})
    #g20 = StockScore({"AAOD": "2021-03-24", "symbol": "CDLX"})
    #g20 = StockScore({"AAOD": "2021-03-24", "symbol": "SHOP"})
    #g20 = StockScore({"AAOD": "2021-03-24", "symbol": "BAND"})
    #g20 = StockScore({"AAOD": "2021-03-24", "symbol": "ACMR"})
    #g20 = StockScore({"AAOD": "2021-03-24", "symbol": "APPN"})
    g20 = StockScore({"AAOD": "2021-03-24", "symbol": "META"})

    #g20.averagePE("2019-09-01")
    #g20.averagePE("2020-05-22")
    #g20.averagePE()

    #print(json.dumps(g20.PEScore(), indent=4))
    #print(g20.capScore())

    #print(g20.get_sr(1))
    #print(g20.get_sr(5))
    #print(g20.get_sr(10))
    #print(g20.get_sr(20))

    g20.run()
    endTime = datetime.now()
    runTime = endTime - startTime

    print(json.dumps(g20.result, indent=4))
    print('run time: ', runTime)
    '''

    mongo = MongoExplorer()
    mongoDB = mongo.mongoDB
    # mongo_client = pymongo.MongoClient('mongodb://192.168.1.6:27017/')
    # mongoDB = mongo_client['riverhill']
    mongo_col = mongoDB['etrade_companies']
    # mongo_query = {"Yahoo_Symbol": 'BRK-A'}
    # mongo_query = {"Yahoo_Symbol": 'APG'}
    # mongo_query = {"Yahoo_Symbol": 'FOE'}
    # mongo_query = {"Yahoo_Symbol": 'AMD'}
    #mongo_query = {"Yahoo_Symbol": 'TSLA'}
    # mongo_query = {"Yahoo_Symbol": 'BILL'}
    #mongo_query = {"Yahoo_Symbol": 'SHOP'}
    #mongo_query = {"Yahoo_Symbol": 'AYX'}
    #mongo_query = {"Yahoo_Symbol": 'BOLL'}
    #mongo_query = {"Yahoo_Symbol": 'AAPL'}
    #mongo_query = {"Yahoo_Symbol": 'AMD'}
    #mongo_query = {"Yahoo_Symbol": 'VRUS'}
    #mongo_query = {"Yahoo_Symbol": 'ICE'}
    #mongo_query = {"Yahoo_Symbol": 'GOOG'}
    #mongo_query = {"Yahoo_Symbol": 'VISL'}
    #mongo_query = {"Yahoo_Symbol": 'GOOGL'}
    #mongo_query = {"Yahoo_Symbol": 'SHOP'}
    #mongo_query = {"Yahoo_Symbol": 'NTES'}
    #3mongo_query = {"Yahoo_Symbol": 'LI'}
    #mongo_query = {"Yahoo_Symbol": 'BKNG'}
    #mongo_query = {"Yahoo_Symbol": 'TSLA'}
    #mongo_query = {"Yahoo_Symbol": 'META'}
    #mongo_query = {"Yahoo_Symbol": 'SPY'}
    #mongo_query = {"Yahoo_Symbol": 'ETNI'}
    mongo_query = {"Yahoo_Symbol": 'ALNY'}

    # mongo_query = {}
    com = mongo_col.find(mongo_query, no_cursor_timeout=True)
    # com = mongo_col.find(no_cursor_timeout=True)

    # aaod = "2009-12-09"
    # aaod = "2020-08-14"
    # aaod = "2020-08-17"
    # aaod = "2020-11-27"
    # aaod = "2021-03-26"
    #aaod = "2013-11-17"
    #aaod = "2014-09-11"
    #aaod = '2010-11-23'
    aaod = datetime.now().strftime("%Y-%m-%d")

    index = 1
    restartIndex = 1  # 3752
    stopIndex = 1000000  # 3753
    for i in com:
        print(str(index) + "	" + i['Yahoo_Symbol'])
        if index > stopIndex:
            break
        if index >= restartIndex:
            try:
                q = QuoteExplorer()
                q.get_quotes(i['Yahoo_Symbol'], aaod)

                g20 = StockScore({'AAOD': aaod, 'symbol': i['Yahoo_Symbol']})
                if g20.run_fundamentals() == True:
                    g20.run(run_rl=2, retrain_rl=True)
                    # g20.save_g20()
                print(json.dumps(g20.result, indent=4))
            except Exception as error:
                # print(error)
                print(traceback.format_exc())
        index += 1

    '''
    aaod = "2021-03-26"
    mongo = MongoExplorer()
    mongo_col = mongo.mongoDB['stock_g_score']
    mongo_query = {"runDate": aaod, "Recommendation": ""}
    g = mongo_col.find(mongo_query, no_cursor_timeout=True)
    df = pd.DataFrame(list(g))

    macd = json_normalize(df['MACD'])
    df = df.join(macd)

    rl_result = json_normalize(df['rl_result'])
    df = df.join(rl_result)

    excel_file_name = 'stock_g_score_' + aaod.replace('-', '') + '.xlsx'
    w = pd.ExcelWriter(excel_file_name, engine='xlsxwriter')
    df.to_excel(w, sheet_name='Sheet1',
                columns=[
                    'symbol',
                    'Reason',
                    'Recommendation',
                    'AAOD',
                    'close',
                    'Score',
                    'CAP',
                    'CapScore',
                    'PEScore',
                    'AveragePE',
                    'PE',
                    'EPS',
                    'Rev Growth',
                    'Gross Margin',
                    'IndustryRank',
                    'G20',
                    'SR20',
                    'G20Close',
                    'G20Date',
                    'G20Total',
                    'G10',
                    'SR10',
                    'G10Close',
                    'G10Date',
                    'G10Total',
                    'G5',
                    'SR5',
                    'G5Close',
                    'G5Date',
                    'G5Total',
                    'G1',
                    'SR1',
                    'G1Close',
                    'G1Date',
                    'G1Total',
                    'runDate',
                    'macd_sign',
                    'peak',
                    'peak_date',
                    'accum',
                    'len',
                    'r',
                    'pre_macd_sign',
                    'pre_peak',
                    'pre_peak_date',
                    'pre_accum',
                    'pre_len',
                    'model_run_date',
                    'start_date',
                    'end_date',
                    'duration',
                    'model_gain',
                    'model_perf',
                    'buy_and_hold_gain',
                    'buy_and_hold_perf',
                    'model_score',
                    'predict_date',
                    'predict_macd_accum',
                    'predict_macd_len',
                    'predict_action',
                    'predict_vol'
                ])
    w.save()

    '''
