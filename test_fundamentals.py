"""
https://www.alphavantage.co/documentation/  key:  1IF9D4J1Z0B94FFD
"""
from datetime import datetime
from datetime import timedelta
#import pymongo
import simfin as sf
#from simfin.names import *
#from dateutil.relativedelta import relativedelta
import pandas as pd
import json
from test_mongo import MongoExplorer

class StockFundamentalsExplorer:
    def __init__(self):
        mongo_client = MongoExplorer()
        #mongo_client = pymongo.MongoClient('mongodb://192.168.1.6:27017/')
        #self.mongoDB = mongo_client['riverhill']
        self.mongoDB = mongo_client.mongoDB
        self.mongo_etrade = self.mongoDB['etrade_fundamentals']
        self.mongo_rocket = self.mongoDB['rocket_financials']
        self.mongo_sec_rev = self.mongoDB['sec_rev']
        self.mongo_sec_eps = self.mongoDB['sec_eps']

    def get_quarter(self):
        s = self.date.split('-')
        q = ''
        if s[1] == '03' or s[1] == '01' or s[1] == '02' or s[1] == '3' or s[1] == '1' or s[1] == '2' or s[1].upper() == 'MAR' or s[1].upper() == 'JAN' or s[1].upper() == 'FEB':
            q = 'Q1'
        elif s[1] == '06' or s[1] == '04' or s[1] == '05' or s[1] == '6' or s[1] == '4' or s[1] == '5' or s[1].upper() == 'APR' or s[1].upper() == 'MAY' or s[1].upper == 'JUN':
            q = 'Q2'
        elif s[1] == '09' or s[1] == '07' or s[1] == '08' or s[1] == '9' or s[1] == '7' or s[1] == '8' or s[1].upper() == 'SEP' or s[1].upper() == 'JAL' or s[1].upper == 'AUG':
            q = 'Q3'
        elif s[1] == '12' or s[1] == '10' or s[1] == '11' or s[1].upper() == 'DEC' or s[1].upper() == 'OCT' or s[1].upper == 'NOV':
            q = 'Q4'
        return s[0]+q

    def get_etrade(self):
        mongo_query1 = {"symbol": self.ticker, "date": {"$lte": self.date}}
        mongo_query2 = {"symbol": self.ticker, "date": {"$lte": datetime(*(int(s) for s in self.date.split('-')))}}
        mongo_query3 = {"symbol": self.ticker}
        fundamentals = list(self.mongo_etrade.find(mongo_query1).sort("date", -1))
        if len(fundamentals) == 0:
            fundamentals = list(self.mongo_etrade.find(mongo_query2).sort("date", -1))
        if len(fundamentals) == 0:
            fundamentals = list(self.mongo_etrade.find(mongo_query3).sort("date", 1))
        if len(fundamentals) > 0:
            return fundamentals[0]
        else:
            return None

    def get_rocket(self):
        one_quarter_ago = (datetime.now() + timedelta(days=-90))
        this_date = datetime(*(int(s) for s in self.date.split('-')))

        if this_date > one_quarter_ago:
            return 'Date > One Quarter Ago'

        #mongo_query1 = {"symbol": self.ticker, "date": {"$lte": self.date}, 'type': 'year'}
        mongo_query1 = {"symbol": self.ticker, "date": {"$lte": self.date}, 'type': 'TTM', 'Shares outstanding (diluted)': {'$exists': True, '$ne': ''}}
        fundamentals = list(self.mongo_rocket.find(mongo_query1).sort("date", -1))
        if len(fundamentals) > 0:
            rocket_date = fundamentals[0]['date']
            df = (this_date - datetime(*(int(s) for s in rocket_date.split('-')))).days
            if df > 90:
                return 'Date > One Quarter Ago'
            else:
                return fundamentals[0]
        else:
            return None

    def get_simfin(self):
        return None
    '''
        one_year_ago = (datetime.now() + timedelta(days=-365))
        this_date = datetime(*(int(s) for s in self.date.split('-')))
        #print(one_year_ago, this_date)

        if this_date > one_year_ago:
            return 'Date > One Year Ago'

        #sf.set_api_key('free')
        sf.set_api_key('xYrW6xuY7L4uDQSqVDKoHoXjYho6D2WV')
        #sf.set_data_dir('C:/Users/3203142/OneDrive/Stock/simfin_data')
        sf.set_data_dir('C:/Users/342/OneDrive/Stock/simfin_data')
        df_income = sf.load_income(variant='ttm', market='us')
        try:
            f = df_income.loc[self.ticker]
            return f.loc[f.index <= self.date].max()
        except:
            return None
    '''

    def get_sec(self):
        q = self.get_quarter()
        #print(q)

        mongo_query1 = {"symbol": self.ticker, "rev_quarter": {"$lte": q}, 'rev_type': 'Year'}
        rev_list = list(self.mongo_sec_rev.find(mongo_query1).sort("rev_quarter", -1))
        if len(rev_list) > 0:
            rev = rev_list[0]
        else:
            rev = {
                'rev_quarter': q,
                'rev': ''
            }

        mongo_query2 = {"symbol": self.ticker, "eps_quarter": {"$lte": q}, 'eps_type': 'Year'}
        eps_list = list(self.mongo_sec_eps.find(mongo_query2).sort("eps_quarter", -1))
        if len(eps_list) > 0:
            eps = eps_list[0]
        else:
            eps = {
                'eps_quarter': q,
                'eps': 0
            }

        return {
            'symbol':           self.ticker,
            'rev_quarter':      rev['rev_quarter'],
            'rev':              rev['rev'],
            'eps_quarter':      eps['eps_quarter'],
            'eps':              eps['eps']
        }

    def get_fund(self, ticker, date):
        self.ticker = ticker
        self.date = date

        #fund_sec = self.get_sec()
        #print(fund_sec)

        fund = self.get_rocket()
        source = 'rocket'
        if fund == None or fund == 'Date > One Quarter Ago':
            fund = self.get_simfin()
            source = 'simfin'
            if (isinstance(fund, pd.Series) == False and (fund == None or fund == 'Date > One Year Ago')) or (pd.isna(fund['Net Income'])):
                fund = self.get_etrade()
                source = 'etrade'
        #print(fund)
        if isinstance(fund, pd.Series) == True or (fund is not None and fund != 'Date > One Year Ago' and fund != 'Date > One Quarter Ago'):
            fund['source'] = source

        self.fund = fund
        #print(fund)
        return fund

    def get_eps(self):
        fund = self.fund
        eps = 0
        if fund is not None and 'source' in fund:
            if fund['source'] == 'etrade':
                try:
                    eps = float(fund['EPS'].replace(',', ''))
                except Exception as error:
                    #continue
                    return eps
            elif fund['source'] == 'rocket':
                eps = fund['Diluted EPS']
                if eps[0] == '(':
                    eps = float('-' + eps[1:len(eps) - 1])
                else:
                    eps = float(eps)
            elif fund['source'] == 'simfin':
                eps = fund['Net Income'] / fund['Shares (Diluted)']

        if pd.isna(eps):
            eps = 0
        return eps

    def get_rev(self):
        fund = self.fund
        rev = 0
        #if fund['source'] == 'etrade':
        #    rev = ''
        if fund is not None and 'source' in fund:
            if fund['source'] == 'rocket':
                #rocket = json.load(fund)
                if 'Total revenues' in fund:
                    rev = float(fund['Total revenues'].replace(',', '')) * 1000000
                elif 'Revenues' in fund:
                    rev = float(fund['Revenues'].replace(',', '')) * 1000000
            elif fund['source'] == 'simfin':
                rev = fund['Revenue']

        if pd.isna(rev):
            rev = 0
        return rev

    def get_shares(self):
        fund = self.fund
        shareNum = 0
        if fund is not None and 'source' in fund:
            if fund['source'] == 'etrade':
                shares = fund['shares']
                shareNum = float(shares[:-1].replace(' ', '').replace(',',''))
                shareBase = shares[-1:]
                if shareBase == "B":
                    shareNum = shareNum * 1000
                elif shareBase == "K":
                    shareNum = shareNum / 1000
                elif shareBase == "T":
                    shareNum = shareNum * 1000000
            elif fund['source'] == 'rocket':
                shareNum = float(fund['Shares outstanding (diluted)'].replace(',', ''))
            elif fund['source'] == 'simfin':
                shareNum = fund['Shares (Diluted)'] / 1000000
        return shareNum

    def averagePE(self, AAOD):
    #def averagePE(self):
        #endDate = datetime(*(int(s) for s in AAOD.split('-')))
        #startDate = endDate + timedelta(days = -365)

        #compute the Industry Average PE
        ind = self.mongoDB['etrade_companies'].find().distinct("industry")
        for i in ind:
            finalAAOD = AAOD
            #finalAAOD = self.AAOD
            comCount = 0
            totalPE = 0
            avePE = 0
            #pe = 0

            com = list(self.mongoDB['etrade_companies'].find({"industry": i}))
            for j in com:
                #get eps
                ##f = StockFundamentalsExplorer()
                self.get_fund(j['Yahoo_Symbol'], AAOD)
                eps = f.get_eps()
                #eps = self.mongoDB['etrade_fundamentals'].find_one({"$and": [{"symbol": j['Symbol']},\
                #        {"date": {"$lte": endDate}}, {"date": {"$gte": startDate}}]}, sort=[("date", -1)])
                #get close
                mongo_col_close = self.mongoDB.get_collection(j['Yahoo_Symbol'])
                #close = mongo_col_close.find_one({"Date": {"$lte": AAOD}}, sort=[("Date", -1)])
                close = mongo_col_close.find_one({"Date": {"$lte": AAOD}}, sort=[("Date", -1)])
                #compute pe
                #if eps is not None and not re.match('[a-zA-Z]', eps['EPS']) and eps['EPS'] != '' and float(eps['EPS'].replace(',', '')) > 0 and close is not None and close['Close'] != 'null':
                if eps > 0 and close is not None and close['Close'] != 'null':
                    #print(close['Close'], eps['EPS'])
                    #pe = close['Close'] / float(eps['EPS'].replace(',', ''))
                    #print(j['Symbol'], close['Close'], eps, self.f.fund['source'])
                    pe = close['Close'] / eps
                    if finalAAOD == AAOD and finalAAOD > close['Date']:
                        finalAAOD = close['Date']
                    if finalAAOD != AAOD and finalAAOD < close['Date']:
                        finalAAOD = close['Date']
                else:
                    pe = 0
                #print(j, eps, close)

                #add to total, increment count
                if pe > 0:
                    totalPE = totalPE + pe
                    comCount += 1
            if comCount > 0:
                avePE = totalPE / comCount
                result = {
                    "Date":             finalAAOD,
                    "Industry":         i,
                    "AveragePE":        avePE,
                    "Count":            comCount
                }
                print(json.dumps(result, indent=4))
                self.mongoDB['average_pe'].replace_one({'Date': finalAAOD, 'Industry': i}, result, upsert=True)
                #self.mongoDB['average_pe'].insert_one(result)

    def get_rocket_data(self):
        fund = self.fund
        rev_growth = 0
        gross_margin = 0
        if fund is not None and 'source' in fund:
            if fund['source'] == 'rocket' and 'Gross margin' in fund and 'Revenue growth' in fund:
                try:
                    rev_growth = float(fund['Revenue growth'].replace(',', '').replace(' ', ''))
                    gross_margin = float(fund['Gross margin'].replace(',', '').replace(' ', ''))
                except Exception as error:
                    print(error)
        return rev_growth, gross_margin

