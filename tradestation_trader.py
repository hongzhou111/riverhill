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

class TS_Trader:
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
                    | ((df["Side"] == "Ask") & (df["Dif"] <= self.sell_thresholds[hour]))].copy()
        df_long.loc[df_long["Side"] == "Bid", "Multiplier"] = df_long.loc[df_long["Side"] == "Bid", "Dif"] - self.buy_thresholds[hour]
        df_long.loc[df_long["Side"] == "Ask", "Multiplier"] = df_long.loc[df_long["Side"] == "Ask", "Dif"] - self.sell_thresholds[hour]
        print(df_long)
        df_short = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= self.buy_to_cover_thresholds[hour]))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= self.sell_short_thresholds[hour]))].copy()
        df_short.loc[df_short["Side"] == "Bid", "Multiplier"] = df_short.loc[df_short["Side"] == "Bid", "Dif"] - self.buy_to_cover_thresholds[hour]
        df_short.loc[df_short["Side"] == "Ask", "Multiplier"] = df_short.loc[df_short["Side"] == "Ask", "Dif"] - self.sell_short_thresholds[hour]
        #print(df_short)
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
        for _ in range(5):
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
        #print(short_volume_sum)
        if long_volume_sum > self.size_threshold and not self.holding_long[symbol]:
            self.trade_shares(symbol, "BUY", "1", time, long_volume_sum)
        elif long_volume_sum < -self.size_threshold and self.holding_long[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, long_volume_sum)
        # if short_volume_sum < -size_threshold and not self.holding_short[symbol]:
        #     self.trade_shares(symbol, "SELLSHORT", "1", time, short_volume_sum)
        # elif short_volume_sum > size_threshold and self.holding_short[symbol]:
        #     self.trade_shares(symbol, "BUYTOCOVER", "1", time, short_volume_sum)
    
    def close_eoh(self, symbol):
        time = datetime.utcnow()
        if self.holding_long[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, 0)
        if self.holding_short[symbol]:
            self.trade_shares(symbol, "BUYTOCOVER", "1", time, 0)

    def close_eod(self, symbol):
        self.close_eoh(symbol)
        with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
            f.write("\n")

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
            scheduler.add_job(self.trade, 'cron', args=[symbol, 13], max_instances=2,
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.close_eoh, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="13", minute="59", second="55")
            for hr in range(14, 19):
                scheduler.add_job(self.trade, 'cron', args=[symbol, hr], max_instances=2,
                    day_of_week='mon-fri', hour=hr, second="*/10")
                scheduler.add_job(self.close_eoh, 'cron', args=[symbol], 
                    day_of_week='mon-fri', hour=hr, minute="59", second="55")
            scheduler.add_job(self.trade, 'cron', args=[symbol, 19], max_instances=2, \
                day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
            scheduler.add_job(self.close_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    #symbols = ['NVDA', 'AMZN', 'AAPL', 'GOOG', 'MSFT', 'TSLA', 'MDB', 'SMCI', 'COCO', 'RCM']   
    buy_thresholds = {13: .045, 14: .13, 15: .08, 16: .045, 17: .035, 18: .135, 19: .02}
    sell_thresholds = {13: -.055, 14: -.135, 15: -.18, 16: -.07, 17: -.09, 18: -.205, 19: -.065}
    buy_to_cover_thresholds = {13: .045, 14: .24, 15: .035, 16: .055, 17: .035, 18: .08, 19: .02}
    sell_short_thresholds = {13: -.055, 14: -.12, 15: -.085, 16: -.07, 17: -.09, 18: -.1, 19: -.065}
    
    size_threshold = 0
    simulator = False
    trader = TS_Trader(buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, size_threshold, simulator)
    trader.start_scheduler(["TSLA"])

"""
13: ([0.04500000000000001, -0.055, 1.089999999999975, -1.650000000000034, 6.440000000000055, 0.769999999999925, 3.430000000000007, -1.8500000000002501, 3.9499999999999886, 1.2200000000000273, 3.5600000000000307, 16.959999999999724], 
[0.04500000000000001, -0.055, 1.160000000000025, 0.9699999999999704, -0.05999999999997385, -2.2900000000000773, -0.3700000000000614, 5.319999999999766, -2.6499999999999773, 4.759999999999991, -2.130000000000024, 4.7099999999996385])
14: ([0.11499999999999999, -0.08, 0.0, 3.219999999999999, -1.2800000000000296, 0.2400000000000091, 0.3199999999999932, 0.5, 0.7599999999999909, 0.0, 1.5000000000000568, 0.0, -0.8300000000000125, 0.0, 4.430000000000007], 
[0.245, -0.12, 0.0, 0.0, 2.3000000000000114, 0.6999999999999886, 0.0, 0.8000000000000114, 2.6999999999999886, 0.0, 1.169999999999959, 2.680000000000007, 0.0, 0.0, 10.349999999999966])
15: ([0.07999999999999999, -0.185, 0.8299999999999841, 0.30000000000001137, 0.0, 1.9699999999999704, 0.0, 0.0, 0.5400000000000205, 0.0, 0.40999999999996817, 4.269999999999982, 2.4799999999999613, 0.0, 10.799999999999898], 
[0.175, -0.12, 0.0, 3.670000000000016, 0.0, -2.180000000000007, 0.0, 0.0, 0.0, 0.0, 3.8899999999999864, 0.0, -2.0300000000000296, 0.0, 3.349999999999966])
16: ([0.04500000000000001, -0.07, -0.6999999999999886, 1.1399999999999864, 0.8600000000000136, 1.8800000000000523, 1.8199999999999932, -0.31999999999996476, 1.2200000000000273, 3.590000000000032, -1.6300000000000523, -2.329999999999984, 1.6400000000000432, 2.609999999999985, 9.780000000000143], 
[0.05499999999999999, -0.07, 0.0, 0.5599999999999739, 0.0, -0.5199999999999818, 0.0, 0.29000000000002046, 0.0, 0.0, 2.0500000000000114, 1.6899999999999977, 0.36000000000001364, 3.039999999999992, 7.470000000000027])
17: ([0.0050000000000000044, -0.11, 0.6400000000000148, 1.9499999999999886, 2.219999999999999, 1.0699999999999932, 0.18000000000000682, 0.1500000000000341, 0.10000000000002274, -0.4500000000000455, 2.6399999999999864, 1.4800000000000182, -0.2400000000000091, -1.509999999999991, 8.230000000000018], 
[0.035, -0.09, 0.0, 1.6099999999999852, 0.0, -0.10000000000002274, 0.0, 0.9499999999999886, 0.0, -0.12000000000000455, 0.0, 0.0, -0.5300000000000296, -0.2699999999999818, 1.5399999999999352])
18: ([0.024999999999999994, -0.235, 0.6899999999999977, -1.450000000000017, 1.75, 1.1800000000000068, 1.3299999999999557, 0.1199999999999477, 0.08000000000004093, 0.7199999999999704, 2.6299999999999955, 1.089999999999975, -3.9399999999999977, 0.8700000000000045, 5.0699999999998795], 
[0.07999999999999999, -0.18, 0.0, 0.0, 0.0, 0.0, 4.639999999999901, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.639999999999901])
19: ([0.07, -0.04, 1.5400000000000205, 0.3299999999999841, 0.0, 0.0, 1.700000000000017, 0.0, -0.6199999999999477, 0.0, 0.0, 1.2300000000000182, 0.4800000000000182, -1.509999999999991, 3.1500000000001194], 
[0.01999999999999999, -0.065, 0.0, -0.20000000000001705, 0.3599999999999852, -0.25, 2.21000000000015, 0.29000000000002046, 0.3800000000000523, -0.16999999999995907, 2.7399999999999523, 0.8800000000000523, -0.22999999999996135, -0.15000000000000568, 5.860000000000269])
"""

"""
13: ([0.04500000000000001, -0.055, 1.089999999999975, -1.650000000000034, 6.440000000000055, 0.769999999999925, 3.430000000000007, -1.8500000000002501, 3.9499999999999886, 1.2200000000000273, 3.5600000000000307, 2.8400000000000603, 19.799999999999784], 
[0.04500000000000001, -0.055, 1.160000000000025, 0.9699999999999704, -0.05999999999997385, -2.2900000000000773, -0.3700000000000614, 5.319999999999766, -2.6499999999999773, 4.759999999999991, -2.130000000000024, 0.11000000000004206, 4.8199999999996805])
14: ([0.13, -0.135, 0.0, 0.0, -1.210000000000008, 0.0, 0.0, 2.130000000000024, 0.0, 0.0, 1.4800000000000182, 0.0, 1.7299999999999898, 0.0, 1.170000000000016, 5.30000000000004], 
[0.24, -0.12, 0.0, 0.0, 2.3000000000000114, 0.6999999999999886, 0.0, 0.8000000000000114, 2.6999999999999886, 0.0, 1.169999999999959, 2.680000000000007, 0.0, 0.0, 2.7900000000000205, 13.139999999999986])
15: ([0.07999999999999999, -0.18, 0.8299999999999841, 0.30000000000001137, 0.0, 1.9699999999999704, 0.0, 0.0, 0.5400000000000205, 0.0, 0.40999999999996817, 4.269999999999982, 2.4799999999999613, 0.0, 2.7600000000000193, 13.559999999999917], 
[0.035, -0.085, -0.10999999999998522, -0.1799999999999784, -0.30999999999997385, 0.09000000000003183, -0.3299999999999841, -0.5800000000000409, 0.0, 0.0, 4.739999999999895, 0.5, -1.6000000000000227, 0.3499999999999943, 0.15000000000000568, 2.719999999999942])
16: ([0.04500000000000001, -0.07, -0.6999999999999886, 1.1399999999999864, 0.8600000000000136, 1.8800000000000523, 1.8199999999999932, -0.31999999999996476, 1.2200000000000273, 3.590000000000032, -1.6300000000000523, -2.329999999999984, 1.6400000000000432, 2.609999999999985, 1.1699999999999875, 10.95000000000013], 
[0.05499999999999999, -0.07, 0.0, 0.5599999999999739, 0.0, -0.5199999999999818, 0.0, 0.29000000000002046, 0.0, 0.0, 2.0500000000000114, 1.6899999999999977, 0.36000000000001364, 3.039999999999992, -0.5200000000000102, 6.950000000000017])
17: ([0.035, -0.09, 0.6400000000000148, 1.9499999999999886, 0.7600000000000193, 1.3000000000000114, 0.6499999999999773, 0.9399999999999977, 0.07000000000005002, 0.5399999999999636, 2.6399999999999864, 1.3799999999999955, -0.8100000000000023, -1.9799999999999613, 3.5200000000000102, 11.600000000000051], 
[0.035, -0.09, 0.0, 1.6099999999999852, 0.0, -0.10000000000002274, 0.0, 0.9499999999999886, 0.0, -0.12000000000000455, 0.0, 0.0, -0.5300000000000296, -0.2699999999999818, 0.0, 1.5399999999999352])
18: ([0.135, -0.205, 0.0, 0.0, 0.0, 0.0, 1.7899999999999636, 0.0, 0.0, 0.0, 0.8199999999999932, 0.0, 0.0, 0.0, 0.0, 2.609999999999957], 
[0.07999999999999999, -0.1, 0.0, 0.0, 0.0, 1.6399999999999864, 2.569999999999993, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8900000000000432, -0.7399999999999807, 2.3799999999999955, 6.7400000000000375])
19: ([0.01999999999999999, -0.065, 1.6900000000000261, -0.6200000000000045, 0.2799999999999727, 0.17999999999994998, 1.6600000000001387, -0.6899999999999409, -0.5300000000000296, 3.759999999999991, -0.5000000000000568, 1.8100000000000591, 0.2599999999999909, -5.039999999999992, 3.1100000000000136, 5.370000000000118], 
[0.01999999999999999, -0.065, 0.0, -0.20000000000001705, 0.3599999999999852, -0.25, 2.21000000000015, 0.29000000000002046, 0.3800000000000523, -0.16999999999995907, 2.7399999999999523, 0.8800000000000523, -0.22999999999996135, -0.15000000000000568, -0.03999999999999204, 5.820000000000277])
"""