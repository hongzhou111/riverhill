import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
import json
import re
#from test2 import SECExplorer
#from test_g20 import StockScore

from bs4 import BeautifulSoup
import requests
from test_yahoo import QuoteExplorer
#from test_etrade import EtradeExplorer
from test_mongo import MongoExplorer
from test_sec import SECExplorer
import time

class StockSpliter:
    def __init__(self):
        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB

    def get_split(self):
        #get start event_date
        end_date = (datetime.now() + timedelta(days=-2)).strftime("%Y-%m-%d")
        eventDate = self.mongoDB['yahoo_splits'].find_one(sort=[("split_date", -1)])
        if eventDate == None:
            #event_date = '2020-08-31'
            event_date = '2020-01-01'
        else:
            event_date = (datetime.strptime(eventDate['split_date'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        while event_date < end_date:
            # Obtain Yahoo HTML for split calendar
            base_url = "https://finance.yahoo.com/calendar/splits?day={}"
            print(base_url, event_date)
            yahoo_resp = requests.get(base_url.format(event_date))
            yahoo_str = yahoo_resp.text

            # Find the document link
            soup = BeautifulSoup(yahoo_str, 'html.parser')
            try:
                table_tag = soup.find('table')
                rows = table_tag.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) > 0:
                        symbol = cells[0].text
                        payable = cells[2].text
                        ratio = cells[4].text
                        #print(symbol, payable, ratio)

                        if not re.search('\.', symbol):                          #exclude non_US symbols
                            split_date = (datetime.strptime(payable, '%b %d, %Y')).strftime('%Y-%m-%d')
                            a = ratio.split(' - ')
                            r = float(a[1]) / float(a[0])
                            print(symbol, split_date, r)

                            #save the record
                            if split_date != '' and symbol != '':
                                query = {
                                    "symbol": symbol,
                                    "split_date": split_date
                                }
                                result = {
                                    "symbol": symbol,
                                    "split_date": split_date,
                                    "ratio": r,
                                    'process_flag': ''
                                }
                                print(result)
                                self.mongoDB['yahoo_splits'].replace_one(query, result, upsert=True)
            except Exception as error:
                print(error)
                #continue

            event_date = (datetime(*(int(s) for s in event_date.split('-'))) + timedelta(days=1)).strftime("%Y-%m-%d")

    def split_update(self):
        #mongo_query = {'symbol': 'TSLA'}
        mongo_query = {'process_flag': ''}
        splits = self.mongoDB['yahoo_splits'].find(mongo_query, no_cursor_timeout=True).sort('split_date', 1)

        index = 1
        restart = 1
        stopIndex = 2000000
        for split in splits:
            if index >= stopIndex:
                break
            if index >= restart:
                print(split)
                #reload quotes
                self.mongoDB[split['symbol']].drop()
                q = QuoteExplorer()
                AAOD = datetime.now().strftime("%Y-%m-%d")
                try:
                    q.get_quotes(split['symbol'], AAOD)
                except Exception as error:
                    print(error)

                #update etrade_fundamentals
                query2 = {'$and': [{'symbol': split['symbol']}, {'date': {'$lt': datetime.strptime(split['split_date'], '%Y-%m-%d')}}]}
                funds = self.mongoDB['etrade_fundamentals'].find(query2)
                for fund in funds:
                    print(fund)
                    try:
                        if re.search('$', fund['close']):
                            new_close = float(fund['close'][1:].replace(',', '')) / split['ratio']
                        else:
                            new_close = float(fund['close'].replace(',', '')) / split['ratio']
                        new_close_str = '$' + str(round(new_close, 2))

                        new_eps = float(fund['EPS'].replace(',', '')) / split['ratio']
                        new_eps_str = str(round(new_eps, 2))

                        new_shares = float(fund['shares'][:-1].replace(',', '')) * split['ratio']
                        new_shares_str = str(round(new_shares, 1)) + ' ' + fund['shares'][-1]

                        if (not re.match('-', fund['dividend'])) and fund['dividend'] != '' and (not re.search('%', fund['dividend'])):
                            new_div = float(fund['dividend'].replace(',', '')) / split['ratio']
                            new_div_str = str(round(new_div, 2))
                        else:
                            new_div_str = fund['dividend']

                        new_fund = fund
                        new_fund['close'] = new_close_str
                        new_fund['EPS'] = new_eps_str
                        new_fund['shares'] = new_shares_str
                        new_fund['dividend'] = new_div_str
                        query3 = {
                            #"symbol": fund['symbol'],
                            #"date": fund['date']
                            "_id": fund['_id']
                        }
                        print(new_fund)
                        self.mongoDB['etrade_fundamentals'].replace_one(query3, new_fund, upsert=True)
                    except Exception as error:
                        print(error)

                #reload SEC
                #self.update_sec(split['symbol'])
                #reload rocket_financials - handled in test_rocketfiancials.py

            query4 = {
            #    "symbol": split['symbol'],
            #    "split_date": split['split_date']
                "_id": split['_id']
            }
            process_result = split
            process_result['process_flag'] = '1'
            self.mongoDB['yahoo_splits'].replace_one(query4, process_result, upsert=True)
            index += 1

    def update_sec(self, s):
        mongo_col2 = self.mongoDB['cik_ticker']

        types = ['10-K', '10-Q']
        dateb = '21200101'  # '20200101'
        count = 100

        # if score is not None and score['Recommendation'] != 'n':
        mongo_query2 = {"Ticker": s, "Status": {"$ne": "Inactive"}}
        mongo_cik = mongo_col2.find_one(mongo_query2)

        if mongo_cik is None:
            cik = ''
        else:
            cik = mongo_cik['CIK']

        for type in types:
            sec = SECExplorer(s, cik, type, dateb, count)

            if cik == '':
                cik_json = sec.get_cik()
                if cik_json is not None and cik_json['CIK'] != '':
                    mongo_col2.insert_one(cik_json)
                else:
                    break
            print(i, type + "  " + sec.ticker + "    " + sec.cik)
            try:
                # sec.get_sbrl('tags')
                sec.get_sbrl()
            except:
                continue

if __name__ == '__main__':
    ss = StockSpliter()
    ss.get_split()
    ss.split_update()

'''
#clean up sec one time
    mongo_query = {}
    splits = self.mongoDB['yahoo_splits'].find(mongo_query, no_cursor_timeout=True).sort('split_date', 1)
    
    index = 1
    restart = 1
    stopIndex = 2000000
    for split in splits:
        if index >= stopIndex:
            break
        if index >= restart:
            print(index, split)
            #reload SEC
            ss.update_sec(split['symbol'])
            
            if i % 5 == 0:
                time.sleep(60.00)
    index += 1
'''
