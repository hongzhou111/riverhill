import pandas as pd
from test_mongo import MongoExplorer
import requests
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
from datetime import datetime
import logging
import time
import numpy as np

class TS_Trader:
    def __init__(self, account_id, buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, size_threshold=0, stop_loss=100, quantity=1, simulator=False):
        self.mongo = MongoExplorer()
        self.account_id = account_id

        self.buy_thresholds = buy_thresholds
        self.sell_thresholds = sell_thresholds
        self.buy_to_cover_thresholds = buy_to_cover_thresholds
        self.sell_short_thresholds = sell_short_thresholds
        self.size_threshold = size_threshold
        self.stop_loss = stop_loss
        self.quantity = quantity

        self.holding_long = {}
        self.holding_short = {}
        self.balance = {}
        self.boh_balance = {}
        self.hourly_stop_loss_hit = {}
        self.trade_price = {}

        self.simulator = simulator

    def read_lvl1(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl1"
        lvl1 = None
        while lvl1 is None:
            lvl1 = self.mongo.mongoDB[collection].find_one({"CurTime": time})
        return lvl1

    def read_lvl2(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl2"
        df = pd.DataFrame()
        while df.empty:
            df = pd.DataFrame(list(self.mongo.mongoDB[collection].find({"CurTime": time})))
        return df

    def calc_volume_sum(self, symbol, time, hour):
        lvl1 = self.read_lvl1(symbol, time)
        df = self.read_lvl2(symbol, time)
        print(lvl1["Last"])
        df["Dif"] = (df["Price"] - lvl1["Last"])
        df = df[["GetTime", "Side", "Price", "Dif", "TotalSize"]]
        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] > 0))
                    | ((df["Side"] == "Ask") & (df["Dif"] < 0))]
        df["VolumeSum"]= df["TotalSize"] * df["Dif"]
        if not df.empty:
            print(df)
        return lvl1["Last"], df["VolumeSum"].sum()

    def trade_shares(self, symbol, action, quantity):
        if self.simulator:
            url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"
        else:
            url = "https://api.tradestation.com/v3/orderexecution/orders"
        access_token = self.mongo.mongoDB["TS_auth"].find_one({"account_id": self.account_id})["access_token"]
        payload = {
            "AccountID": self.account_id,
            "Symbol": symbol,
            "Quantity": str(quantity),
            "OrderType": "Market",
            "TradeAction": action,
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {"content-type": "application/json", "Authorization": f"Bearer {access_token}"}
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code != 200:
            logging.warning(f"{symbol} {action} {response.text}")
            return None, None
        response = response.json()
        if (self.simulator and "Confirmations" not in response) or (not self.simulator and "Orders" not in response):
            logging.warning(f"{symbol} {action} {response}")
            return None, None

        if self.simulator:
            price = float(response["Confirmations"][0]["EstimatedPrice"])
            filled_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            status_response = self.check_status(response["Orders"][0]["OrderID"])
            if status_response is False:
                return None, None
            price = float(status_response["Orders"][0]["FilledPrice"])
            filled_time = status_response["Orders"][0]["ClosedDateTime"]

        if action == "BUY":
            self.holding_long[symbol] = True
            self.balance[symbol] = self.balance[symbol] - (price * quantity)
            self.trade_price[symbol] = price
        elif action == "SELL":
            self.holding_long[symbol] = False
            self.balance[symbol] = self.balance[symbol] + (price * quantity)
        elif action == "SELLSHORT":
            self.holding_short[symbol] = True
            self.balance[symbol] = self.balance[symbol] + (price * quantity)
            self.trade_price[symbol] = price
        elif action == "BUYTOCOVER":
            self.holding_short[symbol] = False
            self.balance[symbol] = self.balance[symbol] - (price * quantity)
        return filled_time, price
        
    def check_status(self, order_id):
        url = f"https://api.tradestation.com/v3/brokerage/accounts/{self.account_id}/orders/{order_id}"
        for _ in range(5):
            access_token = self.mongo.mongoDB["TS_auth"].find_one({"account_id": self.account_id})["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.request("GET", url, headers=headers)
            if response.status_code != 200:
                logging.warning(f"{order_id} {response.text}")
            response = response.json()
            if response["Orders"][0]["Status"] == "FLL":
                return response
            print(response)
            time.sleep(.5)
        return False
    
    def trade(self, symbol, hour, long):
        collection = f"{symbol}_ts_trades"
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(time)
        last_price, volume_sum = self.calc_volume_sum(symbol, time, hour)
        print(volume_sum)
        if self.hourly_stop_loss_hit[symbol]:
            return
        action = None
        if long:
            if not self.holding_long[symbol] and volume_sum > self.buy_thresholds[hour]:
                action = "BUY"
            elif self.holding_long[symbol] and self.boh_balance[symbol] - (self.balance[symbol] + (last_price * self.quantity)) >= self.stop_loss:
                action = "SELL"
                self.hourly_stop_loss_hit[symbol] = True
            elif self.holding_long[symbol] and volume_sum < self.sell_thresholds[hour]:
                action = "SELL"
        else:
            if not self.holding_short[symbol] and volume_sum < self.sell_short_thresholds[hour]:
                action = "SELLSHORT"
            elif self.holding_short[symbol] and self.boh_balance[symbol] - (self.balance[symbol] - (last_price * self.quantity)) >= self.stop_loss:
                action = "BUYTOCOVER"
                self.hourly_stop_loss_hit[symbol] = True
            elif self.holding_short[symbol] and volume_sum > self.buy_to_cover_thresholds[hour]:
                action = "BUYTOCOVER"

        if action is not None:
            filled_time, price = self.trade_shares(symbol, action, self.quantity)
            dict = {"Time": time, "FilledTime": filled_time, "Action": action, "Price": price, "Balance": self.balance[symbol], "VolumeSum": volume_sum}
            with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
                f.write(f"{dict}\n")
            self.mongo.mongoDB[collection].insert_one(dict)
    
    def close_eoh(self, symbol):
        collection = f"{symbol}_ts_trades"
        time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        action = None
        if self.holding_long[symbol]:
            action = "SELL"
        elif self.holding_short[symbol]:
            action = "BUYTOCOVER"
        if action is not None:
            filled_time, price = self.trade_shares(symbol, action, self.quantity)
            dict = {"Time": time, "FilledTime": filled_time, "Action": action, "Price": price, "Balance": self.balance[symbol]}
            with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
                f.write(f"{dict}\n")
            self.mongo.mongoDB[collection].insert_one(dict)
        self.boh_balance[symbol] = self.balance[symbol]
        self.hourly_stop_loss_hit[symbol] = False

    def close_eod(self, symbol):
        self.close_eoh(symbol)
        date = datetime.utcnow().strftime("%Y-%m-%d")
        start = f"{date}T13:30:00Z"
        end = f"{date}T19:55:00Z"
        collection = f"{symbol}_10sec_ts_lvl1"
        with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
            start_price = pd.DataFrame(list(self.mongo.mongoDB[collection].find({"CurTime": start})))["Last"].loc[0]
            end_price = pd.DataFrame(list(self.mongo.mongoDB[collection].find({"CurTime": end})))["Last"].loc[0]
            f.write(f"EOD Balance: {self.balance[symbol]} = {self.balance[symbol]/self.quantity} per share  = {self.balance[symbol] * (100/self.quantity) /start_price}%\n")
            f.write(f"Market Change: {end_price - start_price} = {(end_price - start_price) * 100 / (start_price)}%\n")
            f.write("\n")
    
    def reset_bod(self, symbol):
        self.balance[symbol] = 0
        self.boh_balance[symbol] = 0
        self.hourly_stop_loss_hit[symbol] = False

#     def start_scheduler(self, symbols):
#         executors = {
#             'default': ThreadPoolExecutor(100),
#             'processpool': ProcessPoolExecutor(8)
#         }
#         scheduler = BlockingScheduler(executors=executors, timezone=utc)
#         for symbol in symbols:
#             self.holding_long[symbol] = False
#             self.holding_short[symbol] = False
#             self.balance[symbol] = 0
#             scheduler.add_job(self.reset_bod, 'cron', args=[symbol],
#                 day_of_week='mon-fri', hour="13", minute="25")
#             scheduler.add_job(self.trade, 'cron', args=[symbol, 13, True],
#                 day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
#             scheduler.add_job(self.close_eoh, 'cron', args=[symbol], 
#                 day_of_week='mon-fri', hour="13", minute="59", second="55")
#             for hr in range(14, 19):
#                 scheduler.add_job(self.trade, 'cron', args=[symbol, hr, True],
#                     day_of_week='mon-fri', hour=hr, second="*/10")
#                 scheduler.add_job(self.close_eoh, 'cron', args=[symbol], 
#                     day_of_week='mon-fri', hour=hr, minute="59", second="55")
#             scheduler.add_job(self.trade, 'cron', args=[symbol, 19, True],
#                 day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
#             scheduler.add_job(self.close_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
#         scheduler.start()

# if __name__ == '__main__':
#     logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
#     logging.getLogger('apscheduler').setLevel(logging.WARNING)
#     #symbols = ['NVDA', 'AMZN', 'AAPL', 'GOOG', 'MSFT', 'TSLA', 'MDB', 'SMCI', 'COCO', 'RCM']   
#     buy_thresholds = {13: .045, 14: .13, 15: .08, 16: .045, 17: .035, 18: .135, 19: .02}
#     sell_thresholds = {13: -.055, 14: -.135, 15: -.18, 16: -.07, 17: -.09, 18: -.205, 19: -.065}
#     buy_to_cover_thresholds = {13: .045, 14: .24, 15: .035, 16: .055, 17: .035, 18: .08, 19: .02}
#     sell_short_thresholds = {13: -.055, 14: -.12, 15: -.085, 16: -.07, 17: -.09, 18: -.1, 19: -.065}
    
#     size_threshold = 0
#     simulator = False
#     trader = TS_Trader(buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, size_threshold, simulator)
#     trader.start_scheduler(["TSLA"])
