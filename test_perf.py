'''
History
2022/12/26 - created
'''
from datetime import datetime
import pandas as pd
import traceback
from test_mongo import MongoExplorer

import warnings
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    macd_list = [[3, 7, 19], [6, 13, 9], [12, 26, 9]]  # , [6,13,9],[12,26,9]
    macd_threshold_list = [0, 0.2, 0.5, 1]  # ,0.2,0.5,1
    macd_min_len_list = [0, 5]
    repeat = 10

    mongo = MongoExplorer()
    #com_query = {'status': 'active'}
    #com_query = {'status': 'active', 'Yahoo_Symbol': 'TSLA'}
    com = mongo.mongoDB['stock_rl_macd_perf_results'].distinct('symbol')

    index = 1
    restartIndex = 1
    stopIndex = 1000000

    for ticker in com:
        print(str(index) + "	" + ticker)
        if index > stopIndex:
            break
        if index >= restartIndex:
            mongo_query = {"symbol": ticker}
            r = pd.DataFrame(list(mongo.mongoDB['stock_rl_macd_perf_results'].find(mongo_query, no_cursor_timeout=True)))
            #print(r)
            #print(r.to_csv())  #.strip('\n').split('\n')

            if len(r.index) < len(macd_list) * len(macd_threshold_list) * len(macd_min_len_list) * repeat:
                print(ticker, len(r.index))
            else:
                r['group'] = r['run_id'] / 100
                r['group'] = r['group'].astype(int)
                s = r.groupby('group').agg(['mean'])
                #print(s)

                max_score = s['model_score'].max()['mean']
                smax = s[s['model_score']['mean'] == max_score]
                smax = smax.reset_index()

                macd_list_index = int(smax['group']/100) - 1
                macd_threshold_list_index = int((smax['group']%100)/10) - 1
                macd_min_len_list_index = int(smax['group']%10) - 1
                model_perf = smax['model_perf']['mean'][0]
                buy_and_hold_perf = smax['buy_and_hold_perf']['mean'][0]
                duration = smax['duration']['mean'][0]

                #print(ticker, max_score, duration, model_perf, buy_and_hold_perf, macd_list[macd_list_index], macd_threshold_list[macd_threshold_list_index], macd_min_len_list[macd_min_len_list_index])

                p = {
                    'symbol': ticker,
                    'rl_macd_score': max_score,
                    'duration': duration,
                    'model_perf': model_perf,
                    'buy_and_hold_perf': buy_and_hold_perf,
                    'short': macd_list[macd_list_index][0],
                    'long': macd_list[macd_list_index][1],
                    'signal': macd_list[macd_list_index][2],
                    'threshold': macd_threshold_list[macd_threshold_list_index],
                    'min_len': macd_min_len_list[macd_min_len_list_index]
                }
                print(p)
                #mongo.mongoDB['stock_rl_macd_param'].replace_one({'symbol': ticker}, p, upsert=True)
        index += 1

'''
PAYC 220
GOOGL 74
LYFT 26
AYX 19
SNOW 210
JBHT 230
KRNT 230
POOL 93
CLH 36
ARES 5
'''
