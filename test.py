import time
#from SECEdgar.crawler import SecCrawler
import random
import platform
from stockstats import StockDataFrame as Sdf
from test_stockstats_v2 import StockStats
import pandas as pd

def get_filings():
    t1 = time.time()
    SECpath = 'C:\\Users\\hong\\OneDrive\\Stock\\'
    seccrawler = SecCrawler(SECpath)    # create object

    companyCode = 'SEC'    # company code for apple
    #cik = '0000320193'      # cik code for apple
    cik = 'ayx'      # cik code for apple
    date = '20010101'       # date from which filings should be downloaded
    count = '10'            # no of filings

    #seccrawler.filing_10Q(companyCode, cik, date, count)
    seccrawler.filing_10K(companyCode, cik, date, count)
    #seccrawler.filing_8K(companyCode, cik, date, count)
    #seccrawler.filing_13F(companyCode, cik, date, count)

    t2 = time.time()
    print("Total Time taken: {0}".format(t2-t1))

if __name__ == '__main__':
    #get_filings()
    #print(random.uniform(1, -1))
    #print(random.uniform(0, 1))

    print(platform.node())


    #a = 0
    #if not a < 1: print('None < 1 is not true')


    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

    ss = StockStats('TSLA')
    ss.stock = df.copy()
    ss.stock = Sdf.retype(ss.stock)
    ss.macd()
    print(ss.stock)
    print(ss.stock.index)
