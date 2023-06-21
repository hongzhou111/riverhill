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
    def __init__(self, buy_thresholds, sell_thresholds, size_threshold, simulator):
        self.ts_reader = TS_Reader()
        self.mongo = MongoExplorer()

        self.buy_thresholds = buy_thresholds
        self.sell_thresholds = sell_thresholds
        self.size_threshold = size_threshold

        self.holding_share = {}
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

    def calc_volume_sum(self, symbol, time, buy_threshold, sell_threshold):
        lvl1 = self.read_lvl1(symbol, time)
        df = self.read_lvl2(symbol, time)
        df["Dif"] = (df["Price"] - lvl1["Last"])
        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= buy_threshold))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= sell_threshold))]
        df = df[["GetTime", "Side", "Dif", "TotalSize"]]
        return (df["TotalSize"] * df["Dif"]).sum(), df

    def trade_shares(self, symbol, action, quantity, time, volume_sum):
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

        collection = f"{symbol}_ts_trades"
        if self.simulator:
            price = float(response["Confirmations"][0]["EstimatedPrice"])
        else:
            status_response = self.check_status(response["Orders"][0]["OrderID"])
            if status_response is False:
                return
            price = float(status_response["Orders"][0]["FilledPrice"])
        filled_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.holding_share[symbol] = (action == "BUY")
        self.balance[symbol] = self.balance[symbol] - price if action == "BUY" else self.balance[symbol] + price
        dict = {"Time": time, "FilledTime": filled_time, "Price": price, "Balance": self.balance[symbol], "VolumeSum": volume_sum}
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
    
    def trade(self, symbol, buy_threshold, sell_threshold):
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        volume_sum, df = self.calc_volume_sum(symbol, time, buy_threshold, sell_threshold)
        print(df)
        print(volume_sum)
        if volume_sum > size_threshold and not self.holding_share[symbol]:
            self.trade_shares(symbol, "BUY", "1", time, volume_sum)
        elif volume_sum < -size_threshold and self.holding_share[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, volume_sum)
    
    def sell_eod(self, symbol):
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.holding_share[symbol]:
            self.trade_shares(symbol, "SELL", "1", time, 0)

    def start_scheduler(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            self.holding_share[symbol] = False
            self.balance[symbol] = 0
            scheduler.add_job(self.trade, 'cron', args=[symbol, self.buy_thresholds[13], self.sell_thresholds[13]], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            for hr in range(14, 19):
                scheduler.add_job(self.trade, 'cron', args=[symbol, self.buy_thresholds[hr], self.sell_thresholds[hr]], max_instances=2, \
                    day_of_week='mon-fri', hour=hr, second="*/10")
            scheduler.add_job(self.trade, 'cron', args=[symbol, self.buy_thresholds[19], self.sell_thresholds[19]], max_instances=2, \
                day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
            scheduler.add_job(self.sell_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
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
    buy_thresholds = {13: .04, 14: .12, 15: .1, 16: -.07, 17: .03, 18: .02, 19: .02}
    sell_thresholds = {13: -.06, 14: -.13, 15: -.18, 16: -.07, 17: -.08, 18: .02, 19: -.05}
    size_threshold = 0
    simulator = False
    trader = Lvl2Trader(buy_thresholds, sell_thresholds, size_threshold, simulator)
    trader.start_scheduler(["TSLA"])
    
"""
13: [0.32000000000000006, -0.16000000000000014, 0.7599999999999909, 0.0, 4.760000000000019, 0.0, 0.0, 0.0, 5.52000000000001]
14: [-0.31999999999999984, 1.6, 0.009999999999990905, 0.4499999999999602, -0.4900000000000091, 0.009999999999990905, 0.34999999999990905, 0.8400000000000318, 0.2599999999999909, -0.2699999999999818, 0.0, 1.159999999999883]
15: [0.08000000000000007, -0.16000000000000014, 1.1999999999999886, 0.30000000000001137, 0.0, 3.0, 0.0, 0.0, -0.5500000000000114, 0.0, 3.3899999999999295, 7.339999999999918]
16: [-0.48, 0.08000000000000007, -0.7099999999999227, -0.5, -0.5, 2.339999999999975, 1.910000000000025, -0.9799999999999613, 1.480000000000075, 5.0, -3.480000000000018, 4.560000000000173]
17: [0.0, -0.08000000000000007, 0.5900000000000034, 1.9399999999999977, 2.299999999999983, 0.8599999999999568, 0.160000000000025, 0.9600000000000364, -0.25, -0.26000000000004775, 2.519999999999982, 8.819999999999936]
"""
"""
13: [0.03999999999999998, -0.06000000000000005, 0.25999999999993406, -0.9500000000000455, 6.440000000000111, 0.7799999999999159, 3.429999999999893, -1.8500000000002501, 8.109999999999559]
14: [0.12, -0.07999999999999996, 0.0, 3.219999999999999, -1.410000000000025, 0.2400000000000091, 0.3199999999999932, 0.5, 0.7599999999999909, 0.0, 1.5, 5.129999999999967]
15: [0.09999999999999998, -0.18000000000000005, 1.8599999999999852, 1.6400000000000148, 0.0, 2.469999999999999, 0.0, 0.0, 0.0, 0.0, 3.569999999999993, 9.539999999999992]
16: [-0.09999999999999998, -0.040000000000000036, -0.9099999999999966, -0.6700000000000159, -0.5, 2.3700000000000614, 1.8400000000000318, -1.1999999999999886, 1.400000000000034, 5.0, -2.6000000000000227, 4.7300000000001035]
17: [0.020000000000000018, -0.07999999999999996, 0.6000000000000227, 1.9399999999999977, 1.8000000000000114, 0.8699999999999477, 0.3299999999999841, 0.2300000000000182, 0.35000000000002274, 0.3499999999999659, 2.519999999999982, 8.989999999999952]
18: [0.020000000000000018, -0.4, 0.45000000000001705, -1.4699999999999989, 1.5600000000000023, 1.25, 0.4399999999999977, 0.1199999999999477, 0.5600000000000023, 0.9900000000000091, 2.9600000000000364, 6.860000000000014]
"""
"""
13: [0.04000000000000001, -0.06, 0.25999999999993406, -0.9500000000000455, 6.440000000000111, 0.7799999999999159, 3.429999999999893, -1.8500000000002501, 8.109999999999559]
14: [0.12, -0.13, 0.0, 3.2700000000000102, -1.7800000000000011, -0.4099999999999966, 0.0, 2.130000000000024, 0.7599999999999909, 0.0, 1.4800000000000182, 5.4500000000000455]
15: [0.1, -0.18, 1.8599999999999852, 1.6400000000000148, 0.0, 2.469999999999999, 0.0, 0.0, 0.0, 0.0, 3.569999999999993, 9.539999999999992]
16: [-0.07, -0.07, -0.8299999999999841, -0.8300000000000125, -0.5, 2.3700000000000614, 1.910000000000025, -0.9799999999999613, 1.400000000000034, 4.949999999999989, -2.4600000000000364, 5.030000000000115]
17: [0.03, -0.08000000000000002, 0.6000000000000227, 2.0299999999999727, 1.8000000000000114, 0.8699999999999477, 0.6800000000000068, 0.8199999999999932, 0.0, 0.4900000000000091, 2.4799999999999613, 9.769999999999925]
18: [0.01999999999999999, -0.24, 0.45000000000001705, -1.4699999999999989, 1.5600000000000023, 1.25, 0.4399999999999977, 0.1199999999999477, 0.5600000000000023, 0.9900000000000091, 2.9600000000000364, 6.860000000000014]
19: [0.01999999999999999, -0.04999999999999999, 1.9400000000000261, 0.47999999999996135, 0.14999999999997726, -0.060000000000002274, 2.5400000000001057, -1.2099999999999795, -0.5000000000000568, 1.6899999999999409, 0.5299999999999727, 5.559999999999945]
"""