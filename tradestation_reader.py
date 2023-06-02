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
authorization_code = "i_TSPBeCF8-1sjJs"
public_key = "r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4"
private_key = "hFBk8xgV_UGJEUFnxVW-AFz6YToqZwdvM-48x5wLUQhzKiR99r2w780hL0giBfvd"
token_url = "https://signin.tradestation.com/oauth/token"
mongo = MongoExplorer()

last_bids_and_asks = {}
getTime = {}

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

def stream_quotes(symbols, path):
    url = f"https://api.tradestation.com/v3/marketdata/stream/quotes/{symbols}"
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, stream=True)

            fieldnames = ["Symbol", "Last", "Ask", "AskSize", "Bid", "BidSize", "Volume", "TradeTime"]
            with open(path, "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                if os.path.getsize(path) == 0:
                    writer.writeheader()
                for line in response.iter_lines():
                    if line:
                        row = json.loads(line)
                        if "Error" in row:
                            break
                        if "Heartbeat" not in row:
                            writer.writerow(row)
                            print(row)
        except requests.exceptions.ChunkedEncodingError as chunkError:
            print(chunkError)
            continue
        except Exception as e:
            print(e)
            break

def stream_marketdepth_aggregates_quotes(symbol):
    url = f"https://api.tradestation.com/v3/marketdata/stream/marketdepth/aggregates/{symbol}"
    
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                logging.warning(f"{symbol} {response}")
                continue            
            
            for line in response.iter_lines():
                if line:
                    bids_and_asks = json.loads(line)
                    if "Heartbeat" in bids_and_asks:
                        continue
                    last_bids_and_asks[symbol] = bids_and_asks
                    getTime[symbol] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            logging.exception(f"{symbol} {e}")
            continue

def get_market_depth_aggregates_quote(symbol):
    collection = f"{symbol}_10sec_lvl2"
    string_fields = ["EarliestTime", "LatestTime", "Side"]
    float_fields = ['Price', 'TotalSize', 'BiggestSize', 'SmallestSize', 'NumParticipants', 'TotalOrderCount']
            
    print(f"{symbol} {datetime.datetime.now()} {getTime[symbol]}")
    for row in last_bids_and_asks[symbol]["Bids"]:
        dict = {"GetTime": getTime[symbol]}
        dict.update({key: row[key] for key in string_fields})
        dict.update({key: float(row[key]) for key in float_fields})
        mongo.mongoDB[collection].insert_one(dict)
    for row in last_bids_and_asks[symbol]["Asks"]:
        dict = {"GetTime": getTime[symbol]}
        dict.update({key: row[key] for key in string_fields})
        dict.update({key: float(row[key]) for key in float_fields})
        mongo.mongoDB[collection].insert_one(dict)

def get_marketdepth_aggregates_quotes_10sec(symbols):
    executors = {
        'default': ThreadPoolExecutor(100),
        'processpool': ProcessPoolExecutor(8)
    }
    scheduler = BlockingScheduler(executors=executors, timezone=utc)
    for symbol in symbols:
        scheduler.add_job(stream_marketdepth_aggregates_quotes, args=[symbol])
        scheduler.add_job(get_market_depth_aggregates_quote, 'cron', args=[symbol], max_instances=2, \
            day_of_week='mon-fri', hour="8-23", second="*/10")
    scheduler.start()

def get_quote(symbol):
    url = f"https://api.tradestation.com/v3/marketdata/quotes/{symbol}"
    collection = f"{symbol}_10sec_ts"
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.warning(f"{symbol} {response}")
                continue
            response = response.json()
            string_fields = ["Symbol", "TradeTime"]
            float_fields = ["Open", "High", "Low", "PreviousClose", "PreviousVolume", "Last", "Ask", "AskSize", "Bid", "BidSize", "NetChange", "NetChangePct", "Volume", "VWAP"]
            #fieldnames = ["Symbol", "Open", "High", "Low", "PreviousClose", "PreviousVolume", "Last", "Ask", "AskSize", "Bid", "BidSize", "NetChange", "NetChangePct", "Volume", "VWAP", "TradeTime"]
            dict = {key: response["Quotes"][0][key] for key in string_fields}
            dict.update({key: float(response["Quotes"][0][key]) for key in float_fields})
            tradeTime = response["Quotes"][0]["TradeTime"]
            last = response["Quotes"][0]["Last"]
            print(f"{symbol} {datetime.datetime.now()} {tradeTime} {last}")
            mongo.mongoDB[collection].replace_one({"TradeTime": dict["TradeTime"]}, dict, upsert=True)
            break
        except Exception as e:
            logging.exception(f"{symbol} {e}")
            continue

def get_quotes_10sec(symbols):
    # Default MemoryJobStore - stores job (fn get_quote) in memory
    # Default ThreadPoolExecutor(10) - max 10 threads
    executors = {
        'default': ThreadPoolExecutor(40),
        'processpool': ProcessPoolExecutor(8)
    }
    scheduler = BlockingScheduler(executors=executors, timezone=utc)
    for symbol in symbols:
        scheduler.add_job(get_quote, 'cron', args=[symbol], max_instances=2, \
            day_of_week='mon-fri', hour="8-23", second="*/10")
    scheduler.start()

if __name__ == '__main__':
    #print(get_tokens())
    logging.basicConfig(filename="tradestation_data/exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    refresh_token = "RsHzxnj7GVWK03IhN3gSXdwSF34a55gmtuDYQxjqioPBs"
    #symbols = ["TSLA", "AAPL", "GOOGL", "MSFT", "AMZN", "BABA", "LYFT", "GE", "META", "MDB"]
    symbols = ['NVDA', 'AMC', 'META', 'NFLX', 'AMZN', 'AAPL', 'ZM', 'GOOG', 'MSFT', 'TSLA']   
    #symbols = 'TSLA'
    #get_quotes_10sec(symbols)
    get_marketdepth_aggregates_quotes_10sec(symbols)
