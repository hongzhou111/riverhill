'''
Minute Data MACD Daytrading
1. get real-time minute data for a stock
2. check MACD crossing
3. Trade at crossing based on RL or MACD

2023/08/28  create this file
'''
import time
from datetime import datetime
from datetime import timedelta
import pandas as pd
from test_mongo import MongoExplorer
import yfinance as yf
from stockstats import StockDataFrame as Sdf
from test_stockstats_v2 import StockStats
from test_rl_macd_v3 import StockRL
#from test_excel import PyExcel
import csv
import traceback

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

class MinMACDTrader:
    def __init__(self, ticker, short=3, long=7, signal=19, tname='min_macd_1'):
        self.short = short
        self.long = long
        self.signal = signal

        mongo = MongoExplorer()
        self.mongoDB = mongo.mongoDB
        self.current_time = datetime.now()
        self.current_state = 'idle'
        self.ticker = ticker

        self.yf = yf.Ticker(ticker)
        self.reload_history()

        self.ss = StockStats(ticker)
        self.ss.stock = self.df.copy()
        self.ss.stock = Sdf.retype(self.ss.stock)

        self.tname = tname + '_yahoo_' + ticker
        self.p_rl = {
                "tname":    tname + '_rl',
                "symbol":   ticker,
                "share":    0,
                "cash":     0,
                "init_investment": 1000,
                "actions":  []
                }
        self.p_macd = {
                "tname":    tname + '_macd',
                "symbol":   ticker,
                "share":    0,
                "cash":     0,
                "init_investment": 1000,
                "actions":  []
                }
        self.rl_orders = []
        self.old_rl_orders = []
        self.macd_orders = []
        self.old_macd_orders = []

    def reload_history(self):
        start = (datetime.now() + timedelta(days=-1)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')

        #start = datetime.strptime('2023-03-28 09:30:00', '%Y-%m-%d %H:%M:%S')
        #end = datetime.strptime('2023-03-28 16:01:00', '%Y-%m-%d %H:%M:%S')
        try:
            #df = self.yf.history(interval="1m", start=start, end=end)
            df = self.yf.history(period='1d', interval="1m")
            df = df.reset_index()
            df = df.rename(columns={"Datetime": "Date"})
        except Exception as error:
            df = pd.DataFrame()
            print(traceback.format_exc())
        self.df = df
        #print(df)

    def reset_history(self):
        cdate = datetime(self.current_time.strftime('%Y-%m-%d'))
        hdate = datetime((self.current_time+timedelta(dyas=-1)).strftime('%Y-%m-%d'))
        history_csv_fname = self.ticker + '_history_finnhub_' + hdate.strftime(('%Y_%m_%d')) + '.csv'
        h_df = self.df.loc[self.df['date'] < cdate]
        print(cdate, hdate, hdf)
        h_df.to_csv(history_csv_fname, index=False)
        #h_df.to_csv(history_csv_fname, mode='a', index=False, header=False)
        self.df = self.df.loc[self.df['date'] >= cdate]
        print(self.df)

    def reload(self):
        if self.mongoDB['stock_rl_macd_min_trading_results'].count_documents({'tname': self.tname+'_rl'}) > 0:
            self.p_rl = self.mongoDB['stock_ga_results'].find_one({'tname': self.tname+'_rl'})
        if self.mongoDB['stock_rl_macd_min_trading_results'].count_documents({'tname': self.tname+'_macd'}) > 0:
            self.p_macd = self.mongoDB['stock_ga_results'].find_one({'tname': self.tname+'_macd'})

    def save_p(self):
        self.mongoDB['stock_rl_macd_min_trading_results'].replace_one({"symbol": self.ticker}, self.p_rl, upsert=True)
        self.mongoDB['stock_rl_macd_min_trading_results'].replace_one({"symbol": self.ticker}, self.p_macd, upsert=True)

    def get_real_time_data(self, last_datetime):
        last_datetime = last_datetime + timedelta(seconds=55)
        if (self.current_time.timestamp() - last_datetime.timestamp()) >= 60 and self.current_time.strftime("%H:%M:%S") >= '09:29:55':
            try:
                df = self.yf.history(start=last_datetime, interval='1m')
            except Exception as e:
                #print(traceback.format_exc())
                df = pd.DataFrame()

            if not df.empty:
                df = df.reset_index()
                df = df.rename(columns={"Datetime": "Date"})
                df = df.loc[df['Date'] > last_datetime]
                #print(df)
                #print('get_real_time_date:', last_datetime, df['Date'][0])
                self.df = pd.concat([self.df, df])
                self.ss.stock = self.df.copy()
                self.ss.stock = Sdf.retype(self.ss.stock)
                #print(self.df)
                self.ss.macd()
                #print(self.ss.stock)
    def run(self):
        rl = StockRL(self.ticker, 0, 3, 7, 19, interval='no')
        rl.reload()
        refresh_history = False
        p_saved = False

        macd_csv_name = 'test_min_macd_trader_macd_yahoo.csv'
        rl_csv_name = 'test_min_macd_trader_rl_yahoo.csv'
        #pyexcel = PyExcel()

        last_check_macd_datetime = self.current_time + timedelta(seconds=-120)
        while True:
            cur_time = self.current_time.strftime("%H:%M:%S")
            print('current time:', cur_time)

            #if cur_time > '09:30:00:':
            if cur_time >= "09:25:00" and cur_time < '16:01:00':
                p_saved = False
                self.current_state = 'work'
                s = self.ss.stock
                s = s.reset_index()  # .reset_index()
                last_datetime = s.loc[len(s.loc[: 'date'])-1, 'date']

                self.get_real_time_data(last_datetime)

                s = self.ss.stock
                s = s.reset_index()  # .reset_index()
                check_macd_datetime = s.loc[len(s.loc[: 'date'])-1, 'date']
                #print(last_check_macd_datetime, check_macd_datetime)
                #if True:
                if check_macd_datetime.timestamp() > last_check_macd_datetime.timestamp():
                    print('check macd:', check_macd_datetime)
                    last_check_macd_datetime = check_macd_datetime
                    m = self.ss.macd_by_date(check_macd_datetime, self.short, self.long, self.long)
                    print(m)
                    #if True:
                    if m['len'] == 1:
                        # add order to the order_queue
                        #macd order
                        f = {'date': check_macd_datetime, 'accum': m['pre_accum'], 'l': m['pre_len']}
                        price = s.loc[len(s.loc[: 'date'])-1, 'close']
                        share = 0
                        value = 0
                        if m['pre_macd_sign'] == -1:
                            macd_action_type = 'buy'
                            if self.p_macd['share'] == 0:
                                if self.p_macd['cash'] == 0:
                                    share = int(self.p_macd['init_investment'] / price)
                                else:
                                    share = int(self.p_macd['cash'] / price)
                                value = share * price
                        elif m['pre_macd_sign'] == 1:
                            macd_action_type = 'sell'
                            if self.p_macd['share'] > 0:
                                share = -1 * self.p_macd['share']
                                value = share * price
                        else:
                            macd_action_type = ''

                        if macd_action_type != '':
                            if not (self.p_macd['cash'] == 0 and self.p_macd['share'] == 0):
                                self.p_macd['cash'] = self.p_macd['cash'] - value
                            self.p_macd['share'] = self.p_macd['share'] + share
                            macd_o = {
                                "date": self.current_time,
                                "action_type": macd_action_type,
                                "fitness": f,
                                "price": price,
                                "share": share,
                                "value": value,
                                "status": 'done'
                            }
                            print(macd_o)
                            mfile = open(macd_csv_name, 'a')
                            w = csv.DictWriter(mfile, fieldnames=list(macd_o.keys()))
                            w.writerow(macd_o)
                            mfile.close()
                            #pyexcel.append_df_to_excel(macd_excel_name, pd.DataFrame([macd_o], columns=macd_o.keys()), header=False)
                            self.p_macd['actions'].append(macd_o)
                            print(self.p_macd)

                        #rl order
                        rl.stock_env.ss = self.ss.stock
                        rl.stock_env.c2 = self.ss.macd_crossing_by_threshold_min_len()
                        rl.stock_env.current_step = len(rl.stock_env.c2.loc[:, 'open'].values) - 1
                        action, _states = rl.model.predict(rl.stock_env._next_observation_test())

                        share = 0
                        value = 0
                        if action[0] < 1:
                            rl_action_type = 'buy'
                            if self.p_rl['share'] == 0:
                                if self.p_rl['cash'] == 0:
                                    share = int(self.p_rl['init_investment'] / price)
                                else:
                                    share = int(self.p_rl['cash'] / price)
                                value = share * price
                        elif action[0] < 2:
                            rl_action_type = 'sell'
                            if self.p_rl['share'] > 0:
                                share = -1 * self.p_rl['share']
                                value = share * price
                        else:
                            rl_action_type = ''

                        if rl_action_type != '':
                            if not (self.p_rl['cash'] == 0 and self.p_rl['share'] == 0):
                                self.p_rl['cash'] = self.p_rl['cash'] - value
                            self.p_rl['share'] = self.p_rl['share'] + share
                            rl_o = {
                                "date": self.current_time,
                                "action_type": rl_action_type,
                                "fitness": {'date': check_macd_datetime, 'model_predict': action[0]},
                                "price": price,
                                "share": share,
                                "value": value,
                                "status": 'done'
                            }
                            print(rl_o)
                            rfile = open(rl_csv_name, 'a')
                            w_r = csv.DictWriter(rfile, fieldnames=list(rl_o.keys()))
                            w_r.writerow(rl_o)
                            rfile.close()
                            #pyexcel.append_df_to_excel(rl_excel_name, pd.DataFrame([rl_o], columns=rl_o.keys()), header=False)
                            self.p_rl['actions'].append(rl_o)
                            print(self.p_rl)

                        self.save_p()
                #execute order
                #print('macd_orders:', self.macd_orders)
                #print('rl_orders:', self.rl_orders)
            elif cur_time >= '16:01:00' and cur_time < '16:02:00':
                if p_saved is False:
                    print(self.p_rl)
                    print(self.p_macd)
                    self.save_p()
                    p_saved = True
            elif cur_time >= "16:02:00" and cur_time < '23:00:00':
                self.current_state = 'idle'
                refresh_history = True

            if cur_time > '23:00:00' and refresh_history is True:
                self.reload_history()
                refresh_history = False

            if self.current_state == 'idle':
                sleep_time = 60 * 10            # sleep 10 min
            elif self.current_state == 'work':
                sleep_time = 1
            elif self.current_state == 'order pending':
                sleep_time = 0
            else:
                sleep_time = 1

            #self.save_p()
            #print(self.current_state)

            time.sleep(sleep_time)
            self.current_time = datetime.now()

if __name__ == '__main__':
    mm = MinMACDTrader('TSLA')
    mm.reload()
    mm.run()


'''
pip install finnhub-python

pip install websocket-client

pip install twelvedata[pandas,matplotlib,plotly,websocket-client]

pip install fhub

{'macd_sign': 1, 'peak': 0.09259405987479108, 'peak_date': '2023-03-31', 'r': 1.0, 'accum': 0.09259405987479108, 'len': 1, 'pre_macd_sign': -1, 'pre_peak': -0.05186352663801644, 'pre_peak_date': '2023-03-31', 'pre_accum': -0.07321168692672689, 'pre_len': 2}
{'date': datetime.datetime(2023, 3, 31, 15, 55, 59, 832000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:55:00-0400', tz='America/New_York'), 'accum': -0.07321168692672689, 'l': 2}, 'price': 206.89999389648438, 'share': 3, 'value': 620.6999816894531, 'status': 'done'}
{'tname': 'min_macd_1_macd', 'symbol': 'TSLA', 'share': 3, 'cash': 201.2888641357422, 'init_investment': 1000, 'actions': [{'date': datetime.datetime(2023, 3, 31, 12, 32, 59, 150000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:32:00-0400', tz='America/New_York'), 'accum': -0.04050595745360221, 'l': 2}, 'price': 205.85069274902344, 'share': 4, 'value': 823.4027709960938, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 36, 59, 41000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 12:36:00-0400', tz='America/New_York'), 'accum': 0.23901408639566812, 'l': 4}, 'price': 205.85279846191406, 'share': -4, 'value': -823.4111938476562, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 43, 0, 138000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:42:00-0400', tz='America/New_York'), 'accum': -0.34501074139722715, 'l': 6}, 'price': 206.1750030517578, 'share': 3, 'value': 618.5250091552734, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 43, 59, 635000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 12:43:00-0400', tz='America/New_York'), 'accum': 0.0210237287155626, 'l': 1}, 'price': 205.9510040283203, 'share': -3, 'value': -617.8530120849609, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 49, 59, 28000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:49:00-0400', tz='America/New_York'), 'accum': -0.4902933062952205, 'l': 6}, 'price': 205.69000244140625, 'share': 3, 'value': 617.0700073242188, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 52, 59, 10000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 12:52:00-0400', tz='America/New_York'), 'accum': 0.14180943539654245, 'l': 3}, 'price': 205.38999938964844, 'share': -3, 'value': -616.1699981689453, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 57, 59, 241000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:57:00-0400', tz='America/New_York'), 'accum': -0.41429716249535065, 'l': 5}, 'price': 204.91000366210938, 'share': 4, 'value': 819.6400146484375, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 2, 59, 144000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:02:00-0400', tz='America/New_York'), 'accum': 0.17432990150282138, 'l': 5}, 'price': 204.5500030517578, 'share': -4, 'value': -818.2000122070312, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 5, 59, 33000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:05:00-0400', tz='America/New_York'), 'accum': -0.10081753850110356, 'l': 3}, 'price': 204.33999633789062, 'share': 4, 'value': 817.3599853515625, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 14, 59, 163000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:14:00-0400', tz='America/New_York'), 'accum': 0.6929709601067362, 'l': 9}, 'price': 205.0399932861328, 'share': -4, 'value': -820.1599731445312, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 16, 59, 137000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:16:00-0400', tz='America/New_York'), 'accum': -0.020617801118177126, 'l': 2}, 'price': 205.51820373535156, 'share': 4, 'value': 822.0728149414062, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 19, 59, 906000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:19:00-0400', tz='America/New_York'), 'accum': 0.15665980927621942, 'l': 3}, 'price': 205.39999389648438, 'share': -4, 'value': -821.5999755859375, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 32, 0, 237000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:31:00-0400', tz='America/New_York'), 'accum': -0.5940458744740299, 'l': 12}, 'price': 205.0, 'share': 4, 'value': 820.0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 32, 59, 222000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:32:00-0400', tz='America/New_York'), 'accum': 0.01820270061820696, 'l': 1}, 'price': 204.7449951171875, 'share': -4, 'value': -818.97998046875, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 33, 59, 137000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:33:00-0400', tz='America/New_York'), 'accum': -0.018993384556020357, 'l': 1}, 'price': 204.8699951171875, 'share': 4, 'value': 819.47998046875, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 44, 0, 186000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:43:00-0400', tz='America/New_York'), 'accum': 0.3120074605889662, 'l': 10}, 'price': 204.91000366210938, 'share': -4, 'value': -819.6400146484375, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 47, 59, 168000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:47:00-0400', tz='America/New_York'), 'accum': -0.16989411299347162, 'l': 4}, 'price': 204.89999389648438, 'share': 4, 'value': 819.5999755859375, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 48, 58, 572000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:48:00-0400', tz='America/New_York'), 'accum': 0.0016156305373990626, 'l': 1}, 'price': 204.83999633789062, 'share': -4, 'value': -819.3599853515625, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 49, 59, 496000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:49:00-0400', tz='America/New_York'), 'accum': -0.004249016929770838, 'l': 1}, 'price': 205.08999633789062, 'share': 4, 'value': 820.3599853515625, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 55, 59, 235000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 13:55:00-0400', tz='America/New_York'), 'accum': 0.3130001722563302, 'l': 6}, 'price': 205.3000030517578, 'share': -4, 'value': -821.2000122070312, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 58, 0, 115000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:57:00-0400', tz='America/New_York'), 'accum': -0.024949740313926064, 'l': 2}, 'price': 205.63009643554688, 'share': 3, 'value': 616.8902893066406, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 6, 0, 170000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:05:00-0400', tz='America/New_York'), 'accum': 0.3048229941710823, 'l': 8}, 'price': 206.3404998779297, 'share': -3, 'value': -619.0214996337891, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 8, 59, 546000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:08:00-0400', tz='America/New_York'), 'accum': -0.10207007203254323, 'l': 3}, 'price': 206.53500366210938, 'share': 3, 'value': 619.6050109863281, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 13, 59, 826000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:13:00-0400', tz='America/New_York'), 'accum': 0.12277671616614824, 'l': 5}, 'price': 206.77000427246094, 'share': -3, 'value': -620.3100128173828, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 23, 59, 677000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:23:00-0400', tz='America/New_York'), 'accum': -0.4828341599214142, 'l': 10}, 'price': 206.97999572753906, 'share': 3, 'value': 620.9399871826172, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 24, 59, 291000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:24:00-0400', tz='America/New_York'), 'accum': 0.0019297391748616284, 'l': 1}, 'price': 206.85000610351562, 'share': -3, 'value': -620.5500183105469, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 25, 59, 711000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:25:00-0400', tz='America/New_York'), 'accum': -0.0063252513752645595, 'l': 1}, 'price': 207.0832061767578, 'share': 3, 'value': 621.2496185302734, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 26, 59, 286000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:26:00-0400', tz='America/New_York'), 'accum': 0.03492845015774212, 'l': 1}, 'price': 206.82000732421875, 'share': -3, 'value': -620.4600219726562, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 32, 59, 584000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:32:00-0400', tz='America/New_York'), 'accum': -0.07022076005670919, 'l': 6}, 'price': 206.90989685058594, 'share': 3, 'value': 620.7296905517578, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 37, 59, 542000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:37:00-0400', tz='America/New_York'), 'accum': 0.17693712446282597, 'l': 5}, 'price': 207.0998992919922, 'share': -3, 'value': -621.2996978759766, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 40, 59, 560000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:40:00-0400', tz='America/New_York'), 'accum': -0.09429909651211413, 'l': 3}, 'price': 207.25999450683594, 'share': 3, 'value': 621.7799835205078, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 42, 59, 918000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:42:00-0400', tz='America/New_York'), 'accum': 0.007310516658283778, 'l': 2}, 'price': 206.89999389648438, 'share': -3, 'value': -620.6999816894531, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 49, 0, 39000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:48:00-0400', tz='America/New_York'), 'accum': -0.23725348269363197, 'l': 6}, 'price': 207.08999633789062, 'share': 3, 'value': 621.2699890136719, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 51, 59, 125000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:51:00-0400', tz='America/New_York'), 'accum': 0.11933687434869425, 'l': 3}, 'price': 206.9499969482422, 'share': -3, 'value': -620.8499908447266, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 52, 59, 31000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:52:00-0400', tz='America/New_York'), 'accum': -0.004781804356553691, 'l': 1}, 'price': 207.1072998046875, 'share': 3, 'value': 621.3218994140625, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 57, 0, 176000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 14:56:00-0400', tz='America/New_York'), 'accum': 0.07373873631551939, 'l': 4}, 'price': 206.89169311523438, 'share': -3, 'value': -620.6750793457031, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 0, 59, 921000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:00:00-0400', tz='America/New_York'), 'accum': -0.052614175401607205, 'l': 4}, 'price': 207.1199951171875, 'share': 3, 'value': 621.3599853515625, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 7, 59, 111000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 15:07:00-0400', tz='America/New_York'), 'accum': 0.30893452484308337, 'l': 7}, 'price': 207.63999938964844, 'share': -3, 'value': -622.9199981689453, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 20, 59, 871000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:20:00-0400', tz='America/New_York'), 'accum': -0.5515147240179561, 'l': 13}, 'price': 207.14540100097656, 'share': 3, 'value': 621.4362030029297, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 26, 59, 388000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 15:26:00-0400', tz='America/New_York'), 'accum': 0.13007108267215498, 'l': 6}, 'price': 206.76010131835938, 'share': -3, 'value': -620.2803039550781, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 29, 0, 13000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:28:00-0400', tz='America/New_York'), 'accum': -0.07480950168591972, 'l': 2}, 'price': 207.02049255371094, 'share': 3, 'value': 621.0614776611328, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 33, 0, 126000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 15:32:00-0400', tz='America/New_York'), 'accum': 0.10559570161616652, 'l': 4}, 'price': 206.88999938964844, 'share': -3, 'value': -620.6699981689453, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 39, 59, 291000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:39:00-0400', tz='America/New_York'), 'accum': -0.34306731967641196, 'l': 7}, 'price': 206.35000610351562, 'share': 3, 'value': 619.0500183105469, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 53, 59, 24000), 'action_type': 'sell', 'fitness': {'date': Timestamp('2023-03-31 15:53:00-0400', tz='America/New_York'), 'accum': 0.4987334079492993, 'l': 14}, 'price': 206.16000366210938, 'share': -3, 'value': -618.4800109863281, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 55, 59, 832000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:55:00-0400', tz='America/New_York'), 'accum': -0.07321168692672689, 'l': 2}, 'price': 206.89999389648438, 'share': 3, 'value': 620.6999816894531, 'status': 'done'}]}
{'date': datetime.datetime(2023, 3, 31, 15, 55, 59, 832000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:55:00-0400', tz='America/New_York'), 'model_predict': 0.614961}, 'price': 206.89999389648438, 'share': 0, 'value': 0, 'status': 'done'}
{'tname': 'min_macd_1_rl', 'symbol': 'TSLA', 'share': 4, 'cash': 0, 'init_investment': 1000, 'actions': [{'date': datetime.datetime(2023, 3, 31, 12, 32, 59, 150000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:32:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.85069274902344, 'share': 4, 'value': 823.4027709960938, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 36, 59, 41000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:36:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.85279846191406, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 43, 0, 138000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:42:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.1750030517578, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 43, 59, 635000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:43:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.9510040283203, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 49, 59, 28000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:49:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.69000244140625, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 52, 59, 10000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:52:00-0400', tz='America/New_York'), 'model_predict': 0.10263011}, 'price': 205.38999938964844, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 12, 57, 59, 241000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 12:57:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.91000366210938, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 2, 59, 144000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:02:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.5500030517578, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 5, 59, 33000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:05:00-0400', tz='America/New_York'), 'model_predict': 0.971132}, 'price': 204.33999633789062, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 14, 59, 163000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:14:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.0399932861328, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 16, 59, 137000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:16:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.51820373535156, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 19, 59, 906000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:19:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.39999389648438, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 32, 0, 237000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:31:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.0, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 32, 59, 222000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:32:00-0400', tz='America/New_York'), 'model_predict': 0.24772134}, 'price': 204.7449951171875, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 33, 59, 137000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:33:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.8699951171875, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 44, 0, 186000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:43:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.91000366210938, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 47, 59, 168000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:47:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.89999389648438, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 48, 58, 572000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:48:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 204.83999633789062, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 49, 59, 496000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:49:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 205.08999633789062, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 55, 59, 235000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:55:00-0400', tz='America/New_York'), 'model_predict': 0.6583014}, 'price': 205.3000030517578, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 13, 58, 0, 115000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 13:57:00-0400', tz='America/New_York'), 'model_predict': 0.90368074}, 'price': 205.63009643554688, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 6, 0, 170000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:05:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.3404998779297, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 8, 59, 546000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:08:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.53500366210938, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 13, 59, 826000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:13:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.77000427246094, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 23, 59, 677000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:23:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.97999572753906, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 24, 59, 291000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:24:00-0400', tz='America/New_York'), 'model_predict': 0.8394191}, 'price': 206.85000610351562, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 25, 59, 711000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:25:00-0400', tz='America/New_York'), 'model_predict': 0.6268387}, 'price': 207.0832061767578, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 26, 59, 286000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:26:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.82000732421875, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 32, 59, 584000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:32:00-0400', tz='America/New_York'), 'model_predict': 0.0227151}, 'price': 206.90989685058594, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 37, 59, 542000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:37:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 207.0998992919922, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 40, 59, 560000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:40:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 207.25999450683594, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 42, 59, 918000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:42:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.89999389648438, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 49, 0, 39000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:48:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 207.08999633789062, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 51, 59, 125000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:51:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.9499969482422, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 52, 59, 31000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:52:00-0400', tz='America/New_York'), 'model_predict': 0.124883965}, 'price': 207.1072998046875, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 14, 57, 0, 176000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 14:56:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.89169311523438, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 0, 59, 921000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:00:00-0400', tz='America/New_York'), 'model_predict': 0.25501496}, 'price': 207.1199951171875, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 7, 59, 111000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:07:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 207.63999938964844, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 20, 59, 871000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:20:00-0400', tz='America/New_York'), 'model_predict': 0.06201887}, 'price': 207.14540100097656, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 26, 59, 388000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:26:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.76010131835938, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 29, 0, 13000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:28:00-0400', tz='America/New_York'), 'model_predict': 0.35863617}, 'price': 207.02049255371094, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 33, 0, 126000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:32:00-0400', tz='America/New_York'), 'model_predict': 0.2683463}, 'price': 206.88999938964844, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 39, 59, 291000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:39:00-0400', tz='America/New_York'), 'model_predict': 0.8795441}, 'price': 206.35000610351562, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 53, 59, 24000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:53:00-0400', tz='America/New_York'), 'model_predict': 0.0}, 'price': 206.16000366210938, 'share': 0, 'value': 0, 'status': 'done'}, {'date': datetime.datetime(2023, 3, 31, 15, 55, 59, 832000), 'action_type': 'buy', 'fitness': {'date': Timestamp('2023-03-31 15:55:00-0400', tz='America/New_York'), 'model_predict': 0.614961}, 'price': 206.89999389648438, 'share': 0, 'value': 0, 'status': 'done'}]}

macd perf
start 4 * 205.8507 = 223.3628
end 3 * 207.46 + 201.288864 = 823.668864
gain = -0.306064

rl perf
start 4 * 205.8507 = 223.3628
end 4 * 207.4601 = 829.8404
gain = 6.4776

buy and hold
start 4 * 205.8507 = 223.3628
end 4 * 207.4601 = 829.8404
gain = 6.4776

'''