'''
https://towardsdatascience.com/collect-stock-and-options-data-easily-using-python-and-ally-financial-api-3-example-queries-45d162e4f055
'''
import requests
from requests_oauthlib import OAuth1
from config import (api_key, secret, oath_token, oath_secret)

import pandas as pd
import sqlalchemy
import numpy as np

import sqlite3
from sqlite3 import Error

import matplotlib.pyplot as plt
import datetime as dt

# authentication
auth = OAuth1(api_key, secret, oath_token, oath_secret)
# url
url = 'https://api.tradeking.com/v1/market/timesales.json?symbols=MSFT&startdate=2019-05-03&interval=1min'
# api request
response = requests.get(url, auth=auth).json()
# send to data frame and format data types
df = pd.DataFrame(response["response"]["quotes"]["quote"])
df = df.sort_values(['datetime'], ascending=False)
df['date'] = pd.to_datetime(df['date'])
df['datetime'] = pd.to_datetime(df['datetime'], utc=False).dt.tz_convert('US/Central')
df['hi'] = df["hi"].astype(float)
df['incr_vol'] = df["incr_vl"].astype(float)
df['last'] = df["last"].astype(float)
df['lo'] = df["lo"].astype(float)
df['opn'] = df["opn"].astype(float)
df['vl'] = df['vl'].astype(float)
df.head()
# resample the time value to be greater than 1 min as needed. Example: 30 min resample for last price
df.set_index(df['datetime'], inplace=True)
df.head()
df_resample30 = df.resample(rule='30min', label='right').last()
df_resample30.head()
# Options Search Example
url = 'https://api.tradeking.com/v1/market/options/search.json?symbol=MSFT&query=xyear-eq%3A2019%20AND%20xmonth-eq%3A06%20AND%20strikeprice-eq%3A140'
response = requests.get(url, auth=auth).json()

df = pd.DataFrame(response["response"]["quotes"]["quote"])
df.head()
# Extended Quote Example
url = 'https://api.tradeking.com/v1/market/ext/quotes.json?symbols=MSFT190607C00140000'
response = requests.get(url, auth=auth).json()
df = pd.DataFrame(response["response"]["quotes"]["quote"], index=[0])
df.head()