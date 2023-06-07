import pandas as pd
from test_mongo import MongoExplorer
import requests
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
import datetime
from tradestation_reader import refresh

class Lvl2Trader:
    def __init__(self, price_dif_threshold, size_threshold):
        self.account_id = "11655345"
        self.mongo = MongoExplorer()
        self.price_dif_threshold = price_dif_threshold
        self.size_threshold = size_threshold
        self.holding_share = False
        self.balance = 0

    # returns dictionary
    def read_lvl1(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl1"
        lvl1 = None
        while lvl1 is None:
            lvl1 = self.mongo.mongoDB[collection].find_one({"CurTime": time})
            print(lvl1)
        return lvl1

    def read_lvl2(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl2"
        df = pd.DataFrame()
        while df.empty:
            df = pd.DataFrame(list(self.mongo.mongoDB[collection].find({"CurTime": time})))
            print(df)
        return df

    def calc_volume_sum(self, symbol):
        time = datetime.datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        lvl1 = self.read_lvl1(symbol, time)
        df = self.read_lvl2(symbol, time)
        df.loc[df["Side"] == "Bid", "Dif"] = (df["Price"] - lvl1["Last"])
        df.loc[df["Side"] == "Ask", "Dif"] = (lvl1["Last"] - df["Price"])
        df.loc[df["Side"] == "Ask", "TotalSize"] *= -1
        df = df.loc[df["Dif"] >= self.price_dif_threshold]
        volume_sum = df["TotalSize"].sum()
        print(df)
        print(volume_sum)
        return volume_sum

    def trade_shares(self, symbol, action, quantity):
        access_token = refresh()
        url = "https://api.tradestation.com/v3/orderexecution/orders"
        payload = {
            "AccountID": "11655345",
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": "Market",
            "TradeAction": action,
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        print(response.text)

    def check_status():
        access_token = refresh()
        url = "https://api.tradestation.com/v3/brokerage/accounts/11655345/orders"

        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.request("GET", url, headers=headers)

        print(response.text)

    def trade(self, symbol):
        volume_sum = self.calc_volume_sum(symbol)
        if volume_sum >= size_threshold and not self.holding_share:
            self.trade_shares(symbol, "BUY", "1")
            self.holding_share = True
        elif volume_sum < size_threshold and self.holding_share:
            self.trade_shares(symbol, "SELL", "1")
            self.holding_share = False
        self.check_status()

    def trade_10sec(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            scheduler.add_job(self.trade, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="8-23", second="*/10")
        scheduler.start()

if __name__ == '__main__':
    symbols = ['TSLA']
    price_dif_threshold = -.015
    size_threshold = 0
    trader = Lvl2Trader(price_dif_threshold=price_dif_threshold, size_threshold=size_threshold)
    trader.trade_10sec(symbols)