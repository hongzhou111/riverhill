import robin_stocks.robinhood as rh
from time import sleep
import pandas as pd
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

class Robin:
    def __init__(self, ticker, tname='min_macd_1'):
        self.ticker = ticker
        self.tname = tname
        login = rh.login(username='hongzhou111@gmail.com',
                 password='Xiaominlin111')      #,
                 #expiresIn=86400,
                 #by_sms=True)          # sms code=283872
        #print(login)

        self.tname = 'min_rl_macd_finnhub_' + ticker
        self.p_rl = {
            "tname": self.tname + '_rl',
            "symbol": ticker,
            "share": 1,
            "cash": 0.0,
            "init_investment": 10,
            "actions": []
        }

        self.current_time = datetime.now()

    def robin_order(self, action, close_market_sell=False):
        # check robnin quanity
        my_stocks = rh.build_holdings()
        # my_stocks = {'TSLA': {'price': '187.880000', 'quantity': '4.96374100', 'average_buy_price': '187.0464',
        #          'equity': '932.59', 'percent_change': '0.45', 'intraday_percent_change': '0.45',
        #          'equity_change': '4.137774', 'type': 'stock', 'name': 'Tesla',
        #          'id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 'pe_ratio': '50.951300', 'percentage': '50.11'}}
        print(my_stocks)
        if self.ticker in my_stocks:
            robin_quantity = float(my_stocks[self.ticker]['quantity'])
        else:
            robin_quantity = 0

        if self.p_rl['share'] != robin_quantity:
            print('wrong share number: ', self.p_rl['share'], robin_quantity)
            self.p_rl['share'] = robin_quantity

        #price = s.loc[len(s.loc[: 'date']) - 1, 'close']
        price = 0
        share = 0
        value = 0
        status = 'None'
        if action < 1:      # and self.cur_time <= '14:30:00:000000':
            rl_action_type = 'buy'

            if self.p_rl['share'] == 0:
                if self.p_rl['cash'] == 0:
                    amount = self.p_rl['init_investment']
                else:
                    amount = self.p_rl['cash']
                print(amount)
                if amount > 1:
                    #robin_buy = rh.orders.order_buy_fractional_by_price(self.ticker, amount, timeInForce='gfd', extendedHours=False)        #gtc
                    #print(robin_buy)
                    robin_buy = {'id': '6436e133-bcde-44ea-bd9d-196a5b892bd7', 'ref_id': 'a1b9a2ee-07c5-4de2-856a-fcbc68c62bb5',
                     'url': 'https://api.robinhood.com/orders/6436e133-bcde-44ea-bd9d-196a5b892bd7/',
                     'account': 'https://api.robinhood.com/accounts/5SI52427/',
                     'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                     'cancel': 'https://api.robinhood.com/orders/6436e133-bcde-44ea-bd9d-196a5b892bd7/cancel/',
                     'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                     'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '0.00000000',
                     'average_price': None, 'fees': '0.00', 'state': 'unconfirmed', 'pending_cancel_open_agent': None,
                     'type': 'market', 'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': '9.03000000',
                     'stop_price': None, 'quantity': '1.11000000', 'reject_reason': None,
                     'created_at': '2023-04-12T16:49:55.723496Z', 'updated_at': '2023-04-12T16:49:55.726765Z',
                     'last_transaction_at': '2023-04-12T16:49:55.723496Z', 'executions': [], 'extended_hours': False,
                     'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False,
                     'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None,
                     'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
                     'total_notional': {'amount': '10.03', 'currency_code': 'USD',
                                        'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': None,
                     'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None,
                     'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None,
                     'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False,
                     'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True,
                     'order_form_version': 0, 'preset_percent_limit': None, 'order_form_type': None}
                    '''
                    robin_buy = {'id': '6435675e-1380-4e22-af68-0095e3433335', 'ref_id': 'c3ce0359-a02a-4878-949b-4ed050547379', 'url': 'https://api.robinhood.com/orders/6435675e-1380-4e22-af68-0095e3433335/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None,
                        'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483',
                        'cumulative_quantity': '4.95991400', 'average_price': '187.59800000', 'fees': '0.00', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market',
                        'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate',
                        'price': '187.61000000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                        #'price': '187.61000000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None,
                        'created_at': '2023-04-11T13:57:50.938320Z', 'updated_at': '2023-04-11T13:57:52.248640Z', 'last_transaction_at': '2023-04-11T13:57:51.935573Z', 'executions': [{'price': '187.59800000', 'quantity': '4.95991400', 'rounded_notional': '930.47000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T13:57:51.345000Z', 'id': '6435675f-105e-43bd-9e78-71fd3bdee706', 'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': {'amount': '930.47000000', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'total_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}
                    '''
                    price = float(robin_buy.get('paverage_rice', 0))
                    print(price)
                    share = float(robin_buy.get('cumulative_quantity', 0))
                    value = share * price
                    status = robin_buy.get('state', 'Failed')
        elif action < 2:
            rl_action_type = 'sell'

            #if True:
            if self.p_rl['share'] > 0:
                #robin_sell = rh.order_sell_fractional_by_quantity(self.ticker, self.p_rl['share'], timeInForce='gfd', extendedHours=False)          #gtc
                robin_sell = {'id': '64396508-3f5b-4e8c-8789-03dfca6f2efe', 'ref_id': 'd01bd759-ab3b-440e-82cf-ce89212498c4',
                 'url': 'https://api.robinhood.com/orders/64396508-3f5b-4e8c-8789-03dfca6f2efe/',
                 'account': 'https://api.robinhood.com/accounts/5SI52427/',
                 'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                 'cancel': 'https://api.robinhood.com/orders/64396508-3f5b-4e8c-8789-03dfca6f2efe/cancel/',
                 'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                 'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '0.00000000',
                 'average_price': None, 'fees': '0.00', 'state': 'unconfirmed', 'pending_cancel_open_agent': None,
                 'type': 'market', 'side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': None,
                 'stop_price': None, 'quantity': '1.11000000', 'reject_reason': None,
                 'created_at': '2023-04-14T14:36:56.739653Z', 'updated_at': '2023-04-14T14:36:56.743824Z',
                 'last_transaction_at': '2023-04-14T14:36:56.739653Z', 'executions': [], 'extended_hours': False,
                 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False,
                 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None,
                 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
                 'total_notional': None, 'executed_notional': None, 'investment_schedule_id': None,
                 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None,
                 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None,
                 'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False,
                 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True,
                 'order_form_version': 0, 'preset_percent_limit': None, 'order_form_type': None}
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
                print(robin_sell)
                share = -1 * float(robin_sell.get('cumulative_quantity',0))
                status = robin_sell.get('state', 'Failed')
                price = robin_sell.get('average_price', 0)
                if price is not None:
                    price = float(price)
                else:
                    time.sleep(2)
                    _id = robin_sell.get('id')
                    _order_info = rh.get_stock_order_info(_id)
                    print(_order_info)
                    '''
                    _order_info = {'id': '64396508-3f5b-4e8c-8789-03dfca6f2efe', 'ref_id': 'd01bd759-ab3b-440e-82cf-ce89212498c4',
                     'url': 'https://api.robinhood.com/orders/64396508-3f5b-4e8c-8789-03dfca6f2efe/',
                     'account': 'https://api.robinhood.com/accounts/5SI52427/',
                     'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                     'cancel': None,
                     'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
                     'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '1.11000000',
                     'average_price': '9.29730000', 'fees': '0.00', 'state': 'filled',
                     'pending_cancel_open_agent': None, 'type': 'market', 'side': 'sell', 'time_in_force': 'gfd',
                     'trigger': 'immediate', 'price': None, 'stop_price': None, 'quantity': '1.11000000',
                     'reject_reason': None, 'created_at': '2023-04-14T14:36:56.739653Z',
                     'updated_at': '2023-04-14T14:36:57.847445Z', 'last_transaction_at': '2023-04-14T14:36:57.546933Z',
                     'executions': [{'price': '9.29500000', 'quantity': '0.11000000', 'rounded_notional': '1.02000000',
                                     'settlement_date': '2023-04-18', 'timestamp': '2023-04-14T14:36:56.971973Z',
                                     'id': '64396508-f6ec-4da2-a536-05b9ad649986', 'ipo_access_execution_rank': None},
                                    {'price': '9.30000000', 'quantity': '1.00000000', 'rounded_notional': '9.30000000',
                                     'settlement_date': '2023-04-18', 'timestamp': '2023-04-14T14:36:57.047000Z',
                                     'id': '64396509-5dcd-4b3e-8fa9-48ba9aed16e5', 'ipo_access_execution_rank': None}],
                     'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False,
                     'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None,
                     'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None,
                     'dollar_based_amount': None, 'total_notional': None,
                     'executed_notional': {'amount': '10.32', 'currency_code': 'USD',
                                           'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
                     'investment_schedule_id': None, 'is_ipo_access_order': False,
                     'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None,
                     'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None,
                     'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True,
                     'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 0,
                     'preset_percent_limit': None, 'order_form_type': None}
                    '''
                    price = float(_order_info.get('average_price', 0))
                    status = _order_info.get('state', 'Failed')

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
            "fitness": {'date': self.current_time, 'model_predict': action},     #,
                        #'accum': s.loc[len(s.loc[: 'date']) - 2, 'accum'], 'l': s.loc[len(s.loc[: 'date']) - 2, 'len']},
            "price": price,
            "share": share,
            "value": value,
            "status": status
        }
        if close_market_sell is True:
            rl_o['fitness'] = {'date': self.current_time, 'reason': 'close_market_sell'}

        print(rl_o)
        self.p_rl['actions'].append(rl_o)
        print(self.p_rl)

    def check_robin_holdings(self):
        # check robnin quanity
        my_stocks = rh.build_holdings()
        #my_stocks = {'TSLA': {'price': '187.880000', 'quantity': '4.96374100', 'average_buy_price': '187.0464',
        #                      'equity': '932.59', 'percent_change': '0.45', 'intraday_percent_change': '0.45',
        #                      'equity_change': '4.137774', 'type': 'stock', 'name': 'Tesla',
        #                      'id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 'pe_ratio': '50.951300',
        #                      'percentage': '50.11'}}
        print(my_stocks)
        if self.ticker in my_stocks:
            robin_quantity = float(my_stocks[self.ticker]['quantity'])
        else:
            robin_quantity = 0
        print(self.ticker, robin_quantity)

