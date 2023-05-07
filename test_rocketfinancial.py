'''
#History
#2022-11/29 - Comment out rocket_falg,  replace all records, no need to check existing records

'''
# import mechanize
# from bs4 import BeautifulSoup
# import requests
# import urllib
# from http.cookiejar import CookieJar
# import webbrowser
from datetime import datetime
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
#import time
#import logging
#from datetime import datetime
#from datetime import timedelta
import pymongo
# import json
#import traceback
#import numpy
import json

#from test_g20 import StockScore
from test_mongo import MongoExplorer

class RocketFin:
    def __init__(self):
        #logging.basicConfig(filename='test_rocketfinancial.log', level=logging.INFO)
        #logging.info(self.today)

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB

        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36")
        self.browser = webdriver.Chrome(options=opts)

    def get_date(self, d):   # d = 'Dec-31-03
        ll = d.split('-')
        if int(ll[2]) > 70:
            year = '19' + ll[2]
        else:
            year = '20' + ll[2]

        if ll[0] == 'Dec':
            month = '12'
        elif ll[0] == 'Nov':
            month = '11'
        elif ll[0] == 'Oct':
            month = '10'
        elif ll[0] == 'Sep':
            month = '09'
        elif ll[0] == 'Aug':
            month = '08'
        elif ll[0] == 'Jul':
            month = '07'
        elif ll[0] == 'Jun':
            month = '06'
        elif ll[0] == 'May':
            month = '05'
        elif ll[0] == 'Apr':
            month = '04'
        elif ll[0] == 'Mar':
            month = '03'
        elif ll[0] == 'Feb':
            month = '02'
        elif ll[0] == 'Jan':
            month = '01'
        q = year + '-' + month + '-' + ll[1]
        return q

    def get_quarter(self, d):   # d = 'Dec-31-03
        ll = d.split('-')
        q = ''
        if int(ll[2]) > 70:
            year = '19' + ll[2]
        else:
            year = '20' + ll[2]

        if ll[0] == 'Dec':
            q = year + 'Q4'
        elif ll[0] == 'Sep':
            q = year + 'Q3'
        elif ll[0] == 'Jun':
            q = year + 'Q2'
        elif ll[0] == 'Mar':
            q = year + 'Q1'
        return q

    def check_exclude_chars(self, exclude, str):
        for e in exclude:
            if e in str:
                return 1
        return 0

    def login(self):
        username_str = "hongzhou111@gmail.com"
        password_str = "lin111"

        url = "https://www.rocketfinancial.com/Login.aspx"
        self.browser.get(url)
        username = self.browser.find_element_by_name("username")
        password = self.browser.find_element_by_name("password")
        username.send_keys(username_str)
        password.send_keys(password_str)
        password.send_keys(Keys.RETURN)

    def get_financials(self, s):
        # check split flag - comment out 2002/11/29
        #query2 = {'$and': [{'symbol': s}, {'$or': [{'rocket_flag': {'$exists': False}}, {'rocket_flag': {'$ne': 1}}]}]}
        #splitChecking = self.mongoDB['yahoo_splits'].find_one(query2)
        #if splitChecking is not None:
        #    print('processing splits')
        #    self.update_yahoo_splits(s)

        exclude_key_list = ['.']
        # search for stock
        url = "https://www.rocketfinancial.com/Dashboard.aspx?pID=0"
        self.browser.get(url)
        #print(self.browser.page_source)
        search = self.browser.find_element_by_id("ctrlHeader_searchBar_txtSearch")
        search.send_keys(s)
        search.send_keys(Keys.RETURN)
        if 'Overview.aspx?fID=' not in self.browser.current_url:
            return
        fin_url = self.browser.current_url.replace('Overview', 'Financials')
        quarter_url = fin_url + '&p=1'
        ttm_url = fin_url + '&p=3'
        annual_quarter_url_list = [fin_url, quarter_url, ttm_url]
        #annual_quarter_url_list = [fin_url, quarter_url]
        type_list = ['year', 'quarter', 'TTM']
        #type_list = ['year', 'quarter']

        #annual_quarter_url_list = [quarter_url]
        for uIndex, u in enumerate(annual_quarter_url_list):
        #for u in annual_quarter_url_list:
            self.browser.get(u)

            getNext = 1
            while getNext != 0:
                try:
                    w = self.browser.find_element_by_xpath("//table[@id='gridReport']")
                    a = []
                    i = 0
                    for t in w.find_elements_by_tag_name('tr'):
                        row = []
                        if i == 0:
                            th_list = t.find_elements_by_tag_name('th')
                            th_len = len(th_list)
                            th_list = [header.text for header in th_list]
                            a.append(th_list)
                        elif i > 1:
                            td_list = t.find_elements_by_tag_name('td')
                            td_len = len(td_list)
                            if td_len == th_len:
                                #print(td_len)
                                for d in t.find_elements_by_tag_name('td'):
                                    row.append(d.text.replace('[+]', '').replace('$', '').replace('%', '').strip())
                                #print(row)
                                a.append(row)
                        i = i + 1
                    #print(a)
                    #print(len(a[0]))
                    #print(numpy.transpose(a))
                    #print(list(map(list, zip(*a))))
                    #print([list(i) for i in zip(*a)])
                    #print([[row[i] for row in a] for i in range(len(a[0]))])
                    for j in range(1, len(a[0])):
                        col = {'symbol': s, 'original_date': a[0][j], 'date': self.get_date(a[0][j]), 'type': type_list[uIndex], 'quarter': self.get_quarter(a[0][j])}
                        for i in range(1, len(a)):
                            if a[i][0] != '' and self.check_exclude_chars(exclude_key_list, a[i][0]) == 0:
                                col[a[i][0]] = a[i][j]
                        print(j, col)
                        #check existing data - comment out 2022/11/29
                        #mongo_query = {'symbol': col['symbol'], 'date': col['date'], 'type': col['type']}
                        #recExisting = self.mongoDB['rocket_financials'].find_one(mongo_query)

                        #if recExisting is None:
                        self.save_rocket(col)
                        #else:
                        #    getNext = 0
                        #    break
                    if getNext != 0:
                        next = self.browser.find_element_by_xpath("//a[text() = 'Older >>']")
                        # next = self.browser.find_element_by_id("ctrlReportPagingBar_lnkNex")
                        next.click()
                except Exception as error:
                    getNext = 0


    def save_rocket(self, r):
        filter = {'symbol': r['symbol'], 'date': r['date'], 'type': r['type']}
        self.mongoDB['rocket_financials'].replace_one(filter, r, upsert=True)

    def update_yahoo_splits(self, s):
        filter = {'symbol': s}
        self.mongoDB['yahoo_splits'].update_many(filter, {'$set': {'rocket_flag': 1}})

    def run(self):
        print(datetime.now().strftime("%Y-%m-%d"))

        self.login()
        # r.get_financials('AXAS')     #AXAS, PIH
        mongo_query = {'status': 'active'}
        coms = self.mongoDB['etrade_companies'].find(mongo_query, no_cursor_timeout=True)
        i = 1

        with open('C:/Users/3203142/OneDrive/Stock/PycharmProjects/riverhill/rocket_financials_restart.json') as f:
            restart_json = json.load(f)  # {'restart': 649} {"restart": 10310}
        # print(restart_json)

        restartIndex = restart_json['restart']  # limit to 15 daily
        # stopIndex = restartIndex + 15               # 15000
        visitCount = 0
        stopCount = 15

        for x in coms:
            if visitCount >= stopCount:
                # if i > stopIndex:
                break

            if i >= restartIndex:
                # check g score
                # print(i, x['Yahoo_Symbol'])
                # AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")
                # g20 = StockScore({"AAOD": AAOD, "symbol": x['Symbol']})
                '''
                try:
                    #score = g20.run()
                    score = r.mongoDB['stock_g_score'].find_one({'symbol': x['Yahoo_Symbol'], 'Recommendation': ''}, sort=[('AAOD', -1)])
                except:
                    score = None

                if score is not None and 'Recommendation' in score and score['Recommendation'] != 'n':
                    visitCount = visitCount + 1
                    print(i, x['Yahoo_Symbol'])
                    r.get_financials(x['Yahoo_Symbol'])
                else:
                    if score is not None and 'Reason' in score:
                        # print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'], 'Score:' + str(score['Score']))
                        print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'])
                    else:
                        print(i, x['Yahoo_Symbol'], score)
                '''
                visitCount = visitCount + 1
                print(i, x['Yahoo_Symbol'])
                self.get_financials(x['Yahoo_Symbol'])
            i = i + 1

        restart_json = {'restart': i}
        with open('C:/Users/3203142/OneDrive/Stock/PycharmProjects/riverhill/rocket_financials_restart.json',
                  'w') as json_file:
            json.dump(restart_json, json_file)

        self.browser.quit()


