import polygon
#from datetime import date
import time
from datetime import datetime
from datetime import timedelta
import json

import pandas as pd

startTime = datetime.now()
startTime = startTime + timedelta(hours=-27)
endTime = startTime + timedelta(minutes=3*24*60 + 5)

print(startTime.strftime("%Y-%m-%d %H:%M:%S"),endTime.strftime("%Y-%m-%d %H:%M:%S"))
epoch1 = int(startTime.timestamp()*1000)
epoch2 = int(endTime.timestamp()*1000)

#print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

#date_start = '2023-03-24 15:10:00'
#date_end = '2023-03-24 15:59:00'
#d1 = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
#d2 = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
#epoch1 = int(startTime.timestamp()*1000)
#epoch2 = int(endTime.timestamp()*1000)
#print(epoch1, epoch2)
#start_date = datetime(2023, 3, 24, 10, 12, 00)
#end_date = datetime(2023, 3, 24, 15, 53, 00)
#dur = (end_date - start_date).days / 365
#dur2 = (datetime.timestamp(end_date) - datetime.timestamp(start_date)) / (365 * 24 * 60 * 60)
#dur3 = (end_date - start_date).total_seconds() / (365 * 24 * 60 * 60)
#print(end_date - start_date, dur, dur2, dur3)

#KEY = '2XGlG6VPav5gtw01g_FB7IE2CwlvDgbT'  # recommend to keep your key in a separate file and import that here
                                            #https://api.polygon.io/v3/quotes/AAPL?apiKey=2XGlG6VPav5gtw01g_FB7IE2CwlvDgbT
#client = polygon.StocksClient(KEY)

#agg = client.get_aggregate_bars('TSLA', epoch1, epoch2, timespan='minute')
#agg = client.get_aggregate_bars('TSLA', '2023-03-24', '2023-03-27', timespan='minute', sort='desc')
#print(agg)

#macd = client.get_macd('TSLA', timespan='day', long_window_size=7,short_window_size=3,signal_window_size=19)
#print(macd)

#agg_group = client.get_grouped_daily_bars('2023-03-23')
#print(agg_group)
#snap = client.get_snapshot('TSLA')
#print(snap)
# current price for a stock
#current_price = client.get_current_price('AMD')
#print(current_price)

# LAST QUOTE for a stock
#last_quote = client.get_last_quote('AMD')

#print(last_quote)

# LAST TRADE for a stock
#last_trade = client.get_last_trade('NVDA')

# You get the idea, right? ...RIGHT??

# okay a few more

# TRADES on a specific date for a stock
#trades = client.get_trades('AMD', date(2021, 6, 28))

# OCHLV for a specific day for a stock
#ochlv = client.get_daily_open_close('AMD', '2021-06-21')

# Day's Gainers OR Losers
#gainers = client.get_gainers_and_losers()
#losers = client.get_gainers_and_losers('losers')

# Snapshot for a stock

#snapshot = client.get_snapshot('NVDA')


import yfinance as yf
from stockstats import StockDataFrame as Sdf

# Get the data
#data = yf.download(tickers="TSLA", period="1d", interval="1m",)
#data = yf.download(tickers="TSLA", interval="1m", start='2023-03-27', end='2023-03-28')

#stock = Sdf.retype(data)

# Print the data
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
#print(pd.options.display.max_columns)

#print(data)
#s = stock.reset_index()
#data = data.reset_index()
#d0 = data.iloc[0]['Datetime']
#d1 = data.iloc[-1]['Datetime']
#print(d0, d1, type(d0), d1-d0, type(data['Datetime'][0]))

#print(data.tail(50))
#print(len(data.index))

#import pendulum
#pd.options.display.max_rows=10  # To decrease printouts
#start = pendulum.parse('2021-10-18 09:30')      #.add(hours=7)  # My tz is UTC+03:00, original TZ UTC-04:00. So adds to my local time 7 hours
#end = pendulum.parse('2021-10-18 10:30')        #.add(hours=7)  # Same
#start = datetime.strptime('2023-03-27 09:30:00', '%Y-%m-%d %H:%M:%S')
#end = datetime.strptime('2023-03-27 10:30:00', '%Y-%m-%d %H:%M:%S')
#print(start, end)
#print(yf.download(tickers="TSLA", interval="1m", start=start, end=end))

