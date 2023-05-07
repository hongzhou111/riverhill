# import mechanize
# from bs4 import BeautifulSoup
# import requests
# import urllib
# from http.cookiejar import CookieJar
# import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import logging
from datetime import datetime
from datetime import timedelta
import pymongo
# import json
import traceback
import numpy
import json
from test_mongo import MongoExplorer


class RocketFin:
    def __init__(self):
        #logging.basicConfig(filename='test_rocketfinancial.log', level=logging.INFO)
        #logging.info(self.today)

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        #self.mongo_client = pymongo.MongoClient('mongodb://192.168.1.14:27017/')
        #self.mongoDB = self.mongo_client['riverhill']

        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36")
        self.browser = webdriver.Chrome(options=opts)

    def get_date(self, d):   # d = 'Dec-31-03
        ll = d.split('-')
        q = ''
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
                            #print(th_list)
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
                        self.save_rocket(col)
                    next = self.browser.find_element_by_xpath("//a[text() = 'Older >>']")
                    #next = self.browser.find_element_by_id("ctrlReportPagingBar_lnkNex")
                    next.click()
                except Exception as error:
                    getNext = 0

    def save_rocket(self, r):
        filter = {'symbol': r['symbol'], 'date': r['date'], 'type': r['type']}
        self.mongoDB['rocket_financials'].replace_one(filter, r, upsert=True)

if __name__ == '__main__':
    r = RocketFin()
    r.login()
    #r.get_financials('AXAS')     #AXAS, PIH
    coms = r.mongoDB['etrade_companies'].find()
    i = 1

    with open('./rocket_financials_restart.json') as f:
        restart_json = json.load(f)             #{'restart': 649}
    #print(restart_json)

    restartIndex = restart_json['restart']      # limit to 15 daily
    stopIndex = restartIndex + 13               # 15000

    for x in coms:
        if i > stopIndex:
            break

        if i >= restartIndex:
            print(i, x['Yahoo_Symbol'])
            r.get_financials(x['Yahoo_Symbol'])
        i = i + 1

    #r.browser.close()

    restart_json = {'restart': stopIndex+1}
    with open('./rocket_financials_restart.json', 'w') as json_file:
        json.dump(restart_json, json_file)

