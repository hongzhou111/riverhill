import requests
import csv
import json
import pandas as pd
from test_mongo import MongoExplorer
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import logging
from datetime import datetime
from pytz import utc
from tradestation_authenticator import ts_authenticator

class TS_Reader:
    def __init__(self, account_id):   
        self.mongo = MongoExplorer()
        self.account_id = account_id

        self.last_quote = {}
        self.lvl1_getTime = {}
        self.last_bids_and_asks = {}
        self.lvl2_getTime = {}

        self.prices = {}

    def stream_lvl1_quotes(self, symbol):
        url = f"https://api.tradestation.com/v3/marketdata/stream/quotes/{symbol}"
        while True:
            try:
                access_token = self.mongo.mongoDB["TS_auth"].find_one({"account_id": self.account_id})["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(url, headers=headers, stream=True)
                if response.status_code != 200:
                    logging.warning(f"{symbol} {response} {response.text}")
                    ts_authenticator.refresh()
                    continue   

                for line in response.iter_lines():
                    if line:
                        row = json.loads(line)
                        if "Error" in row:
                            logging.warning(f"{symbol} {response} {response.text}")
                            continue
                        if "Heartbeat" in row:
                            continue
                        if symbol not in self.last_quote:
                            self.last_quote[symbol] = row
                        else:
                            self.last_quote[symbol].update(row)
                        self.lvl1_getTime[symbol] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                logging.exception(f"{symbol} {e}")
                ts_authenticator.refresh()
                continue

    def stream_lvl2_quotes(self, symbol):
        url = f"https://api.tradestation.com/v3/marketdata/stream/marketdepth/aggregates/{symbol}"
        while True:
            try:
                access_token = self.mongo.mongoDB["TS_auth"].find_one({"account_id": self.account_id})["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(url, headers=headers, stream=True)
                if response.status_code != 200:
                    logging.warning(f"{symbol} {response} {response.text}")
                    ts_authenticator.refresh()
                    continue            
                
                for line in response.iter_lines():
                    if line:
                        bids_and_asks = json.loads(line)
                        if "Heartbeat" in bids_and_asks:
                            continue
                        self.last_bids_and_asks[symbol] = bids_and_asks
                        self.lvl2_getTime[symbol] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                logging.exception(f"{symbol} {e}")
                ts_authenticator.refresh()
                continue

    def get_lvl1_quote(self, symbol):
        collection = f"{symbol}_10sec_ts_lvl1"
        string_fields = ["Symbol", "TradeTime"]
        float_fields = ["Last", "Ask", "AskSize", "Bid", "BidSize", "Volume", "VWAP", "Open", "High", "Low", "PreviousClose", "PreviousVolume", "NetChange", "NetChangePct"]
        
        row = self.last_quote[symbol]
        curTime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        dict = {"CurTime": curTime, "GetTime": self.lvl1_getTime[symbol]}
        dict.update({key: row[key] for key in string_fields})
        dict.update({key: float(row[key]) for key in float_fields})
        self.mongo.mongoDB[collection].insert_one(dict)

        print_fields = ["Symbol", "CurTime", "GetTime", "TradeTime", "Last", "Bid", "BidSize", "Ask", "AskSize",  "Volume"]
        print_dict = {key: dict[key] for key in print_fields}
        with open(f"tradestation_data/{symbol}.log", 'a') as f:
            f.write(f"LVL1: {print_dict}\n")

    def get_lvl2_quote(self, symbol):
        collection = f"{symbol}_10sec_ts_lvl2"
        string_fields = ["EarliestTime", "LatestTime", "Side"]
        float_fields = ['Price', 'TotalSize', 'BiggestSize', 'SmallestSize', 'NumParticipants', 'TotalOrderCount']
        
        curTime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        bids = []
        asks = []
        for row in self.last_bids_and_asks[symbol]["Bids"]:
            dict = {"CurTime": curTime, "GetTime": self.lvl2_getTime[symbol]}
            dict.update({key: row[key] for key in string_fields})
            dict.update({key: float(row[key]) for key in float_fields})
            self.mongo.mongoDB[collection].insert_one(dict)
            bids.append((dict["Price"], dict["TotalSize"]))
        for row in self.last_bids_and_asks[symbol]["Asks"]:
            dict = {"CurTime": curTime, "GetTime": self.lvl2_getTime[symbol]}
            dict.update({key: row[key] for key in string_fields})
            dict.update({key: float(row[key]) for key in float_fields})
            self.mongo.mongoDB[collection].insert_one(dict)
            asks.append((dict["Price"], dict["TotalSize"]))

        print_dict = {"Symbol": symbol, "CurTime": curTime, "GetTime": self.lvl2_getTime[symbol], "Bids": bids, "Asks": asks}
        with open(f"tradestation_data/{symbol}.log", 'a') as f:
            f.write(f"LVL2: {print_dict}\n")

    def get_price(self, symbol, action, quantity):
        url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"
        for _ in range(2):
            access_token = self.mongo.mongoDB["TS_auth"].find_one({"account_id": self.account_id})["access_token"]
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
            response = requests.request("POST", url, json=payload, headers=headers)
            if response.status_code != 200:
                logging.warning(f"{symbol} {action} {response.text}")
                ts_authenticator.refresh()
                continue
            response = response.json()
            if "Confirmations" not in response:
                logging.warning(f"{symbol} {action} {response}")
                ts_authenticator.refresh()
                continue
            break
            
        price = {action: float(response["Confirmations"][0]["EstimatedPrice"])}
        self.prices[symbol].update(price)

    def store_prices(self, symbol):
        collection = f"{symbol}_ts_trade_prices"
        time = datetime.utcnow()
        time = time.replace(second=time.second - time.second%10).strftime("%Y-%m-%dT%H:%M:%SZ")
        dict = {"Time": time}
        dict.update(self.prices[symbol])
        with open(f"tradestation_data/{symbol}_trade_prices.log", 'a') as f:
            f.write(f"{dict}\n")
        self.mongo.mongoDB[collection].insert_one(dict)
        self.prices[symbol] = {}

    def clear_log(self, file):
        with open(file, 'w'):
            pass

    def start_quotes_scheduler(self, symbols):
        # Default MemoryJobStore - stores job (fn get_quote) in memory
        executors = {
            'default': ThreadPoolExecutor(100), # max 100 threads
            'processpool': ProcessPoolExecutor(8)   # secondary executor - max 8 cpus
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            scheduler.add_job(self.stream_lvl1_quotes, args=[symbol])
            scheduler.add_job(self.stream_lvl2_quotes, args=[symbol])
            scheduler.add_job(self.get_lvl1_quote, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="8-23", second="*/10")
            scheduler.add_job(self.get_lvl2_quote, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="8-23", second="*/10")
            scheduler.add_job(self.clear_log, 'cron', args=[f"tradestation_data/{symbol}.log"], \
                day_of_week='mon', hour="0")
        scheduler.add_job(self.clear_log, 'cron', args=["tradestation_data/exceptions.log"], \
            day_of_week='mon', hour="0")
        scheduler.start()
        
    def start_prices_scheduler(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        actions = ["BUY", "SELL"]
        for symbol in symbols:
            self.prices[symbol] = {}
            for action in actions:
                scheduler.add_job(self.get_price, 'cron', args=[symbol, action, "1"], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
                scheduler.add_job(self.get_price, 'cron', args=[symbol, action, "1"], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="*/10")
            scheduler.add_job(self.store_prices, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="13", minute="30-59", second="2/10")
            scheduler.add_job(self.store_prices, 'cron', args=[symbol], max_instances=2, \
                day_of_week='mon-fri', hour="14-19", second="2/10")
            scheduler.add_job(self.clear_log, 'cron', args=[f"tradestation_data/{symbol}_trade_prices.log"], \
                day_of_week='mon', hour="0")
        scheduler.start()


if __name__ == '__main__':
    # print(get_tokens())
    logging.basicConfig(filename="tradestation_data/exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    ts_reader = TS_Reader(account_id="11655345")
    ts_reader.start_quotes_scheduler(['TSLA', 'NVDA', 'AMZN', 'AAPL', 'GOOG', 'MSFT', 'MDB', 'SMCI', 'COCO', 'RCM'])
    # ts_reader.start_prices_scheduler(['TSLA', 'NVDA', 'AMZN', 'AAPL', 'GOOG'])