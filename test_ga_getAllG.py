#import time
#import logging
from datetime import datetime
#from datetime import timedelta
#import pymongo
#import json
#import traceback
#import math
#from bson import json_util
#import pandas as pd
#import numpy as np

from test_g20 import StockScore
from test_ga import RuleGA

if __name__ == '__main__':
    startTime = datetime.now()

    save_p_flag = 0
    ga = RuleGA(save_p_flag)
    mutate_buy_period = 30

    start_date = '2009-12-09'
    end_date = '2030-12-31'
    mongo_query = {'$and': [{'Date': {'$gte': start_date}}, {'Date': {'$lte': end_date}}]}
    mongo_col_q = ga.mongoDB.get_collection('AMZN')
    qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))
    startMutateBuy = qDates[0]['Date']

    mongo_query2 = {}
    #mongo_query2 = {"Yahoo_Symbol": "TWLO"}
    #mongo_query2 = {"Yahoo_Symbol": "AMZN"}

    index = 1
    restartIndex = 1        #2529
    # stopIndex = len(qDates) - 7
    stopIndex = 1500000
    for q in qDates:
        print(index, q['Date'])
        if index > stopIndex:
            break
        if index >= restartIndex:
            d = q['Date']
            dd = ga.getDate(d)
            #print(index, d)

            if ga.getDateDiff(startMutateBuy, d) >= mutate_buy_period and dd.weekday() != 0 and dd.weekday() != 4:
                gList = list(ga.mongoDB['stock_g_score'].find({"$and": [{'runDate': d}, {'Recommendation': ''}]}))
                if len(gList) < 100:
                #if len(gList) < 100000:
                    print(index, startMutateBuy, d, 'new g score')
                    com = ga.mongoDB['etrade_companies'].find(mongo_query2, no_cursor_timeout=True)
                    dbList = ga.mongoDB.list_collection_names()
                    for c in com:
                        if c['Yahoo_Symbol'] in dbList:
                            try:
                                g20 = StockScore({'AAOD': d, 'symbol': c['Symbol']})
                                g = g20.run()
                                #print(json_util.dumps(g, indent=4))

                                if g['Recommendation'] == '' and g['CAP'] > 0:
                                    g20.save_g20()
                            except Exception as error:
                                continue
                else:
                    print(index, startMutateBuy, d, 'g score already done')
                startMutateBuy = d
        index = index + 1

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time: ', runTime)
