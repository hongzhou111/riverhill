from bs4 import BeautifulSoup
import requests
#import sys
import os
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
import pymongo
import json
import re
#import matplotlib.pyplot as plt
#import pandas as pd
from test_plot import StockPlotter
from test_g20 import StockScore
from test_yahoo import QuoteExplorer
from test_etrade import EtradeExplorer
from test_mongo import MongoExplorer
from test_sec import SECExplorer

#class SECExplorer:
class Test2:
    def __init__(self, ticker, cik, type, dateb, count):
        self.ticker = ticker
        self.cik = cik
        self.type = type
        self.dateb = dateb
        self.count = count

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
        if ref_month == '03' or ref_month == '01' or ref_month == '02' or ref_month == '3' or ref_month == '1' or ref_month == '2' or ref_month.upper() == 'MAR' or ref_month.upper() == 'JAN' or ref_month.upper == 'FEB':
            q = 'Q1'
        elif ref_month == '06' or ref_month == '04' or ref_month == '05' or ref_month == '6' or ref_month == '4' or ref_month == '5' or ref_month.upper() == 'APR' or ref_month.upper() == 'MAY' or ref_month.upper == 'JUN':
            q = 'Q2'
        elif ref_month == '09' or ref_month == '07' or ref_month == '08' or ref_month == '9' or ref_month == '7' or ref_month == '8' or ref_month.upper() == 'SEP' or ref_month.upper() == 'JAL' or ref_month.upper == 'AUG':
            q = 'Q3'
        elif ref_month == '12' or ref_month == '10' or ref_month == '11' or ref_month.upper() == 'DEC' or ref_month.upper() == 'OCT' or ref_month.upper == 'NOV':
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

    def get_sbrl(self):
        eps_json_list = []
        rev_json_list = []

        # Obtain HTML for search page
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type={}&dateb={}&count={}"
        edgar_resp = requests.get(base_url.format(self.cik, self.type, self.dateb, self.count))
        edgar_str = edgar_resp.text

        # Find the document link
        soup = BeautifulSoup(edgar_str, 'html.parser')
        table_tag = soup.find('table', class_='tableFile2')
        rows = table_tag.find_all('tr')
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
                    rows = table_tag.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) > 3:
                            if 'INS' in cells[3].text or 'XML' in cells[3].text:
                                xbrl_link = 'https://www.sec.gov' + cells[2].a['href']
                                try:
                                    xbrl_splits = xbrl_link.split('/')
                                    xbrl_name = xbrl_splits[len(xbrl_splits)-1]
                                    xbrl_name_splits = xbrl_name.split('-')
                                    xbrl_date = xbrl_name_splits[1][:8]
                                except:
                                    continue
                                break

                    # Obtain XBRL text from document
                    if xbrl_link != '':
                        #print(xbrl_link)
                        xbrl_resp = requests.get(xbrl_link)
                        xbrl_str = xbrl_resp.text
                        #save_flag = self.save_xbrl(xbrl_name, xbrl_str)
                        #return xbrl_str
                        eps_json_list.extend(self.get_eps(filing_date, xbrl_date, xbrl_name, xbrl_str))
                        rev_json_list.extend(self.get_rev(filing_date, xbrl_date, xbrl_name, xbrl_str))
        self.eps_json_list = eps_json_list
        self.rev_json_list = rev_json_list

    def get_rev(self, filing_date, xbrl_date, xbrl_name, xbrl_str):
        rev_json_list = []

        #parse xbrl, get eps
        soup = BeautifulSoup(xbrl_str, 'lxml')
        tag_list = soup.find_all()
        for tag in tag_list:
            if tag.name == 'us-gaap:revenues' or tag.name == 'us-gaap:revenuefromcontractwithcustomerexcludingassessedtax' or tag.name == 'us-gaap:salesrevenuenet'\
                    or tag.name =='us-gaap:salesrevenuegoodsnet' or tag.name =='us-gaap:revenuefromcontractwithcustomerincludingassessedtax'\
                    or tag.name == 'us-gaap:contractsrevenue':                      #or tag.name == 'us-gaap:netincomeloss':
                rev_quarter = ''
                rev_type = ''
                rev = tag.text
                ref = tag['contextref']
                ref_result = self.parse_contextref(ref)
                rev_quarter = ref_result['ref_quarter']
                rev_type = ref_result['ref_type']

                if rev_type != '':
                    rev_json = {
                        "symbol":               self.ticker,
                        "cik":                  self.cik,
                        "filing_date":          filing_date,
                        "xbrl_date":            xbrl_date,
                        "xbrl_name":            xbrl_name,
                        "rev_ContextRef":       tag['contextref'],
                        "rev":                  rev,
                        "rev_quarter":          rev_quarter,
                        "rev_type":             rev_type
                    }
                    rev_json_list.append(rev_json)
                else:
                    #logging.info(xbrl_name + ",  " + str(tag))
                    continue
        return rev_json_list

    def parse_contextref(self, ref):
        try:
            ref_quarter = ''
            ref_type = ''
            if (ref[:2] == 'FD' or ref[:1] == 'D') and (ref[-3:] == 'YTD' or ref[-3:] == 'QTD') and (ref[1:2] != '-'):
                # FD2018Q1QTD
                # D2013Q3QTD
                if ref[:2] == 'FD':
                    ref_quarter = ref[2:8]
                elif ref[:1] == 'D':
                    ref_quarter = ref[1:7]
                if ref[-5:] == 'Q4YTD':
                    ref_type = 'Year'
                if ref[-3:] == 'QTD' or ref[-5:] == 'Q1YTD':
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
            elif '_365_' in ref or '_366_' in ref or '_364_' in ref or '_371_' in ref:
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
                    ref_type = 'Quarter'
            elif ref[:2] == 'C_\d$':
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
            elif re.match('^c\d+to\d+$', ref):
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
            elif re.match('^FROM_*\w+\d+$', ref):                #elif re.match('^FROM_[a-zA-Z]', ref):
                # FROM_Jan01_2012_TO_Dec31_2012 - ANTM old
                # FROM_Jan01_2012_TO_Dec31_2012_dei_LegalEntityAxis_WellpointIncMember
                #FROM_Jan01_2012_TO_Mar31_2012
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
            elif re.match('^c\d_From\w+To\w+\d+$', ref):
                # c2_From1Jan2016To31Mar2016
                # c0_From31Mar2012To30Jun2012
                # c8_From1Apr2011To31Mar2012_RetainedEarningsMember
                # c1_From4Jul2011To1Jul2012
                ref_splits = ref.split('_')
                toPos = ref_splits[1].find("To")
                startYear = ref_splits[1][toPos-4:toPos]
                startMonth = self.get_month_str(ref_splits[1][toPos-7:toPos-4])
                endYear = ref_splits[1][len(ref_splits[1])-4:len(ref_splits[1])]
                endMonth = self.get_month_str(ref_splits[1][len(ref_splits[1])-7:len(ref_splits[1])-4])
                #endYear = ref[toPos+7:toPos+11]
                #endMonth = self.get_month_str(ref[toPos+4:toPos+7])
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
            elif re.match('^Duration_*.+o*\w+\d+$', ref):
                # Duration_1_1_2016_To_12_31_2016 - SERV
                # Duration_1_1_2009_To_3_31_20092
                # Duration_1_1_2016_To_12_31_2016
                ref_splits = ref.split('_')
                startYear = ref_splits[3][0:4]
                startMonth = ref_splits[1]
                endYear = ref_splits[7][0:4]
                endMonth = ref_splits[5]
                #print(startYear, startMonth, endYear, endMonth)
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
            elif re.match('^From\d.+\d+$', ref):
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
            elif re.match('^P\d+.+\d+$', ref):
                #P01_01_2018To12_30_2018
                #print(ref)
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

            result = {
                "ref_quarter":      ref_quarter,
                "ref_type":         ref_type
            }
            return result
        except Exception as error:
            logging.info(ref, error)
            return {
                "ref_quarter": '',
                "ref_type": ''
            }

    def save_rev(self, col, rev_json):
        print(json.dumps(rev_json))
        if rev_json['rev'] != '' and rev_json['rev_quarter'] != '' and rev_json['rev_type'] != '':
            query = {
                "symbol":           rev_json["symbol"],
                "rev_type":         rev_json["rev_type"],
                "rev_quarter":      rev_json["rev_quarter"]
            }
            mongo_eps = col.find_one(query)

            if mongo_eps is None:   # save
                print("save")
                col.insert_one(rev_json)
            else:
                if mongo_eps["xbrl_date"] <= rev_json["xbrl_date"]:
                    print("update")
                    col.delete_one(query)
                    col.insert_one(rev_json)
            #save json

    def get_eps(self, filing_date, xbrl_date, xbrl_name, xbrl_str):
        eps_json_list = []

        #parse xbrl, get eps
        soup = BeautifulSoup(xbrl_str, 'lxml')
        tag_list = soup.find_all()
        for tag in tag_list:
            if tag.name == 'us-gaap:earningspersharediluted' or tag.name == 'us-gaap:earningspersharebasicanddiluted' or tag.name == 'us-gaap:incomelossfromcontinuingoperationsperdilutedshare':
                eps = tag.text
                eps_quarter = ''
                eps_type = ''
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
                        "eps_ContextRef":       tag['contextref'],
                        "eps":                  eps,
                        "eps_quarter":          eps_quarter,
                        "eps_type":             eps_type
                    }
                    eps_json_list.append(eps_json)
                else:
                    #logging.info(xbrl_name + ",  " + str(tag))
                    continue
        return eps_json_list

    def save_eps(self, col, eps_json):
        print(json.dumps(eps_json))
        if eps_json['eps'] != '' and eps_json['eps_quarter'] != '' and eps_json['eps_type'] != '':
            query = {
                "symbol": eps_json["symbol"],
                "eps_type": eps_json["eps_type"],
                "eps_quarter": eps_json["eps_quarter"]
            }
            mongo_eps = col.find_one(query)

            if mongo_eps is None:  # save
                print("save")
                col.insert_one(eps_json)
            else:
                if mongo_eps["xbrl_date"] <= eps_json["xbrl_date"]:
                    print("update")
                    col.delete_one(query)
                    col.insert_one(eps_json)
            # save json

