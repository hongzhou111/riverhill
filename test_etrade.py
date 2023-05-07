#import mechanize
#from bs4 import BeautifulSoup
#import requests
#import urllib
#from http.cookiejar import CookieJar
#import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
#import time
#import logging
from datetime import datetime
from datetime import timedelta
#import pymongo
#import json
#import traceback
from test_mongo import MongoExplorer

class EtradeExplorer:
    def __init__(self):
        self.today = datetime.now() + timedelta(days=-2)
        #logging.basicConfig(filename='test_etrade.log', level=logging.INFO)
        #logging.info(self.today)

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        self.mongo_com = self.mongoDB['etrade_companies']
        self.mongo_fund = self.mongoDB['etrade_fundamentals']

        opts = Options()
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36")
        self.browser = webdriver.Chrome(options=opts)

    def get_companies(self):
        # login to etrade
        username_str = "hongzhou111"
        password_str = "lin111"

        cj = CookieJar()
        opts = Options()
        #opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36")
        #browser = webdriver.Chrome(options=opts)
        browser = webdriver.Ie()
        #browser = webdriver.Chrome()
        browser.get("https://us.etrade.com/e/t/user/login")
        print(browser.get_cookies())

        #time.sleep(1)
        username = browser.find_element_by_name("USER")
        password = browser.find_element_by_name("PASSWORD")
        username.send_keys(username_str)
        password.send_keys(password_str)
        password.send_keys(Keys.RETURN)
        #form1 = browser.find_element_by_id("log-on-form")
        #form1.submit()

        #print(browser.page_source)

        '''
        br = mechanize.Browser()
        br.set_cookiejar(cj)
        br.open("https://us.etrade.com/e/t/user/login")
        br.select_form(nr=0)
        br.form['USER'] = username
        br.form['PASSWORD'] = password
        br.submit()
        
        print(br.response().read())
        '''
        # go to Saved Screener

        #res = mechanize.urlopen("https://www.etrade.wallst.com/v1/tradingideas/screener/stock_screener_results_iframe.asp?savedScreenName=My%20Screen%20All")
        #print(res.read())
        #br.select_form(nr=0)
        #br.submit()
        #print(br.response().read())
        #soup = BeautifulSoup(br.response().read())

        #for link in br.links():
        #    print(link.url)


    def get_fundamentals(self, com):
        check_date = self.today + timedelta(days=-90)
        mongo_query = {"symbol": com, "date": {"$gt": check_date}}
        mongo_fund_check = self.mongo_fund.find_one(mongo_query, sort=[('date', -1)])

        # get the new data
        close = ''
        pe = ''
        eps = ''
        shares = ''
        divident = ''
        return_on_asset = ''

        # go to snapshot page
        try:
            url = "https://www.etrade.wallst.com/v1/stocks/snapshot/snapshot.asp?symbol=" + com
            #url = "https://us.etrade.com/etx/mkt/quotes?symbol=" + com + "#/snapshot"
            # url = "https://www.etrade.wallst.com/v1/stocks/snapshot/snapshot.asp?ChallengeUrl=https://idp.etrade.com/idp/SSO.saml2&reinitiate-handshake=0&AuthnContext=authenticated&env=PRD&symbol=$company&rsO=new&country=US"
            self.browser.get(url)
            # quotes = self.browser.find_elements_by_class_name('quoteTableData')
            # i = 0
            # for x in quotes:
            #    print(i, x.text)
            #    i = i + 1
            # close = self.browser.find_element_by_class_name('quoteTableData').text
            close = self.browser.find_element_by_class_name('large-header.mRight5').text

            data1 = self.browser.find_elements_by_class_name("redesignBox-info.fRight")
            #close = data1[0].text
            #pe = data1[3].text
            pe = data1[7].text
            #eps = data1[4].text
            eps = data1[8].text
            #shares = data1[7].text
            shares = data1[5].text
            #dividend = data1[10].text
            dividend = data1[9].text

            checkPE = pe[-1:]
            if checkPE == 'M' or checkPE == 'B' or checkPE == 'K' or checkPE == 'T':
                shares = eps
                pe = ''
                eps = ''

            url2 = "https://www.etrade.wallst.com/v1/stocks/fundamentals/fundamentals.asp?symbol=" + com
            self.browser.get(url2)
            data2 = self.browser.find_elements_by_class_name("right.redesignTableInfo.txt13.et-fort-medium")
            return_on_assets = data2[16].text
            if return_on_assets[-1:] != '%':
                return_on_assets = ''

            #print(com, self.today, close, pe, eps, shares, dividend, return_on_assets, mongo_fund_check['EPS'])

            if eps != '' and (mongo_fund_check == None or eps != mongo_fund_check['EPS']):
                #print(com, self.today, close, pe, eps, shares, dividend, return_on_assets)
                # insert into etrade_fundamentals
                rec = {
                    'symbol': com,
                    'date': self.today,
                    'close': close,
                    'PE': pe,
                    'EPS': eps,
                    'shares': shares,
                    'dividend': dividend,
                    'return_on_assets': return_on_assets
                }
                print(rec)
                #logging.info(rec)
                #self.mongo_fund.insert_one(rec)
                self.mongo_fund.replace_one({'symbol': com, 'date': self.today}, rec, upsert=True)
        except Exception as error:
            print(com, error)
            #logging.info(com)
            #logging.info(error)

if __name__ == '__main__':
    etrade = EtradeExplorer()

    ss = ['MA', 'MSFT', 'PAYC', 'EVBG', 'SHOP', 'GOOGL', 'ANTM', 'AMZN', 'TSLA', 'AYX', 'TTD', 'SQ', 'LSXMB', 'FBIO']

    #mongo_query = {"Yahoo_Symbol": 'YY'}
    # mongo_query = {"Yahoo_Symbol": 'ANTM'}
    #mongo_query = {"Yahoo_Symbol": ss[len(ss) - 1]}
    #mongo_query = {}
    #mongo_query = {"Yahoo_Symbol": ss[0]}
    mongo_query = {'status': 'active'}
    coms = etrade.mongo_com.find(mongo_query,no_cursor_timeout=True)
    i = 1
    restartIndex = 1        #2990
    stopIndex = 1000000

    for x in coms:
        if i > stopIndex:
            break

        if i >= restartIndex:
            print(i, x['Symbol'])
            etrade.get_fundamentals(x['Symbol'])
        i = i + 1

    #etrade.get_fundamentals('EPS')
    etrade.browser.quit()

    exit(0)
