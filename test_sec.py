import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
import json
import re
#from test2 import SECExplorer
#from test_g20 import StockScore
import traceback
from bs4 import BeautifulSoup
import requests
#import sys
import os
import time
#import matplotlib.pyplot as plt
#import pandas as pd
#from test_plot import StockPlotter
#from test_g20 import StockScore
#from test_yahoo import QuoteExplorer
#from test_etrade import EtradeExplorer
from test_mongo import MongoExplorer

class SECExplorer:
    def __init__(self, ticker, cik, type, dateb, count):
        self.ticker = ticker
        self.cik = cik
        self.type = type
        self.dateb = dateb
        self.count = count

        mongo = MongoExplorer()
        mongoDB = mongo.mongoDB
        self.mongo_sec_eps = mongoDB['sec_eps']
        self.mongo_sec_rev = mongoDB['sec_rev']
        self.mongo_sec_tags = mongoDB['sec_tags']
        self.mongo_sec_shares = mongoDB['sec_shares']
        self.mongo_sec_income = mongoDB['sec_income']

    def get_month_str(self, month):
        if month == 'Jan':
            return '01'
        elif month == 'Feb':
            return '02'
        elif month == 'Mar':
            return '03'
        elif month == 'Apr':
            return '04'
        elif month == 'May':
            return '05'
        elif month == 'Jun':
            return '06'
        elif month == 'Jul':
            return '07'
        elif month == 'Aug':
            return '08'
        elif month == 'Sep':
            return '09'
        elif month == 'Oct':
            return '10'
        elif month == 'Nov':
            return '11'
        elif month == 'Dec':
            return '12'
        else:
            return ''

    def get_quarter(self, ref_month):
        q = ''
        if ref_month == '03' or ref_month == '01' or ref_month == '02' or ref_month == '3' or ref_month == '1' or ref_month == '2' or ref_month.upper() == 'MAR' or ref_month.upper() == 'JAN' or ref_month.upper() == 'FEB':
            q = 'Q1'
        elif ref_month == '06' or ref_month == '04' or ref_month == '05' or ref_month == '6' or ref_month == '4' or ref_month == '5' or ref_month.upper() == 'APR' or ref_month.upper() == 'MAY' or ref_month.upper() == 'JUN':
            q = 'Q2'
        elif ref_month == '09' or ref_month == '07' or ref_month == '08' or ref_month == '9' or ref_month == '7' or ref_month == '8' or ref_month.upper() == 'SEP' or ref_month.upper() == 'JAL' or ref_month.upper() == 'AUG':
            q = 'Q3'
        elif ref_month == '12' or ref_month == '10' or ref_month == '11' or ref_month.upper() == 'DEC' or ref_month.upper() == 'OCT' or ref_month.upper() == 'NOV':
            q = 'Q4'
        return q

    def save_xbrl(self, doc_name, data):
        path = "C:\\Users\\3203142\\OneDrive\\Stock\\SEC\\" + self.ticker + "\\" + self.type
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + "\\" + doc_name
        if os.path.exists(path):
            return -1
        else:
            with open(path, "wb") as f:
                f.write(data.encode('ascii', 'ignore'))
            return 1

    def get_cik(self):
        # Obtain HTML for search page
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}"
        edgar_resp = requests.get(base_url.format(self.ticker))
        edgar_str = edgar_resp.text

        # Find the document link
        soup = BeautifulSoup(edgar_str, 'html.parser')
        span_tags = soup.find_all('span', class_= 'companyName')
        if len(span_tags) > 0:
            t = span_tags[0].text
            cik_pos = t.find("CIK")
            company_name = t[: cik_pos]
            cik = t[cik_pos + 9:cik_pos + 16]
            self.cik = cik

            a_tags = soup.find_all('a')
            sic = ''
            for x in a_tags:
                if 'SIC' in x['href']:
                    sic = x.text
                    break

            return {
                "CIK":      cik,
                "Ticker":   self.ticker,
                "Name":     company_name,
                "SIC":      sic
            }

    def get_sbrl(self, option=''):         #options:  tags: get all tags;  '': get rev, eps, shares, grossprofit
        # Obtain HTML for search page
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type={}&dateb={}&count={}"
        edgar_resp = requests.get(base_url.format(self.cik, self.type, self.dateb, self.count))
        edgar_str = edgar_resp.text

        # Find the document link
        soup = BeautifulSoup(edgar_str, 'html.parser')
        table_tag = soup.find('table', class_='tableFile2')
        rows = table_tag.find_all('tr')
        i = 1
        for row in rows:
            doc_link = ''
            cells = row.find_all('td')
            if len(cells) > 3 and cells[0].text == self.type:
                filing_date = cells[3].text
                doc_link = 'https://www.sec.gov' + cells[1].a['href']

                # Obtain HTML for document page
                doc_resp = requests.get(doc_link)
                doc_str = doc_resp.text

                # Find the XBRL link
                xbrl_link = ''
                xbrl_name = ''
                xbrl_date = ''
                soup = BeautifulSoup(doc_str, 'html.parser')
                table_tag = soup.find('table', class_='tableFile', summary='Data Files')
                if table_tag is not None:
                    rows2 = table_tag.find_all('tr')
                    for row2 in rows2:
                        #print(row2)
                        cells = row2.find_all('td')
                        if len(cells) > 3:
                            if 'INS' in cells[3].text or 'XML' in cells[3].text:
                                xbrl_link = 'https://www.sec.gov' + cells[2].a['href']
                                print(xbrl_link)
                                try:
                                    xbrl_splits = xbrl_link.split('/')
                                    xbrl_name = xbrl_splits[len(xbrl_splits)-1]
                                    xbrl_name_splits = xbrl_name.split('-')
                                    xbrl_date = xbrl_name_splits[1][:8]
                                    #print(xbrl_name, xbrl_date)
                                except Exception as error:
                                    #except error:
                                    print(error)
                                    #continue
                                break

                    # Obtain XBRL text from document
                    if xbrl_link != '':
                        #print(xbrl_link)
                        xbrl_resp = requests.get(xbrl_link)
                        xbrl_str = xbrl_resp.text
                        #save_flag = self.save_xbrl(xbrl_name, xbrl_str)
                        #return xbrl_str
                        soup = BeautifulSoup(xbrl_str, 'lxml')
                        tag_list = soup.find_all()

                        rev_flag = 0
                        for tag in tag_list:
                            #print(tag)
                            if option == 'tags':
                                self.get_xbrl_tags(tag)
                            else:
                                self.get_eps(filing_date, xbrl_date, xbrl_name, tag)
                                flag = self.get_rev(filing_date, xbrl_date, xbrl_name, tag)
                                if flag == 1:
                                    rev_flag = flag
                                self.get_shares(filing_date, xbrl_date, xbrl_name, tag)
                                self.get_income(filing_date, xbrl_date, xbrl_name, tag)
                        if rev_flag == 0:
                            logging.info(xbrl_link + ' has no revenues')
                if i % 9 == 0:
                    time.sleep(90.00)
                i = i + 1

    def get_rev(self, filing_date, xbrl_date, xbrl_name, tag):
        #parse xbrl, get eps
        if tag.name == 'us-gaap:revenues' or tag.name == 'us-gaap:revenuefromcontractwithcustomerexcludingassessedtax' or tag.name == 'us-gaap:salesrevenuenet'\
                or tag.name == 'us-gaap:contractsrevenue' or tag.name =='us-gaap:salesrevenuegoodsnet' or tag.name =='us-gaap:revenuefromcontractwithcustomerincludingassessedtax'\
                or tag.name =='us-gaap:revenuemineralsales' or tag.name =='us-gaap:salesrevenueservicesnet' or tag.name =='us-gaap:realestaterevenuenet' or tag.name =='us-gaap:homebuildingrevenue'\
                or tag.name =='us-gaap:revenuesexcludinginterestanddividends' or tag.name =='us-gaap:oilandgasrevenue' or tag.name =='us-gaap:salesrevenuegoodsgross'\
                or tag.name =='us-gaap:investmentbankingrevenue' or tag.name =='us-gaap:investmentadvisorymanagementandadministrativefees' or tag.name =='us-gaap:healthcareorganizationrevenue'\
                or tag.name =='us-gaap:licenseandservicesrevenue' or tag.name == 'us-gaap:healthcareorganizationpatientservicerevenue' or tag.name =='us-gaap:brokeragecommissionsrevenue'\
                or tag.name =='us-gaap:revenuesnetofinterestexpense' or tag.name =='us-gaap:healthcareorganizationrevenuenetofpatientservicerevenueprovisions'\
                or tag.name == 'us-gaap:regulatedandunregulatedoperatingrevenue' or tag.name =='us-gaap:foodandbeveragerevenue':
                #or tag.name == 'us-gaap:netincomeloss':
                #or tag.name =='us-gaap:salesrevenuegoodsnet' or tag.name =='us-gaap:revenuefromcontractwithcustomerincludingassessedtax'\
            rev = tag.text
            ref = tag['contextref']
            ref_result = self.parse_contextref(ref)
            rev_quarter = ref_result['ref_quarter']
            rev_type = ref_result['ref_type']
            #print(ref_result)

            if rev_type != '':
                rev_json = {
                    "symbol":               self.ticker,
                    "cik":                  self.cik,
                    "filing_date":          filing_date,
                    "xbrl_date":            xbrl_date,
                    "xbrl_name":            xbrl_name,
                    "tag":                  tag.name,
                    "ContextRef":       tag['contextref'],
                    "rev":                  rev,
                    "quarter":          rev_quarter,
                    "type":             rev_type
                }
                self.save_rev(rev_json)
                return 1
            else:
                return 0

    def save_rev(self, rev_json):
        print(json.dumps(rev_json))
        if rev_json['rev'] != '' and rev_json['quarter'] != '' and rev_json['type'] != '':
            query = {
                "symbol":           rev_json["symbol"],
                "type":         rev_json["type"],
                "quarter":      rev_json["quarter"]
            }
            mongo_eps = self.mongo_sec_rev.find_one(query)

            if mongo_eps is None:   # save
                print("save")
                self.mongo_sec_rev.insert_one(rev_json)
            else:
                if mongo_eps["xbrl_date"] < rev_json["xbrl_date"]:
                    print("update")
                    self.mongo_sec_rev.delete_one(query)
                    self.mongo_sec_rev.insert_one(rev_json)

    def get_eps(self, filing_date, xbrl_date, xbrl_name, tag):
        #parse xbrl, get eps
        if tag.name == 'us-gaap:earningspersharediluted' or tag.name == 'us-gaap:earningspersharebasicanddiluted' or tag.name == 'us-gaap:incomelossfromcontinuingoperationsperdilutedshare':
            eps = tag.text
            ref = tag['contextref']
            ref_result = self.parse_contextref(ref)
            eps_quarter = ref_result['ref_quarter']
            eps_type = ref_result['ref_type']

            if eps_type != '':
                eps_json = {
                    "symbol":               self.ticker,
                    "cik":                  self.cik,
                    "filing_date":          filing_date,
                    "xbrl_date":            xbrl_date,
                    "xbrl_name":            xbrl_name,
                    "tag":                  tag.name,
                    "ContextRef":       tag['contextref'],
                    "eps":                  eps,
                    "quarter":          eps_quarter,
                    "type":             eps_type
                }
                self.save_eps(eps_json)

    def save_eps(self, eps_json):
        print(json.dumps(eps_json))
        if eps_json['eps'] != '' and eps_json['quarter'] != '' and eps_json['type'] != '':
            query = {
                "symbol": eps_json["symbol"],
                "type": eps_json["type"],
                "quarter": eps_json["quarter"]
            }
            mongo_eps = self.mongo_sec_eps.find_one(query)

            if mongo_eps is None:  # save
                print("save")
                self.mongo_sec_eps.insert_one(eps_json)
            else:
                if mongo_eps["xbrl_date"] < eps_json["xbrl_date"]:
                    print("update")
                    self.mongo_sec_eps.delete_one(query)
                    self.mongo_sec_eps.insert_one(eps_json)

    def get_shares(self, filing_date, xbrl_date, xbrl_name, tag):
        #parse xbrl, get shares
        if tag.name == 'us-gaap:commonstocksharesoutstanding' or tag.name == 'us-gaap:weightedaveragenumberofdilutedsharesoutstanding':
            shares = tag.text
            #shares_quarter = ''
            #shares_type = ''
            ref = tag['contextref']
            ref_result = self.parse_contextref(ref)
            shares_quarter = ref_result['ref_quarter']
            shares_type = ref_result['ref_type']

            if shares_type != '':
                shares_json = {
                    "symbol":               self.ticker,
                    "cik":                  self.cik,
                    "filing_date":          filing_date,
                    "xbrl_date":            xbrl_date,
                    "xbrl_name":            xbrl_name,
                    "tag":                  tag.name,
                    "ContextRef":       tag['contextref'],
                    "shares_outstanding":                  shares,
                    "quarter":          shares_quarter,
                    "type":             shares_type
                }
                self.save_shares(shares_json)

    def save_shares(self, shares_json):
        print(json.dumps(shares_json))
        if shares_json['shares_outstanding'] != '' and shares_json['quarter'] != '' and shares_json['type'] != '':
            query = {
                "symbol": shares_json["symbol"],
                "type": shares_json["type"],
                "quarter": shares_json["quarter"]
            }
            mongo_shares = self.mongo_sec_shares.find_one(query)

            if mongo_shares is None:  # save
                print("save")
                self.mongo_sec_shares.insert_one(shares_json)
            else:
                if mongo_shares["xbrl_date"] < shares_json["xbrl_date"]:
                    print("update")
                    self.mongo_sec_shares.replace_one(query, shares_json, upsert=True)

    def get_income(self, filing_date, xbrl_date, xbrl_name, tag):
        #parse xbrl, get shares
        if tag.name == 'us-gaap:grossprofit' or tag.name == 'us-gaap:operatingincomeloss' or tag.name == 'us-gaap:netincomeloss':
            income_type = ''
            if tag.name == 'us-gaap:grossprofit':
                income_type = 'grossprofit'
            elif tag.name == 'us-gaap:operatingincomeloss':
                income_type = 'operatingincome'
            elif tag.name == 'us-gaap:netincomeloss':
                income_type = 'netincome'

            income = tag.text
            ref = tag['contextref']
            ref_result = self.parse_contextref(ref)
            profit_quarter = ref_result['ref_quarter']
            profit_type = ref_result['ref_type']

            if income_type != '' and profit_type != '':
                income_json = {
                    "symbol":               self.ticker,
                    "cik":                  self.cik,
                    "filing_date":          filing_date,
                    "xbrl_date":            xbrl_date,
                    "xbrl_name":            xbrl_name,
                    "tag":                  tag.name,
                    "ContextRef":           tag['contextref'],
                    "income":           income,
                    "income_type":      income_type,
                    "quarter":          profit_quarter,
                    "type":             profit_type
                }
                self.save_income(income_json)

    def save_income(self, income_json):
        print(json.dumps(income_json))
        if income_json['income'] != '' and income_json['quarter'] != '' and income_json['type'] != '' and income_json['income_type'] != '':
            query = {
                "symbol": income_json["symbol"],
                "income_type": income_json['income_type'],
                "type": income_json["type"],
                "quarter": income_json["quarter"]
            }
            mongo_income = self.mongo_sec_income.find_one(query)

            if mongo_income is None:  # save
                print("save")
                self.mongo_sec_income.insert_one(income_json)
            else:
                if mongo_income["xbrl_date"] < income_json["xbrl_date"]:
                    print("update")
                    self.mongo_sec_income.replace_one(query, income_json, upsert=True)
            # save json

    def get_xbrl_tags(self, tag):
        #parse xbrl, get tags
        if 'us-gaap:' in tag.name:
            t = {'tag_name': tag.name, 'contextref': tag['contextref'], 'text': tag.text[0:min(20, len(tag.text)-1)], 'symbol': self.ticker}
            print(t)
            filter = {'tag_name': tag.name, 'contextref': tag['contextref']}
            self.mongo_sec_tags.replace_one(filter, t, upsert=True)


    def parse_contextref(self, ref):
        try:
            ref_quarter = ''
            ref_type = ''
            if (ref[:2] == 'FD' or ref[:1] == 'D') and (ref[-3:] == 'YTD' or ref[-3:] == 'QTD' or ref[-13:] == 'Quartertodate') and (ref[1:2] != '-'):
                # FD2018Q1QTD
                # D2013Q3QTD
                #D2012Q3Quartertodate
                if ref[:2] == 'FD':
                    ref_quarter = ref[2:8]
                elif ref[:1] == 'D':
                    ref_quarter = ref[1:7]
                if ref[-5:] == 'Q4YTD':
                    ref_type = 'Year'
                if ref[-3:] == 'QTD' or ref[-5:] == 'Q1YTD' or ref[-13:] == 'Quartertodate':
                    ref_type = 'Quarter'
            elif (ref[:2] == 'D-') and (ref[8:11] == 'YTD' or ref[8:11] == 'QTD'):
                # D-Q22013QTD
                ref_quarter = ref[4:8] + ref[2:4]
                if ref[6:11] == 'Q4YTD':
                    ref_type = 'Year'
                if ref[8:11] == 'QTD' or ref[6:11] == 'Q1YTD':
                    ref_type = 'Quarter'
            elif (ref[:2] == 'FD' or ref[:1] == 'D') and (
                    (ref[8:11] == 'YTD' or ref[8:11] == 'QTD') and 'gaap_StatementClass' in ref):
                # FD2018Q1QTD_us - gaap_StatementClassOfStockAxis_us - gaap_CommonClassAMember
                if ref[:2] == 'FD':
                    ref_quarter = ref[2:8]
                elif ref[:1] == 'D':
                    ref_quarter = ref[1:7]
                if ref[6:11] == 'Q4YTD':
                    ref_type = 'Year'
                if ref[8:11] == 'QTD' or ref[6:11] == 'Q1YTD':
                    ref_type = 'Quarter'
            elif 'eof_PE51057' in ref and ('_365_' in ref or '_366_' in ref or '_364_' in ref or '_371_' in ref):
                # eol_PE51057 - --1210 - K0012_STD_365_20101231_0
                ref_splits = ref.split('_')
                ref_year = ref_splits[len(ref_splits) - 2][0:4]
                ref_month = ref_splits[len(ref_splits) - 2][4:6]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
                    ref_type = 'Year'
            elif '_90_' in ref or '_91_' in ref or '_92_' in ref:
                # eol_PE51057 - --1210 - K0012_STD_90_20110331_0
                # eol_PE51057 - --1210 - K0012_STD_91_20110630_0
                # eol_PE51057 - --1210 - K0012_STD_92_20121231_0
                if '_90_' in ref:
                    delimiter = '_90_'
                if '_91_' in ref:
                    delimiter = '_91_'
                if '_92_' in ref:
                    delimiter = '_92_'

                date_pos = ref.find(delimiter)
                ref_year = ref[date_pos + 4:date_pos + 8]
                ref_month = ref[date_pos + 8: date_pos + 10]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
                    if q == 'Q4':
                        ref_type = 'Year'
                    else:
                        ref_type = 'Quarter'
            elif ref[:2] == 'C_' and len(ref) <= 30:     #re.match('\d+$', ref):
                # C_0001318605_20180101_20181231 - TSLA
                # C_0001437352_20190101_20190331
                ref_splits = ref.split('_')
                startYear = ref_splits[len(ref_splits) - 2][0:4]
                startDate = ref_splits[len(ref_splits) - 2][4:8]
                endYear = ref_splits[len(ref_splits) - 1][0:4]
                endDate = ref_splits[len(ref_splits) - 1][4:8]
                diff = (int(endYear) - int(startYear)) * 1200 + int(endDate) - int(startDate)
                if diff < 400:
                    ref_type = 'Quarter'
                elif diff > 1000:
                    ref_type = 'Year'

                ref_year = ref_splits[len(ref_splits) - 1][0:4]
                ref_month = ref_splits[len(ref_splits) - 1][4:6]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
                #print(startYear, startDate, endYear, endDate, ref_type, ref_quarter)
            elif re.match('c\d+to\d+$', ref):
                # c20180204to20190202 - OLLI
                startYear = ref[1:9][0:4]
                startDate = ref[1:9][4:8]
                endYear = ref[11:19][0:4]
                endDate = ref[11:19][4:8]
                diff = (int(endYear) - int(startYear)) * 1200 + int(endDate) - int(startDate)
                if diff < 400:
                    ref_type = 'Quarter'
                elif diff > 1000:
                    ref_type = 'Year'

                ref_year = ref[11:15]
                ref_month = ref[15:17]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('FROM_*\w+\d+$', ref):  # elif re.match('^FROM_[a-zA-Z]', ref):
                # FROM_Jan01_2012_TO_Dec31_2012 - ANTM old
                # FROM_Jan01_2012_TO_Dec31_2012_dei_LegalEntityAxis_WellpointIncMember
                # FROM_Jan01_2012_TO_Mar31_2012
                ref_splits = ref.split('_')
                startYear = ref_splits[2][0:4]
                startMonth = self.get_month_str(ref_splits[1][0:3])
                endYear = ref_splits[5][0:4]
                endMonth = self.get_month_str(ref_splits[4][0:3])
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('c\d+_From\w+To\w+\d+$', ref):
                # c2_From1Jan2016To31Mar2016
                # c0_From31Mar2012To30Jun2012
                # c8_From1Apr2011To31Mar2012_RetainedEarningsMember
                # c1_From4Jul2011To1Jul2012
                ref_splits = ref.split('_')
                toPos = ref_splits[1].find("To")
                startYear = ref_splits[1][toPos - 4:toPos]
                startMonth = self.get_month_str(ref_splits[1][toPos - 7:toPos - 4])
                endYear = ref_splits[1][len(ref_splits[1]) - 4:len(ref_splits[1])]
                endMonth = self.get_month_str(ref_splits[1][len(ref_splits[1]) - 7:len(ref_splits[1]) - 4])
                # endYear = ref[toPos+7:toPos+11]
                # endMonth = self.get_month_str(ref[toPos+4:toPos+7])
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif ref[:2] == 'd_' and len(ref) < 25:
                # d_2018-12-30_2019-03-30
                # d_2016-01-01_2016-12-31
                startYear = ref[2:6]
                startMonth = ref[7:9]
                endYear = ref[13:17]
                endMonth = ref[18:20]
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('Duration_*.+o*\w+\d+', ref):
                # Duration_1_1_2016_To_12_31_2016 - SERV
                # Duration_1_1_2009_To_3_31_20092
                # Duration_1_1_2016_To_12_31_2016
                ref_splits = ref.split('_')
                startYear = ref_splits[3][0:4]
                startMonth = ref_splits[1]
                endYear = ref_splits[7][0:4]
                endMonth = ref_splits[5]
                # print(startYear, startMonth, endYear, endMonth)
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('From\d.+\d+$', ref):
                # From2018-01-01to2018-12-31
                startYear = ref[4:8]
                startMonth = ref[9:11]
                endYear = ref[16:20]
                endMonth = ref[21:23]
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('P\d+.+\d+$', ref):
                # P01_01_2018To12_30_2018
                # print(ref)
                startYear = ref[7:11]
                startMonth = ref[1:3]
                endYear = ref[19:23]
                endMonth = ref[13:15]
                diff = (int(endYear) - int(startYear)) * 12 + int(endMonth) - int(startMonth)
                if diff < 4:
                    ref_type = 'Quarter'
                elif diff > 10:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif re.match('eol_PE7235', ref) or re.match('eol_PE919', ref) or re.match('eol_PE7353', ref) or re.match('eol_PE', ref):
                # eol_PE7235----0910-Q0007_STD_Inst_20081231_0 for commonstocksharesoutstanding
                # eol_PE7235----0910-K0010_STD_365_20071231_0 for grossprofit
                # eol_PE919-----0910-K0013_STD_366_20081231_0 for https://www.sec.gov/Archives/edgar/data/933974/000119312512347789/brks-20120630.xml
                # eol_PE7353----1210-K0011_STD_365_20100930_0 for https://www.sec.gov/Archives/edgar/data/933974/000119312512478743/brks-20120930.xml
                # eol_PE9387----0910-Q0004_STD_p3m_20080930_0 for https://www.sec.gov/Archives/edgar/data/76334/000119312509221583/ph-20090930.xml
                ref_splits = ref.split('_')
                ref_year = ref_splits[4][0:4]
                ref_month = ref_splits[4][4:6]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
                    if q == 'Q4':
                        ref_type = 'Year'
                    else:
                        ref_type = 'Quarter'
            elif re.match('FI', ref):
                # FI2018Q1 for commonstocksharesoutstanding
                ref_type = 'Quarter'
                ref_quarter = ref[2:8]
            elif re.search('_D\d.+\d$', ref):     #re.match('\d+$', ref):
                #print(ref)
                #idd5da4ae8ae445dcb33767935e12a742_D20190331-20190629  for AMD
                #ic28a1bbbc6494e45a2ce0eb2177edbf3_D20190701-20190930
                startYear = ref[-17:-13]
                startDate = ref[-13:-9]
                endYear = ref[-8:-4]
                endDate = ref[-4:]
                diff = (int(endYear) - int(startYear)) * 1200 + int(endDate) - int(startDate)
                if diff < 400:
                    ref_type = 'Quarter'
                elif diff > 1000:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = ref[-4:-2]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
                #print(startYear, startDate, endYear, endDate, ref_type, ref_quarter)
            elif re.match('D\d+Q\d$', ref):
                # D2013Q3 for ABBV
                ref_type = 'Quarter'
                ref_quarter = ref[-6:]
            elif re.match('D\d+$', ref):
                #D2013 for ABBV
                ref_type = 'Year'
                ref_quarter = ref[-4:] + 'Q4'
            elif re.match('TwelveMonthsEnded_\w{9}$', ref):
                # TwelveMonthsEnded_31Dec2008 for aimt for https://www.sec.gov/Archives/edgar/data/35214/000119312512086029/foe-20111231.xml
                ref_type = 'Year'
                ref_quarter = ref[-4:] + 'Q4'
            elif re.match('ThreeMonthsEnded_\w{9}$', ref) or re.match('ThreeMonthsEnded_\w{10}$', ref):
                #ThreeMonthsEnded_30Sept2011
                # ThreeMonthsEnded_03Apr2010 for aimt, https://www.sec.gov/Archives/edgar/data/37785/000119312509165435/fmc-20090630.xml
                ref_type = 'Quarter'
                ref_year = ref[-4:]
                ref_splits = ref.split('_')
                ref_month = ref_splits[1][2:5]
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q
            elif ref[:1] == 'Y' and ref[-2:-1] == 'Q':
                # Y12Q3 for https://www.sec.gov/Archives/edgar/data/1058828/000105882812000055/hdii-20120930.xml
                # Y11Q4 for https://www.sec.gov/Archives/edgar/data/1058828/000105882813000010/hdii-20121231.xml,  type=Year
                # Y12Q1 for https://www.sec.gov/Archives/edgar/data/1058828/000105882812000021/hdii-20120331.xml type=quarter
                y = ref[1:3]
                if int(y) < 50:
                    ref_year = '20' + y
                else:
                    ref_year = '19' + y
                ref_quarter = ref[-2:]
                if ref_quarter == 'Q4':
                    ref_type = 'Year'
                else:
                    ref_type = 'Quarter'
                ref_quarter = ref_year + ref_quarter
                #Pri_3mos_20090927 for https://www.sec.gov/Archives/edgar/data/901491/000115752310006540/pzza-20100a26.xml
                #Cur_3mos_20100926 for https://www.sec.gov/Archives/edgar/data/901491/000115752310006540/pzza-20100a26.xml
                #D120701_121231 for https://www.sec.gov/Archives/edgar/data/1058828/000105882813000010/hdii-20121231.xml
                #Context_3ME_01_Jul_2013T00_00_00_TO_30_Sep_2013T00_00_00 for https://www.sec.gov/Archives/edgar/data/1425287/000101376214001326/ampd-20140930.xml
                #Cur_12mos_20101231 for https://www.sec.gov/Archives/edgar/data/1067983/000119312511048914/brka-20101231.xml
                #Context_FYE_31-Mar-2012 for https://www.sec.gov/Archives/edgar/data/1311538/000114420412037336/rox-20120331.xml type = year
                #Context_3ME_31-Dec-2012 for https://www.sec.gov/Archives/edgar/data/1311538/000114420413009303/rox-20121231.xml type = quarter
                #Twelve_Months_12_31_2013 for https://www.sec.gov/Archives/edgar/data/1381197/000104746914001697/ibkr-20131231.xml
                #YearEnded_31Dec2011 for https://www.sec.gov/Archives/edgar/data/944809/000119312512117417/opk-20111231.xml
                #Dec31_2007 for https://www.sec.gov/Archives/edgar/data/89800/000095012310016198/shw-20091231.xml type = year
                #from-2013-01-01-to-2013-12-31.7277.0.0.0.0.0.0.0 for https://www.sec.gov/Archives/edgar/data/95029/000117494714000046/rgr-20131231.xml type=year
                #D2015-01-01_To_2015-12-31 for https://www.sec.gov/Archives/edgar/data/95029/000117494716002118/rgr-20151231.xml type = year
                #D-FY2013 for https://www.sec.gov/Archives/edgar/data/1341439/000119312515235239/orcl-20150531.xml type = year

            #else
            #    logging.info(ref)

            result = {
                "ref_quarter": ref_quarter,
                "ref_type": ref_type
            }
            return result
        except Exception as error:
            print(error)
            print(traceback.format_exc())
            # logging.info(ref, error)
            return {
                "ref_quarter": '',
                "ref_type": ''
            }