'''
import finnhub
finnhub_client = finnhub.Client(api_key="cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90")

print(finnhub_client.stock_candles('AAPL', 'D', epoch1, epoch2))

print(finnhub_client.quote('AAPL'))

2023-03-31 10:30:51 2023-04-03 10:35:51
{'s': 'no_data'}
{'c': 162.65, 'd': 0.29, 'dp': 0.1786, 'h': 163.09, 'l': 162.13, 'o': 162.44, 'pc': 162.36, 't': 1680273039}        # 1680273039 = 2023-03-31 10:30:39 delay of 12 sec
2023-03-31 10:32:28 2023-04-03 10:37:28
{'s': 'no_data'}
{'c': 162.75, 'd': 0.39, 'dp': 0.2402, 'h': 163.09, 'l': 162.13, 'o': 162.44, 'pc': 162.36, 't': 1680273141}        # 1680273141 = 2023-03-31 10:32:21 delay of 7 sec

{'c': 162.36, 'd': 1.59, 'dp': 0.989, 'h': 162.47, 'l': 161.271, 'o': 161.53, 'pc': 160.77, 't': 1680206404}
'''
'''
#https://pypi.org/project/websocket_client/
import websocket

def on_message(ws, message):
    _json = json.loads(message)
    print(_json)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    #ws.send('{"type":"subscribe","symbol":"AMZN"}')
    #ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    #ws.send('{"type":"subscribe","symbol":"IC MARKETS:1"}')

if __name__ == "__main__":
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
'''

