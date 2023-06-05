import requests
import csv
import json
import pandas as pd
import os
from test_mongo import MongoExplorer
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import logging
import datetime
from pytz import utc

""" auth_url to copy
https://signin.tradestation.com/authorize?response_type=code&client_id=r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4&redirect_uri=http%3A%2F%2Flocalhost&audience=https%3A%2F%2Fapi.tradestation.com&state=STATE&scope=openid+offline_access+profile+MarketData+ReadAccount+Trade+Crypto+Matrix+OptionSpreads
"""
auth_url = "https://signin.tradestation.com/authorize?response_type=code&client_id=r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4&redirect_uri=http%3A%2F%2Flocalhost&audience=https%3A%2F%2Fapi.tradestation.com&state=STATE&scope=openid+offline_access+profile+MarketData+ReadAccount+Trade+Crypto+Matrix+OptionSpreads"
authorization_code = "e37HZhkr8HBokHSw"
public_key = "r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4"
private_key = "hFBk8xgV_UGJEUFnxVW-AFz6YToqZwdvM-48x5wLUQhzKiR99r2w780hL0giBfvd"
token_url = "https://signin.tradestation.com/oauth/token"
mongo = MongoExplorer()

last_quote = {}
lvl1_getTime = {}
last_bids_and_asks = {}
lvl2_getTime = {}

def get_tokens():
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "authorization_code", "client_id": public_key, "client_secret": private_key, "code": authorization_code, "redirect_uri": "http://localhost"}

    r = requests.post(token_url, headers=headers, data=data).json()

    return r["access_token"], r["refresh_token"], r["id_token"]

def refresh():
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "client_id": public_key, "client_secret": private_key, "refresh_token": refresh_token}

    r = requests.post(token_url, headers=headers, data=data).json()

    access_token = r["access_token"]
    return access_token

def stream_lvl1_quotes(symbol):
    url = f"https://api.tradestation.com/v3/marketdata/stream/quotes/{symbol}"
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                logging.warning(f"{symbol} {response} {response.text}")
                continue   

            for line in response.iter_lines():
                if line:
                    row = json.loads(line)
                    if "Error" in row:
                        logging.warning(f"{symbol} {response} {response.text}")
                        continue
                    if "Heartbeat" in row:
                        continue
                    if symbol not in last_quote:
                        last_quote[symbol] = row
                    else:
                        last_quote[symbol].update(row)
                    lvl1_getTime[symbol] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            logging.exception(f"{symbol} {e}")
            continue

def stream_lvl2_quotes(symbol):
    url = f"https://api.tradestation.com/v3/marketdata/stream/marketdepth/aggregates/{symbol}"
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                logging.warning(f"{symbol} {response} {response.text}")
                continue            
            
            for line in response.iter_lines():
                if line:
                    bids_and_asks = json.loads(line)
                    if "Heartbeat" in bids_and_asks:
                        continue
                    last_bids_and_asks[symbol] = bids_and_asks
                    lvl2_getTime[symbol] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            logging.exception(f"{symbol} {e}")
            continue

# def get_quote(symbol):
#     url = f"https://api.tradestation.com/v3/marketdata/quotes/{symbol}"
#     collection = f"{symbol}_10sec_ts_lvl1"
#     string_fields = ["Symbol", "TradeTime"]
#     float_fields = ["Last", "Ask", "AskSize", "Bid", "BidSize", "Volume", "VWAP", "Open", "High", "Low", "PreviousClose", "PreviousVolume", "NetChange", "NetChangePct"]
#     while True:
#         try:
#             access_token = refresh()
#             headers = {"Authorization": f"Bearer {access_token}"}

#             response = requests.get(url, headers=headers)
#             if response.status_code != 200:
#                 logging.warning(f"{symbol} {response} {response.text}")
#                 continue
#             response = response.json()

#             dict = {key: response["Quotes"][0][key] for key in string_fields}
#             dict.update({key: float(response["Quotes"][0][key]) for key in float_fields})
#             tradeTime = response["Quotes"][0]["TradeTime"]
#             last = response["Quotes"][0]["Last"]
#             print(f"{symbol} {datetime.datetime.now()} {tradeTime} {last}")
#             mongo.mongoDB[collection].replace_one({"TradeTime": dict["TradeTime"]}, dict, upsert=True)
#             break
#         except Exception as e:
#             logging.exception(f"{symbol} {e}")
#             continue   