if __name__ == '__main__':
    tname = 'min_macd_1'
    #r = Robin(ticker='TSLA', tname=tname)
    r = Robin(ticker='NIO', tname=tname)
    #r.check_robin_holdings()

    r.robin_order(0)
    #r.robin_order(1)
    #r.robin_order(2)

#price = rh.stocks.get_latest_price('TSLA', includeExtendedHours=True)
#print(price)
#pos = rh.account.get_all_positions()
#print(pos)
#acc = rh.account.load_phoenix_account()
#print(acc)
#orders = rh.orders.get_all_open_stock_orders()
#orders = rh.orders.get_all_stock_orders()
#print(orders)


#get_stock_order_info(orderID)


'''
rh.orders.order_buy_fractional_by_quantity('AAPL',
                                          7.3,
                                          timeInForce='gtc',
                                          extendedHours=False)

positions_data = rh.get_current_positions()
>>> ## Note: This for loop adds the stock ticker to every order, since Robinhood
>>> ## does not provide that information in the stock orders.
>>> ## This process is very slow since it is making a GET request for each order.
>>> for item in positions_data:
>>>     item['symbol'] = rh.get_symbol_by_url(item['instrument'])
>>> TSLAData = [item for item in positions_data if item['symbol'] == 'TSLA']
>>> sellQuantity = float(TSLAData['quantity'])//2.0
>>> rh.order_sell_limit('TSLA',sellQuantity,200.00)


get_all_open_stock_orders

order = rh.order_buy_market(stock, quantity, jsonify=False)
# Feel free to use more advanced orders
attempts = 0
while order.status_code != 200 and attempts < max_attempts:
    order = rh.order_buy_market(stock, quantity, jsonify=False)
    attempts += 1
    sleep(sleep_time)

if attempts == max_attempts:
    print(f"ERROR CODE: {order.status_code}")
    print("max number of tries exceeded. Order failed because ")
    data = order.json()
    print(data['detail'])
    
#rh.logout()

acc = rh.account.load_phoenix_account()
{'account_buying_power': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '1069.52'}, 
    'cash_available_from_instant_deposits': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_currency_orders': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_dividends': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_equity_orders': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_options_collateral': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_orders': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'cash_held_for_restrictions': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 
    'crypto': None, 'crypto_buying_power': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '1069.52'}, 'equities': {'active_subscription_id': None, 'apex_account_number': '5SI52427', 'available_margin': None, 'equity': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2004.838213'}, 'margin_maintenance': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '375.289113'}, 'market_value': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '935.318213'}, 'opened_at': '2017-08-09T05:47:50.736297Z', 'rhs_account_number': '122524275', 'total_margin': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}}, 'extended_hours_portfolio_equity': None, 'instant_allocated': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 'levered_amount': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '0'}, 'near_margin_call': False, 'options_buying_power': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '1069.52'}, 'portfolio_equity': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2004.838213'}, 'portfolio_previous_close': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2000'}, 'previous_close': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2000'}, 'regular_hours_portfolio_equity': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2004.838213'}, 'total_equity': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2004.838213'}, 'total_extended_hours_equity': None, 'total_extended_hours_market_value': None, 'total_market_value': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '935.318213'}, 'total_regular_hours_equity': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '2004.838213'}, 'total_regular_hours_market_value': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '935.318213'}, 'uninvested_cash': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '1069.52'}, 'withdrawable_cash': {'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762', 'amount': '141.08'}, 'margin_health': {'margin_buffer': '1.0000', 'margin_health_state': 'healthy', 'margin_buffer_amount': {'amount': '2004.94', 'currency_code': 'USD', 'currency_id': 'USD'}}}

#pos = rh.account.get_all_positions()
[{'url': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 
'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 
'account': 'https://api.robinhood.com/accounts/5SI52427/', 
'account_number': '5SI52427', 'average_buy_price': '187.0464', 'pending_average_buy_price': '187.0464', 
'quantity': '4.96374100', 'intraday_average_buy_price': '187.0464', 'intraday_quantity': '4.96374100', 
'shares_available_for_exercise': '4.96374100', 
'shares_held_for_buys': '0.00000000', 'shares_held_for_sells': '0.00000000', 'shares_held_for_stock_grants': '0.00000000', 
'shares_held_for_options_collateral': '0.00000000', 'shares_held_for_options_events': '0.00000000', 'shares_pending_from_options_events': '0.00000000', 
'shares_available_for_closing_short_position': '0.00000000', 
'ipo_allocated_quantity': '0.00000000', 
'ipo_dsp_allocated_quantity': '0.00000000', 'avg_cost_affected': False, 'avg_cost_affected_reason': [], 'is_primary_account': True, 'updated_at': '2023-04-11T16:05:46.594402Z', 'created_at': '2023-04-11T13:57:50.974802Z'}]

#orders = rh.orders.get_all_stock_orders()
[{'id': '64358559-f3da-4d88-86ba-22087ebccc16', 'ref_id': 'ae47ca28-3472-482e-9697-7e97cc5f6e78', 
'url': 'https://api.robinhood.com/orders/64358559-f3da-4d88-86ba-22087ebccc16/', 
'account': 'https://api.robinhood.com/accounts/5SI52427/', 
'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None, 
'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 
'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 
'cumulative_quantity': '4.96374100', 
'average_price': '187.04640000', 'fees': '0.00', 
'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market', 'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate', 
'price': '187.03000000', 'stop_price': None, 'quantity': '4.96374100', 'reject_reason': None, 
'created_at': '2023-04-11T16:05:45.458679Z', 'updated_at': '2023-04-11T16:05:46.477923Z', 'last_transaction_at': '2023-04-11T16:05:46.168159Z', 
'executions': [
    {'price': '187.04640000', 'quantity': '4.96374100', 'rounded_notional': '928.45000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T16:05:45.723000Z', 
    'id': '6435855a-962f-4688-b88f-1badfa583735', 'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 
    'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 
    'dollar_based_amount': {'amount': '928.45000000', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 
    'total_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 
    'executed_notional': {'amount': '928.45', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 
    'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 
    'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 
    'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}, 

{'id': '64357423-29c8-4c21-a97e-99c1427ad6f2', 'ref_id': 'f1267061-68a8-4cec-a102-00fc8d7f5a9b', 'url': 'https://api.robinhood.com/orders/64357423-29c8-4c21-a97e-99c1427ad6f2/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None, 
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
    'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}, 

{'id': '6435675e-1380-4e22-af68-0095e3433335', 'ref_id': 'c3ce0359-a02a-4878-949b-4ed050547379', 'url': 'https://api.robinhood.com/orders/6435675e-1380-4e22-af68-0095e3433335/', 'account': 'https://api.robinhood.com/accounts/5SI52427/', 'position': 'https://api.robinhood.com/positions/5SI52427/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'cancel': None, 
    'instrument': 'https://api.robinhood.com/instruments/e39ed23a-7bd1-4587-b060-71988d9ef483/', 'instrument_id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 
    'cumulative_quantity': '4.95991400', 'average_price': '187.59800000', 'fees': '0.00', 'state': 'filled', 'pending_cancel_open_agent': None, 'type': 'market', 
    'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate', 
    'price': '187.61000000', 'stop_price': None, 'quantity': '4.95991400', 'reject_reason': None, 
    'created_at': '2023-04-11T13:57:50.938320Z', 'updated_at': '2023-04-11T13:57:52.248640Z', 'last_transaction_at': '2023-04-11T13:57:51.935573Z', 'executions': [{'price': '187.59800000', 'quantity': '4.95991400', 'rounded_notional': '930.47000000', 'settlement_date': '2023-04-13', 'timestamp': '2023-04-11T13:57:51.345000Z', 'id': '6435675f-105e-43bd-9e78-71fd3bdee706', 'ipo_access_execution_rank': None}], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None, 'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': {'amount': '930.47000000', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'total_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': {'amount': '930.47', 'currency_code': 'USD', 'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 2, 'preset_percent_limit': None, 'order_form_type': 'collaring_removal'}]

order returns:
 "updated_at": "2016-04-01T21:24:13.698563Z",
    "executions": [],
    "time_in_force": "gtc",
    "fees": "0.00",
    "cancel": "https://api.robinhood.com/orders/15390ade-face-caca-0987-9fdac5824701/cancel/",
    "id": "15390ade-face-caca-0987-9fdac5824701",
    "cumulative_quantity": "0.00000",
    "stop_price": null,
    "reject_reason": null,
    "instrument": "https://api.robinhood.com/instruments/50810c35-d215-4866-9758-0ada4ac79ffa/",
    "state": "queued",
    "trigger": "immediate",
    "type": "market",
    "override_dtbp_checks": false,
    "last_transaction_at": "2016-04-01T23:34:54.237390Z",
    "price": null,
    "client_id": null,
    "extended_hours": false,
    "account": "https://api.robinhood.com/accounts/8UD09348/",
    "url": "https://api.robinhood.com/orders/15390ade-face-caca-0987-9fdac5824701/",
    "created_at": "2016-04-01T22:12:14.890283Z",
    "side": "sell",
    "override_day_trade_checks": false,
    "position": "https://api.robinhood.com/positions/8UD09348/50810c35-d215-4866-9758-0ada4ac79ffa/",
    "average_price": null,
    "quantity": "1.00000"
    
{'TSLA': {'price': '187.880000', 'quantity': '4.96374100', 'average_buy_price': '187.0464', 'equity': '932.59', 'percent_change': '0.45', 'intraday_percent_change': '0.45', 'equity_change': '4.137774', 'type': 'stock', 'name': 'Tesla', 'id': 'e39ed23a-7bd1-4587-b060-71988d9ef483', 'pe_ratio': '50.951300', 'percentage': '50.11'}}

    {'id': '64419401-cbd1-4b81-9232-b5083900abb1', 'ref_id': 'affdd4c0-6a30-4dfe-b3d5-7ef9fcd78049',
     'url': 'https://api.robinhood.com/orders/64419401-cbd1-4b81-9232-b5083900abb1/',
     'account': 'https://api.robinhood.com/accounts/5SI52427/',
     'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
     'cancel': 'https://api.robinhood.com/orders/64419401-cbd1-4b81-9232-b5083900abb1/cancel/',
     'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
     'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '0.00000000',
     'average_price': None, 'fees': '0.00', 'state': 'unconfirmed', 'pending_cancel_open_agent': None, 'type': 'market',
     'side': 'buy', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': '8.27000000', 'stop_price': None,
     'quantity': '1.21000000', 'reject_reason': None, 'created_at': '2023-04-20T19:35:29.436867Z',
     'updated_at': '2023-04-20T19:35:29.439625Z', 'last_transaction_at': '2023-04-20T19:35:29.436867Z',
     'executions': [], 'extended_hours': False, 'market_hours': 'regular_hours', 'override_dtbp_checks': False,
     'override_day_trade_checks': False, 'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None,
     'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
     'total_notional': {'amount': '10.01', 'currency_code': 'USD',
                        'currency_id': '1072fc76-1862-41ab-82c2-485837590762'}, 'executed_notional': None,
     'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None,
     'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None,
     'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False, 'is_visible_to_user': True,
     'has_ipo_access_custom_price_limit': False, 'is_primary_account': True, 'order_form_version': 0,
     'preset_percent_limit': None, 'order_form_type': None}

        robin_sell = {'id': '644194fa-1d91-4cad-b6ea-7869dfa3028f', 'ref_id': '7e2e040b-cf9c-4180-b217-7ed0ae2e4a5c',
         'url': 'https://api.robinhood.com/orders/644194fa-1d91-4cad-b6ea-7869dfa3028f/',
         'account': 'https://api.robinhood.com/accounts/5SI52427/',
         'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
         'cancel': 'https://api.robinhood.com/orders/644194fa-1d91-4cad-b6ea-7869dfa3028f/cancel/',
         'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
         'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '0.00000000',
         'average_price': None, 'fees': '0.00', 'state': 'unconfirmed', 'pending_cancel_open_agent': None,
         'type': 'market', 'side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': None,
         'stop_price': None, 'quantity': '1.21000000', 'reject_reason': None,
         'created_at': '2023-04-20T19:39:38.126385Z', 'updated_at': '2023-04-20T19:39:38.129382Z',
         'last_transaction_at': '2023-04-20T19:39:38.126385Z', 'executions': [], 'extended_hours': False,
         'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False,
         'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None,
         'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
         'total_notional': None, 'executed_notional': None, 'investment_schedule_id': None,
         'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None, 'ipo_access_lower_collared_price': None,
         'ipo_access_upper_collared_price': None, 'ipo_access_upper_price': None, 'ipo_access_lower_price': None,
         'is_ipo_access_price_finalized': False, 'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False,
         'is_primary_account': True, 'order_form_version': 0, 'preset_percent_limit': None, 'order_form_type': None}
        robin_sell_hist = {'id': '644194fa-1d91-4cad-b6ea-7869dfa3028f', 'ref_id': '7e2e040b-cf9c-4180-b217-7ed0ae2e4a5c',
         'url': 'https://api.robinhood.com/orders/644194fa-1d91-4cad-b6ea-7869dfa3028f/',
         'account': 'https://api.robinhood.com/accounts/5SI52427/',
         'position': 'https://api.robinhood.com/positions/5SI52427/9f1399e5-5023-425a-9eb5-cd3f91560189/',
         'cancel': None, 'instrument': 'https://api.robinhood.com/instruments/9f1399e5-5023-425a-9eb5-cd3f91560189/',
         'instrument_id': '9f1399e5-5023-425a-9eb5-cd3f91560189', 'cumulative_quantity': '1.21000000',
         'average_price': '8.27270000', 'fees': '0.00', 'state': 'filled', 'pending_cancel_open_agent': None,
         'type': 'market', 'side': 'sell', 'time_in_force': 'gfd', 'trigger': 'immediate', 'price': None,
         'stop_price': None, 'quantity': '1.21000000', 'reject_reason': None,
         'created_at': '2023-04-20T19:39:38.126385Z', 'updated_at': '2023-04-20T19:39:39.246743Z',
         'last_transaction_at': '2023-04-20T19:39:38.949467Z', 'executions': [
            {'price': '8.27500000', 'quantity': '0.21000000', 'rounded_notional': '1.74000000',
             'settlement_date': '2023-04-24', 'timestamp': '2023-04-20T19:39:38.281368Z',
             'id': '644194fa-e3bb-441e-804a-87e004241d1e', 'ipo_access_execution_rank': None},
            {'price': '8.27440000', 'quantity': '1.00000000', 'rounded_notional': '8.27000000',
             'settlement_date': '2023-04-24', 'timestamp': '2023-04-20T19:39:38.333000Z',
             'id': '644194fa-e32e-41a5-be2b-6ba4a018fdac', 'ipo_access_execution_rank': None}], 'extended_hours': False,
         'market_hours': 'regular_hours', 'override_dtbp_checks': False, 'override_day_trade_checks': False,
         'response_category': None, 'stop_triggered_at': None, 'last_trail_price': None,
         'last_trail_price_updated_at': None, 'last_trail_price_source': None, 'dollar_based_amount': None,
         'total_notional': None, 'executed_notional': {'amount': '10.01', 'currency_code': 'USD',
                                                       'currency_id': '1072fc76-1862-41ab-82c2-485837590762'},
         'investment_schedule_id': None, 'is_ipo_access_order': False, 'ipo_access_cancellation_reason': None,
         'ipo_access_lower_collared_price': None, 'ipo_access_upper_collared_price': None,
         'ipo_access_upper_price': None, 'ipo_access_lower_price': None, 'is_ipo_access_price_finalized': False,
         'is_visible_to_user': True, 'has_ipo_access_custom_price_limit': False, 'is_primary_account': True,
         'order_form_version': 0, 'preset_percent_limit': None, 'order_form_type': None}



'''