if __name__ == '__main__':
    today = date.today()
    logging.basicConfig(filename='test_sec.log', level=logging.INFO)
    logging.info(today)

    mongo = MongoExplorer()
    mongoDB = mongo.mongoDB
    mongo_col = mongoDB['etrade_companies']
    #mongo_query = {"Yahoo_Symbol": 'AMZN'}
    #mongo_query = {"Yahoo_Symbol": 'TSLA'}
    #mongo_query = {"Yahoo_Symbol": 'AMD'}
    #mongo_query = {"Yahoo_Symbol": 'SAM'}
    #mongo_query = {"Yahoo_Symbol": 'BRKS'}
    #mongo_query = {"Yahoo_Symbol": 'FOE'}
    #mongo_query = {"Yahoo_Symbol": 'PKG'}
    #mongo_query = {"Yahoo_Symbol": 'ZNGA'}
    #mongo_query = {"Yahoo_Symbol": 'VRSK'}
    #mongo_query = {"Yahoo_Symbol": 'TPH'}
    #mongo_query = {"Yahoo_Symbol": 'TOL'}
    #mongo_query = {"Yahoo_Symbol": 'TIF'}
    #mongo_query = {"Yahoo_Symbol": 'HZNP'}
    #mongo_query = {"Yahoo_Symbol": 'HDII'}
    #mongo_query = {"Yahoo_Symbol": 'FIS'}
    mongo_query = {}
    coms = mongo_col.find(mongo_query, no_cursor_timeout=True)
    mongo_col2 = mongoDB['cik_ticker']

    #types = ['10-Q']
    types = ['10-K', '10-Q']
    dateb = '21200101'          #'20200101'
    count = 100

    i = 1
    restartIndex = 4252       #8076    #3110   7096       #6790    # 4262 3597
    stopIndex = 6636000    #1284000
    #restartIndex = 1284
    #stopIndex = 1284

    for x in coms:
        if i > stopIndex:
            break

        if i >= restartIndex:
            #check g score
            #print(i, x['Yahoo_Symbol'])

            #AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")
            #g20 = StockScore({"AAOD": AAOD, "symbol": x['Symbol']})
            #try:
            #    score = g20.run()
            #except:
            #    score = None

            #if score is not None and score['Recommendation'] != 'n':
            mongo_query2 = {"Ticker": x['Symbol'], "Status": {"$ne": "Inactive"}}
            mongo_cik = mongo_col2.find_one(mongo_query2)
            #eps_list = []

            if mongo_cik is None:
                cik = ''
            else:
                cik = mongo_cik['CIK']

            for type in types:
                sec = SECExplorer(x['Yahoo_Symbol'], cik, type, dateb, count)

                if cik == '':
                    cik_json = sec.get_cik()
                    if cik_json is not None and cik_json['CIK'] != '':
                        mongo_col2.insert_one(cik_json)
                    else:
                        #logging.info(x['Symbol'] + " - No CIK")
                        break
                print(i, type + "  " + sec.ticker + "    " + sec.cik)
                try:
                    #sec.get_sbrl('tags')
                    sec.get_sbrl()

                    if i % 5 == 0:
                        time.sleep(60.00)
                except:
                    continue
            #else:
            #    if score is not None:
            #        #print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'], 'Score:' + str(score['Score']))
            #        print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'])
            #    else:
            #        print(i, x['Yahoo_Symbol'], 'score is None')
        i = i + 1

