'''
History
2022/12/09 - created
'''
from datetime import datetime
from datetime import timedelta
import pandas as pd
import traceback
from test_mongo import MongoExplorer
#from test_yahoo import QuoteExplorer
#from test_g20_v2 import StockScore
from test_rl_macd_v2 import StockRL
from test_rl_macd_daily import RLDailyTrader

import warnings
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    macd_list = [[3, 7, 19], [6, 13, 9], [12, 26, 9]]  # , [6,13,9],[12,26,9]
    macd_threshold_list = [0, 0.2, 0.5, 1]  # ,0.2,0.5,1
    macd_min_len_list = [0, 5]

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
    restartIndex = 706       #6,7,8,10
    stopIndex = 800      #1000000
    repeat = 10      #10

    #for ticker in com:
    for ticker in d.list:
        #ticker = 'TSLA'         #'ILIM'     #'AZO'     #'TCEHY'        #'AYX'      #'LYFT'     #'PUMP'     #'CDLX' #'APPN' #'EYE'  #'RNG'     #'GOOGL'     #'EVBG'     #'BAND'     #'NFLX' #'GRWG'     #'ACMR'     #'MDB'     #'RCM'     #'FB'     #'AAPL'     #'ANTM'     #'AMZN'     #'TSLA'   #'BAND'     #'ROKU'     #'SHOP'     #'TWLO'
        #ticker = i['Yahoo_Symbol']
        #ticker = i

        print(str(index) + "	" + ticker)
        if index > stopIndex:
            break
        if index >= restartIndex:
            #q = QuoteExplorer()
            #q.get_quotes(ticker, aaod)

            #g20 = StockScore({'AAOD': aaod, 'symbol': ticker})
            #if g20.run_fundamentals() == True:
            #    g20.run()

            #if g20.result.get('Recommendation') == '' or ticker in d.list:
            #if True:
            #run_query = {"symbol": ticker}
            #run_count = mongo.mongoDB['stock_rl_macd_perf_results'].count_documents(run_query)

            #index2 = 1
            #restartIndex2 = run_count + 1

            r = pd.DataFrame()

            m_i = 0
            for m in macd_list:
                m_i += 1
                mtl_i = 0
                for macd_threshold in macd_threshold_list:
                    mtl_i += 1
                    mmll_i = 0
                    for macd_min_len in macd_min_len_list:
                        mmll_i += 1
                        for i in range(repeat):
                            #if index2 >= restartIndex2:
                            run_id = m_i * 10000 + mtl_i * 1000 + mmll_i * 100 + i

                            run_query = {"symbol": ticker, 'run_id': run_id, "model_run_date": {"$gt": check_date}}
                            run_count = mongo.mongoDB['stock_rl_macd_perf_results'].count_documents(run_query)
                            if run_count == 0:
                                short = m[0]
                                long = m[1]
                                signal = m[2]

                                try:
                                    s = StockRL(ticker, 0, short=short, long=long, signal=signal, macd_threshold=macd_threshold, macd_min_len=macd_min_len)
                                    #s = StockRL(ticker, 0, 12, 26, 9, aaod='2019-11-13')
                                    #s = StockRL(ticker, 0, 6, 13, 9, aaod='2019-11-13')

                                    s.train(save=False)
                                    #s.train(save=True)
                                    #s.retrain(save=False)
                                    #s.retrain()
                                    #s.reload()
                                    #print(s.run())
                                    #print(s.stock_env.c2)

                                    rr = s.run(save_flag='stock_rl_macd_perf_results', run_id=run_id)
                                    print(rr.to_string(header=False))
                                    #print(s.run(save_flag='screen', run_id=run_id))
                                    #print(s.run('db'))
                                    #df, a = s.run('df')
                                    #print(df)
                                    #print(a)
                                    #print(s.run('df'))
                                    r = pd.concat([r, rr])
                                except Exception as error:
                                    # print(error)
                                    print(traceback.format_exc())
                            else:
                                print(ticker, run_id)
                            #index2 += 1

            print(len(r.index), len(macd_list) * len(macd_threshold_list) * len(macd_min_len_list) * repeat)
            if r.empty or len(r.index) < len(macd_list) * len(macd_threshold_list) * len(macd_min_len_list) * repeat:
                mongo_query = {"symbol": ticker}
                r = pd.DataFrame(list(mongo.mongoDB['stock_rl_macd_perf_results'].find(mongo_query, no_cursor_timeout=True)))

            r['group'] = r['run_id'] / 100
            r['group'] = r['group'].astype(int)
            s = r.groupby('group').agg(['mean'])

            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(s)

            max_score = s['model_score'].max()['mean']
            smax = s[s['model_score']['mean'] == max_score]
            smax = smax.reset_index()

            macd_list_index = int(smax['group'] / 100) - 1
            macd_threshold_list_index = int((smax['group'] % 100) / 10) - 1
            macd_min_len_list_index = int(smax['group'] % 10) - 1
            model_perf = smax['model_perf']['mean'][0]
            buy_and_hold_perf = smax['buy_and_hold_perf']['mean'][0]
            duration = smax['duration']['mean'][0]

            # print(ticker, max_score, duration, model_perf, buy_and_hold_perf, macd_list[macd_list_index], macd_threshold_list[macd_threshold_list_index], macd_min_len_list[macd_min_len_list_index])

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
            mongo.mongoDB['stock_rl_macd_param'].replace_one({'symbol': ticker}, p, upsert=True)

        index += 1

# print(r)
# print(r.to_csv())  #.strip('\n').split('\n')

'''
r['group'] = r['run_id'] / 100
r['group'] = r['group'].astype(int)
s = r.groupby('group').model_score.agg(['mean', 'std'])
print(s)

max_score = s['mean'].max()
smax = s[s['mean'] == max_score]
smax = smax.reset_index()
macd_list_index = int(smax['group']/100) - 1
macd_threshold_list_index = int((smax['group']%100)/10) - 1
macd_min_len_list_index = int(smax['group']%10) - 1
print(ticker, max_score, macd_list[macd_list_index], macd_threshold_list[macd_threshold_list_index], macd_min_len_list[macd_min_len_list_index])

p = {
    'symbol': ticker,
    'rl_macd_score': max_score,
    'short': macd_list[macd_list_index][0],
    'long': macd_list[macd_list_index][1],
    'signal': macd_list[macd_list_index][2],
    'threshold': macd_threshold_list[macd_threshold_list_index],
    'min_len': macd_min_len_list[macd_min_len_list_index]
}
mongo.mongoDB['stock_rl_macd_param'].replace_one({'symbol': ticker}, p, upsert=True)
'''