if __name__ == '__main__':
#    d = '2021-03-26'            #'2021-01-10'
#    f = StockFundamentalsExplorer()
#    f.averagePE(d)

#"""
    today = (datetime.now() + timedelta(days=-480)).strftime("%Y-%m-%d")
    #today = '2015-04-17'

    ss = ['MSFT', 'MA', 'PAYC', 'EVBG', 'SHOP', 'GOOGL', 'ANTM', 'AMZN', 'TSLA', 'AYX', 'TTD', 'SQ', 'LSXMB', 'FBIO', 'PIH', 'XMEX', 'AMZN', 'TURN', 'BIEI']
    mongo_client = MongoExplorer()
    #mongo_client = pymongo.MongoClient('mongodb://192.168.1.6:27017/')
    #mongoDB = mongo_client['riverhill']
    mongoDB = mongo_client.mongoDB
    mongo_col = mongoDB['etrade_companies']

    #mongo_query = {"Yahoo_Symbol": 'ANTM'}
    #mongo_query = {"Yahoo_Symbol": ss[len(ss)-1]}
    mongo_query = {"Yahoo_Symbol": ss[0]}

    coms = mongo_col.find(mongo_query)
    f = StockFundamentalsExplorer()

    for x in coms:
        f.get_fund(x['Yahoo_Symbol'], today)
        #fund_sec = f.get_sec()
        #print(fund_sec)
        print(f.fund)
        #eps = f.get_eps()
        #print(eps)

        #rev = f.get_rev()
        #print(rev)

        shares = f.get_shares()
        print(shares)

        #print(f.get_rocket_data())
#"""
