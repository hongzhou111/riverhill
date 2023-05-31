from tkinter import E
from webbrowser import get
import requests
import csv
import json
import pandas as pd
import os
import datetime
import pause
from test_mongo import MongoExplorer

""" auth_url to copy
https://signin.tradestation.com/authorize?response_type=code&client_id=r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4&redirect_uri=http%3A%2F%2Flocalhost&audience=https%3A%2F%2Fapi.tradestation.com&state=STATE&scope=openid+offline_access+profile+MarketData+ReadAccount+Trade+Crypto+Matrix+OptionSpreads
"""
auth_url = "https://signin.tradestation.com/authorize?response_type=code&client_id=r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4&redirect_uri=http%3A%2F%2Flocalhost&audience=https%3A%2F%2Fapi.tradestation.com&state=STATE&scope=openid+offline_access+profile+MarketData+ReadAccount+Trade+Crypto+Matrix+OptionSpreads"
authorization_code = "Q6IimMWRRH2o_BjC"
public_key = "r4bJ08Nbz9f8b6djDhoyCmazNnrrLFL4"
private_key = "hFBk8xgV_UGJEUFnxVW-AFz6YToqZwdvM-48x5wLUQhzKiR99r2w780hL0giBfvd"
token_url = "https://signin.tradestation.com/oauth/token"

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

def stream_marketdepth_quotes(symbols, path):
    url = f"https://api.tradestation.com/v3/marketdata/stream/marketdepth/quotes/{symbols}"
    while True:
        try:
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, stream=True)

            fieldnames = ["TimeStamp", "Side", "Price", "Size", "OrderCount", "Name"]
            with open(path, "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                if not os.path.isfile(path):
                    writer.writeheader()
                for line in response.iter_lines():
                    if line:
                        bids_and_asks = json.loads(line)
                        if "Error" in bids_and_asks:
                            break
                        if "Heartbeat" not in bids_and_asks:
                            for row in bids_and_asks["Bids"]:
                                writer.writerow(row)
                                print(row)
                            for row in bids_and_asks["Asks"]:
                                writer.writerow(row)
                                print(row)
        except requests.exceptions.ChunkedEncodingError as chunkError:
            print(chunkError)
            continue
        except Exception as e:
            print(e)
            break

def get_quotes_10sec(symbol):
    next_time = datetime.datetime.now() + datetime.timedelta(0, 10)
    url = f"https://api.tradestation.com/v3/marketdata/quotes/{symbol}"
    collection = f"{symbol}_10sec_ts"
    mongo = MongoExplorer()
    while True:
        try:
            pause.until(next_time)
            access_token = refresh()
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers).json()
            print(response["Quotes"][0])
            fieldnames = ["Symbol", "Open", "High", "Low", "Last", "Ask", "AskSize", "Bid", "BidSize", "Volume", "TradeTime"]
            dict = {key: response["Quotes"][0][key] for key in fieldnames}
            print(dict)
            mongo.mongoDB[collection].replace_one({"TradeTime": dict["TradeTime"]}, dict, upsert=True)
            next_time += datetime.timedelta(0, 10)
        except requests.exceptions.ChunkedEncodingError as chunkError:
            print(chunkError)
            continue
        except Exception as e:
            print(e)
            break

if __name__ == '__main__':
    #access_token, refresh_token, id_token = get_tokens()
    refresh_token = "EMDit_4j9JcSMuURcS0uNigyWpWuJ19gfAmzek6nwlfLR"
    symbols = "TSLA"
    get_quotes_10sec(symbols)
