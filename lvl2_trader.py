import pandas as pd
from test_mongo import MongoExplorer
import requests
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
from datetime import datetime
from tradestation_reader import TS_Reader
import logging
import time
import numpy as np

class Lvl2Trader:
    def __init__(self, buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, size_threshold, simulator):
        self.ts_reader = TS_Reader()
        self.mongo = MongoExplorer()

        self.buy_thresholds = buy_thresholds
        self.sell_thresholds = sell_thresholds
        self.buy_to_cover_thresholds = buy_to_cover_thresholds
        self.sell_short_thresholds = sell_short_thresholds
        self.size_threshold = size_threshold

        self.holding_long = {}
        self.holding_short = {}
        self.balance = {}

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

    def calc_volume_sums(self, symbol, time, hour):
        lvl1 = self.read_lvl1(symbol, time)
        df = self.read_lvl2(symbol, time)
        df["Dif"] = (df["Price"] - lvl1["Last"])
        df = df[["GetTime", "Side", "Price", "Dif", "TotalSize"]]
        df_long = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= self.buy_thresholds[hour]))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= self.sell_thresholds[hour]))]
        df_long.loc[df_long["Side"] == "Bid", "Multiplier"] = df_long.loc[df_long["Side"] == "Bid", "Dif"] - self.buy_thresholds[hour]
        df_long.loc[df_long["Side"] == "Ask", "Multiplier"] = df_long.loc[df_long["Side"] == "Ask", "Dif"] - self.sell_thresholds[hour]
        print(df_long)
        df_short = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= self.buy_to_cover_thresholds[hour]))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= self.sell_short_thresholds[hour]))]
        df_short.loc[df_short["Side"] == "Bid", "Multiplier"] = df_short.loc[df_short["Side"] == "Bid", "Dif"] - self.buy_to_cover_thresholds[hour]
        df_short.loc[df_short["Side"] == "Ask", "Multiplier"] = df_short.loc[df_short["Side"] == "Ask", "Dif"] - self.sell_short_thresholds[hour]
        print(df_short)
        return (df_long["TotalSize"] * df_long["Multiplier"]).sum(), (df_short["TotalSize"] * df_short["Multiplier"]).sum()

    def trade_shares(self, symbol, action, quantity, time, volume_sum):
        collection = f"{symbol}_ts_trades"
        if self.simulator:
            url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"
        else:
            url = "https://api.tradestation.com/v3/orderexecution/orders"
        access_token = self.ts_reader.refresh()
        payload = {
            "AccountID": self.ts_reader.account_id,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": "Market",
            "TradeAction": action,
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {"content-type": "application/json", "Authorization": f"Bearer {access_token}"}
        
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code != 200:
            logging.warning(f"{symbol} {action} {response.text}")
            return
        response = response.json()
        if (self.simulator and "Confirmations" not in response) or (not self.simulator and "Orders" not in response):
            logging.warning(f"{symbol} {action} {response}")
            return

        if self.simulator:
            price = float(response["Confirmations"][0]["EstimatedPrice"])
            filled_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            status_response = self.check_status(response["Orders"][0]["OrderID"])
            if status_response is False:
                return
            price = float(status_response["Orders"][0]["FilledPrice"])
            filled_time = status_response["Orders"][0]["ClosedDateTime"]

        if action == "BUY":
            self.holding_long[symbol] = True
            self.balance[symbol] = self.balance[symbol] - price
        elif action == "SELL":
            self.holding_long[symbol] = False
            self.balance[symbol] = self.balance[symbol] + price
        elif action == "SELLSHORT":
            self.holding_short[symbol] = True
            self.balance[symbol] = self.balance[symbol] + price
        elif action == "BUYTOCOVER":
            self.holding_short[symbol] = False
            self.balance[symbol] = self.balance[symbol] - price
        dict = {"Time": time, "FilledTime": filled_time, "Action": action, "Price": price, "Balance": self.balance[symbol], "VolumeSum": volume_sum}
        with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
            f.write(f"{dict}\n")
        self.mongo.mongoDB[collection].insert_one(dict)
        
    def check_status(self, order_id):
        url = f"https://api.tradestation.com/v3/brokerage/accounts/{self.ts_reader.account_id}/orders/{order_id}"
        for i in range(5):
            access_token = self.ts_reader.refresh()
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
    
    def trade(self, symbol, hour):
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(time)
        long_volume_sum, short_volume_sum = self.calc_volume_sums(symbol, time, hour)
        print(long_volume_sum)
        print(short_volume_sum)
        if long_volume_sum > size_threshold and not self.holding_long[symbol]:
            self.trade_shares(symbol, "BUY", "1", time, long_volume_sum)
        elif long_volume_sum < -size_threshold and self.holding_long[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, long_volume_sum)
        # if short_volume_sum < -size_threshold and not self.holding_short[symbol]:
        #     self.trade_shares(symbol, "SELLSHORT", "1", time, short_volume_sum)
        # elif short_volume_sum > size_threshold and self.holding_short[symbol]:
        #     self.trade_shares(symbol, "BUYTOCOVER", "1", time, short_volume_sum)
    
    def close_eod(self, symbol):
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.holding_long[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, 0)
        if self.holding_short[symbol]:
            self.trade_shares(symbol, "BUYTOCOVER", "1", time, 0)

    def start_scheduler(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            self.holding_long[symbol] = False
            self.holding_short[symbol] = False
            self.balance[symbol] = 0
            scheduler.add_job(self.trade, 'cron', args=[symbol, 13], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            for hr in range(14, 19):
                scheduler.add_job(self.trade, 'cron', args=[symbol, hr], max_instances=2, \
                    day_of_week='mon-fri', hour=hr, second="*/10")
            scheduler.add_job(self.trade, 'cron', args=[symbol, 19], max_instances=2, \
                day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
            scheduler.add_job(self.close_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    #symbols = ['NVDA', 'AMZN', 'AAPL', 'GOOG', 'MSFT', 'TSLA', 'MDB', 'SMCI', 'COCO', 'RCM']   
    # price_dif_thresholds = {13: .069, 14: .069, 15: .052, 16: .13, 17: .03, 18: .011, 19: .031}
    # price_dif_thresholds = {13: -.07, 14: .069, 15: .147, 16: .045, 17: .028, 18: .011, 19: .09}
    # price_dif_thresholds = {13: .17, 14: .089, 15: .147, 16: .045, 17: .036, 18: .1, 19: .02}
    # price_dif_thresholds = {13: .17, 14: .089, 15: .147, 16: .1, 17: .03, 18: .1, 19: .07}
    # price_dif_thresholds = {13: .189, 14: .129, 15: .147, 16: .1, 17: .03, 18: .1, 19: .099}
    # price_dif_thresholds = {13: .189, 14: .129, 15: .147, 16: .04, 17: .03, 18: .1, 19: .02}
    # buy_thresholds = {13: .017, 14: .118, 15: .106, 16: -.1, 17: .026, 18: .100, 19: .02}
    # sell_thresholds = {13: -.232, 14: -.109, 15: -.180, 16: .666, 17: -.069, 18: -.580, 19: -.94}
    # # last gain = {13: 11.47, 14: 4.62, 15: 5.97, 16: 7.54, 17: 8.52, 18: 5.73, 19: 3.42}
    # buy_thresholds = {13: .04, 14: .12, 15: .1, 16: -.07, 17: .03, 18: .02, 19: .02}
    # sell_thresholds = {13: -.06, 14: -.13, 15: -.18, 16: -.07, 17: -.08, 18: .02, 19: -.05}
    # sell_short_thresholds = {13: -.06, 14: -.05, 15: -.07, 16: -.07, 17: -.08, 18: -.18, 19: -.05}
    # buy_to_cover_thresholds = {13: .04, 14: .12, 15: .16, 16: .1, 17: .03, 18: .08, 19: .02}
    # buy_thresholds = {13: .17, 14: .12, 15: .1, 16: -.07, 17: .03, 18: .02, 19: .02}
    # sell_thresholds = {13: -.21, 14: -.13, 15: -.18, 16: -.07, 17: -.08, 18: -.24, 19: -.05}
    # buy_to_cover_thresholds = {13: .04, 14: .12, 15: .16, 16: .1, 17: .03, 18: .08, 19: .02}
    # sell_short_thresholds = {13: -.06, 14: -.05, 15: -.07, 16: -.07, 17: -.08, 18: -.18, 19: -.05}
    buy_thresholds = {13: .04, 14: .12, 15: .02, 16: .04, 17: .03, 18: .03, 19: .02}
    sell_thresholds = {13: -.06, 14: -.08, 15: -.11, 16: -.07, 17: -.09, 18: -.22, 19: -.05}
    buy_to_cover_thresholds = {13: -.24, 14: .23, 15: .19, 16: .22, 17: .03, 18: .08, 19: .02}
    sell_short_thresholds = {13: -.1, 14: -.12, 15: -.12, 16: -.08, 17: -.09, 18: -.18, 19: -.05}
    size_threshold = 0
    simulator = False
    trader = Lvl2Trader(buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, size_threshold, simulator)
    trader.start_scheduler(["TSLA"])

"""
13: [0.04000000000000001, -0.06, 0.25999999999993406, -0.9500000000000455, 6.440000000000111, 0.7799999999999159, 3.429999999999893, -1.8500000000002501, 8.109999999999559]
14: [0.12, -0.13, 0.0, 3.2700000000000102, -1.7800000000000011, -0.4099999999999966, 0.0, 2.130000000000024, 0.7599999999999909, 0.0, 1.4800000000000182, 5.4500000000000455]
15: [0.1, -0.18, 1.8599999999999852, 1.6400000000000148, 0.0, 2.469999999999999, 0.0, 0.0, 0.0, 0.0, 3.569999999999993, 9.539999999999992]
16: [-0.07, -0.07, -0.8299999999999841, -0.8300000000000125, -0.5, 2.3700000000000614, 1.910000000000025, -0.9799999999999613, 1.400000000000034, 4.949999999999989, -2.4600000000000364, 5.030000000000115]
17: [0.03, -0.08000000000000002, 0.6000000000000227, 2.0299999999999727, 1.8000000000000114, 0.8699999999999477, 0.6800000000000068, 0.8199999999999932, 0.0, 0.4900000000000091, 2.4799999999999613, 9.769999999999925]
18: [0.01999999999999999, -0.24, 0.45000000000001705, -1.4699999999999989, 1.5600000000000023, 1.25, 0.4399999999999977, 0.1199999999999477, 0.5600000000000023, 0.9900000000000091, 2.9600000000000364, 6.860000000000014]
19: [0.01999999999999999, -0.04999999999999999, 1.9400000000000261, 0.47999999999996135, 0.14999999999997726, -0.060000000000002274, 2.5400000000001057, -1.2099999999999795, -0.5000000000000568, 1.6899999999999409, -0.1600000000001387, 4.869999999999834]
"""
"""
13: [0.04000000000000001, -0.06, -0.0700000000000216, 1.740000000000009, -0.029999999999972715, -2.210000000000207, -1.060000000000116, 5.36999999999972, 3.7399999999994122]
14: [0.12, -0.04999999999999999, 0.0, 4.199999999999989, 1.5699999999999648, 0.7800000000000011, -1.7800000000000296, -0.9099999999999966, 1.589999999999975, 1.660000000000025, 2.5699999999999363, 9.679999999999865]
15: [0.16, -0.07, 0.4299999999999784, 3.1100000000000136, 0.46999999999999886, -1.8100000000000023, 1.9800000000000182, -0.9499999999999886, 0.9800000000000182, 0.0, 5.880000000000052, 10.090000000000089]
16: [0.1, -0.07, 0.0, 0.5599999999999739, 0.0, -2.390000000000043, 0.0, 0.5699999999999932, 0.0, 0.0, 4.289999999999964, 3.0299999999998875]
17: [0.03, -0.08000000000000002, 0.0, 1.6099999999999852, 0.0, 0.32999999999992724, 0.0, 0.20999999999997954, 0.0, -0.5199999999999818, 0.0, 1.6299999999999102]
18: [0.07999999999999999, -0.18, 0.0, 0.0, 0.0, 0.0, 4.639999999999901, 0.0, 0.0, 0.0, 0.0, 4.639999999999901]
19: [0.01999999999999999, -0.04999999999999999, 0.10000000000002274, 0.06999999999996476, 0.3599999999999852, -0.25, 3.360000000000184, -0.23000000000007503, 0.4099999999998545, -2.2100000000000364, 3.189999999999827, 4.799999999999727]
"""


"""
13: ([0.04000000000000001, -0.06, 0.25999999999993406, -0.9500000000000455, 6.440000000000111, 0.7799999999999159, 3.429999999999893, -1.8500000000002501, 3.9499999999999886, 12.059999999999548], 
[-0.24, -0.09999999999999998, 0.0, 0.0, -0.22999999999998977, 0.040000000000020464, 0.009999999999990905, 1.8199999999999932, 0.36000000000001364, 2.0000000000000284])
14: ([0.12, -0.08000000000000002, 0.0, 3.219999999999999, -1.2800000000000296, 0.2400000000000091, 0.3199999999999932, 0.5, 0.7599999999999909, 0.0, 1.5, 0.0, 5.2599999999999625], 
[0.23, -0.12, 0.0, 0.0, 2.3000000000000114, 0.6999999999999886, 0.0, 0.8000000000000114, 2.6999999999999886, 0.0, 1.169999999999959, 2.680000000000007, 10.349999999999966])
15: ([0.01999999999999999, -0.10999999999999999, 1.2199999999999989, -0.7699999999999818, 0.24000000000003752, 1.5699999999999648, -1.5900000000000318, 0.7899999999999636, 0.20000000000004547, 1.3500000000000227, -0.5999999999999659, 5.919999999999959, 8.330000000000013], 
[0.19, -0.12, 0.0, 2.030000000000001, 0.0, -2.180000000000007, 0.0, 0.0, 0.0, 0.0, 4.670000000000016, 0.0, 4.52000000000001])
16: ([0.04000000000000001, -0.07, -1.0300000000000011, 1.1399999999999864, 0.8600000000000136, 1.8800000000000523, 1.8199999999999932, -0.31999999999993634, 1.4399999999999977, 3.240000000000009, -1.6300000000000523, -2.329999999999984, 5.070000000000078], 
[0.22, -0.08000000000000002, 0.0, 0.4899999999999807, 0.0, 0.0, 0.0, -1.0999999999999943, 0.0, 0.0, 4.159999999999968, 1.2399999999999523, 4.789999999999907])
17: ([0.03, -0.09000000000000002, 0.6400000000000148, 1.9499999999999886, 1.8000000000000114, 0.6200000000000045, 0.6499999999999773, 0.8199999999999932, -0.08999999999997499, 0.13999999999998636, 2.6399999999999864, 1.3799999999999955, 10.549999999999983], 
[0.03, -0.09000000000000002, 0.0, 1.6099999999999852, 0.0, 0.08999999999997499, 0.0, 0.8299999999999841, 0.0, -0.5199999999999818, 0.0, 0.0, 2.0099999999999625])
18: ([0.03, -0.21999999999999997, 0.28000000000000114, -1.5900000000000034, 1.0, 1.1800000000000068, 1.3299999999999557, 0.1199999999999477, 0.10000000000002274, 0.7199999999999704, 3.2099999999999795, 1.0299999999999727, 7.379999999999853], 
[0.07999999999999999, -0.18, 0.0, 0.0, 0.0, 0.0, 4.639999999999901, 0.0, 0.0, 0.0, 0.0, 0.0, 4.639999999999901])
19: ([0.01999999999999999, -0.04999999999999999, 1.9400000000000261, -0.35000000000002274, 0.2799999999999727, 0.17999999999994998, 2.8100000000001444, -1.2100000000000932, -0.5000000000000568, 1.6899999999999409, -0.0500000000001819, 1.0500000000000682, 5.839999999999748], 
[0.01999999999999999, -0.04999999999999999, 0.10000000000002274, 0.06999999999996476, 0.3599999999999852, -0.25, 3.360000000000184, -0.23000000000007503, 0.4099999999998545, -2.240000000000009, 3.189999999999827, 0.12000000000006139, 4.889999999999816])
"""

['Time', 'VolumeSum', 'BUY', 'SELL', 'Long', 'Short', 'Buy Action',
       'Sell Action', 'Gain'],