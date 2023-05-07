import yfinance as yf
import streamlit as st
import datetime
import talib
#import ta
import pandas as pd
import requests
import plotly.graph_objects as go
from test_rl_macd_v2 import StockRL
from test_plot import StockPlotter
import numpy as np
from test_stockstats import StockStats
from test_mongo import MongoExplorer
import time
import threading
#from streamlit.report_thread import add_report_ctx
import asyncio
from test_cup_with_handle import Rule_Cup_with_Handle
import os.path

yf.pdr_override()

st.write("""
# My Stock
""")
#Technical Analysis Web Application
#Shown below are the **Moving Average Crossovers**, **Bollinger Bands**, **MACD's**, **Commodity Channel Indexes**, and **Relative Strength Indexes** of any stock!

st.sidebar.header('User Input Parameters')

today = datetime.date.today()
start = today + datetime.timedelta(days=-365*20)
end = today + datetime.timedelta(days=1)
def user_input_features():
    ticker = st.sidebar.text_input("Ticker", 'TSLA')
    start_date = st.sidebar.text_input("Start Date", f'{start}')
    end_date = st.sidebar.text_input("End Date", f'{end}')
    run_rl = st.sidebar.checkbox('Run RL', False)
    run_g20 = st.sidebar.checkbox('Run G20', False)
    return ticker, start_date, end_date, run_rl, run_g20

symbol, start, end, run_rl, run_g20 = user_input_features()

def get_symbol(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']
#company_name = get_symbol(symbol.upper())
company_name = symbol.upper()

start = pd.to_datetime(start)
end = pd.to_datetime(end)

# Read data
data = yf.download(symbol,start,end)
data = data.reset_index()

st.header(f"Adjusted Close Price\n {company_name}")
c1 = st.empty()

def candlestick():
    #candlestick
    #set1 = { 'x': data.AdaDate, 'open': df.AdaOpen, 'close': df.AdaClose, 'high': df.AdaHigh, 'low': df.AdaLow, 'type': 'candlestick',}
    #data = [set1, set2, set3, set4]
    #fig = go.Figure(data=data)
    #st.header(f"Adjusted Close Price\n {company_name}")
    # Exponential Moving Average
    data['EMA5'] = talib.EMA(data['Adj Close'], timeperiod = 5)
    data['EMA20'] = talib.EMA(data['Adj Close'], timeperiod = 20)
    data['EMA60'] = talib.EMA(data['Adj Close'], timeperiod = 60)
    data['EMA120'] = talib.EMA(data['Adj Close'], timeperiod = 120)
    data['EMA250'] = talib.EMA(data['Adj Close'], timeperiod = 250)
    fig1 = go.Figure(data=[go.Candlestick(x=data['Date'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Adj Close'], increasing_line_color= 'green', decreasing_line_color= 'red')])
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['EMA5'], name='EMA5', line=dict(color='purple')))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['EMA20'], name='EMA20', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['EMA60'], name='EMA60', line=dict(color='green')))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['EMA120'], name='EMA120', line=dict(color='yellow')))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['EMA250'], name='EMA250', line=dict(color='red')))
    fig1.update_layout(
        autosize=False,
        width=800,
        height=600,
        margin=dict(l=20, r=0, b=0, t=40))
    c1.plotly_chart(fig1)

# Adjusted Close Price
#st.header(f"Adjusted Close Price\n {company_name}")
#st.line_chart(data['Adj Close'])

# ## SMA and EMA
#Simple Moving Average
#data['SMA'] = talib.SMA(data['Adj Close'], timeperiod = 20)

#fig2 = go.Figure()
#fig2.add_trace(go.Scatter(x=data['Date'], y=data['Adj Close'], name='Close', line=dict(color='grey')))
#fig2.add_trace(go.Scatter(x=data['Date'], y=data['EMA20'], name='EMA20', line=dict(color='blue')))
#fig2.add_trace(go.Scatter(x=data['Date'], y=data['EMA60'], name='EMA60', line=dict(color='green')))
#fig2.add_trace(go.Scatter(x=data['Date'], y=data['EMA120'], name='EMA120', line=dict(color='yellow')))
#fig2.add_trace(go.Scatter(x=data['Date'], y=data['EMA250'], name='EMA250', line=dict(color='red')))
candlestick()

# Plot
#st.header(f"Exponential Moving Average\n {company_name}")
#st.line_chart(data[['Adj Close','EMA20', 'EMA60', 'EMA120', 'EMA250']])
#st.plotly_chart(fig2)

# Bollinger Bands
#data['upper_band'], data['middle_band'], data['lower_band'] = talib.BBANDS(data['Adj Close'], timeperiod =20)

