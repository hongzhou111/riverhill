'''
Minute Data MACD Daytrading
1. get real-time minute data for a stock
2. check MACD crossing
3. Trade at crossing based on RL or MACD

2023/08/28  create this file
2023/04/02  add finnhub
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
import csv
import traceback
from fhub import Subscription
import json
import numpy
import pytz

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

class MinMACDTrader:
    def __init__(self, ticker, short=3, long=7, signal=19, tname='min_macd_1'):
        self.short = short
        self.long = long
        self.signal = signal

        #mongo = MongoExplorer()
        #self.mongoDB = mongo.mongoDB
        self.current_state = 'postmarket'
        self.ticker = ticker

        self.yf = yf.Ticker(ticker)
        #self.reload_history()
        self.df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

        self.ss = StockStats(ticker, interval='no')
        #self.ss.stock = self.df.copy()
        #self.ss.stock = Sdf.retype(self.ss.stock)
        #self.ss.macd()
        #print(self.ss.stock)

        self.subs = Subscription("cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90")

        self.tname = tname + '_finnhub_' + ticker
        self.p_rl = {
                "tname":    self.tname + '_rl',
                "symbol":   ticker,
                "share":    0,
                "cash":     0.0,
                "init_investment": 954.029137,
                "actions":  []
                }
        self.p_macd = {
                "tname":    self.tname + '_macd',
                "symbol":   ticker,
                "share":    0,
                "cash":     0.0,
                "init_investment": 954.029137,
                "actions":  []
                }

        self.macd_csv_name = './finnhub_data/test_min_macd_trader_macd_finnhub.csv'
        self.rl_csv_name = './finnhub_data/test_min_macd_trader_rl_finnhub.csv'


    def reload_history(self):
        n = datetime.now()
        if datetime.now().weekday() == 0:
            ds = -3
        elif datetime.now().weekday() == 6:
            ds = -2
        else:
            ds = -1
        start = (n + timedelta(days=ds)).strftime('%Y-%m-%d')
        end = (n + timedelta(days=1)).strftime('%Y-%m-%d')

        #start = datetime.strptime('2023-03-28 09:30:00', '%Y-%m-%d %H:%M:%S')
        #end = datetime.strptime('2023-03-28 16:01:00', '%Y-%m-%d %H:%M:%S')
        try:
            df = self.yf.history(interval="1m", start=start, end=end)
            #df = self.yf.history(period='1d', interval="1m")
            df = df.reset_index()
            df = df.rename(columns={"Datetime": "Date"})
        except Exception as error:
            df = pd.DataFrame()
            print(traceback.format_exc())
        self.df = df

    def reset_history(self):
        cdate = self.current_time.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.timezone('America/New_York'))
        #hdate = self.current_time+timedelta(days=-1)
        hdate = self.current_time
        history_csv_fname = './finnhub_data/' + self.ticker + '_history_finnhub_' + hdate.strftime(('%Y_%m_%d')) + '.csv'
        #h_df = self.df.loc[self.df['Date'] < cdate]
        h_df = self.df
        #print(cdate, hdate, h_df)
        if not h_df.empty:
            h_df.to_csv(history_csv_fname, mode='a', index=False)
            #self.df = self.df.loc[self.df['Date'] >= cdate]
        self.df = self.df[0:0]
        #print(self.df)

    def reload(self):
        if self.mongoDB['stock_rl_macd_trading_results'].count_documents({'tname': self.tname+'_rl'}) > 0:
            self.p_rl = self.mongoDB['stock_rl_macd_trading_results'].find_one({'tname': self.tname+'_rl'})
            if '_id' in self.p_rl:
                del self.p_rl['_id']
        if self.mongoDB['stock_rl_macd_trading_results'].count_documents({'tname': self.tname+'_macd'}) > 0:
            self.p_macd = self.mongoDB['stock_rl_macd_trading_results'].find_one({'tname': self.tname+'_macd'})
            if '_id' in self.p_macd:
                del self.p_macd['_id']

    def save_p(self):
        self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_rl['tname']}, self.encode_json(self.p_rl), upsert=True)
        self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_macd['tname']}, self.encode_json(self.p_macd), upsert=True)

    def archive_p(self):
        adate = datetime.now().strftime('%Y_%m_%d')
        achive_p_rl = self.p_rl
        achive_p_rl['tname'] = achive_p_rl['tname'] + '_' + adate
        self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': achive_p_rl['tname']}, self.encode_json(achive_p_rl), upsert=True)
        self.p_rl['actions'] = []
        achive_p_macd = self.p_macd
        achive_p_macd['tname'] = achive_p_macd['tname'] + '_' + adate
        self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': achive_p_macd['tname']}, self.encode_json(achive_p_macd), upsert=True)
        self.p_macd['actions'] = []

    def get_finnhub_data(self):
        if self.subs.reconnect:
            self.refresh_finnhub()

        #print(self.subs.tickers[self.ticker].history.tail(5))
        #if len(self.subs.tickers[self.ticker].history.loc[: 'Date']) > 0:
        if not self.subs.tickers[self.ticker].history.empty:
            last_history_time = self.subs.tickers[self.ticker].history.iloc[len(self.subs.tickers[self.ticker].history)-1]['Date']
            #if self.current_time.timestamp() - self.last_subs_time.timestamp() >= 60:      # sample by system time
            if last_history_time.timestamp() - self.last_subs_time.timestamp() >= 59:     #>= 60: sample by msg timestamp
                self.df.loc[len(self.df)] = self.subs.tickers[self.ticker].history.iloc[len(self.subs.tickers[self.ticker].history)-1]      # append last record from finnhub msg history
                #self.df['Open'] = self.df['Close']
                #self.df['High'] = self.df['Close']
                #self.df['Low'] = self.df['Close']
                self.ss.stock = self.df.copy()
                self.ss.stock = Sdf.retype(self.ss.stock)
                #print(self.df)
                #self.ss.macd()
                #print(self.ss.stock.tail(5))

                #self.last_subs_time = self.current_time
                self.last_subs_time = last_history_time

    def refresh_finnhub(self):
        self.subs.ws.close()
        time.sleep(1)
        self.subs.connect([self.ticker])

    def robin_order(self, action, close_market_sell=False):
        # rl order
        s = self.ss.stock
        s = s.reset_index()
        if not s.empty:
            check_macd_datetime = s.loc[len(s.loc[: 'date']) - 1, 'date']
            price = s.loc[len(s.loc[: 'close']) - 1, 'close']
        else:
            check_macd_datetime = self.current_time
            price = 0

        share = 0
        value = 0
        if action < 1 and self.cur_time <= '15:00:00:000000':           # no buy after 15:00
            rl_action_type = 'buy'
            if self.p_rl['share'] == 0:
                if self.p_rl['cash'] == 0:
                    share = self.p_rl['init_investment'] / price
                else:
                    share = self.p_rl['cash'] / price
                value = share * price
        elif action < 2:
            rl_action_type = 'sell'
            if self.p_rl['share'] > 0:
                share = -1 * self.p_rl['share']
                value = share * price
        else:
            rl_action_type = 'hold'

        if rl_action_type == 'buy' or rl_action_type == 'sell':
            if not (self.p_rl['cash'] == 0 and self.p_rl['share'] == 0):
                self.p_rl['cash'] = self.p_rl['cash'] - value
            self.p_rl['share'] = self.p_rl['share'] + share

        rl_o = {
            "date": self.current_time,
            "action_type": rl_action_type,
            "fitness": {'date': check_macd_datetime, 'model_predict': action,
                        'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']},
            "price": price,
            "share": share,
            "value": value,
            "status": 'done'
        }
        if close_market_sell is True:
            rl_o['fitness'] = {'date': check_macd_datetime, 'reason': 'close_market_sell'}

        print(rl_o)
        rfile = open(self.rl_csv_name, 'a')
        w_r = csv.DictWriter(rfile, fieldnames=list(rl_o.keys()))
        w_r.writerow(rl_o)
        rfile.close()
        self.p_rl['actions'].append(rl_o)
        print(self.p_rl)

        # macd order
        f = {'date': check_macd_datetime, 'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']}
        share = 0
        value = 0
        if s.loc[len(s.loc[: 'date']) - 2, 'macd_sign'] == -1 and close_market_sell is False and self.cur_time <= '15:00:00:000000':           # no buy after 15:00
            macd_action_type = 'buy'
            if self.p_macd['share'] == 0:
                if self.p_macd['cash'] == 0:
                    share = self.p_macd['init_investment'] / price
                else:
                    share = self.p_macd['cash'] / price
                value = share * price
        elif s.loc[len(s.loc[: 'date']) - 2, 'macd_sign'] == 1 or close_market_sell is True:
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
            if close_market_sell is True:
                macd_o['fitness'] = {'date': check_macd_datetime, 'reason': 'close_market_sell'}

            print(macd_o)
            mfile = open(self.macd_csv_name, 'a')
            w = csv.DictWriter(mfile, fieldnames=list(macd_o.keys()))
            w.writerow(macd_o)
            mfile.close()
            self.p_macd['actions'].append(macd_o)
            print(self.p_macd)

        #self.save_p()

    def run(self):
        self.current_time = datetime.now()
        self.last_subs_time = datetime.now()

        # connect to finnhub
        self.subs.connect([self.ticker])
        finnhub_connect_status = True

        rl = StockRL(self.ticker, 0, 3, 7, 19, save_loc='./rl_min/test_rl_', interval='no')
        rl.reload()

        refresh_history = False
        market_closed = False

        init_time = datetime.strptime('2023-01-01','%Y-%m-%d')
        last_finnhub_datetime = init_time
        last_check_macd_datetime = init_time

        macd_crossing_count = 0
        while True:
            self.cur_time = self.current_time.strftime("%H:%M:%S:%f")

            if self.cur_time >= "00:00:00:000000" and self.cur_time < '23:00:00:000000':
                #    self.current_state = 'premarket'
                if finnhub_connect_status is False:
                    self.refresh_finnhub()
                    finnhub_connect_status = True

                self.get_finnhub_data()

                #if len(self.ss.stock.loc[: 'date']) > 0:
                if not self.ss.stock.empty:
                    check_macd_datetime = self.ss.stock.tail(1).index.item()
                    #self.ss.macd()
                    #print(self.ss.stock.tail(1))
                else:
                    check_macd_datetime = self.current_time

                if self.current_time.timestamp() - check_macd_datetime.timestamp() >= 60 and check_macd_datetime.timestamp() > last_finnhub_datetime.timestamp() and last_finnhub_datetime > init_time:       # check finnhub delay, excluding the initial yahoo history load
                    print('finnhub slow delay =', self.current_time.timestamp() - check_macd_datetime.timestamp())
                    #self.refresh_finnhub()
                last_finnhub_datetime = check_macd_datetime

            if self.cur_time >= "09:30:00:000000" and self.cur_time < '15:56:00:000000':
                self.current_state = 'market'
                market_closed = False
                #if len(self.ss.stock.loc[: 'date']) > 0:
                if not self.ss.stock.empty:
                    check_macd_datetime = self.ss.stock.tail(1).index.item()

                    if check_macd_datetime.timestamp() > last_check_macd_datetime.timestamp():          # process new record
                        #print('current time:', self.cur_time, 'check macd:', check_macd_datetime)
                        self.ss.macd(3,7,19)
                        s = self.ss.stock
                        s = s.reset_index()  # .reset_index()
                        print(s.tail(1))

                        if s.loc[len(s.loc[: 'date'])-1, 'len'] == 1:       # crossing
                            #print(s.tail(1))
                            macd_crossing_count += 1
                            if macd_crossing_count > 5:                     # wait after 5 crossings
                                #rl order
                                rl.stock_env.ss = self.ss.stock
                                rl.stock_env.c2 = self.ss.macd_crossing_by_threshold_min_len()
                                rl.stock_env.current_step = len(rl.stock_env.c2.loc[:, 'open'].values) - 1
                                #print(rl.stock_env.current_step, rl.stock_env._next_observation_test())
                                action, _states = rl.model.predict(rl.stock_env._next_observation_test())

                                self.robin_order(action=action[0])
                    last_check_macd_datetime = check_macd_datetime
            elif self.cur_time >= '15:56:00:000000' and self.cur_time < '16:02:00:000000':
                if market_closed is False:
                    market_closed = True
                    #close_market_sell
                    self.robin_order(action=1, close_market_sell=True)

                    #self.archive_p()
                    macd_crossing_count = 0
            elif self.cur_time >= "16:02:00:000000" and self.cur_time < '21:00:00:000000':
                self.current_state = 'postmarket'
                refresh_history = True
            else:
                self.current_state = 'postmarket'

            if self.cur_time >= '21:00:00:000000' and refresh_history is True:
                self.reset_history()
                refresh_history = False

            if self.cur_time >= '21:00:00:000000' and finnhub_connect_status is True:
                self.subs.ws.close()
                finnhub_connect_status = False

            if self.current_state == 'postmarket':
                sleep_time = 10          #60 * 10            # sleep 10 min
            elif self.current_state == 'market':
                sleep_time = 0
            else:
                sleep_time = 1

            time.sleep(sleep_time)
            self.current_time = datetime.now()

    def encode_json(self, data):
        data_dict_1 = json.dumps(data, cls=CustomEncoder, default=str)
        return json.loads(data_dict_1)

class CustomEncoder(json.JSONEncoder):          # use CustomEncoder to fix pymongo error with numpy float(32)
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(CustomEncoder, self).default(obj)

if __name__ == '__main__':
    tname = 'min_macd_3'
    mmt = MinMACDTrader(ticker='TSLA', tname=tname)
    #mmt.reload()
    mmt.run()

    '''
    mmt.subs.connect([mmt.ticker])
    print(mmt.subs.tickers)
    msg = '{"data":[{"c":["1","12"],"p":164.0601,"s":"TSLA","t":1680286537580,"v":5},{"c":["1","12"],"p":164.0615,"s":"TSLA","t":1680286538049,"v":10},{"c":["1","8"],"p":164.06,"s":"TSLA","t":1680286538064,"v":142},{"c":["1","8","12"],"p":164.065,"s":"TSLA","t":1680286538064,"v":35},{"c":["1","8"],"p":164.06,"s":"TSLA","t":1680286538064,"v":100},{"c":["1","8","12"],"p":164.06,"s":"TSLA","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"TSLA","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"TSLA","t":1680286538064,"v":15},{"c":["1","12"],"p":164.0601,"s":"TSLA","t":1680286538276,"v":26},{"c":["1","12"],"p":164.0615,"s":"TSLA","t":1680286538295,"v":1}],"type":"trade"}'
    j = json.loads(msg)
    mmt.subs._feeder(j)
    print(mmt.subs.tickers[mmt.ticker].history)
    mmt.reset_finnhub_data()
    print(mmt.subs.tickers[mmt.ticker].history)

    s = mmt.ss.stock
    s = s.reset_index()
    last_datetime = s.loc[len(s.loc[: 'date']) - 1, 'date']
    mmt.get_finnhub_data(last_datetime)
    print(mmt.subs.tickers[mmt.ticker].history)

    s = mmt.ss.stock
    s = s.reset_index()
    check_macd_datetime = s.loc[len(s.loc[: 'date']) - 1, 'date']
    m = mmt.ss.macd_by_date(check_macd_datetime, 3, 7, 19)
    print(m)

    # subs.close()

2023-04-12 11:18:03.662000
{"data":[{"c":["8","12","41"],"p":183.24,"s":"TSLA","t":1681312681830,"v":5},{"c":[],"p":183.23,"s":"TSLA","t":1681312681832,"v":100},{"c":[],"p":183.23,"s":"TSLA","t":1681312681833,"v":100},{"c":[],"p":183.221,"s":"TSLA","t":1681312681835,"v":100},{"c":["12"],"p":183.235,"s":"TSLA","t":1681312681840,"v":10},{"c":["1"],"p":183.23,"s":"TSLA","t":1681312681826,"v":500},{"c":["1","8","12"],"p":183.24,"s":"TSLA","t":1681312681830,"v":5},{"c":["1"],"p":183.23,"s":"TSLA","t":1681312681832,"v":100},{"c":["1"],"p":183.23,"s":"TSLA","t":1681312681833,"v":100},{"c":["1"],"p":183.221,"s":"TSLA","t":1681312681835,"v":100}],"type":"trade"}
    
'''
