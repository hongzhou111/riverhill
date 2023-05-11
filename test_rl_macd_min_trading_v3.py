'''
Minute Data MACD Daytrading
1. get real-time minute data for a stock
2. check MACD crossing
3. Trade at crossing based on RL or MACD

2023/08/28  create this file
2023/04/02  add finnhub
223/04/20   add robin api
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
#import pytz
import robin_stocks.robinhood as rh
import os.path
#import math
import copy

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
        self.current_state = 'postmarket'
        self.ticker = ticker

        self.yf = yf.Ticker(ticker)
        # self.reload_history()
        self.df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.reload_df()

        self.ss = StockStats(ticker, interval='no')

        self.subs = Subscription("cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90")

        self.tname = tname + '_finnhub_' + ticker
        self.p_rl = {
            "tname": self.tname + '_rl',
            "symbol": ticker,
            "share": 0,
            "cash": 0,
            "init_investment": 10163.979669,
            "actions": []
        }
        self.p_macd = {
            "tname": self.tname + '_macd',
            "symbol": ticker,
            "share": 0,
            "cash": 0,
            "init_investment": 10094.973790867101,
            "actions": []
        }

        self.macd_csv_name = './finnhub_data/test_min_macd_trader_macd_finnhub_' + ticker + '.csv'
        self.rl_csv_name = './finnhub_data/test_min_macd_trader_rl_finnhub_' + ticker + '.csv'

        self.MAX_ROBIN_BUY_RETRY = 3

        self.current_time = datetime.now()

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

        # start = datetime.strptime('2023-03-28 09:30:00', '%Y-%m-%d %H:%M:%S')
        # end = datetime.strptime('2023-03-28 16:01:00', '%Y-%m-%d %H:%M:%S')
        try:
            df = self.yf.history(interval="1m", start=start, end=end)
            # df = self.yf.history(period='1d', interval="1m")
            df = df.reset_index()
            df = df.rename(columns={"Datetime": "Date"})
        except Exception as error:
            df = pd.DataFrame()
            print(traceback.format_exc())
        self.df = df

    def reload_df(self):
        today = datetime.now().strftime("%Y_%m_%d")
        fname = './finnhub_data/TSLA_history_finnhub_' + today + '.csv'
        if os.path.exists(fname) and os.stat(fname).st_size > 0:
            self.df = pd.read_csv(fname)
            if (not self.df.empty) and 'Date' in self.df:
                self.df['Date'] = pd.to_datetime(self.df['Date'])
                print(self.df)

    def save_history(self):
        hdate = self.current_time
        history_csv_fname = './finnhub_data/' + self.ticker + '_history_finnhub_' + hdate.strftime(('%Y_%m_%d')) + '.csv'
        if not self.df.empty:
            self.df.to_csv(history_csv_fname, mode='w', index=False)

    def reset_history(self):
        hdate = self.current_time
        history_csv_fname = './finnhub_data/' + self.ticker + '_history_finnhub_' + hdate.strftime(('%Y_%m_%d')) + '.csv'
        # h_df = self.df.loc[self.df['Date'] < cdate]
        h_df = self.df
        if not h_df.empty:
            h_df.to_csv(history_csv_fname, mode='w', index=False)
            # self.df = self.df.loc[self.df['Date'] >= cdate]
        self.df = self.df[0:0]
        # print(self.df)

    def reload(self):
        try:
            if self.mongoDB['stock_rl_macd_trading_results'].count_documents({'tname': self.tname + '_rl'}) > 0:
                self.p_rl = self.mongoDB['stock_rl_macd_trading_results'].find_one({'tname': self.tname + '_rl'})
                if '_id' in self.p_rl:
                    del self.p_rl['_id']
            if self.mongoDB['stock_rl_macd_trading_results'].count_documents({'tname': self.tname + '_macd'}) > 0:
                self.p_macd = self.mongoDB['stock_rl_macd_trading_results'].find_one({'tname': self.tname + '_macd'})
                if '_id' in self.p_macd:
                    del self.p_macd['_id']
        except Exception as error:
            pass

    def save_p_rl(self):
        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_rl['tname']}, self.encode_json(self.p_rl), upsert=True)
        except Exception as error:
            pass

    def save_p_macd(self):
        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_macd['tname']}, self.encode_json(self.p_macd), upsert=True)
        except Exception as error:
            pass

    def archive_p(self):
        adate = datetime.now().strftime('%Y_%m_%d')

        achive_p_rl = copy.deepcopy(self.p_rl)
        achive_p_rl['tname'] = achive_p_rl['tname'] + '_' + adate

        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': achive_p_rl['tname']}, self.encode_json(achive_p_rl), upsert=True)
        except Exception as error:
            pass

        self.p_rl['actions'].clear()
        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_rl['tname']}, self.encode_json(self.p_rl), upsert=True)
        except Exception as error:
            pass

        achive_p_macd = copy.deepcopy(self.p_macd)
        achive_p_macd['tname'] = achive_p_macd['tname'] + '_' + adate

        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': achive_p_macd['tname']}, self.encode_json(achive_p_macd), upsert=True)
        except Exception as error:
            pass

        self.p_macd['actions'].clear()
        try:
            self.mongoDB['stock_rl_macd_trading_results'].replace_one({'tname': self.p_macd['tname']}, self.encode_json(self.p_macd), upsert=True)
        except Exception as error:
            pass

    def get_finnhub_data(self):
        if self.subs.reconnect:
            self.refresh_finnhub()

        # print(self.subs.tickers[self.ticker].history.tail(5))
        # if len(self.subs.tickers[self.ticker].history.loc[: 'Date']) > 0:
        if not self.subs.tickers[self.ticker].history.empty:
            last_history_time = self.subs.tickers[self.ticker].history.iloc[len(self.subs.tickers[self.ticker].history) - 1]['Date']
            # if self.current_time.timestamp() - self.last_subs_time.timestamp() >= 60:      # sample by system time
            if last_history_time.timestamp() - self.last_subs_time.timestamp() >= 9.5:       #59.5:  # >= 60: sample by msg timestamp
                self.df.loc[len(self.df)] = self.subs.tickers[self.ticker].history.iloc[len(self.subs.tickers[self.ticker].history) - 1]  # append last record from finnhub msg history
                # self.df['Open'] = self.df['Close']
                # self.df['High'] = self.df['Close']
                # self.df['Low'] = self.df['Close']
                self.ss.stock = self.df.copy()
                self.ss.stock = Sdf.retype(self.ss.stock)
                # print(self.df)
                # self.ss.macd()
                #print(self.ss.stock.tail(5))

                # self.last_subs_time = self.current_time
                self.last_subs_time = last_history_time

    def refresh_finnhub(self):
        self.subs.ws.close()
        time.sleep(1)
        self.subs.connect([self.ticker])

    def robin_login(self):
        login = rh.login(username='hongzhou111@gmail.com',
                 password='Xiaominlin111')      #,
                 #expiresIn=86400,
                 #by_sms=True)          # sms code=283872
        #print(login)
        return login

    def robin_logout(self):
        rh.logout()

    def robin_order(self, action, close_market_sell=False):
        s = self.ss.stock
        s = s.reset_index()
        if not s.empty:
            check_macd_datetime = s.loc[len(s.loc[: 'date']) - 1, 'date']
            price = s.loc[len(s.loc[: 'close']) - 1, 'close']
        else:
            check_macd_datetime = self.current_time
            price = 0

        # check robnin quanity
        my_stocks = rh.build_holdings()
        #print(my_stocks)
        if self.ticker in my_stocks:
            robin_quantity = float(my_stocks[self.ticker]['quantity'])
        else:
            robin_quantity = 0

        if self.p_rl['share'] != robin_quantity:
            print('wrong share number: ', self.p_rl['share'], robin_quantity)
            self.p_rl['share'] = robin_quantity

        share = 0
        value = 0
        status = 'unsent'
        if action < 1 and self.cur_time <= '15:00:00:000000':       #no buy after 15:00
            rl_action_type = 'buy'

            if self.p_rl['share'] == 0 and self.p_rl['cash'] == 0:
                amount = self.p_rl['init_investment']
            else:
                amount = self.p_rl['cash']
            #print(amount)
            if amount > 1:
                try:
                    if price > 0:
                        #quantity = math.floor((amount/price)*10000)/10000
                        quantity = round(amount/price, 2)
                        print(quantity)
                        robin_buy = rh.orders.order_buy_fractional_by_quantity(self.ticker, quantity, timeInForce='gfd', extendedHours=False)
                    else:
                        robin_buy = rh.orders.order_buy_fractional_by_price(self.ticker, amount, timeInForce='gfd', extendedHours=False)
                    print(robin_buy)

                    '''
                    robin_buy = {'id': '6435675e-1380-4e22-af68-0095e3433335', 'ref_id': 'c3ce0359-a02a-4878-949b-4ed050547379', 'url': 'https://api.robinhood.com/orders/6435675e-1380-4e22-af68-0095e3433335/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None,
                        'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483',
                        'cumulative_quantity': '4.95991400', 'average_price': '187.59800000', 'fees': '0.00', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market',
                        'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate',
                        'price': '187.61000000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                        'created_at': '2023-04-11T13:57:50.938320Z', 'updated_at': '2023-04-11T13:57:52.248640Z', 'last_transaction_at': '2023-04-11T13:57:51.935573Z', 'executions': [{'price': '187.59800000', 'quantity': '4.95991400', 'rounded_notional': '930.47000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T13:57:51.345000Z', 'id': '6435675f-105e-43bd-9e78-71fd3bdee706', 'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': {'amount': '930.47000000', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'total_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}
                    '''
                    time.sleep(3)
                    _id = robin_buy.get('id')
                    _order_info = rh.get_stock_order_info(_id)
                    #print(_order_info)

                    status = _order_info.get('state', 'failed')
                    if status == 'filled' or status == 'partially_filled' or status == 'cancelled':
                        if _order_info.get('average_price', 0) is not None:
                            price = float(_order_info.get('average_price', 0))
                        if _order_info.get('cumulative_quantity', 0) is not None:
                            share = float(_order_info.get('cumulative_quantity', 0))
                        value = share * price
                except Exception as error:
                    status = 'failed'
                    print(error)
                    pass

                retry_num = 0
                while retry_num < self.MAX_ROBIN_BUY_RETRY and (status == 'cancelled' or status == 'partially_filled' or status == 'failed'):            #retry 2 times if cancelled or failed
                    retry_num += 1
                    print('buy', status, ', retry', retry_num)

                    if not (self.p_rl['cash'] == 0 and self.p_rl['share'] == 0):            #update with partial buy in cancelled order
                        self.p_rl['cash'] = self.p_rl['cash'] - value
                        if self.p_rl['cash'] < 0:
                            self.p_rl['cash'] = 0
                    self.p_rl['share'] = self.p_rl['share'] + share

                    amount = amount - value
                    if amount > 1:
                        try:
                            if price is not None and price > 0:
                                # quantity = math.floor((amount/price)*10000)/10000
                                quantity = round(amount / price, 2)
                                print(quantity)
                                robin_buy = rh.orders.order_buy_fractional_by_quantity(self.ticker, quantity, timeInForce='gfd', extendedHours=False)
                            else:
                                robin_buy = rh.orders.order_buy_fractional_by_price(self.ticker, amount, timeInForce='gfd', extendedHours=False)
                            print(robin_buy)
                            '''
                            robin_buy = {'id': '6435675e-1380-4e22-af68-0095e3433335', 'ref_id': 'c3ce0359-a02a-4878-949b-4ed050547379', 'url': 'https://api.robinhood.com/orders/6435675e-1380-4e22-af68-0095e3433335/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None,
                                'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483',
                                'cumulative_quantity': '4.95991400', 'average_price': '187.59800000', 'fees': '0.00', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market',
                                'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate',
                                'price': '187.61000000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                                'created_at': '2023-04-11T13:57:50.938320Z', 'updated_at': '2023-04-11T13:57:52.248640Z', 'last_transaction_at': '2023-04-11T13:57:51.935573Z', 'executions': [{'price': '187.59800000', 'quantity': '4.95991400', 'rounded_notional': '930.47000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T13:57:51.345000Z', 'id': '6435675f-105e-43bd-9e78-71fd3bdee706', 'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': {'amount': '930.47000000', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'total_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}
                            '''
                            time.sleep(3)
                            _id = robin_buy.get('id')
                            _order_info = rh.get_stock_order_info(_id)
                            # print(_order_info)

                            status = _order_info.get('state', 'failed')
                            if status == 'filled' or status == 'partially_filled' or status == 'cancelled':
                                if _order_info.get('average_price', 0) is not None:
                                    price = float(_order_info.get('average_price', 0))
                                if _order_info.get('cumulative_quantity', 0) is not None:
                                    share = float(_order_info.get('cumulative_quantity', 0))
                                value = share * price
                        except Exception as error:
                            status = 'failed'
                            print(error)
                            pass
        elif action < 2:
            rl_action_type = 'sell'

            if self.p_rl['share'] > 0:
                quantity = self.p_rl['share']
                try:
                    robin_sell = rh.order_sell_fractional_by_quantity(self.ticker, quantity, timeInForce='gfd', extendedHours=False)
                    #print(robin_sell)
                    '''
                    robin_sell = {'id': '64357423-29c8-4c21-a97e-99c1427ad6f2', 'ref_id': 'f1267061-68a8-4cec-a102-00fc8d7f5a9b', 'url': 'https://api.robinhood.com/orders/64357423-29c8-4c21-a97e-99c1427ad6f2/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None,
                        'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483',
                        'cumulative_quantity': '4.95991400', 'average_price': '187.19070000', 'fees': '0.01', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market',
                        'side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate',
                        'price': '187.19110000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                        'created_at': '2023-04-11T14:52:19.269479Z', 'updated_at': '2023-04-11T14:52:20.519954Z', 'last_transaction_at': '2023-04-11T14:52:20.211613Z',
                        'executions': [{'price': '187.19110000', 'quantity': '4.95991400', 'rounded_notional': '928.45000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T14:52:19.534000Z', 'id': '64357424-0339-4b53-86d7-6a8415447e5a',
                        'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None,
                        'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
                        'total_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
                        'executed_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
                        'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None,
                        'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True,
                        'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}
                    '''
                    time.sleep(3)
                    _id = robin_sell.get('id')
                    _order_info = rh.get_stock_order_info(_id)
                    #print(_order_info)

                    status = _order_info.get('state', 'failed')
                    if status == 'filled' or status == 'partially_filled' or status == 'cancelled':
                        if _order_info.get('average_price', 0) is not None:
                            price = float(_order_info.get('average_price', 0))
                        if _order_info.get('cumulative_quantity', 0) is not None:
                            share = -1 * float(_order_info.get('cumulative_quantity', 0))
                        value = share * price
                except Exception as error:
                    status = 'failed'
                    print(error)
                    pass

                if status == 'cancelled' or status == 'partially_filled' or status == 'failed':         #retry if failed
                    print('first sell ', status)

                    if not (self.p_rl['cash'] == 0 and self.p_rl['share'] == 0):            # update with partial sell in cancelled order
                        self.p_rl['cash'] = self.p_rl['cash'] - value
                        if self.p_rl['cash'] < 0:
                            self.p_rl['cash'] = 0
                    self.p_rl['share'] = self.p_rl['share'] + share

                    quantity = quantity + share
                    if quantity > 0:
                        try:
                            robin_sell = rh.order_sell_fractional_by_quantity(self.ticker, quantity, timeInForce='gfd', extendedHours=False)
                            # print(robin_sell)
                            '''
                            robin_sell = {'id': '64357423-29c8-4c21-a97e-99c1427ad6f2', 'ref_id': 'f1267061-68a8-4cec-a102-00fc8d7f5a9b', 'url': 'https://api.robinhood.com/orders/64357423-29c8-4c21-a97e-99c1427ad6f2/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None,
                                'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483',
                                'cumulative_quantity': '4.95991400', 'average_price': '187.19070000', 'fees': '0.01', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market',
                                'side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate',
                                'price': '187.19110000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                                'created_at': '2023-04-11T14:52:19.269479Z', 'updated_at': '2023-04-11T14:52:20.519954Z', 'last_transaction_at': '2023-04-11T14:52:20.211613Z',
                                'executions': [{'price': '187.19110000', 'quantity': '4.95991400', 'rounded_notional': '928.45000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T14:52:19.534000Z', 'id': '64357424-0339-4b53-86d7-6a8415447e5a',
                                'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None,
                                'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
                                'total_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
                                'executed_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
                                'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None,
                                'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True,
                                'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}
                            '''
                            time.sleep(3)
                            _id = robin_sell.get('id')
                            _order_info = rh.get_stock_order_info(_id)
                            # print(_order_info)

                            status = _order_info.get('state', 'failed')
                            if status == 'filled' or status == 'partially_filled' or status == 'cancelled':
                                if _order_info.get('average_price', 0) is not None:
                                    price = float(_order_info.get('average_price', 0))
                                if _order_info.get('cumulative_quantity', 0) is not None:
                                    share = -1 * float(_order_info.get('cumulative_quantity', 0))
                                value = share * price
                        except Exception as error:
                            print(error)
                            status = 'failed'
                            pass
        else:
            rl_action_type = 'hold'

        if rl_action_type == 'buy' or rl_action_type == 'sell':
            if not (self.p_rl['cash'] == 0 and self.p_rl['share'] == 0):
                self.p_rl['cash'] = self.p_rl['cash'] - value
                if self.p_rl['cash'] < 0:
                    self.p_rl['cash'] = 0
            self.p_rl['share'] = self.p_rl['share'] + share

        rl_o = {
            "date": self.current_time,
            "action_type": rl_action_type,
            "fitness": {'date': check_macd_datetime, 'model_predict': action, 'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']},
            "price": price,
            "share": share,
            "value": value,
            "status": status
        }
        if close_market_sell is True:
            rl_o['fitness'] = {'date': self.current_time, 'reason': 'close_market_sell'}

        print(rl_o)
        rfile = open(self.rl_csv_name, 'a')
        w_r = csv.DictWriter(rfile, fieldnames=list(rl_o.keys()))
        w_r.writerow(rl_o)
        rfile.close()
        self.p_rl['actions'].append(rl_o)
        print(self.p_rl['tname'], self.p_rl['symbol'], self.p_rl['share'], self.p_rl['cash'], self.p_rl['init_investment'])

        self.save_p_rl()

    def paper_order(self, action, close_market_sell=False):
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
        status = 'unsent'
        if action < 1 and self.cur_time <= '15:00:00:000000':       #no buy after 15:00
            rl_action_type = 'buy'

            if self.p_rl['share'] == 0:
                if self.p_rl['cash'] == 0:
                    amount = self.p_rl['init_investment']
                else:
                    amount = self.p_rl['cash']
                #print(amount)
                if amount > 1:
                    if price > 0:
                        share = round(amount/price, 2)
                        print(share)
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
                if self.p_rl['cash'] < 0:
                    self.p_rl['cash'] = 0
            self.p_rl['share'] = self.p_rl['share'] + share

        rl_o = {
            "date": self.current_time,
            "action_type": rl_action_type,
            "fitness": {'date': check_macd_datetime, 'model_predict': action, 'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']},
            "price": price,
            "share": share,
            "value": value,
            "status": status
        }
        if close_market_sell is True:
            rl_o['fitness'] = {'date': self.current_time, 'reason': 'close_market_sell'}

        print(rl_o)
        rfile = open(self.rl_csv_name, 'a')
        w_r = csv.DictWriter(rfile, fieldnames=list(rl_o.keys()))
        w_r.writerow(rl_o)
        rfile.close()
        self.p_rl['actions'].append(rl_o)
        print(self.p_rl['tname'], self.p_rl['symbol'], self.p_rl['share'], self.p_rl['cash'], self.p_rl['init_investment'])

        self.save_p_rl()

    def macd_order(self, close_market_sell=False):
        # macd order
        s = self.ss.stock
        s = s.reset_index()
        if not s.empty:
            check_macd_datetime = s.loc[len(s.loc[: 'date']) - 1, 'date']
            price = s.loc[len(s.loc[: 'close']) - 1, 'close']
        else:
            check_macd_datetime = self.current_time
            price = 0

        f = {'date': check_macd_datetime, 'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']}
        share = 0
        value = 0
        if s.loc[len(s.loc[: 'date']) - 2, 'macd_sign'] == -1 and close_market_sell is False and self.cur_time <= '15:00:00:000000':  # no buy after 15:00
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
            print(self.p_macd['tname'], self.p_macd['symbol'], self.p_macd['share'], self.p_macd['cash'], self.p_macd['init_investment'])

        self.save_p_macd()

    def run(self, rerun=False, paper_trade=False):
        if rerun is True and len(self.df.loc[: 'Date']) >= 200:
            self.MACD_CROSSING_WAIT = 0
        else:
            self.MACD_CROSSING_WAIT = 0     #6     #5

        self.current_time = datetime.now()
        self.last_subs_time = datetime.now()

        # connect to finnhub
        self.subs.connect([self.ticker])
        finnhub_connect_status = True

        # login Ronbinhood
        if not paper_trade:
            robin_login = self.robin_login()
            if robin_login is not None:
                robin_login_status = True
            else:
                robin_login_status = False
        else:
            robin_login_status = False

        #rl1 for 9:30 - 11:00 trading
        #rl = StockRL(self.ticker, 0, short=self.short, long=self.long, signal=self.signal, save_loc='./rl_min/test_rl_', interval='no')
        rl1 = StockRL(self.ticker, 0, short=self.short, long=self.long, signal=self.signal, save_loc='./rl_sec_8_11/test_rl_', interval='no')
        rl1.reload()

        #rl2 for 11:00 - 15:00 trading
        rl2 = StockRL(self.ticker, 0, short=self.short, long=self.long, signal=self.signal, save_loc='./rl_sec_10_15/test_rl_', interval='no')
        rl2.reload()

        refresh_history = False
        market_closed = False

        #init_time = datetime.strptime('2023-01-01', '%Y-%m-%d')
        init_time = pd.to_datetime('2023-01-01 00:00:00-04:00')
        last_finnhub_datetime = init_time
        last_check_macd_datetime = init_time
        save_history_status = False

        macd_crossing_count = 0
        while True:
            self.cur_time = self.current_time.strftime("%H:%M:%S:%f")

            if self.cur_time >= "03:00:00:000000" and self.cur_time < '21:00:00:000000':
                self.current_state = 'premarket'
                if finnhub_connect_status is False:
                    self.refresh_finnhub()
                    finnhub_connect_status = True

                self.get_finnhub_data()

                # if len(self.ss.stock.loc[: 'date']) > 0:
                if not self.ss.stock.empty:
                    check_macd_datetime = self.ss.stock.tail(1).index.item()
                    # self.ss.macd()
                    #print(self.ss.stock.tail(1))
                else:
                    check_macd_datetime = self.current_time

                if check_macd_datetime.timestamp() > last_finnhub_datetime.timestamp():     # and last_finnhub_datetime > init_time:
                    save_history_status = False
                    if self.cur_time < "09:30:00:000000":
                        print(self.ss.stock.tail(1))

                if self.current_time.timestamp() - check_macd_datetime.timestamp() >= 60 and check_macd_datetime.timestamp() > last_finnhub_datetime.timestamp():       # and last_finnhub_datetime > init_time:  # check finnhub delay, excluding the initial yahoo history load
                    print('finnhub slow delay =', self.current_time.timestamp() - check_macd_datetime.timestamp())
                    # self.refresh_finnhub()
                last_finnhub_datetime = check_macd_datetime

                # login Ronbinhood
                if not paper_trade:
                    if robin_login_status is False:
                        robin_login = self.robin_login()
                        if robin_login is not None:
                            robin_login_status = True
                        else:
                            robin_login_status = False

            if self.cur_time >= "09:30:00:000000" and self.cur_time < '15:56:00:000000':
                self.current_state = 'market'
                market_closed = False
                # if len(self.ss.stock.loc[: 'date']) > 0:
                if not self.ss.stock.empty:
                    check_macd_datetime = self.ss.stock.tail(1).index.item()

                    if check_macd_datetime.timestamp() > last_check_macd_datetime.timestamp():  # process new record
                        # print('current time:', self.cur_time, 'check macd:', check_macd_datetime)
                        self.ss.macd(self.short, self.long, self.signal)
                        s = self.ss.stock
                        s = s.reset_index()  # .reset_index()
                        print(s.tail(1))

                        if s.loc[len(s.loc[: 'date']) - 1, 'len'] == 1:  # crossing
                            # print(s.tail(1))
                            macd_crossing_count += 1
                            if macd_crossing_count > self.MACD_CROSSING_WAIT:  # wait after 6/5 crossings
                                # rl order

                                if self.cur_time >= "09:30:00:000000" and self.cur_time <= '11:00:00:000000':
                                    rl1.stock_env.ss = self.ss.stock
                                    rl1.stock_env.c2 = self.ss.macd_crossing_by_threshold_min_len()
                                    rl1.stock_env.current_step = len(rl1.stock_env.c2.loc[:, 'open'].values) - 1
                                    # print(rl1.stock_env.current_step, rl1.stock_env._next_observation_test())
                                    action, _states = rl1.model.predict(rl1.stock_env._next_observation_test())
                                else:
                                    rl2.stock_env.ss = self.ss.stock
                                    rl2.stock_env.c2 = self.ss.macd_crossing_by_threshold_min_len()
                                    rl2.stock_env.current_step = len(rl2.stock_env.c2.loc[:, 'open'].values) - 1
                                    # print(rl2.stock_env.current_step, rl2.stock_env._next_observation_test())
                                    action, _states = rl2.model.predict(rl2.stock_env._next_observation_test())

                                if not paper_trade:
                                    self.robin_order(action=action[0])
                                else:
                                    self.paper_order(action=action[0])

                                self.macd_order()
                    last_check_macd_datetime = check_macd_datetime
            elif self.cur_time >= '15:56:00:000000' and self.cur_time < '16:02:00:000000':
                if market_closed is False:
                    market_closed = True
                    # close_market_sell
                    if not paper_trade:
                        self.robin_order(action=1, close_market_sell=True)
                    else:
                        self.paper_order(action=action[0], close_market_sell=True)

                    self.macd_order(close_market_sell=True)

                    self.archive_p()

                    macd_crossing_count = 0
                    if self.MACD_CROSSING_WAIT == 0:            #reset after rerun
                        self.MACD_CROSSING_WAIT = 0     #6             #5
            elif self.cur_time >= "16:02:00:000000" and self.cur_time < '21:00:00:000000':
                self.current_state = 'postmarket'
                refresh_history = True

            if self.cur_time >= "00:00:00:000000" and self.cur_time < '21:00:00:000000' and save_history_status is False:        #save df
                self.save_history()
                save_history_status = True

            if self.cur_time >= '21:00:00:000000' and refresh_history is True:                  #save df then empty df
                self.reset_history()
                refresh_history = False

            if self.cur_time >= '21:00:00:000000' and finnhub_connect_status is True:           # close finnhub
                self.subs.ws.close()
                finnhub_connect_status = False

            if self.cur_time >= '21:00:00:000000' and robin_login_status is True:               # logout robin
                self.robin_logout()
                robin_login_status = False

            if self.cur_time > '21:00:00:000000':
                self.current_state = 'sleep'

            if self.current_state == 'sleep':
                sleep_time = 60       #10  # 60 * 10            # sleep 1 min
            elif self.current_state == 'postmarket':
                sleep_time = 0  # 10  # 60 * 10            # sleep 1 min
            elif self.current_state == 'market':
                sleep_time = 0
            else:
                sleep_time = 0      #1

            time.sleep(sleep_time)
            self.current_time = datetime.now()

    def encode_json(self, data):
        data_dict_1 = json.dumps(data, cls=CustomEncoder, default=str)
        return json.loads(data_dict_1)


class CustomEncoder(json.JSONEncoder):  # use CustomEncoder to fix pymongo error with numpy float(32)
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
    ticker='TSLA'
    short = 12      #3  #6
    long = 26       #7  #13
    signal = 9      #19 #9
    tname = 'sec_macd_1'
    mmt = MinMACDTrader(ticker=ticker, short=short, long=long, signal=signal, tname=tname)
    mmt.reload()
    #mmt.run()
    mmt.run(paper_trade=True)
    #mmt.run(rerun=True)

    '''
    start = datetime.now()
    mmt.reload_df()
    mmt.save_history()
    end = datetime.now()
    dur = end - start
    print(start, end, dur)
    '''

    '''
    mmt.robin_login()
    mmt.robin_order(action=0)
    mmt.p_rl['share'] = 5.9
    mmt.robin_order(action=1)
    mmt.robin_order(action=1,close_market_sell=True)

    '''