'''
ws = create_connection("ws://192.168.1.5:6437")
allowedProcessingTime = .1 #seconds
timeStep = 0 
while True:
    result = ws.recv()
    if time.clock() - timeStep > allowedProcessingTime:
        timeStep = time.clock()
        resultj = json.loads(result)
        if "hands" in resultj and len(resultj["hands"]) > 0:
                # print resultj["hands"][0]["palmNormal"]
                rotation = math.atan2(resultj["hands"][0]["palmNormal"][0], -resultj["hands"][0]["palmNormal"][1])
                dc = translate(rotation, -1, 1, 5, 20)
                pwm.ChangeDutyCycle(float(dc))
        print "processing time = " + str(time.clock() - timeStep) #informational
        
        
2023-03-31 14:15:34 2023-04-03 14:20:34
1680286538049 = 2023-03-31 14:15:38 delay of 4 sec

--- request header ---
GET /?token=cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90 HTTP/1.1
Upgrade: websocket
Host: ws.finnhub.io
Origin: https://ws.finnhub.io
Sec-WebSocket-Key: U34XGhcFj5TiUXxZst9QoQ==
Sec-WebSocket-Version: 13
Connection: Upgrade


-----------------------
--- response header ---
HTTP/1.1 101 Switching Protocols
Date: Fri, 31 Mar 2023 18:15:38 GMT
Connection: upgrade
Upgrade: websocket
Sec-WebSocket-Accept: ZuCwKavnG39m9mkP4oerpQ4By6k=
CF-Cache-Status: DYNAMIC
Report-To: {"endpoints":[{"url":"https:\/\/a.nel.cloudflare.com\/report\/v3?s=tra7hviAw5Kvzqr%2FiHea5JxQWVwVJ0Wn7ABGa1UeRIqILMrSBkBtKAfMopzxMv1Tq%2BY5TzmzS44mX6uV3eoCaQbWh%2BcRPrcUDu1GJlfExi3B711mphWELgaAYt2ruVFS"}],"group":"cf-nel","max_age":604800}
NEL: {"success_fraction":0,"report_to":"cf-nel","max_age":604800}
Server: cloudflare
CF-RAY: 7b0a9430fd91427c-EWR
alt-svc: h3=":443"; ma=86400, h3-29=":443"; ma=86400
-----------------------
Websocket connected
++Sent raw: b'\x81\xa4\xfc\xb5\xd5\x1a\x87\x97\xa1c\x8c\xd0\xf7 \xde\xc6\xa0x\x8f\xd6\xa7s\x9e\xd0\xf76\xde\xc6\xacw\x9e\xda\xb98\xc6\x97\x94[\xac\xf9\xf7g'
++Sent decoded: fin=1 opcode=1 data=b'{"type":"subscribe","symbol":"AAPL"}'
{"data":[{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286537580,"v":5},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538049,"v":10},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":142},{"c":["1","8","12"],"p":164.065,"s":"AAPL","t":1680286538064,"v":35},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":100},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":15},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286538276,"v":26},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538295,"v":1}],"type":"trade"}
++Rcv raw: b'\x81~\x02\xae{"data":[{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286537580,"v":5},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538049,"v":10},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":142},{"c":["1","8","12"],"p":164.065,"s":"AAPL","t":1680286538064,"v":35},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":100},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":15},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286538276,"v":26},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538295,"v":1}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286537580,"v":5},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538049,"v":10},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":142},{"c":["1","8","12"],"p":164.065,"s":"AAPL","t":1680286538064,"v":35},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":100},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":15},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286538276,"v":26},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538295,"v":1}],"type":"trade"}'
++Rcv raw: b'\x81~\x02\x1d{"data":[{"c":["1","12"],"p":164.0641,"s":"AAPL","t":1680286538611,"v":52},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538661,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538965,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539076,"v":36},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539085,"v":1},{"c":["1","12"],"p":164.0611,"s":"AAPL","t":1680286539096,"v":1},{"c":["1","12"],"p":164.0688,"s":"AAPL","t":1680286539217,"v":1},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286539455,"v":10}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.0641,"s":"AAPL","t":1680286538611,"v":52},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538661,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538965,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539076,"v":36},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539085,"v":1},{"c":["1","12"],"p":164.0611,"s":"AAPL","t":1680286539096,"v":1},{"c":["1","12"],"p":164.0688,"s":"AAPL","t":1680286539217,"v":1},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286539455,"v":10}],"type":"trade"}'
{"data":[{"c":["1","12"],"p":164.0641,"s":"AAPL","t":1680286538611,"v":52},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538661,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286538965,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539076,"v":36},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539085,"v":1},{"c":["1","12"],"p":164.0611,"s":"AAPL","t":1680286539096,"v":1},{"c":["1","12"],"p":164.0688,"s":"AAPL","t":1680286539217,"v":1},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286539455,"v":10}],"type":"trade"}
++Rcv raw: b'\x81~\x02\x89{"data":[{"c":["1","12"],"p":164.0609,"s":"AAPL","t":1680286539668,"v":3},{"c":["1","12"],"p":164.0682,"s":"AAPL","t":1680286539847,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":40},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":2},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":4},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":200},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":182},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":10}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.0609,"s":"AAPL","t":1680286539668,"v":3},{"c":["1","12"],"p":164.0682,"s":"AAPL","t":1680286539847,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":40},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":2},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":4},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":200},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":182},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":10}],"type":"trade"}'
++Rcv raw: b'\x81~\x02\x8e{"data":[{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":3},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":64},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539959,"v":50},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":4},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540042,"v":71},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286540082,"v":173}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":3},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":64},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539959,"v":50},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":4},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540042,"v":71},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286540082,"v":173}],"type":"trade"}'
++Rcv raw: b'\x81~\x02M{"data":[{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":14},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540153,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540154,"v":700},{"c":["1","12"],"p":164.0672,"s":"AAPL","t":1680286540261,"v":1},{"c":["1"],"p":164.061,"s":"AAPL","t":1680286540348,"v":100},{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286540383,"v":3},{"c":["1","12"],"p":164.062,"s":"AAPL","t":1680286540389,"v":1},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286540527,"v":1}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":14},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540153,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540154,"v":700},{"c":["1","12"],"p":164.0672,"s":"AAPL","t":1680286540261,"v":1},{"c":["1"],"p":164.061,"s":"AAPL","t":1680286540348,"v":100},{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286540383,"v":3},{"c":["1","12"],"p":164.062,"s":"AAPL","t":1680286540389,"v":1},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286540527,"v":1}],"type":"trade"}'
{"data":[{"c":["1","12"],"p":164.0609,"s":"AAPL","t":1680286539668,"v":3},{"c":["1","12"],"p":164.0682,"s":"AAPL","t":1680286539847,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":40},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":2},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":4},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":200},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":182},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":10}],"type":"trade"}
{"data":[{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286539953,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":3},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539953,"v":64},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539959,"v":50},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":4},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286539971,"v":11},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540042,"v":71},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286540082,"v":173}],"type":"trade"}
{"data":[{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286540141,"v":14},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540153,"v":100},{"c":["1"],"p":164.06,"s":"AAPL","t":1680286540154,"v":700},{"c":["1","12"],"p":164.0672,"s":"AAPL","t":1680286540261,"v":1},{"c":["1"],"p":164.061,"s":"AAPL","t":1680286540348,"v":100},{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286540383,"v":3},{"c":["1","12"],"p":164.062,"s":"AAPL","t":1680286540389,"v":1},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286540527,"v":1}],"type":"trade"}
++Rcv raw: b'\x81~\x01\x9a{"data":[{"c":["1","12"],"p":164.0608,"s":"AAPL","t":1680286540637,"v":2},{"c":["1"],"p":164.0601,"s":"AAPL","t":1680286541078,"v":1700},{"c":["1","12"],"p":164.0699,"s":"AAPL","t":1680286541118,"v":52},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541129,"v":4},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541236,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286541472,"v":1}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.0608,"s":"AAPL","t":1680286540637,"v":2},{"c":["1"],"p":164.0601,"s":"AAPL","t":1680286541078,"v":1700},{"c":["1","12"],"p":164.0699,"s":"AAPL","t":1680286541118,"v":52},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541129,"v":4},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541236,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286541472,"v":1}],"type":"trade"}'
{"data":[{"c":["1","12"],"p":164.0608,"s":"AAPL","t":1680286540637,"v":2},{"c":["1"],"p":164.0601,"s":"AAPL","t":1680286541078,"v":1700},{"c":["1","12"],"p":164.0699,"s":"AAPL","t":1680286541118,"v":52},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541129,"v":4},{"c":["1","12"],"p":164.065,"s":"AAPL","t":1680286541236,"v":1},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286541472,"v":1}],"type":"trade"}
++Rcv raw: b'\x81~\x00\xd4{"data":[{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286542024,"v":1},{"c":["1"],"p":164.07,"s":"AAPL","t":1680286542124,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542344,"v":50}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286542024,"v":1},{"c":["1"],"p":164.07,"s":"AAPL","t":1680286542124,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542344,"v":50}],"type":"trade"}'
{"data":[{"c":["1","12"],"p":164.07,"s":"AAPL","t":1680286542024,"v":1},{"c":["1"],"p":164.07,"s":"AAPL","t":1680286542124,"v":100},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542344,"v":50}],"type":"trade"}
++Rcv raw: b'\x81~\x01c{"data":[{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":1},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":5},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542996,"v":15},{"c":["1","12"],"p":164.0591,"s":"AAPL","t":1680286543384,"v":1}],"type":"trade"}'
++Rcv decoded: fin=1 opcode=1 data=b'{"data":[{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":1},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":5},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542996,"v":15},{"c":["1","12"],"p":164.0591,"s":"AAPL","t":1680286543384,"v":1}],"type":"trade"}'
{"data":[{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":1},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286542985,"v":5},{"c":["1","12"],"p":164.06,"s":"AAPL","t":1680286542996,"v":15},{"c":["1","12"],"p":164.0591,"s":"AAPL","t":1680286543384,"v":1}],"type":"trade"}
'''

