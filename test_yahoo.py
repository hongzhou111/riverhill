'''
History
2023/03/28  add get_minute_date
'''
#from bs4 import BeautifulSoup
#import requests
#import sys
#import os
#import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
#from datetime import timedelta
#import datetime
#import pymongo
#import json
#import re
#from odo import odo
#import pandas as pd
#import pandas_datareader as pdr
from test_mongo import MongoExplorer
import yfinance as yf
#from stockstats import StockDataFrame as Sdf
import traceback

class QuoteExplorer:
    def __init__(self):
        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB

    def get_quotes(self, ticker, AAOD):
        #baseDate = datetime(1970, 1, 1)
        #today = datetime(*(int(s) for s in AAOD.split('-')))
        end_date = (datetime(*(int(s) for s in AAOD.split('-')))+timedelta(days=1)).strftime("%Y-%m-%d")

        #while sekf.today.weekday() != 6:
        #    today = today - timedelta(days=1)

        yfq = self.mongoDB[ticker]
        queryMaxDate = {"Symbol": ticker}
        qcMaxDate = yfq.find(queryMaxDate).sort("Date", -1)
        if yfq.count_documents(queryMaxDate) == 0:
        #if qcMaxDate is None:
            #start = baseDate
            start_date = '1970-01-01'
        else:
            qcM = qcMaxDate[0]
            #startDate = qcM["Date"]
            start_date = qcM["Date"]
            #start = datetime.strptime(startDate, '%Y-%m-%d')
            #start = start + timedelta(days=1)

        #logging.info(ticker + ": " + str(start) + " - " + str(today))
        #if start < today:
        if start_date < end_date:
            try:
                y = yf.Ticker(ticker)
                # get historical market data
                #quotes = y.history(period="max")
                quotes = y.history(start=start_date, end=end_date)
                #quotes = pdr.get_data_yahoo(ticker,
                #                            start=datetime(start.year, start.month, start.day),
                #                            end=datetime(today.year, today.month, today.day))
            except Exception as e:
                print(traceback.format_exc())
                #print(e)
                quotes = None
                #logging.error(str(e))

            #if quotes is None:
            #    logging.info("No Records")
            #else:
            if quotes is not None:
                quotes["Symbol"] = ticker
                dlist = []
                for d in quotes.index:
                    dlist.append(str(d)[0:10])
                quotes["Date"] = dlist
                #print(quotes.to_dict('records'))
                #quotes = quotes.reset_index(drop=True)
                for row in quotes.to_dict(orient='records'):
                    #print(row)
                    #if yfq.count_documents(queryMaxDate) == 0:
                    #    yfq.insert_one(row)
                    #else:
                    yfq.replace_one({'Symbol': row['Symbol'], 'Date': row['Date']}, row, upsert=True)


    def get_minute_data(self, ticker):
        end_date = datetime.now()       #.strftime("%Y-%m-%d %H:%M:%S")
        db_name = ticker + '_min'

        yfq = self.mongoDB[db_name]
        queryMaxDate = {"Symbol": ticker}
        qcMaxDate = yfq.find(queryMaxDate).sort("Date", -1)
        if yfq.count_documents(queryMaxDate) == 0:
            start_date = datetime.strptime('2023-03-23 09:30:00', '%Y-%m-%d %H:%M:%S')
        else:
            qcM = qcMaxDate[0]
            start_date = qcM["Date"]
        print(start_date, end_date)
        if start_date < end_date:
            try:
                y = yf.Ticker(ticker)
                # get historical market data
                quotes = y.history(start=start_date, end=end_date, interval='1m')
            except Exception as e:
                print(traceback.format_exc())
                # print(e)
                quotes = None

            if quotes is not None:
                quotes = quotes.reset_index()
                quotes = quotes.rename(columns={"Datetime": "Date"})

                quotes["Symbol"] = ticker
                #print(quotes)

                #dlist = []
                #for d in quotes.index:
                #    dlist.append(str(d)[0:10])
                #quotes["Date"] = dlist
                # print(quotes.to_dict('records'))
                # quotes = quotes.reset_index(drop=True)
                for row in quotes.to_dict(orient='records'):
                    print(row)
                    # if yfq.count_documents(queryMaxDate) == 0:
                    #    yfq.insert_one(row)
                    # else:
                    #yfq.replace_one({'Symbol': row['Symbol'], 'Date': row['Date']}, row, upsert=True)

if __name__ == '__main__':
    #logging.basicConfig(filename='test_yahoo.log', level=logging.INFO)
    runday = date.today()
    #logging.info(runday)

    q = QuoteExplorer()

    companies = q.mongoDB['etrade_companies']
    #mongo_query = {"Symbol": 'BVH'}
    #mongo_query = {"Symbol": 'ATVI'}
    #mongo_query = {"Symbol": 'NTES'}
    mongo_query = {"Symbol": 'AMZN'}
    #mongo_query = {"Symbol": 'VRUS'}
    #mongo_query = {"Symbol": 'BILL'}
    #mongo_query = {"Symbol": 'TWLO'}
    #mongo_query = {"Symbol": 'TCEHY'}
    #mongo_query = {"Symbol": 'GOLD'}
    #mongo_query = {}
    tickers = companies.find(mongo_query)

    AAOD = datetime.now().strftime("%Y-%m-%d")
    #AAOD = "2019-11-02"

    companyIndex = 1
    restartIndex = 1
    stopIndex = 1000000

    for t in tickers:
        if companyIndex > stopIndex:
            break

        if companyIndex >= restartIndex:
            company = t["Yahoo_Symbol"]
            #logging.info(str(companyIndex) + ": " + company)
            print(str(companyIndex) + ": " + company)

            q.get_quotes(company, AAOD)
            #q.get_minute_data(company)
        companyIndex = companyIndex + 1

    #from yahoo_historical import Fetcher
    #data = Fetcher("PLNT", [2007,1,1], [2019,6,14])
    ##print(data.getHistorical())
    #print(data)


'''
   "Date" : "2015-08-06", 
    "Open" : 14.5, 
    "High" : 16.18, 
    "Low" : 13.75, 
    "Close" : 16.0, 
    "Adj Close" : 14.066927, 
    "Volume" : NumberInt(16172700), 
    "Symbol" : "PLNT"
    
            s = requests.Session()
            url1 = "https://finance.yahoo.com/quote/" + company + "/history?period1=" + str(baseDateNum) + "&period2=" + str(todayNum) + "&interval=1d&filter=history&frequency=1d"
            yfq_resp = s.get(url1)
            cookies = yfq_resp.cookies.get_dict()
            #scrumStr = cookies["B"][0:13]
            scrumStr = "hSR0KojCveS"
            print(str(cookies) + "   " + scrumStr)

            #soup = BeautifulSoup(yfq_resp.text, 'html.parser')
            #a_tags = soup.find_all('a')
            #for a in a_tags:
            #    print(a)
            #https: // query1.finance.yahoo.com / v7 / finance / download / LYFT?period1 = 1558131030 & period2 = 1560809430 & interval = 1
            #d & events = history & crumb = hSR0KojCveS

            url = "https://query1.finance.yahoo.com/v7/finance/download/" + company + "?period1=" + str(startNum) + "&period2=" + str(todayNum) + "&interval=1d&events=history&crumb=" + str(scrumStr)
            #print(url)
            yfq_csv_resp = s.get(url)
            yfq_csv = yfq_resp.text
            #print(yfq_csv)
'''

'''
y = yf.Ticker(company)
# get historical market data
df = y.history(start='2018-04-01', end='2018-04-10')
print(df)
df = df.reset_index()
q = Sdf.retype(df)
print(q)
'''