# Plot
#st.header(f"Bollinger Bands\n {company_name}")
#st.line_chart(data[['Adj Close','upper_band','middle_band','lower_band']])

## CCI (Commodity Channel Index)
# CCI
#cci = ta.trend.cci(data['High'], data['Low'], data['Close'], n=31, c=0.015)

# Plot
#st.header(f"Commodity Channel Index\n {company_name}")
#st.line_chart(cci)

# ## RSI (Relative Strength Index)
# RSI
#data['RSI'] = talib.RSI(data['Adj Close'], timeperiod=14)

# Plotu
#st.header(f"Relative Strength Index\n {company_name}")
#st.line_chart(data['RSI'])

# ## OBV (On Balance Volume)
# OBV
#data['OBV'] = talib.OBV(data['Adj Close'], data['Volume'])/10**6

# Plot
#st.header(f"On Balance Volume\n {company_name}")
#st.line_chart(data['OBV'])

# ## MACD (Moving Average Convergence Divergence)
# MACD

st.header(f"Moving Average Convergence Divergence\n {company_name}")
pl1 = st.empty()
st.header(f"Moving Average Convergence Divergence - R Vales\n {company_name}")
pl2 = st.empty()
pl3 = st.empty()
stop_button = st.empty()

def macd():
    short = 3
    long = 7
    signal = 19
    macd_threshold = 0
    macd_min_len = 0

    mongo = MongoExplorer()
    mongo_rl_param = mongo.mongoDB['test_rl_macd_param']
    mongo_query_param = {"symbol": symbol}
    quote_param = mongo_rl_param.find(mongo_query_param)
    if mongo_rl_param.count_documents(mongo_query_param) > 0:
        short = quote_param[0]['short']
        long = quote_param[0]['long']
        signal = quote_param[0]['signal']
        macd_threshold = quote_param[0]['macd_threshold']
        macd_min_len = quote_param[0]['macd_min_len']

    #while 1:
    #data['macd'], data['macdsignal'], data['macdhist'] = talib.MACD(data['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    ss = StockStats(symbol.upper())
    ss.macd(short, long, signal)
    s = ss.stock.reset_index()
    #print(s)
    macdh1 = s.loc[(s['macdh'] >= 0) & (s['r'] >= 0.2)]
    macdh2 = s.loc[(s['macdh'] < 0) & (s['r'] >= 0.2)]
    macdh3 = s.loc[s['r'] < 0.2]

    #data['macd'], data['macdsignal'], data['macdhist'] = talib.MACD(data['Adj Close'], fastperiod=6, slowperiod=13, signalperiod=9)
    #data['macd1'] = data['macdhist']
    #data.loc[(data['macd1'] > 0 ), 'macd1'] = 0
    #data['macd2'] = data['macdhist']
    #data.loc[(data['macd2'] <= 0 ), 'macd2'] = 0
    fig3 = go.Figure()
    #fig3.add_trace(go.Bar(x=data['Date'], y=data['macd1'], name='', marker=dict(color='red', line=dict(width=0))))
    #fig3.add_trace(go.Bar(x=data['Date'], y=data['macd2'], name='', marker=dict(color='green', line=dict(width=0))))
    fig3.add_trace(go.Bar(x=macdh1['date'], y=macdh1['macdh'], name='', marker=dict(color='green', line=dict(width=0))))
    fig3.add_trace(go.Bar(x=macdh2['date'], y=macdh2['macdh'], name='', marker=dict(color='red', line=dict(width=0))))
    fig3.add_trace(go.Bar(x=macdh3['date'], y=macdh3['macdh'], name='', marker=dict(color='blue', line=dict(width=0))))

    # Plot
    #st.line_chart(data[['macd','macdsignal', 'macdhist']])
    #st.bar_chart(data[['macd1', 'macd2']])
    pl1.plotly_chart(fig3)

    fig31 = go.Figure()
    #fig3.add_trace(go.Bar(x=data['Date'], y=data['macd1'], name='', marker=dict(color='red', line=dict(width=0))))
    #fig3.add_trace(go.Bar(x=data['Date'], y=data['macd2'], name='', marker=dict(color='green', line=dict(width=0))))
    fig31.add_trace(go.Bar(x=macdh1['date'], y=macdh1['r']*macdh1['macd_sign'], name='', marker=dict(color='green', line=dict(width=0))))
    fig31.add_trace(go.Bar(x=macdh2['date'], y=macdh2['r']*macdh2['macd_sign'], name='', marker=dict(color='red', line=dict(width=0))))
    fig31.add_trace(go.Bar(x=macdh3['date'], y=macdh3['r']*macdh3['macd_sign'], name='', marker=dict(color='blue', line=dict(width=0))))

    # Plot
    #st.line_chart(data[['macd','macdsignal', 'macdhist']])
    #st.bar_chart(data[['macd1', 'macd2']])
    pl2.plotly_chart(fig31)

    #st.write(ss.stock.tail(100))
    #pl3.dataframe(ss.stock.tail(100))
    pl3.dataframe(s.tail(100))

    #time.sleep(2)