from fhub import Subscription
from time import sleep

def price_monitor(ticker):
    # Callback function receive a ticker object
    # calculate the average of the last 30 ticks using the ticker history
    average = ticker.history.price.tail(30).mean()      #.round(2)
    # display the price and the calculated average
    print (f'{ticker.symbol}. Price: {ticker.price} Average(30) : {average}')
    # show a message if price is over its average
    if ticker.price > average:
        print(f'{ticker.symbol} is over its average price')
    return

# Create a subscription and connect
subs = Subscription("cgiakg9r01qnl59fjg8gcgiakg9r01qnl59fjg90")
# A list of the symbols to which to subscribe is passed
# Created function  is assigned as a callback when a new tick is received
#subs.connect(["BINANCE:BTCUSDT", "IC MARKETS:1", "AAPL"],
subs.connect(["AAPL"]       #,
            #on_tick=price_monitor
            )

# Subscription is maintained for 20 seconds and then closed.
#for f in range(20):
#    sleep(1)
m = '{"data":[{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286537580,"v":5},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538049,"v":10},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":142},{"c":["1","8","12"],"p":164.065,"s":"AAPL","t":1680286538064,"v":35},{"c":["1","8"],"p":164.06,"s":"AAPL","t":1680286538064,"v":100},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":4},{"c":["1","8","12"],"p":164.06,"s":"AAPL","t":1680286538064,"v":15},{"c":["1","12"],"p":164.0601,"s":"AAPL","t":1680286538276,"v":26},{"c":["1","12"],"p":164.0615,"s":"AAPL","t":1680286538295,"v":1}],"type":"trade"}'
j = json.loads(m)
subs._feeder(j)
print(subs.tickers['AAPL'].history)
print(subs.tickers['AAPL'].history.loc[subs.tickers['AAPL'].history.shape[0]-1, 'Date'])
print(subs.tickers['AAPL'].history.loc[len(subs.tickers['AAPL'].history)-1, 'Date'])
subs.close()

