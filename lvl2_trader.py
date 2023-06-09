import pandas as pd
from test_mongo import MongoExplorer
import requests
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
import datetime
from tradestation_reader import refresh
import logging

class Lvl2Trader:
    def __init__(self, simulator, price_dif_threshold, size_threshold):
        self.account_id = "11655345"
        self.mongo = MongoExplorer()
        self.price_dif_threshold = price_dif_threshold
        self.size_threshold = size_threshold
        self.holding_share = False
        self.balance = 0

        self.simulator = simulator
        self.prices = {"Last": None, "Ask": None, "Bid": None, "BUY": None, "SELL": None, "BUYTOCOVER": None, "SELLSHORT": None}
        self.volume_sum = 0

    def read_lvl1(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl1"
        lvl1 = None
        while lvl1 is None:
            lvl1 = self.mongo.mongoDB[collection].find_one({"CurTime": time})
        self.prices["Last"] = lvl1["Last"]
        self.prices["Ask"] = lvl1["Ask"]
        self.prices["Bid"] = lvl1["Bid"]
        print(lvl1)
        return lvl1

    def read_lvl2(self, symbol, time):
        collection = f"{symbol}_10sec_ts_lvl2"
        df = pd.DataFrame()
        while df.empty:
            df = pd.DataFrame(list(self.mongo.mongoDB[collection].find({"CurTime": time})))
        print(df)
        return df

    def calc_volume_sum(self, symbol, time):
        lvl1 = self.read_lvl1(symbol, time)
        df = self.read_lvl2(symbol, time)
        df.loc[df["Side"] == "Bid", "Dif"] = (df["Price"] - lvl1["Last"])
        df.loc[df["Side"] == "Ask", "Dif"] = (lvl1["Last"] - df["Price"])
        df.loc[df["Side"] == "Ask", "TotalSize"] *= -1
        df = df.loc[df["Dif"] >= self.price_dif_threshold]
        self.volume_sum = df["TotalSize"].sum()
        print(df)

    def trade_shares(self, symbol, action, quantity, time):
        if self.simulator:
            url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"
        else:
            url = "https://api.tradestation.com/v3/orderexecution/orders"
        access_token = refresh()
        payload = {
            "AccountID": self.account_id,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": "Market",
            "TradeAction": action,
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {"content-type": "application/json", "Authorization": f"Bearer {access_token}"}

        order_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        response = requests.request("POST", url, json=payload, headers=headers).json()
        print(response)
        collection = f"{symbol}_ts_trades"
        if self.simulator:
            price = float(response["Confirmations"][0]["EstimatedPrice"])
        else:
            status_response = self.check_status(response["Orders"][0]["OrderID"])
            price = float(status_response["Orders"][0]["FilledPrice"])
        self.balance = self.balance - price if action == "BUY" else self.balance + price
        dict = {"Time": time, "OrderTime": order_time, "Price": price, "Balance": self.balance, "VolumeSum": self.volume_sum}
        with open(f"tradestation_data/{symbol}_trades.log", 'a') as f:
            f.write(f"{dict}\n")
        self.mongo.mongoDB[collection].insert_one(dict)
        
    def check_status(order_id):
        url = f"https://api.tradestation.com/v3/brokerage/accounts/{self.account_id}/orders/{order_id}"
        while True:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.request("GET", url, headers=headers).json()
            print(response)
            if response["Orders"][0]["Status"] == "FLL":
                return response
    
    def get_price(self, symbol, action):
        url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"
        access_token = refresh()
        payload = {
            "AccountID": self.account_id,
            "Symbol": symbol,
            "Quantity": "1",
            "OrderType": "Market",
            "TradeAction": action,
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {"content-type": "application/json", "Authorization": f"Bearer {access_token}"}
        response = requests.request("POST", url, json=payload, headers=headers).json()
        print(response)
        price = float(response["Confirmations"][0]["EstimatedPrice"])
        self.prices[action] = price

    def store_prices(self, symbol):
        collection = f"{symbol}_ts_trade_prices"
        time = datetime.datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        dict = {"Time": time}
        dict.update(self.prices)
        with open(f"tradestation_data/{symbol}_trade_prices.log", 'a') as f:
            f.write(f"{dict}\n")
        self.mongo.mongoDB[collection].insert_one(dict)
        self.prices = {"Last": None, "Ask": None, "Bid": None, "BUY": None, "SELL": None, "BUYTOCOVER": None, "SELLSHORT": None}

    def trade(self, symbol):
        time = datetime.datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.calc_volume_sum(symbol, time)
        if self.volume_sum >= size_threshold and not self.holding_share:
            self.trade_shares(symbol, "BUY", "1", time)
            self.holding_share = True
        elif self.volume_sum <= -size_threshold and self.holding_share:
            self.trade_shares(symbol, "SELL", "1", time)
            self.holding_share = False

    def trade_10sec(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            scheduler.add_job(self.trade, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.trade, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "BUY"], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "BUY"], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "SELL"], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "SELL"], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "BUYTOCOVER"], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "BUYTOCOVER"], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "SELLSHORT"], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.get_price, 'cron', args=[symbol, "SELLSHORT"], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.store_prices, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="1/10")
            scheduler.add_job(self.store_prices, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="1/10")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    symbols = ['TSLA']
    price_dif_threshold = .007
    size_threshold = 1
    simulator = True
    trader = Lvl2Trader(simulator, price_dif_threshold=price_dif_threshold, size_threshold=size_threshold)
    trader.trade_10sec(symbols)