if __name__ == '__main__':
    r = RocketFin()
    r.login()
    #r.get_financials('AXAS')     #AXAS, PIH
    mongo_query = {'status': 'active'}
    coms = r.mongoDB['etrade_companies'].find(mongo_query,no_cursor_timeout=True)
    i = 1

    with open('C:/Users/3203142/OneDrive/Stock/PycharmProjects/riverhill/rocket_financials_restart.json') as f:
        restart_json = json.load(f)             #{'restart': 649} {"restart": 10310}
    #print(restart_json)

    restartIndex = restart_json['restart']      # limit to 15 daily
    #stopIndex = restartIndex + 15               # 15000
    visitCount = 0
    stopCount = 15

    for x in coms:
        if visitCount >= stopCount:
        #if i > stopIndex:
            break

        if i >= restartIndex:
            #check g score
            #print(i, x['Yahoo_Symbol'])
            #AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")
            #g20 = StockScore({"AAOD": AAOD, "symbol": x['Symbol']})
            '''
            try:
                #score = g20.run()
                score = r.mongoDB['stock_g_score'].find_one({'symbol': x['Yahoo_Symbol'], 'Recommendation': ''}, sort=[('AAOD', -1)])
            except:
                score = None

            if score is not None and 'Recommendation' in score and score['Recommendation'] != 'n':
                visitCount = visitCount + 1
                print(i, x['Yahoo_Symbol'])
                r.get_financials(x['Yahoo_Symbol'])
            else:
                if score is not None and 'Reason' in score:
                    # print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'], 'Score:' + str(score['Score']))
                    print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'])
                else:
                    print(i, x['Yahoo_Symbol'], score)
            '''
            visitCount = visitCount + 1
            print(i, x['Yahoo_Symbol'])
            r.get_financials(x['Yahoo_Symbol'])
        i = i + 1

    restart_json = {'restart': i}
    with open('C:/Users/3203142/OneDrive/Stock/PycharmProjects/riverhill/rocket_financials_restart.json', 'w') as json_file:
        json.dump(restart_json, json_file)

    r.browser.quit()

    exit(0)