#self.data.iloc[len(self.data)] = df.iloc[len(df)-1]
#
'''
from twelvedata import TDClient

# Initialize client - apikey parameter is requiered
td = TDClient(apikey="11b1e495dd874ccfa6643abd352afb37")

# Construct the necessary time series
ts = td.time_series(
    symbol="AAPL",
    interval="1min",
    outputsize=1000,
    timezone="America/New_York",
    start_date = '2023-03-31 10:34:00',
    end_date = '2023-03-31 16:10:00'
)

# Returns pandas.DataFrame
print(ts.as_pandas())
'''

'''
2023-03-31 10:33:58 2023-04-03 10:38:58
delay of 1:58 
                          open       high        low      close  volume
datetime                                                               
2023-03-31 10:32:00  162.72000  162.77930  162.70000  162.73000  125196
2023-03-31 10:31:00  162.66000  162.73000  162.63000  162.72000  172585
2023-03-31 10:30:00  162.56500  162.67000  162.52000  162.65131   88845
2023-03-31 10:29:00  162.67000  162.69000  162.52000  162.56000  100066

2023-03-31 10:35:30 2023-04-03 10:40:30
delay of 1:30

                          open       high        low      close  volume
datetime                                                               
2023-03-31 10:34:00  162.69501  162.75999  162.69501  162.75999   69419
'''

'''
messages_history = []

def on_event(e):
    # do whatever is needed with data
    print(e)
    messages_history.append(e)


#td = TDClient(apikey="YOUR_API_KEY_HERE")
ws = td.websocket(symbols="BTC/USD", on_event=on_event)
ws.subscribe(['ETH/BTC', 'AAPL'])
ws.connect()
while True:
    print('messages received: ', len(messages_history))
    ws.heartbeat()
    time.sleep(10)
'''



