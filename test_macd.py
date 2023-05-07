import pandas as pd
from datetime import datetime
from test_mongo import MongoExplorer
from test_stockstats import StockStats
from test_ga_macd_rl import RuleGA_MACD_RL
from test_fundamentals import StockFundamentalsExplorer
from test_yahoo import QuoteExplorer
import time

class MACD:
    def __init__(self):
        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB

    def macd_crossing_update(self, ticker, crossing=None):
        if crossing == None:
            ss = StockStats(ticker)
            ss.macd(6, 13, 9)
            crossing = ss.macd_crossing_by_threshold(threshold=0.5)

        baseDate = datetime(1960, 1, 1).strftime('%Y-%m-%d')

        macd_crossings = self.mongoDB['macd_crossings']
        queryMaxDate = {"symbol": ticker}
        qcMaxDate = macd_crossings.find(queryMaxDate).sort("date", -1)
        if macd_crossings.count_documents(queryMaxDate) == 0:
            start = baseDate
        else:
            qcM = qcMaxDate[0]
            startDate = qcM["date"]
            start = datetime.strptime(startDate, '%Y-%m-%d')

        c = crossing.loc[crossing['date'] > start]
        if c.empty is False:
            c = c.assign(ticker=ticker)
            p = pd.DataFrame()
            p['symbol'] = c['ticker']
            d = []
            for dd in c['date']:
                d.append(dd.strftime('%Y-%m-%d'))
            p['date'] = d
            p['macd_sign'] = c['macd_sign']
            p['r'] = c['r']
            p['len'] = c['len']
            p['accum'] = c['accum']
            #print(start, p)

            macd_crossings.insert_many(p.to_dict('records'))

            #for row in p.to_dict(orient='records'):
            #    #print(row)
            #    macd_crossings.replace_one({'symbol': row['symbol'], 'date': row['date']}, row, upsert=True)

    def cap_update(self):
        query = {'CAP' : {'$exists': False}}
        com = self.mongoDB['macd_crossings'].find(query, no_cursor_timeout=True)
        ga = RuleGA_MACD_RL()
        for c in com:
            cap = ga.getCAP(c['symbol'], c['date'])
            query2 = {'symbol': c['symbol'], 'date': c['date']}
            newValue = {'$set': {'CAP': cap}}
            print(query2, newValue)
            self.mongoDB['macd_crossings'].update_one(query2, newValue)


    def macd_crossing_cap_update(self, ticker, crossing=None):
        if crossing == None:
            ss = StockStats(ticker)
            ss.macd(6, 13, 9)
            crossing = ss.macd_crossing_by_threshold(threshold=0.5)

        baseDate = datetime(1960, 1, 1).strftime('%Y-%m-%d')

        macd_crossings = self.mongoDB['macd_crossings']
        queryMaxDate = {"symbol": ticker}
        qcMaxDate = macd_crossings.find(queryMaxDate).sort("date", -1)
        if macd_crossings.count_documents(queryMaxDate) == 0:
            start = baseDate
        else:
            qcM = qcMaxDate[0]
            startDate = qcM["date"]
            start = datetime.strptime(startDate, '%Y-%m-%d')

        #print(start)
        #print(qcMaxDate[0])
        #print(crossing)
        c = crossing.loc[crossing['date'] > start]

        if c.empty is False:
            # ga = RuleGA_MACD_RL()
            cap_date = datetime.now().strftime('%Y-%m-%d')
            f = StockFundamentalsExplorer()
            f.get_fund(ticker, cap_date)
            shares = f.get_shares()
            #print(shares)

            c = c.assign(ticker=ticker)
            p = pd.DataFrame()
            p['symbol'] = c['ticker']
            d = []
            for dd in c['date']:
                d.append(dd.strftime('%Y-%m-%d'))
            #for dd in c['date']:
            #    ddd = dd.strftime('%Y-%m-%d')
            #    d.append(ddd)
            #    dd_cap = ga.getCAP(ticker, ddd)
            #    cap.append(dd_cap)

            p['date'] = d

            c['CAP'] = c['close'] * shares
            p['CAP'] = c['CAP']

            p['macd_sign'] = c['macd_sign']
            p['r'] = c['r']
            p['len'] = c['len']
            p['accum'] = c['accum']
            #print(start, p)

            macd_crossings.insert_many(p.to_dict('records'))

            # for row in p.to_dict(orient='records'):
            #    #print(row)
            #    macd_crossings.replace_one({'symbol': row['symbol'], 'date': row['date']}, row, upsert=True)

    def update_all(self):
        aaod = datetime.now().strftime("%Y-%m-%d")
        #aaod = '2022-04-22'

        companies = self.mongoDB['etrade_companies']
        # mongo_query = {"Symbol": 'TURN'}
        mongo_query = {'status': 'active'}
        tickers = companies.find(mongo_query, no_cursor_timeout=True)

        companyIndex = 1
        restartIndex = 4191     #2956 4691  # 3        #1387
        stopIndex = 10000000

        for t in tickers:
            if companyIndex > stopIndex:
                break

            if companyIndex >= restartIndex:
                company = t["Yahoo_Symbol"]
                # logging.info(str(companyIndex) + ": " + company)
                print(str(companyIndex) + ": " + company)
                try:
                    q = QuoteExplorer()
                    q.get_quotes(company, aaod)

                    ss = StockStats(company)
                    m = ss.macd_by_date(aaod, 6, 13, 9)
                    if m is not None and ((m['r'] < 0.2 and m['len'] >= 5) or m['len'] == 1):
                        #self.macd_crossing_update(company)
                        self.macd_crossing_cap_update(company)
                except Exception as error:
                    print(error)

                #3if companyIndex > 893:  # and companyIndex % 5 == 0:
                #    time.sleep(0.100)

            companyIndex = companyIndex + 1

if __name__ == '__main__':
    startTime = datetime.now()

    m = MACD()

    companies = m.mongoDB['etrade_companies']
    #mongo_query = {"Symbol": 'TURN'}
    mongo_query = {'status': 'active'}
    tickers = companies.find(mongo_query, no_cursor_timeout=True)

    companyIndex = 1
    restartIndex = 6            #6218     #3        #1387
    stopIndex = 6           #10000000

    for t in tickers:
        if companyIndex > stopIndex:
            break

        if companyIndex >= restartIndex:
            company = t["Yahoo_Symbol"]
            # logging.info(str(companyIndex) + ": " + company)
            print(str(companyIndex) + ": " + company)
            try:
                #m.macd_crossing_update(company)
                m.macd_crossing_cap_update(company)
            except Exception as error:
                print(error)
        companyIndex = companyIndex + 1

    #m.cap_update()

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time: ', runTime)
