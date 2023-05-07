#from odo import odo
import pandas as pd
from stockstats import StockDataFrame as Sdf
from test_stockstats_v2 import StockStats
from test_rl_macd_v3 import StockRL
import os
from datetime import datetime


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

def daily_run(ticker, short, long, signal, aaod, test=False):
    #today = datetime.now().strftime("%Y_%m_%d")
    fname = './finnhub_data/TSLA_history_finnhub_' + aaod + '.csv'
    #fname = './finnhub_data/TSLA_history_finnhub_2023_04_28.csv'

    #df = odo(fname, pd.DataFrame)
    if os.stat(fname).st_size >0:
        df = pd.read_csv(fname)
        #print(df)
        df1 = df[df['Open'].isnull()]
        df1['Date'] = pd.to_datetime(df1['Date'])
    else:
        df1 = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    print(df1)
    #print(len(df1.loc[: 'Date']))

    ss = StockStats(ticker, interval='no')
    ss.stock = df1.copy()
    ss.stock = Sdf.retype(ss.stock)
    ss.macd(short, long, signal)
    #print(ss.stock)
    #ss.stock = ss.stock.reset_index()

    dd = aaod.replace('_', '-')
    ss.stock = ss.stock.loc[ss.stock.index >= pd.to_datetime(dd + ' 08:00:00-04:00')]
    ss.stock = ss.stock.loc[ss.stock.index <= pd.to_datetime(dd + ' 11:00:00-04:00')]
    cc = ss.macd_crossing_by_threshold_min_len()
    print(cc)

    rl = StockRL(ticker, 0, short, long, signal, save_loc='./rl_focus_8_11/test_rl_', interval='no')
    rl.stock_env.ss = ss.stock
    #print(rl.stock_env.ss)
    rl.stock_env.c2 = cc

    file_path = rl.save_loc + ticker + '.zip'
    if test is False:
        rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
    else:
        rl.reload()

    re = rl.run('screen')
    rl.run_macd('screen')
    print(re)
    return re

model_gain = 1
buy_and_hold_gain = 1
macd_gain = 1

qDates = [
    '2023_04_18',
    '2023_04_19',
    '2023_04_20',
    '2023_04_21',
    '2023_04_25',
    '2023_04_26',
    '2023_04_27'    #,
]

tDates = [
    '2023_04_28',
    '2023_05_01',
    '2023_05_02',
    '2023_05_03',
    '2023_05_04',
    '2023_05_05'
]

ticker='TSLA'
for q in qDates:
    print(q)
    re1 = daily_run(ticker, 3, 7, 19, q)

for t in tDates:
    print(t)
    re1 = daily_run(ticker, 3, 7, 19, t, test=True)
    if re1 is not None:
        model_gain = model_gain * re1['model_gain']
        buy_and_hold_gain = buy_and_hold_gain * re1['buy_and_hold_gain']
        macd_gain = macd_gain * re1['MACD_gain']

    rl2 = daily_run(ticker, 3, 7, 19, t)

print(model_gain, buy_and_hold_gain, macd_gain)

#test_date = '2023_05_05'
#daily_run(ticker, 3, 7, 19, test_date, test=True)

'''
training
1.1251752741217802 1.0490495317978077 1.0260534738325007
test
MACD Perf:          2023-05-05 09:24:14.546000-04:00 - 2023-05-05 10:53:47.371000-04:00   0.00017037116311516997   1.0144498564142865     3.720959110197119e+36
{'model_run_date': '2023-05-06-18-41-29', 'start_date': '2023-05-05', 'end_date': '2023-05-05', 'duration': 0.00017037116311516997, 'model_gain': 1.030250074253555, 'model_perf': 9.276863765374945e+75, 'buy_and_hold_gain': 1.0269658799070565, 'buy_and_hold_perf': 6.737002149298932e+67, 'model_score': 137700175.23803693, 'model_gain_score': 1.0031979585794961, 'predict_date': '2023-05-05', 'predict_macd_accum': 0.01298971174672213, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 1.0144498564142865, 'MACD_perf': 3.720959110197119e+36}
1.1160996305591353 1.0490495317978077 1.0260534738325007
'''