def get_lvl1_quote(symbol):
    collection = f"{symbol}_10sec_ts_lvl1"
    string_fields = ["Symbol", "TradeTime"]
    float_fields = ["Last", "Ask", "AskSize", "Bid", "BidSize", "Volume", "VWAP", "Open", "High", "Low", "PreviousClose", "PreviousVolume", "NetChange", "NetChangePct"]
    
    row = last_quote[symbol]
    curTime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    dict = {"CurTime": curTime, "GetTime": lvl1_getTime[symbol]}
    dict.update({key: row[key] for key in string_fields})
    dict.update({key: float(row[key]) for key in float_fields})
    mongo.mongoDB[collection].insert_one(dict)

    print_fields = ["Symbol", "CurTime", "GetTime", "TradeTime", "Last", "Bid", "BidSize", "Ask", "AskSize",  "Volume"]
    print_dict = {key: dict[key] for key in print_fields}
    with open(f"tradestation_data/{symbol}.log", 'a') as f:
        f.write(f"LVL1: {print_dict}\n")

def get_lvl2_quote(symbol):
    collection = f"{symbol}_10sec_ts_lvl2"
    string_fields = ["EarliestTime", "LatestTime", "Side"]
    float_fields = ['Price', 'TotalSize', 'BiggestSize', 'SmallestSize', 'NumParticipants', 'TotalOrderCount']
    
    curTime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    bids = []
    asks = []
    for row in last_bids_and_asks[symbol]["Bids"]:
        dict = {"CurTime": curTime, "GetTime": lvl2_getTime[symbol]}
        dict.update({key: row[key] for key in string_fields})
        dict.update({key: float(row[key]) for key in float_fields})
        mongo.mongoDB[collection].insert_one(dict)
        bids.append((dict["Price"], dict["TotalSize"]))
    for row in last_bids_and_asks[symbol]["Asks"]:
        dict = {"CurTime": curTime, "GetTime": lvl2_getTime[symbol]}
        dict.update({key: row[key] for key in string_fields})
        dict.update({key: float(row[key]) for key in float_fields})
        mongo.mongoDB[collection].insert_one(dict)
        asks.append((dict["Price"], dict["TotalSize"]))

    print_dict = {"Symbol": symbol, "CurTime": curTime, "GetTime": lvl2_getTime[symbol], "Bids": bids, "Asks": asks}
    with open(f"tradestation_data/{symbol}.log", 'a') as f:
        f.write(f"LVL2: {print_dict}\n")

def get_quotes_10sec(symbols):
    # Default MemoryJobStore - stores job (fn get_quote) in memory
    # Default ThreadPoolExecutor(10) - max 10 threads
    executors = {
        'default': ThreadPoolExecutor(100),
        'processpool': ProcessPoolExecutor(8)
    }
    scheduler = BlockingScheduler(executors=executors, timezone=utc)
    for symbol in symbols:
        scheduler.add_job(stream_lvl1_quotes, args=[symbol])
        scheduler.add_job(stream_lvl2_quotes, args=[symbol])
        scheduler.add_job(get_lvl1_quote, 'cron', args=[symbol], max_instances=2, \
            day_of_week='mon-fri', hour="8-23", second="*/10")
        scheduler.add_job(get_lvl2_quote, 'cron', args=[symbol], max_instances=2, \
            day_of_week='mon-fri', hour="8-23", second="*/10")
    scheduler.start()

if __name__ == '__main__':
    # print(get_tokens())
    logging.basicConfig(filename="tradestation_data/exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    refresh_token = "lzijZJe0VUnjFEzq6dqWK-Q3rqhzyoq7kkrDkqVoJvoYn"
    symbols = ['NVDA', 'AMC', 'META', 'NFLX', 'AMZN', 'AAPL', 'ZM', 'GOOG', 'MSFT', 'TSLA']   
    get_quotes_10sec(symbols)