'''
            AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")
            g20 = StockScore({"AAOD": AAOD, "symbol": x['Symbol']})
            try:
                score = g20.run()
            except:
                score = None

            if score is not None and score['Recommendation'] != 'n':
                mongo_query2 = {"Ticker": x['Symbol'], "Status": {"$ne": "Inactive"}}
                mongo_cik = mongo_col2.find_one(mongo_query2)
                eps_list = []

                if mongo_cik is None:
                    cik = ''
                else:
                    cik = mongo_cik['CIK']

                for type in types:
                    sec = SECExplorer(x['Yahoo_Symbol'], cik, type, dateb, count)

                    if cik == '':
                        cik_json = sec.get_cik()
                        if cik_json is not None and cik_json['CIK'] != '':
                            mongo_col2.insert_one(cik_json)
                        else:
                            #logging.info(x['Symbol'] + " - No CIK")
                            break
                    print(i, type + "  " + sec.ticker + "    " + sec.cik)
                    #sec.get_sbrl('tags')
                    sec.get_sbrl()
            else:
                if score is not None:
                    #print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'], 'Score:' + str(score['Score']))
                    print(i, x['Yahoo_Symbol'], 'Recommendation:n', 'Reason:' + score['Reason'])
                else:
                    print(i, x['Yahoo_Symbol'], 'score is None')
        i = i + 1

        AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")

        q = QuoteExplorer()
        q.get_quotes(x['Yahoo_Symbol'], AAOD)

        etrade = EtradeExplorer()
        etrade.get_fundamentals(x['Yahoo_Symbol'])
        etrade.browser.close()

        #StockScore(x['Yahoo_Symbol'])
        g20 = StockScore({"AAOD": AAOD, "symbol": x['Yahoo_Symbol']})
        # g20.averagePE("2019-07-01")
        # print(json.dumps(g20.PEScore(), indent=4))
        # print(g20.capScore())
        g20.run()
        print(json.dumps(g20.result, indent=4))

        StockPlotter(x['Yahoo_Symbol'])

            elif re.match('\w+-\d{2}-\d{4}_\w+-\d{2}-\d{4}$', ref):
                # January-01-2009_December-31-2009 for
                # Oct-01-2010_Apr-02-2011 for
                ref_splits = ref.split('_')
                starts = ref_splits.split('-')
                startYear = starts[2]
                startMonth = self.get_month_str(starts[0])
                startDate = starts[1]
                ends = ref_splits.split('-')
                endYear = ends[2]
                endMonth = self.get_month_str(ends[0])
                endDate = ends[1]
                diff = (int(endYear) - int(startYear)) * 365 + (int(endMonth) - int(startMonth)) * 30 + int(endDate) - int(startDate)
                if diff < 60:
                    ref_type = 'Quarter'
                elif diff > 300:
                    ref_type = 'Year'

                ref_year = endYear
                ref_month = endMonth
                q = self.get_quarter(ref_month)
                if q != '':
                    ref_quarter = ref_year + q

'''