#thread = threading.Thread(target=macd)
#add_report_ctx(thread)
#thread.start()
#while True:
#    time.sleep(1)

#async def a():
#    while True:
#        candlestick()
#        macd()
#        aw = await asyncio.sleep(100)
#asyncio.run(a())
macd()

if run_rl:
    short = 3
    long = 7
    signal = 19
    macd_threshold = 0
    macd_min_len = 0

    mongo = MongoExplorer()
    mongo_rl_param = mongo.mongoDB['test_rl_macd_param']
    mongo_query_param = {"symbol": symbol}
    quote_param = mongo_rl_param.find(mongo_query_param)
    if mongo_rl_param.count_documents(mongo_query_param) > 0:
        short = quote_param[0]['short']
        long = quote_param[0]['long']
        signal = quote_param[0]['signal']
        macd_threshold = quote_param[0]['macd_threshold']
        macd_min_len = quote_param[0]['macd_min_len']

    # get StockRL
    file_path = './rl/test_rl_' + symbol + '.zip'
    rl = StockRL(symbol.upper(), 0, short, long, signal, save_loc='./rl/test_rl_', macd_threshold=macd_threshold, macd_min_len=macd_min_len)
    rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
    d, a = rl.run('df')
    r = pd.DataFrame(d)

    start = r.iloc[0]['net_worth']
    start_date = r.iloc[0]['date']
    start_price = r.iloc[0]['close']
    end = r.iloc[-1]['net_worth']
    end_date = r.iloc[-1]['date']
    end_price = r.iloc[-1]['close']
    dur = (end_date - start_date).days / 365
    model_gain = end / start
    model_perf = 10 ** (np.log10(end / start) / dur)
    buy_and_hold_gain = end_price / start_price
    buy_and_hold_perf = 10 ** (np.log10(end_price / start_price) / dur)
    model_score = model_perf / buy_and_hold_perf
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=r['date'], y=r['net_worth'], name='Net Worth', line=dict(color='grey')))

    st.header(f"RL Model\ndur: {a['duration']:.2f}    model: {a['model_gain']: .1f}, {a['model_perf']:.4f}        buy and hold: {a['buy_and_hold_gain']:.1f}, {a['buy_and_hold_perf']:.4f}  score: {a['model_score']:.4f}\n\n "
              f"date: {a['predict_date']}   accum: {a['predict_macd_accum']:.2f}    len: {a['predict_macd_len']}    action: {a['predict_action']:.2f}   vol: {a['predict_vol']:.2f}")
    #st.line_chart(r['net_worth'])
    st.plotly_chart(fig4)

#    fig5 = go.Figure()
#    fig5.add_trace(go.Scatter(x=r['date'], y=r['current_price'], name='Current Price', line=dict(color='grey')))
#    fig5.add_trace(go.Scatter(x=r['date'], y=r['close'], name='Close', line=dict(color='red')))
#    fig5.add_trace(go.Scatter(x=r['date'], y=r['next_close'], name='Next Close', line=dict(color='green')))

#    st.header(f"RL Model Transaction Price\n {company_name}")
    #st.line_chart(r[['current_price', 'close', 'next_close']])
#    st.plotly_chart(fig5)

#    fig6 = go.Figure()
#    fig6.add_trace(go.Scatter(x=r['date'], y=r['r'], name='R', line=dict(color='grey')))
#    st.header(f"RL Model MACD R\n {company_name}")
    #st.line_chart(r['r'])
#    st.plotly_chart(fig6)

#    fig61 = go.Figure()
#    fig61.add_trace(go.Scatter(x=r['len'], y=r['r'], mode='markers'))
#    st.header(f"RL Model MACD R vs Len\n {company_name}")
    #st.line_chart(r['r'])
#    st.plotly_chart(fig61)

    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=r['date'], y=r['shares_held'], name='Shares Held', mode='lines+markers', line=dict(color='grey')))
    st.header(f"RL Model Shares Held\n {company_name}")
    #st.line_chart(r['shares_held'])
    st.plotly_chart(fig7)

if run_g20:
    p = StockPlotter(symbol.upper(), print_flag=False)
    #st.write(p.fig)
    st.pyplot(p.fig)

#if stop_button.button('Stop',key='stop'):
#    macd()
    #pass
