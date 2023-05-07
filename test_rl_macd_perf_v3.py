'''
History
2023/04/27 - created
'''
from datetime import datetime
from datetime import timedelta
import pandas as pd
import traceback
from test_mongo import MongoExplorer
from test_rl_macd_v3 import StockRL
from test_rl_macd_daily import RLDailyTrader

import warnings
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    macd_list = [[3, 7, 19], [6, 13, 9], [12, 26, 9]]  # , [6,13,9],[12,26,9]

    mongo = MongoExplorer()
    com_query = {'status': 'active'}
    #com_query = {'status': 'active', 'Yahoo_Symbol': 'TSLA'}
    #com = mongo.mongoDB['etrade_companies'].find(com_query, no_cursor_timeout=True)

    com = mongo.mongoDB['stock_g20'].distinct('symbol')

    aaod = datetime.now().strftime("%Y-%m-%d")
    #d = RLDailyTrader({'AAOD': aaod, 'short': 6, 'long': 13, 'signal': 9})
    d = RLDailyTrader({'AAOD': aaod})

    check_date = (datetime.now() + timedelta(days=-90)).strftime("%Y-%m-%d")

    index = 1
    restartIndex = 1       #6,7,8,10
    stopIndex = 1      #1000000
    repeat = 10      #10

    #for ticker in com:
    for ticker in d.list:
        print(str(index) + "	" + ticker)
        if index > stopIndex:
            break
        if index >= restartIndex:
            r = pd.DataFrame()

            m_i = 0
            for m in macd_list:
                m_i += 1
                for i in range(repeat):
                    run_id = m_i * 10000 + i

                    run_query = {"symbol": ticker, 'run_id': run_id, "model_run_date": {"$gt": check_date}}
                    run_count = mongo.mongoDB['stock_min_rl_macd_perf_results'].count_documents(run_query)
                    if run_count == 0:
                        short = m[0]
                        long = m[1]
                        signal = m[2]

                        try:
                            s = StockRL(ticker, 0, short=short, long=long, signal=signal, save_loc='./rl_min/test_rl_', interval='1m')

                            s.train(save=False)

                            rr = s.run(save_flag='stock_min_rl_macd_perf_results', run_id=run_id)
                            print(rr.to_string(header=False))
                            r = pd.concat([r, rr])
                        except Exception as error:
                            # print(error)
                            print(traceback.format_exc())
                    else:
                        print(ticker, run_id)
                    #index2 += 1

            print(len(r.index), len(macd_list) * repeat)
            if r.empty or len(r.index) < len(macd_list) * repeat:
                mongo_query = {"symbol": ticker}
                r = pd.DataFrame(list(mongo.mongoDB['stock_min_rl_macd_perf_results'].find(mongo_query, no_cursor_timeout=True)))

            r['group'] = r['run_id'] / 100
            r['group'] = r['group'].astype(int)
            s = r.groupby('group').agg(['mean'])

            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(s)

            max_gain_score = s['model_gain_score'].max()['mean']
            smax = s[s['model_gain_score']['mean'] == max_gain_score]
            smax = smax.reset_index()

            macd_list_index = int(smax['group'] / 100) - 1
            model_gain = smax['model_gain']['mean'][0]
            model_perf = smax['model_perf']['mean'][0]
            buy_and_hold_gain = smax['buy_and_hold_gain']['mean'][0]
            buy_and_hold_perf = smax['buy_and_hold_perf']['mean'][0]
            macd_gain = smax['macd_gain']['mean'][0]
            macd_perf = smax['macd_perf']['mean'][0]
            duration = smax['duration']['mean'][0]

            # print(ticker, max_score, duration, model_perf, buy_and_hold_perf, macd_list[macd_list_index], macd_threshold_list[macd_threshold_list_index], macd_min_len_list[macd_min_len_list_index])

            p = {
                'symbol': ticker,
                'min_rl_macd_score': max_gain_score,
                'duration': duration,
                'model_gain': model_gain,
                'model_perf': model_perf,
                'buy_and_hold_gain': buy_and_hold_gain,
                'buy_and_hold_perf': buy_and_hold_perf,
                'macd_gain': macd_gain,
                'macd_perf': macd_perf,
                'short': macd_list[macd_list_index][0],
                'long': macd_list[macd_list_index][1],
                'signal': macd_list[macd_list_index][2]
            }
            print(p)
            mongo.mongoDB['stock_min_rl_macd_param'].replace_one({'symbol': ticker}, p, upsert=True)

        index += 1
