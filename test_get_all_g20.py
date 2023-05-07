from datetime import datetime
#import traceback

from test_g20_v2 import StockScore
from test_mongo import MongoExplorer
from test_yahoo import QuoteExplorer
import traceback

if __name__ == '__main__':
    startTime = datetime.now()
    start_date = '2010-10-01'
    end_date = '2023-01-10'

    mongo = MongoExplorer()
    mongo_query = {'$and': [{'Date': {'$gte': start_date}}, {'Date': {'$lte': end_date}}]}
    mongo_col_q = mongo.mongoDB.get_collection('AMZN')
    qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))

    mongo_query2 = {"status": "active"}

    index = 1
    restartIndex = 201      #63, 78-108
    stopIndex = 300       #1500000
    for q in qDates:
        if index > stopIndex:
            break
        if index >= restartIndex:
            startTime1 = datetime.now()
            print('start', index, q['Date'])

            q4 = {'AAOD': q['Date']}
            if mongo.mongoDB['stock_g20'].count_documents(q4) < 1000:
                com = mongo.mongoDB['etrade_companies'].find(mongo_query2, no_cursor_timeout=True)
                for c in com:
                    #print(c['Yahoo_Symbol'])
                    try:
                        yf = QuoteExplorer()
                        yf.get_quotes(c['Yahoo_Symbol'], q['Date'])

                        q3 = {'symbol': c['Yahoo_Symbol'], 'AAOD': q['Date']}
                        if mongo.mongoDB['stock_g20'].count_documents(q3) == 0:
                            g20 = StockScore({'AAOD': q['Date'], 'symbol': c['Yahoo_Symbol']})
                            g = g20.run(run_rl=0)
                            #print(json_util.dumps(g, indent=4))

                            if g['Recommendation'] == '':
                                print(g)
                                mongo.mongoDB['stock_g20'].replace_one({'symbol': c['Yahoo_Symbol'], 'AAOD': q['Date']}, g, upsert=True)
                    except Exception as error:
                        #print(traceback.format_exc())
                        continue
            endTime1 = datetime.now()
            runTime1 = endTime1 - startTime1
            print('end: ', endTime1, 'run time: ', runTime1)

        index = index + 1

    endTime = datetime.now()
    runTime = endTime - startTime
    print('run time: ', runTime, 'end:', endTime)
