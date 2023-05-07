# Import Matplotlib's `pyplot` module as `plt`
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import sys
import os
import logging
from datetime import date
import pymongo
import json
import re
import pandas as pd

from test_mongo import MongoExplorer

class StockPlotter:
    def __init__(self, ticker, print_flag=True):
        self.ticker = ticker

        mongo = MongoExplorer()
        mongoDB = mongo.mongoDB
        mongo_col = mongoDB['etrade_companies']
        mongo_query = {"Symbol": ticker}
        coms = mongo_col.find(mongo_query)
        mongo_col1 = mongoDB['sec_eps']
        mongo_col2 = mongoDB['sec_rev']

        type1 = 'Quarter'
        type2 = 'Year'

        for x in coms:
            f = plt.figure(0, figsize=(12,10))

            mongo_query4 = {"symbol": x['Yahoo_Symbol'], "type": type1}
            quotes4 = mongo_col2.find(mongo_query4).sort("quarter", 1)
            if mongo_col2.count_documents(mongo_query4) > 0:
                df4 = pd.DataFrame(list(quotes4))
                df4['rev'] = df4['rev'].astype(float)
                #plt.subplot(321)
                ax4 = plt.subplot2grid((5, 2), (0, 0))
                g4 = df4['rev'].plot(grid=True, color='r', xticks=df4.index)
                g4.set_title(ticker + ' Quarterly Revenue', fontsize=6)
                g4.set_xticklabels(df4['quarter'], rotation=90, fontsize=6)

            if print_flag is True:
                quotes4_print = mongo_col2.find(mongo_query4).sort("quarter", 1)
                print('Quarter Rev')
                for q4 in quotes4_print:
                    print(q4['quarter'], q4['rev'])

            mongo_query5 = {"symbol": x['Yahoo_Symbol'], "type": type2}
            quotes5 = mongo_col2.find(mongo_query5).sort("quarter", 1)
            if mongo_col2.count_documents(mongo_query5) > 0:
                df5 = pd.DataFrame(list(quotes5))
                df5['rev'] = df5['rev'].astype(float)
                #plt.subplot(322)
                ax5 = plt.subplot2grid((5, 2), (0, 1))
                g5 = df5['rev'].plot(grid=True, color='r', xticks=df5.index)
                g5.set_title(ticker + ' Yearly Revenue', fontsize=6)
                g5.set_xticklabels(df5['quarter'], rotation=90, fontsize=6)

            if print_flag is True:
                quotes5_print = mongo_col2.find(mongo_query5).sort("quarter", 1)
                print('Year Rev')
                for q5 in quotes5_print:
                    print(q5['quarter'], q5['rev'])

            mongo_query1 = {"symbol": x['Yahoo_Symbol'], "type": type1}
            quotes1 = mongo_col1.find(mongo_query1).sort("quarter", 1)
            if mongo_col1.count_documents(mongo_query1) > 0:
                df1 = pd.DataFrame(list(quotes1))
                df1['eps'] = df1['eps'].astype(float)
                #plt.subplot(323)
                ax1 = plt.subplot2grid((5, 2), (1, 0))
                g1 = df1['eps'].plot(grid=True, color='r', xticks=df1.index)
                g1.set_title(ticker + ' Quarterly Earning', fontsize=6)
                g1.set_xticklabels(df1['quarter'], rotation=90, fontsize=6)

            if print_flag is True:
                quotes1_print = mongo_col1.find(mongo_query1).sort("quarter", 1)
                print('Quarter EPS')
                for q1 in quotes1_print:
                    print(q1['quarter'], q1['eps'])

            mongo_query2 = {"symbol": x['Yahoo_Symbol'], "type": type2}
            quotes2 = mongo_col1.find(mongo_query2).sort("quarter", 1)
            if mongo_col1.count_documents(mongo_query2) > 0:
                df2 = pd.DataFrame(list(quotes2))
                df2['eps'] = df2['eps'].astype(float)
                #plt.subplot(324)
                ax2 = plt.subplot2grid((5, 2), (1, 1))
                g2 = df2['eps'].plot(grid=True, color='r', xticks=df2.index)
                g2.set_title(ticker + ' Yearly Earning', fontsize=6)
                g2.set_xticklabels(df2['quarter'], rotation=90, fontsize=6)

            if print_flag is True:
                quotes2_print = mongo_col1.find(mongo_query2).sort("quarter", 1)
                print('Year EPS')
                for q2 in quotes2_print:
                    print(q2['quarter'], q2['eps'])

            mongo_col3 = mongoDB.get_collection(x['Yahoo_Symbol'])
            mongo_query3 = {"Close": {'$ne': 'null'}}
            t = mongo_col3.find(mongo_query3).sort("Date", 1)
            if mongo_col3.count_documents(mongo_query3) > 0:
                df3 = pd.DataFrame(list(t))
                df3['Close'] = df3['Close'].astype(float)
                #plt.subplot(325)
                ax3 = plt.subplot2grid((5, 2), (2, 0), colspan=2, rowspan=2)
                g3 = df3['Close'].plot(grid=True)
                g3.set_title(ticker + ' Prices', fontsize=6)
                g3.xaxis.set_major_locator(MultipleLocator(200))
                g3.set_xticklabels('')


            mongo_col6 = mongoDB['stock_g_score']
            mongo_query6 = {"symbol": x['Yahoo_Symbol']}
            g20 = mongo_col6.find(mongo_query6).sort("AAOD", 1)
            if mongo_col6.count_documents(mongo_query6) > 0:
                if print_flag is True:
                    g20_print = mongo_col6.find(mongo_query6).sort("AAOD", 1)
                    print('G20 Score')
                    for ig20 in g20_print:
                        try:
                            print(ig20['symbol'], ig20['AAOD'], ig20['Score'])
                        except:
                            continue
                df6 = pd.DataFrame(list(g20))
                #plt.subplot(325)
                ax6 = plt.subplot2grid((5, 2), (4, 0), colspan=2)
                g6 = df6['Score'].plot(grid=True)
                g6.set_title(ticker + ' G20', fontsize=6)
                #g6.xaxis.set_major_locator(MultipleLocator(200))
                g6.set_xticklabels(df6['AAOD'], rotation=90, fontsize=6)
                #g6.set_xticklabels('')

            # Show the plot
            plt.tight_layout()
            self.fig = f
            plt.show(block=False)
            plt.show()
            #plt.pause(0.1)
if __name__ == '__main__':
    StockPlotter('PLNT')