'''
2023-03-31 14:12:04 2023-04-03 14:17:04

1680286328 = 2023-03-31 14:12:08 delay of 4 sec
messages received:  0

{'event': 'subscribe-status', 'status': 'ok', 'success': [{'symbol': 'ETH/BTC', 'exchange': 'Huobi', 'type': 'Digital Currency'}, {'symbol': 'AAPL', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'country': 'United States', 'type': 'Common Stock'}, {'symbol': 'BTC/USD', 'exchange': 'Coinbase Pro', 'type': 'Digital Currency'}], 'fails': None}
{'event': 'price', 'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'type': 'Common Stock', 'timestamp': 1680286328, 'price': 164.13, 'day_volume': 29666927}
{'event': 'price', 'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'type': 'Common Stock', 'timestamp': 1680286329, 'price': 164.12, 'day_volume': 29668437}
{'event': 'price', 'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'type': 'Common Stock', 'timestamp': 1680286330, 'price': 164.12, 'day_volume': 29668800}
{'event': 'price', 'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'type': 'Common Stock', 'timestamp': 1680286331, 'price': 164.115, 'day_volume': 29669569}
{'event': 'price', 'symbol': 'BTC/USD', 'currency_base': 'Bitcoin', 'currency_quote': 'US Dollar', 'exchange': 'Coinbase Pro', 'type': 'Digital Currency', 'timestamp': 1680286333, 'price': 28326.8, 'bid': 28326.8, 'ask': 28326.8, 'day_volume': 18817}
{'event': 'price', 'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ', 'mic_code': 'XNGS', 'type': 'Common Stock', 'timestamp': 1680286333, 'price': 164.1, 'day_volume': 29671277}
'''
'''
#for finnhub winsocket

https://github.com/tspannhw/FLiPN-Py-Stocks/blob/main/stocks.py

#https://pypi.org/project/websocket_client/
# https://finnhub.io/docs/api/websocket-trades
from time import sleep
from math import isnan
import time
import sys
import datetime
import subprocess
import sys
import os
from subprocess import PIPE, Popen
import traceback
import math
import base64
import json
from time import gmtime, strftime
import random, string
import psutil
import base64
import uuid
import json
import socket 
import time
import logging
import pulsar
from pulsar.schema import *
import websocket
from jsonpath_ng import jsonpath, parse


# Pulsar Message Schema
class Stock (Record):
    symbol = String()
    ts = Float()
    currentts = Float()
    volume = Float()
    price = Float()
    tradeconditions = String()
    uuid = String()


client = pulsar.Client('pulsar://localhost:6650')
producer = client.create_producer(topic='persistent://public/default/stocks' ,schema=JsonSchema(Stock),properties={"producer-name": "py-stocks","producer-id": "pystocks1" })


def on_message(ws, message):
    stocks_dict = json.loads(message)

    try:
        if stocks_dict is not None and "data" in stocks_dict:
            for stockitem in stocks_dict['data']:
                try:
                    if stockitem is not None and stockitem['s'] is not None: 
                        print(stockitem['p'])
                        uuid_key = '{0}_{1}'.format(strftime("%Y%m%d%H%M%S",gmtime()),uuid.uuid4())
                        stockRecord = Stock()
                        stockRecord.symbol = stockitem['s']
                        stockRecord.ts = float(stockitem['t'])
                        stockRecord.currentts = float(strftime("%Y%m%d%H%M%S",gmtime()))
                        stockRecord.volume = float(stockitem['v'])
                        stockRecord.price = float(stockitem['p'])
                        stockRecord.tradeconditions = ','.join(stockitem['c'])
                        stockRecord.uuid = uuid_key
                        if ( stockitem['s'] != '' ):
                            producer.send(stockRecord,partition_key=str(uuid_key))
                        print(stockRecord)
                except NameError:
                    print ("skip it")
    except Exception as ex:
        print (ex)

def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed websocket to finnhub ###")
    print(close_status_code)
    print(close_msg)


def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.send('{"type":"subscribe","symbol":"AMZN"}')
    ws.send('{"type":"subscribe","symbol":"TSLA"}')
    ws.send('{"type":"subscribe","symbol":"AMD"}')
    ws.send('{"type":"subscribe","symbol":"MSFT"}')
    ws.send('{"type":"subscribe","symbol":"GOOG"}')
    ws.send('{"type":"subscribe","symbol":"META"}')
    ws.send('{"type":"subscribe","symbol":"NVDA"}')
    ws.send('{"type":"subscribe","symbol":"CRM"}')
    ws.send('{"type":"subscribe","symbol":"BABA"}')
    ws.send('{"type":"subscribe","symbol":"PYPL"}')
    ws.send('{"type":"subscribe","symbol":"EA"}')
    ws.send('{"type":"subscribe","symbol":"WMT"}')
    ws.send('{"type":"subscribe","symbol":"NKE"}')
    ws.send('{"type":"subscribe","symbol":"BRK.B"}')
    ws.send('{"type":"subscribe","symbol":"GOOGL"}')
    ws.send('{"type":"subscribe","symbol":"UNH"}')
    ws.send('{"type":"subscribe","symbol":"JNJ"}')
    ws.send('{"type":"subscribe","symbol":"XOM"}')
    ws.send('{"type":"subscribe","symbol":"JPM"}')
    ws.send('{"type":"subscribe","symbol":"V"}')
    ws.send('{"type":"subscribe","symbol":"HD"}')
    ws.send('{"type":"subscribe","symbol":"LLY"}')
    ws.send('{"type":"subscribe","symbol":"CVX"}')
    ws.send('{"type":"subscribe","symbol":"ABBV"}')
    ws.send('{"type":"subscribe","symbol":"PEP"}')
    ws.send('{"type":"subscribe","symbol":"BAC"}')
    ws.send('{"type":"subscribe","symbol":"KO"}')
    ws.send('{"type":"subscribe","symbol":"MA"}')
    ws.send('{"type":"subscribe","symbol":"AVGO"}')
    ws.send('{"type":"subscribe","symbol":"TMO"}')
    ws.send('{"type":"subscribe","symbol":"COST"}')
    ws.send('{"type":"subscribe","symbol":"CSCO"}')
    ws.send('{"type":"subscribe","symbol":"MCD"}')
    ws.send('{"type":"subscribe","symbol":"ABT"}')
    ws.send('{"type":"subscribe","symbol":"VZ"}')
    ws.send('{"type":"subscribe","symbol":"DIS"}')
    ws.send('{"type":"subscribe","symbol":"BMY"}')
    ws.send('{"type":"subscribe","symbol":"CMCSA"}')
    ws.send('{"type":"subscribe","symbol":"RTX"}')
    ws.send('{"type":"subscribe","symbol":"HON"}')
    ws.send('{"type":"subscribe","symbol":"IBM"}')
    ws.send('{"type":"subscribe","symbol":"CVS"}')
    ws.send('{"type":"subscribe","symbol":"ORCL"}')
    ws.send('{"type":"subscribe","symbol":"CAT"}')
    ws.send('{"type":"subscribe","symbol":"LOW"}')
    ws.send('{"type":"subscribe","symbol":"BLK"}')
    ws.send('{"type":"subscribe","symbol":"MS"}')
    ws.send('{"type":"subscribe","symbol":"BA"}')
    ws.send('{"type":"subscribe","symbol":"INTC"}')
    ws.send('{"type":"subscribe","symbol":"INTU"}')
    ws.send('{"type":"subscribe","symbol":"CB"}')
    ws.send('{"type":"subscribe","symbol":"TMUS"}')
    ws.send('{"type":"subscribe","symbol":"C"}')
    ws.send('{"type":"subscribe","symbol":"DUK"}')
    ws.send('{"type":"subscribe","symbol":"BDX"}')
    ws.send('{"type":"subscribe","symbol":"SLB"}')
    ws.send('{"type":"subscribe","symbol":"MMM"}')
    ws.send('{"type":"subscribe","symbol":"CL"}')
    ws.send('{"type":"subscribe","symbol":"TGT"}')
    ws.send('{"type":"subscribe","symbol":"MRNA"}')
    ws.send('{"type":"subscribe","symbol":"ICE"}')
    ws.send('{"type":"subscribe","symbol":"USB"}')

    print("openned websocket connection to finnhub")
    # ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    # ws.send('{"type":"subscribe","symbol":"IC MARKETS:1"}')


if __name__ == "__main__":
    #websocket.enableTrace(True)

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=token",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
    
    self.wst = threading.Thread(
        target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
    self.wst.daemon = True
    self.wst.start()
'''

'''
https://github.com/RSKriegs/finnhub-streaming-data-pipeline
https://github.com/paduel/fhub/blob/master/fhub/real_time.py

'''