if __name__ == '__main__':
    today = date.today()
    logging.basicConfig(filename='test.log', level=logging.INFO)
    logging.info(today)
    AAOD = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d")

    ss = ['OKTA', 'PLUG', 'KNDI', 'LI', 'WKHS', 'NKLA', 'NIO', 'EVBG', 'PAYC', 'TSLA', 'FOE', 'AMD', 'AMZN', 'TWLO', 'BIIB', 'MSCI', 'SHOP', 'NBLX', 'INFY', 'CPRI', 'BIIB', 'REGN', 'CTSH', 'AYI', 'MA', 'GE', 'GS', 'COST','ANTM', 'FB', 'TCEHY', 'AAPL', 'BABA', 'SQ', 'MDB', 'ATVI', 'CRM', 'ISRG', 'AYX', 'TTD', 'LYFT', 'GOOGL', 'EVBG', 'LSXMB', 'SPY', 'MSFT']
    mongo = MongoExplorer()
    mongoDB = mongo.mongoDB
    mongo_col = mongoDB['etrade_companies']

    #mongo_query = {"Yahoo_Symbol": 'ANTM'}
    #mongo_query = {"Yahoo_Symbol": ss[len(ss)-1]}
    mongo_query = {"Yahoo_Symbol": ss[0]}

    coms = mongo_col.find(mongo_query)
    mongo_col2 = mongoDB['cik_ticker']
    mongo_col3 = mongoDB['sec_eps']
    mongo_col4 = mongoDB['sec_rev']

    types = ['10-K', '10-Q']
    dateb = '20300101'
    count = 100

    for x in coms:
        mongo_query2 = {"Ticker": x['Symbol'], "Status": {"$ne": "Inactive"}}
        mongo_cik = mongo_col2.find_one(mongo_query2)
        eps_list = []

        if mongo_cik is None:
            cik = ''
        else:
            cik = mongo_cik['CIK']

        for type in types:
            try:
                sec = SECExplorer(x['Yahoo_Symbol'], cik, type, dateb, count)

                if cik == '':
                    cik_json = sec.get_cik()
                    if cik_json is not None and cik_json['CIK'] != '':
                        mongo_col2.insert_one(cik_json)
                    else:
                        logging.info(x['Symbol'] + " - No CIK")
                        break
                print(type + "  " + sec.ticker + "    " + sec.cik)
                sec.get_sbrl()
                for y in sec.eps_json_list:
                    #print(y)
                    sec.save_eps(mongo_col3, y)

                for r in sec.rev_json_list:
                    #print(r)
                    sec.save_rev(mongo_col4, r)
            except:
                continue

        q = QuoteExplorer()
        q.get_quotes(x['Yahoo_Symbol'], AAOD)

        etrade = EtradeExplorer()
        etrade.get_fundamentals(x['Yahoo_Symbol'])
        etrade.browser.close()

        #StockScore(x['Yahoo_Symbol'])
        g20 = StockScore({"AAOD": AAOD, "symbol": x['Symbol']})
        # g20.averagePE("2019-07-01")
        # print(json.dumps(g20.PEScore(), indent=4))
        # print(g20.capScore())
        g20.run()
        #g20.save_g20()
        print(json.dumps(g20.result, indent=4))

        StockPlotter(x['Yahoo_Symbol'])
