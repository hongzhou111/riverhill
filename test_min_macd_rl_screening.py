'''
Measure test_rl_macd_v3 performance for all stocks

History:
2023/04/29      created this file
'''
from datetime import datetime
from datetime import timedelta
import pandas as pd
from test_mongo import MongoExplorer
import yfinance as yf
from stockstats import StockDataFrame as Sdf
from test_stockstats_v2 import StockStats
from test_rl_macd_v3 import StockRL
import os.path
import pytz
from test_rl_macd_daily import RLDailyTrader
import traceback

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


class MinMACDStockScreener:
    def __init__(self, short=3, long=7, signal=19):
        self.short = short
        self.long = long
        self.signal = signal

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB

    def get_min_yahoo(self, ticker, start, end):
        df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        try:
            y = yf.Ticker(ticker)
            df = y.history(interval="1m", start=start, end=end)
            #df = y.history(period='1d', interval="1m")
            df = df.reset_index()
            df = df.rename(columns={"Datetime": "Date"})
        except Exception as error:
            print(traceback.format_exc())

        db_name = ticker + '_min'
        yfq = self.mongoDB[db_name]

        if not df.empty:
            df["Symbol"] = ticker
            for row in df.to_dict(orient='records'):
                #print(row)
                yfq.replace_one({'Symbol': row['Symbol'], 'Date': row['Date']}, row, upsert=True)

        return df

    def init_run(self, ticker, data_source='Yahoo'):
        today = datetime.now()
        start = datetime.strptime((today + timedelta(days=-29)).strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime((today + timedelta(days=-22)).strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        print(start, end)

        if data_source == 'Yahoo':
            df = self.get_min_yahoo(ticker, start, end)
        else:
            query = {'$and': [{'Date': {'$gte': start}}, {'Date': {'$lte': end}}]}
            df = pd.DataFrame(list(self.mongoDB[ticker+'_min'].find(query)))
            df.reset_index()
            df.drop(['_id'], axis=1, inplace=True)

        ss = StockStats(ticker, interval='no')
        ss.stock = df.copy()
        ss.stock = Sdf.retype(ss.stock)
        ss.macd(self.short, self.long, self.signal)

        rl = StockRL(ticker, 0, self.short, self.long, self.signal, save_loc='./rl_min_screening/test_rl_', interval='no')
        rl.stock_env.ss = ss.stock
        rl.stock_env.c2 = ss.macd_crossing_by_threshold_min_len()

        #file_path = rl.save_loc + ticker + '.zip'
        #rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
        rl.train(save=True)
        re = rl.run()
        print(re)

        return re

    def daily_run(self, ticker, aaod='2023-04-10'):
        aaod_date = datetime.strptime(aaod, '%Y-%m-%d')
        start = datetime.strptime(aaod + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime((aaod_date + timedelta(days=1)).strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        print(start, end)

        query = {'$and': [{'Date': {'$gte': start}}, {'Date': {'$lte': end}}]}
        df = pd.DataFrame(list(self.mongoDB[ticker+'_min'].find(query)))
        df.reset_index()
        if not df.empty:
            df.drop(['_id'], axis=1, inplace=True)
            data_source = 'db'
        else:
            df = self.get_min_yahoo(ticker, start, end)
            data_source = 'Yahoo'

        ss = StockStats(ticker, interval='no')
        ss.stock = df.copy()
        ss.stock = Sdf.retype(ss.stock)
        ss.macd(self.short, self.long, self.signal)


        if data_source == 'Yahoo':
            hday = datetime.strptime(aaod + ' 15:00:00', '%Y-%m-%d %H:%M:%S').astimezone(pytz.timezone('America/New_York'))
        else:
            hday = datetime.strptime(aaod + ' 19:00:00', '%Y-%m-%d %H:%M:%S')           #.astimezone(pytz.timezone('America/New_York'))
        ss.stock = ss.stock.loc[ss.stock.index < hday]

        rl = StockRL(ticker, 0, self.short, self.long, self.signal, save_loc='./rl_min_screening/test_rl_', interval='no')
        rl.stock_env.ss = ss.stock
        #print(rl.stock_env.ss)
        rl.stock_env.c2 = ss.macd_crossing_by_threshold_min_len()
        print(rl.stock_env.c2)

        if len(rl.stock_env.c2.loc[: 'close']) > 7:
            re1 = rl.run()
            print(re1)
            file_path = rl.save_loc + ticker + '.zip'
            rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
            #re2 = rl.run()
            #print(re2)
        else:
            re1 = None

        return re1

    def run(self, ticker, data_source='Yahoo'):
        model_gain = 1
        buy_and_hold_gain = 1
        macd_gain = 1

        init_re = self.init_run(ticker, data_source)
        model_gain = model_gain * init_re['model_gain']
        buy_and_hold_gain = buy_and_hold_gain * init_re['buy_and_hold_gain']
        macd_gain = macd_gain * init_re['MACD_gain']

        today = datetime.now()
        start_date = (today + timedelta(days=-21)).strftime('%Y-%m-%d')
        mongo_query = {'Date': {'$gte': start_date}}
        mongo_col_q = ms.mongoDB.get_collection('AMZN')
        qDates = list(mongo_col_q.find(mongo_query).sort("Date", 1))

        for q in qDates:
            print(q['Date'])
            re1 = self.daily_run(ticker, q['Date'])
            if re1 is not None:
                model_gain = model_gain * re1['model_gain']
                buy_and_hold_gain = buy_and_hold_gain * re1['buy_and_hold_gain']
                macd_gain = macd_gain * re1['MACD_gain']

        return model_gain, buy_and_hold_gain, macd_gain

if __name__ == '__main__':
    #ms = MinMACDStockScreener(6,13,9)
    #ticker = 'MSFT'
    #ms.init_run(ticker)
    #ms.daily_run(ticker, aaod='2023-04-21')
    #ms.daily_run(ticker, aaod='2023-04-21', data_source='db')
    #print(ms.run(ticker))

    today = datetime.now()
    start_date = (today + timedelta(days=-29)).strftime('%Y-%m-%d')

    macd_list = [[3, 7, 19], [6, 13, 9], [12, 26, 9]]  # , [6,13,9],[12,26,9]

    mongo = MongoExplorer()

    aaod = datetime.now().strftime("%Y-%m-%d")
    d = RLDailyTrader({'AAOD': aaod})

    check_date = (datetime.now() + timedelta(days=-90)).strftime("%Y-%m-%d")

    index = 1
    restartIndex = 463       #6,7,8,10
    stopIndex = 1000      #1000000
    repeat = 1      #10

    for ticker in d.list:
        print(str(index) + "	" + ticker)
        if index > stopIndex:
            break
        if index >= restartIndex:
            m_i = 0
            for m in macd_list:
                m_i += 1
                for i in range(repeat):
                    run_id = m_i * 10000 + i

                    if m_i + i == 1:
                        data_source = 'Yahoo'
                    else:
                        data_source = 'db'

                    run_query = {"symbol": ticker, 'run_id': run_id, "model_run_date": {"$gt": check_date}}
                    run_count = mongo.mongoDB['stock_min_macd_rl_screening_results'].count_documents(run_query)
                    if run_count == 0:
                        short = m[0]
                        long = m[1]
                        signal = m[2]

                        ms = MinMACDStockScreener(short, long, signal)
                        model_gain, buy_and_hold_gain, macd_gain = ms.run(ticker, data_source)

                        result = {
                            'run_id': run_id,
                            'symbol': ticker,
                            'model_run_date': aaod,
                            'start_date': start_date,
                            'model_gain': model_gain,
                            'buy_and_hold_gain': buy_and_hold_gain,
                            'macd_gain': macd_gain,
                            'short': short,
                            'long': long,
                            'signal': signal
                        }
                        print(result)
                        mongo.mongoDB['stock_min_macd_rl_screening_results'].replace_one({'symbol': ticker, 'run_id': run_id}, result, upsert=True)
                    else:
                        print(ticker, run_id)

            mongo_query = {"symbol": ticker}
            r = pd.DataFrame(list(mongo.mongoDB['stock_min_macd_rl_screening_results'].find(mongo_query, no_cursor_timeout=True)))

            r['group'] = r['run_id'] / 100
            r['group'] = r['group'].astype(int)
            s = r.groupby('group').agg(['mean'])

            print(s)

            max_model_gain = s['model_gain'].max()['mean']
            smax = s[s['model_gain']['mean'] == max_model_gain]
            smax = smax.reset_index()

            macd_list_index = int(smax['group'] / 100) - 1
            model_gain = smax['model_gain']['mean'][0]
            buy_and_hold_gain = smax['buy_and_hold_gain']['mean'][0]
            macd_gain = smax['macd_gain']['mean'][0]

            p = {
                'symbol': ticker,
                'model_gain': model_gain,
                'buy_and_hold_gain': buy_and_hold_gain,
                'macd_gain': macd_gain,
                'short': macd_list[macd_list_index][0],
                'long': macd_list[macd_list_index][1],
                'signal': macd_list[macd_list_index][2]
            }
            print(p)
            mongo.mongoDB['stock_min_macd_rl_screening_param'].replace_one({'symbol': ticker}, p, upsert=True)

        index += 1