#else:
#    while True:
#        macd()
#        time.sleep(300)

st.header(f"Cup with Handle\n {company_name}")
pl4 = st.empty()
def cwh():
    #cup with handle
    aaod = today.strftime("%Y-%m-%d")
    c = Rule_Cup_with_Handle(aaod)
    dd = c.getdf(symbol)

    rr = c.fit(ticker=symbol, df=dd, threshold=0.8, log_sign=1)
    cwh_data = [0 * x for x in range(len(dd))]
    #print(len(dd))
    for i, r in rr.iterrows():
        #print(r['end_date'])
        cwh_sign = r['cwh_sign']
        endI = r['cwh_end']
        startI = endI - 4 * r['sigma']
        #print(startI, endI)
        data_slice = dd['close'][startI + 1 : endI + 1]
        base = data_slice[endI]
        price_max = max(data_slice)
        price_min = min(data_slice)

        if cwh_sign ==1:
            cwh_points = c.log(r['sigma'])
        else:
            cwh_points = c.log_negative(r['sigma'])
        cwh_max = max(cwh_points)
        cwh_min = min(cwh_points)
        cwh_up_bound = cwh_points[len(cwh_points)-1]
        scale = (price_max-price_min) / (cwh_max - cwh_min)
        cwh_points_scaled = [base + scale * (x - cwh_up_bound) for x in cwh_points]

        for j in range(4 * r['sigma']):
            cwh_data[startI + j] = cwh_points_scaled[j]

    rr2 = c.fit(ticker=symbol, df=dd, threshold=0.8, log_sign=2)
    cwh_data2 = [0 * x for x in range(len(dd))]
    for i, r in rr2.iterrows():
        cwh_sign = r['cwh_sign']
        endI = r['cwh_end']
        startI = endI - 4 * r['sigma']
        #print(startI, endI)
        data_slice = dd['close'][startI + 1 : endI + 1]
        base = data_slice[endI]
        price_max = max(data_slice)
        price_min = min(data_slice)

        if cwh_sign ==1:
            cwh_points = c.log(r['sigma'])
        else:
            cwh_points = c.log_negative(r['sigma'])
        cwh_max = max(cwh_points)
        cwh_min = min(cwh_points)
        cwh_up_bound = cwh_points[len(cwh_points)-1]
        scale = (price_max-price_min) / (cwh_max - cwh_min)
        cwh_points_scaled = [base + scale * (x - cwh_up_bound) for x in cwh_points]

        for j in range(4 * r['sigma']):
            cwh_data2[startI + j] = cwh_points_scaled[j]

    #dd['EMA5'] = talib.EMA(dd['close'], timeperiod = 5)
    #dd['EMA20'] = talib.EMA(dd['close'], timeperiod = 20)
    #dd['EMA60'] = talib.EMA(dd['close'], timeperiod = 60)
    #dd['EMA120'] = talib.EMA(dd['close'], timeperiod = 120)
    #dd['EMA250'] = talib.EMA(dd['close'], timeperiod = 250)
    #fig1 = go.Figure(data=[go.Candlestick(x=data['Date'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Adj Close'], increasing_line_color= 'green', decreasing_line_color= 'red')])
    fig10 = go.Figure(data=[go.Scatter(x=dd['Date'], y=dd['close'], name='Close', line=dict(color='black'))])
    #fig1 = go.Scatter(x=data['Date'], y=data['Adj Close'], line=dict(color='black'))
    #fig1.add_trace(go.Scatter(x=dd['Date'], y=dd['EMA5'], name='EMA5', line=dict(color='purple')))
    #fig1.add_trace(go.Scatter(x=dd['Date'], y=dd['EMA20'], name='EMA20', line=dict(color='blue')))
    #fig1.add_trace(go.Scatter(x=dd['Date'], y=dd['EMA60'], name='EMA60', line=dict(color='green')))
    #fig1.add_trace(go.Scatter(x=dd['Date'], y=dd['EMA120'], name='EMA120', line=dict(color='yellow')))
    #fig1.add_trace(go.Scatter(x=dd['Date'], y=dd['EMA250'], name='EMA250', line=dict(color='red')))
    fig10.add_trace(go.Scatter(x=dd['Date'], y=cwh_data, name='Cup with Handle 1', line=dict(color='orange')))
    fig10.add_trace(go.Scatter(x=dd['Date'], y=cwh_data2, name='Cup with Handle 2', line=dict(color='blue')))
    fig10.update_layout(
        autosize=False,
        width=800,
        height=600,
        margin=dict(l=00, r=0, b=0, t=40))
    pl4.plotly_chart(fig10)

cwh()
