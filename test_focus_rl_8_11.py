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

def daily_run(ticker, short, long, signal, aaod, test=False, period=1):
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
    #print(df1)
    #print(len(df1.loc[: 'Date']))

    ss = StockStats(ticker, interval='no')
    ss.stock = df1.copy()
    ss.stock = Sdf.retype(ss.stock)
    ss.macd(short, long, signal)
    #print(ss.stock)
    #ss.stock = ss.stock.reset_index()

    dd = aaod.replace('_', '-')
    if period == 1:
        #ss.stock = ss.stock.loc[ss.stock.index >= pd.to_datetime(dd + ' 08:00:00-04:00')]
        ss.stock = ss.stock.loc[ss.stock.index >= pd.to_datetime(dd + ' 08:00:00-04:00')]
        ss.stock = ss.stock.loc[ss.stock.index <= pd.to_datetime(dd + ' 11:00:00-04:00')]
        if short == 6:
            save_loc = './rl_sec_8_11/test_rl_'
        else:
            save_loc = './rl_sec_8_11/test_rl_' + str(short) + '_' + str(long) + '_' + str(signal) + '_'
    elif period == 2:
        ss.stock = ss.stock.loc[ss.stock.index >= pd.to_datetime(dd + ' 10:00:00-04:00')]
        ss.stock = ss.stock.loc[ss.stock.index <= pd.to_datetime(dd + ' 15:00:00-04:00')]
        if short == 6:
            save_loc = './rl_sec_10_15/test_rl_'
        else:
            save_loc = './rl_sec_10_15/test_rl_' + str(short) + '_' + str(long) + '_' + str(signal) + '_'

    cc = ss.macd_crossing_by_threshold_min_len()
    #print(cc)

    #print(save_loc)
    rl = StockRL(ticker, 0, short, long, signal, save_loc=save_loc, interval='no')
    rl.stock_env.ss = ss.stock
    #print(rl.stock_env.ss)
    rl.stock_env.c2 = cc

    file_path = rl.save_loc + ticker + '.zip'
    if test is False:
        rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
    else:
        rl.reload()

    #re = rl.run('screen')
    re = rl.run()
    #rl.run_macd('screen')
    print(rl.stock_env.c2.loc[6, "date"], rl.stock_env.c2.loc[len(rl.stock_env.c2.loc[:, 'open'].values) - 2, "date"], re['model_gain'], re['MACD_gain'], re['buy_and_hold_gain'])
    return re

ticker='TSLA'


today = datetime.now().strftime("%Y_%m_%d")
#today = '2023_05_08'
print(today)

print('10sec data 8-11 12/26/9 before retrain')
re1 = daily_run(ticker, 12, 26, 9, today, test=True, period=1)
print('10sec data 8-11 12/26/9 after retrain')
re1 = daily_run(ticker, 12, 26, 9, today, test=False, period=1)

print('10sec data 8-11 6/13/9 before retrain')
re1 = daily_run(ticker, 6, 13, 9, today, test=True, period=1)
print('10sec data 8-11 6/13/9 after retrain')
re1 = daily_run(ticker, 6, 13, 9, today, test=False, period=1)

print('10sec data 8-11 3/7/19 before retrain')
re1 = daily_run(ticker, 3, 7, 19, today, test=True, period=1)
print('10sec data 8-11 3/7/19 after retrain')
re1 = daily_run(ticker, 3, 7, 19, today, test=False, period=1)

print('10sec data 10-15 12/26/9 before retrain')
re2 = daily_run(ticker, 12, 26, 9, today, test=True, period=2)
print('10sec data 10-15 12/26/9 after retrain')
re2 = daily_run(ticker, 12, 26, 9, today, test=False, period=2)

print('10sec data 10-15 6/13/9 before retrain')
re2 = daily_run(ticker, 6, 13, 9, today, test=True, period=2)
print('10sec data 10-15 6/13/9 after retrain')
re2 = daily_run(ticker, 6, 13, 9, today, test=False, period=2)

print('10sec data 10-15 3/7/19 before retrain')
re2 = daily_run(ticker, 3, 7, 19, today, test=True, period=2)
print('10sec data 10-15 3/7/19 after retrain')
re2 = daily_run(ticker, 3, 7, 19, today, test=False, period=2)

'''
model_gain = 1
buy_and_hold_gain = 1
macd_gain = 1

qDates = [
    '2023_05_08',
    '2023_05_09',
    '2023_05_10',
    '2023_05_11',
    '2023_05_12',
    '2023_05_15',
    '2023_05_16',
    '2023_05_17',
    '2023_05_18',
    '2023_05_19'
]

#ticker='TSLA'
for q in qDates:
    print(q)
    #re1 = daily_run(ticker, 12, 26, 9, q, test=False, period=1)
    re1 = daily_run(ticker, 6, 13, 9, q, test=True, period=1)
    if re1 is not None:
        model_gain = model_gain * re1['model_gain']
        buy_and_hold_gain = buy_and_hold_gain * re1['buy_and_hold_gain']
        macd_gain = macd_gain * re1['MACD_gain']
    #re1 = daily_run(ticker, 12, 26, 9, q, test=False, period=1)

    #re2 = daily_run(ticker, 12, 26, 9, q, test=False, period=2)
    re2 = daily_run(ticker, 6, 13, 9, q, test=True, period=2)
    if re2 is not None:
        model_gain = model_gain * re2['model_gain']
        buy_and_hold_gain = buy_and_hold_gain * re2['buy_and_hold_gain']
        macd_gain = macd_gain * re2['MACD_gain']
    #re2 = daily_run(ticker, 12, 26, 9, q, test=False, period=2)

print(model_gain, buy_and_hold_gain, macd_gain)



    #re1 = daily_run(ticker, 3, 7, 19, q)
    #re1 = daily_run(ticker, 6, 13, 9, q)
    #re1 = daily_run(ticker, 12, 26, 9, today, test=False, period=1)

for t in tDates:
    print(t)
    #re1 = daily_run(ticker, 3, 7, 19, t, test=True)
    #re1 = daily_run(ticker, 6, 13, 9, t, test=True)
    re1 = daily_run(ticker, 12, 26, 9, today, test=True)

if re1 is not None:
    model_gain = model_gain * re1['model_gain']
    buy_and_hold_gain = buy_and_hold_gain * re1['buy_and_hold_gain']
    macd_gain = macd_gain * re1['MACD_gain']

#rl2 = daily_run(ticker, 3, 7, 19, t)
'''

'''
tDates = [
    '2023_05_08',
    '2023_05_09',
    '2023_05_10',
    '2023_05_11',
    '2023_05_12'
]
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
'''

'''
training - min data 3, 7, 19
1.1251752741217802 1.0490495317978077 1.0260534738325007
test
MACD Perf:          2023-05-05 09:24:14.546000-04:00 - 2023-05-05 10:53:47.371000-04:00   0.00017037116311516997   1.0144498564142865     3.720959110197119e+36
{'model_run_date': '2023-05-06-18-41-29', 'start_date': '2023-05-05', 'end_date': '2023-05-05', 'duration': 0.00017037116311516997, 'model_gain': 1.030250074253555, 'model_perf': 9.276863765374945e+75, 'buy_and_hold_gain': 1.0269658799070565, 'buy_and_hold_perf': 6.737002149298932e+67, 'model_score': 137700175.23803693, 'model_gain_score': 1.0031979585794961, 'predict_date': '2023-05-05', 'predict_macd_accum': 0.01298971174672213, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 1.0144498564142865, 'MACD_perf': 3.720959110197119e+36}
1.1160996305591353 1.0490495317978077 1.0260534738325007

training - 10sec data 3, 7, 19
MACD Perf:          2023-05-08 09:15:44.234000-04:00 - 2023-05-08 10:56:24.015000-04:00   0.00019152019913749367   0.9968876270350556     8.537365909247736e-08
{'model_run_date': '2023-05-08-15-37-35', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.00019152019913749367, 'model_gain': 0.9927633143309236, 'model_perf': 3.390802964216212e-17, 'buy_and_hold_gain': 0.9869386811535572, 'buy_and_hold_perf': 1.5374582917412667e-30, 'model_score': 22054601301580.14, 'model_gain_score': 1.0059017173899378, 'predict_date': '2023-05-08', 'predict_macd_accum': 0.05130307032729145, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9968876270350556, 'MACD_perf': 8.537365909247736e-08}
MACD Perf:          2023-05-08 09:15:44.234000-04:00 - 2023-05-08 10:56:24.015000-04:00   0.00019152019913749367   0.9968876270350556     8.537365909247736e-08
{'model_run_date': '2023-05-08-15-39-05', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.00019152019913749367, 'model_gain': 0.9850254551221896, 'model_perf': 6.118668590711569e-35, 'buy_and_hold_gain': 0.9869386811535572, 'buy_and_hold_perf': 1.5374582917412667e-30, 'model_score': 3.9797298070322275e-05, 'model_gain_score': 0.9980614540012442, 'predict_date': '2023-05-08', 'predict_macd_accum': 0.05130307032729145, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.5081906914710999, 'MACD_gain': 0.9968876270350556, 'MACD_perf': 8.537365909247736e-08}
0.9850254551221896 0.9869386811535572 0.9968876270350556

training - 10sec data 6, 13, 9
MACD Perf:          2023-05-08 09:19:13.046000-04:00 - 2023-05-08 10:56:24.015000-04:00   0.0001848988140537798   0.9954235421306844     1.6828328077828667e-11
{'model_run_date': '2023-05-08-15-42-57', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.0001848988140537798, 'model_gain': 0.9835862162065427, 'model_perf': 1.3397698887069309e-39, 'buy_and_hold_gain': 0.9872810313927272, 'buy_and_hold_perf': 8.585937249549569e-31, 'model_score': 1.5604235737655981e-09, 'model_gain_score': 0.996257585156911, 'predict_date': '2023-05-08', 'predict_macd_accum': 0.02751298888723342, 'predict_macd_len': 4, 'predict_action': 1.3991297483444214, 'predict_vol': 0.0, 'MACD_gain': 0.9954235421306844, 'MACD_perf': 1.6828328077828667e-11}

training - 10sec data 12, 26, 9
MACD Perf:          2023-05-08 09:19:52.838000-04:00 - 2023-05-08 10:56:13.938000-04:00   0.00018331747843734146   0.988152082913793     5.803469138725592e-29
{'model_run_date': '2023-05-08-15-50-56', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.00018331747843734146, 'model_gain': 1.0007525125333818, 'model_perf': 60.54731196979956, 'buy_and_hold_gain': 0.9853357237869412, 'buy_and_hold_perf': 1.004284303539435e-35, 'model_score': 6.028901552718738e+36, 'model_gain_score': 1.0156462293756987, 'predict_date': '2023-05-08', 'predict_macd_accum': 0.03509468962401163, 'predict_macd_len': 5, 'predict_action': 1.3068093061447144, 'predict_vol': 0.7516829371452332, 'MACD_gain': 0.988152082913793, 'MACD_perf': 5.803469138725592e-29}
MACD Perf:          2023-05-08 09:19:52.838000-04:00 - 2023-05-08 11:55:13.790000-04:00   0.00029556544901065447   0.9869944043829576     5.816133020003988e-20
{'model_run_date': '2023-05-08-18-32-54', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.00029556544901065447, 'model_gain': 1.0126955518237604, 'model_perf': 3.4436510120974705e+18, 'buy_and_hold_gain': 0.9930888901740791, 'buy_and_hold_perf': 6.453290227402153e-11, 'model_score': 5.336271716828939e+28, 'model_gain_score': 1.019743108440418, 'predict_date': '2023-05-08', 'predict_macd_accum': -0.20421396903659358, 'predict_macd_len': 10, 'predict_action': 0.11769329011440277, 'predict_vol': 0.0, 'MACD_gain': 0.9869944043829576, 'MACD_perf': 5.816133020003988e-20}

training - 10sec data 12, 26, 9
before retrain
MACD Perf:          2023-05-09 09:39:27.801000-04:00 - 2023-05-09 10:57:35.689000-04:00   0.0001486519533231862   0.9894451482668384     9.98975720357514e-32
{'model_run_date': '2023-05-09-20-25-06', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0001486519533231862, 'model_gain': 0.9935372133890442, 'model_perf': 1.1411756629738843e-19, 'buy_and_hold_gain': 0.9955081667542774, 'buy_and_hold_perf': 7.035767258654846e-14, 'model_score': 1.6219633495836578e-06, 'model_gain_score': 0.9980201534944115, 'predict_date': '2023-05-09', 'predict_macd_accum': -0.04699213734379343, 'predict_macd_len': 6, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 0.9894451482668384, 'MACD_perf': 9.98975720357514e-32}
after retrain
MACD Perf:          2023-05-09 09:39:27.801000-04:00 - 2023-05-09 10:57:35.689000-04:00   0.0001486519533231862   0.9894451482668384     9.98975720357514e-32
{'model_run_date': '2023-05-09-20-27-38', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0001486519533231862, 'model_gain': 1.0013831118017509, 'model_perf': 10915.454332370407, 'buy_and_hold_gain': 0.9955081667542774, 'buy_and_hold_perf': 7.035767258654846e-14, 'model_score': 1.5514234526366797e+17, 'model_gain_score': 1.0059014533920179, 'predict_date': '2023-05-09', 'predict_macd_accum': -0.04699213734379343, 'predict_macd_len': 6, 'predict_action': 0.14235302805900574, 'predict_vol': 0.4199652671813965, 'MACD_gain': 0.9894451482668384, 'MACD_perf': 9.98975720357514e-32}

training - 10sec data 6, 13, 9
before retrain
MACD Perf:          2023-05-09 09:38:55.960000-04:00 - 2023-05-09 10:58:39.036000-04:00   0.00015167034500253678   1.0002726314874326     6.033224828182543
{'model_run_date': '2023-05-09-20-37-15', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.00015167034500253678, 'model_gain': 0.9974289975349006, 'model_perf': 4.252890947637626e-08, 'buy_and_hold_gain': 0.9970809808473454, 'buy_and_hold_perf': 4.260166493240891e-09, 'model_score': 9.982921921913595, 'model_gain_score': 1.000349035528949, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.04334686859915423, 'predict_macd_len': 5, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.0002726314874326, 'MACD_perf': 6.033224828182543}
after retrain
MACD Perf:          2023-05-09 09:38:55.960000-04:00 - 2023-05-09 10:58:39.036000-04:00   0.00015167034500253678   1.0002726314874326     6.033224828182543
{'model_run_date': '2023-05-09-20-39-23', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.00015167034500253678, 'model_gain': 0.9982303004407495, 'model_perf': 8.474893747899486e-06, 'buy_and_hold_gain': 0.9970809808473454, 'buy_and_hold_perf': 4.260166493240891e-09, 'model_score': 1989.33392893109, 'model_gain_score': 1.0011526843009555, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.04334686859915423, 'predict_macd_len': 5, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.0002726314874326, 'MACD_perf': 6.033224828182543}

training - 10sec data 3, 7, 19
before retrain
MACD Perf:          2023-05-09 09:37:15.035000-04:00 - 2023-05-09 10:58:27.452000-04:00   0.0001545033295281583   0.991948432544198     1.8888119322079924e-23
{'model_run_date': '2023-05-09-20-43-31', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0001545033295281583, 'model_gain': 0.9915530530356138, 'model_perf': 1.4307686636138643e-24, 'buy_and_hold_gain': 0.9940585279337866, 'buy_and_hold_perf': 1.7752661368452898e-17, 'model_score': 8.059460122167319e-08, 'model_gain_score': 0.9974795499180712, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.08332661858892673, 'predict_macd_len': 5, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.991948432544198, 'MACD_perf': 1.8888119322079924e-23}
after retrain
MACD Perf:          2023-05-09 09:37:15.035000-04:00 - 2023-05-09 10:58:27.452000-04:00   0.0001545033295281583   0.991948432544198     1.8888119322079924e-23
{'model_run_date': '2023-05-09-20-44-52', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0001545033295281583, 'model_gain': 0.9951321093790733, 'model_perf': 1.9204360160938126e-14, 'buy_and_hold_gain': 0.9940585279337866, 'buy_and_hold_perf': 1.7752661368452898e-17, 'model_score': 1081.773586638956, 'model_gain_score': 1.0010799982245695, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.08332661858892673, 'predict_macd_len': 5, 'predict_action': 0.17052164673805237, 'predict_vol': 0.0, 'MACD_gain': 0.991948432544198, 'MACD_perf': 1.8888119322079924e-23}

10sec data 10-15 12/26/9
init train
MACD Perf:          2023-05-08 10:13:11.277000-04:00 - 2023-05-08 14:56:21.254000-04:00   0.0005387486364789447   0.9977302669443312     0.01473159666372061
{'model_run_date': '2023-05-09-19-36-30', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.0005387486364789447, 'model_gain': 0.9841884531766592, 'model_perf': 1.4197122262490852e-13, 'buy_and_hold_gain': 1.0012261341741109, 'buy_and_hold_perf': 9.723043849064654, 'model_score': 1.4601520349881584e-14, 'model_gain_score': 0.9829831839023002, 'predict_date': '2023-05-08', 'predict_macd_accum': -0.0021482666263245593, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.7769011855125427, 'MACD_gain': 0.9977302669443312, 'MACD_perf': 0.01473159666372061}

before retrain
MACD Perf:          2023-05-09 10:18:55.027000-04:00 - 2023-05-09 14:50:38.387000-04:00   0.0005169761542364283   0.9914048055256153     5.6008367790413826e-08
{'model_run_date': '2023-05-09-20-30-44', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005169761542364283, 'model_gain': 0.9975575455147213, 'model_perf': 0.008823996898452062, 'buy_and_hold_gain': 1.0011825528880438, 'buy_and_hold_perf': 9.836405993725203, 'model_score': 0.0008970753041386282, 'model_gain_score': 0.9963792743262798, 'predict_date': '2023-05-09', 'predict_macd_accum': -0.42582239796732463, 'predict_macd_len': 27, 'predict_action': 0.4176784157752991, 'predict_vol': 0.0, 'MACD_gain': 0.9914048055256153, 'MACD_perf': 5.6008367790413826e-08}
after retrain
MACD Perf:          2023-05-09 10:18:55.027000-04:00 - 2023-05-09 14:50:38.387000-04:00   0.0005169761542364283   0.9914048055256153     5.6008367790413826e-08
{'model_run_date': '2023-05-09-20-32-42', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005169761542364283, 'model_gain': 1.0072404064430978, 'model_perf': 1149505.0079854329, 'buy_and_hold_gain': 1.0011825528880438, 'buy_and_hold_perf': 9.836405993725203, 'model_score': 116862.29794893786, 'model_gain_score': 1.0060506982843231, 'predict_date': '2023-05-09', 'predict_macd_accum': -0.42582239796732463, 'predict_macd_len': 27, 'predict_action': 0.0, 'predict_vol': 0.6156662106513977, 'MACD_gain': 0.9914048055256153, 'MACD_perf': 5.6008367790413826e-08}

10sec data 10-15 6/13/9
init train
MACD Perf:          2023-05-08 10:09:06.780000-04:00 - 2023-05-08 14:58:23.386000-04:00   0.0005503743658041604   1.001474451047177     14.541745323131556
{'model_run_date': '2023-05-09-20-48-08', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.0005503743658041604, 'model_gain': 1.0016250371606523, 'model_perf': 19.10990593969092, 'buy_and_hold_gain': 0.9990392173988993, 'buy_and_hold_perf': 0.17437826923642383, 'model_score': 109.58880383071995, 'model_gain_score': 1.0025883065616636, 'predict_date': '2023-05-08', 'predict_macd_accum': -0.0011319302967813596, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.48814648389816284, 'MACD_gain': 1.001474451047177, 'MACD_perf': 14.541745323131556}

before retrain
MACD Perf:          2023-05-09 10:12:51.388000-04:00 - 2023-05-09 14:58:55.771000-04:00   0.0005442790144596652   0.9899048482016729     8.014548595057431e-09
{'model_run_date': '2023-05-09-20-55-22', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005442790144596652, 'model_gain': 0.9976815737656244, 'model_perf': 0.014057859363840578, 'buy_and_hold_gain': 0.9997263045159756, 'buy_and_hold_perf': 0.6047575694839602, 'model_score': 0.02324544589964563, 'model_gain_score': 0.9979547094628654, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.015786891695750167, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0813722014427185, 'MACD_gain': 0.9899048482016729, 'MACD_perf': 8.014548595057431e-09}
after retrain
MACD Perf:          2023-05-09 10:12:51.388000-04:00 - 2023-05-09 14:58:55.771000-04:00   0.0005442790144596652   0.9899048482016729     8.014548595057431e-09
{'model_run_date': '2023-05-09-20-56-47', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005442790144596652, 'model_gain': 1.001586502980604, 'model_perf': 18.403870023806924, 'buy_and_hold_gain': 0.9997263045159756, 'buy_and_hold_perf': 0.6047575694839602, 'model_score': 30.431814254943433, 'model_gain_score': 1.0018607077319317, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.015786891695750167, 'predict_macd_len': 4, 'predict_action': 0.37394410371780396, 'predict_vol': 1.0, 'MACD_gain': 0.9899048482016729, 'MACD_perf': 8.014548595057431e-09}

10sec data 10-15 3/7/19
init train
MACD Perf:          2023-05-08 10:09:06.780000-04:00 - 2023-05-08 14:58:13.725000-04:00   0.0005500680175038052   1.0078286758559045     1435143.59092102
{'model_run_date': '2023-05-09-21-00-38', 'start_date': '2023-05-08', 'end_date': '2023-05-08', 'duration': 0.0005500680175038052, 'model_gain': 0.994920344220422, 'model_perf': 9.533345405914365e-05, 'buy_and_hold_gain': 0.999213905144554, 'buy_and_hold_perf': 0.23939302195293385, 'model_score': 0.0003982298785546339, 'model_gain_score': 0.9957030612744416, 'predict_date': '2023-05-08', 'predict_macd_accum': -0.00671302459989963, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.0078286758559045, 'MACD_perf': 1435143.59092102}

before retrain
MACD Perf:          2023-05-09 10:07:42.109000-04:00 - 2023-05-09 14:58:55.771000-04:00   0.0005540861872146118   0.9824897967537969     1.4251706309155877e-14
{'model_run_date': '2023-05-09-21-06-13', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005540861872146118, 'model_gain': 0.9980295676327311, 'model_perf': 0.02844758239242681, 'buy_and_hold_gain': 0.9962881707678624, 'buy_and_hold_perf': 0.0012168688615059543, 'model_score': 23.377689488431052, 'model_gain_score': 1.0017478847144463, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.029503824072990383, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9824897967537969, 'MACD_perf': 1.4251706309155877e-14}
after retrain
MACD Perf:          2023-05-09 10:07:42.109000-04:00 - 2023-05-09 14:58:55.771000-04:00   0.0005540861872146118   0.9824897967537969     1.4251706309155877e-14
{'model_run_date': '2023-05-09-21-09-18', 'start_date': '2023-05-09', 'end_date': '2023-05-09', 'duration': 0.0005540861872146118, 'model_gain': 0.9991309159839452, 'model_perf': 0.2082155016720622, 'buy_and_hold_gain': 0.9962881707678624, 'buy_and_hold_perf': 0.0012168688615059543, 'model_score': 171.10759282177867, 'model_gain_score': 1.0028533363132195, 'predict_date': '2023-05-09', 'predict_macd_accum': 0.029503824072990383, 'predict_macd_len': 4, 'predict_action': 0.9043782353401184, 'predict_vol': 0.0, 'MACD_gain': 0.9824897967537969, 'MACD_perf': 1.4251706309155877e-14}

training - 10sec data 8-11 12/26/9
before retrain
MACD Perf:          2023-05-10 09:01:53.661000-04:00 - 2023-05-10 10:54:17.209000-04:00   0.0002138365043125317   0.994680384096493     1.469626174856508e-11
{'model_run_date': '2023-05-10-17-55-32', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0002138365043125317, 'model_gain': 0.9902121370584528, 'model_perf': 1.0550346438236361e-20, 'buy_and_hold_gain': 0.9836918806384456, 'buy_and_hold_perf': 4.03397617423494e-34, 'model_score': 26153715298621.656, 'model_gain_score': 1.0066283523818205, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.5574657140765584, 'predict_macd_len': 17, 'predict_action': 0.21116776764392853, 'predict_vol': 1.0, 'MACD_gain': 0.994680384096493, 'MACD_perf': 1.469626174856508e-11}
after retrain
MACD Perf:          2023-05-10 09:01:53.661000-04:00 - 2023-05-10 10:54:17.209000-04:00   0.0002138365043125317   0.994680384096493     1.469626174856508e-11
{'model_run_date': '2023-05-10-17-58-07', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0002138365043125317, 'model_gain': 0.9992335776678672, 'model_perf': 0.02772210299176298, 'buy_and_hold_gain': 0.9836918806384456, 'buy_and_hold_perf': 4.03397617423494e-34, 'model_score': 6.872153377807342e+31, 'model_gain_score': 1.0157993547932251, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.5574657140765584, 'predict_macd_len': 17, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.994680384096493, 'MACD_perf': 1.469626174856508e-11}

training - 10sec data 8-11 6/13/9
before retrain
MACD Perf:          2023-05-10 08:54:34.513000-04:00 - 2023-05-10 10:58:06.264000-04:00   0.00023502508244545916   1.0034519477885406     2332099.9546219776
{'model_run_date': '2023-05-10-18-05-44', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.00023502508244545916, 'model_gain': 0.9770173186800073, 'model_perf': 1.0851466030248536e-43, 'buy_and_hold_gain': 0.9788210410365471, 'buy_and_hold_perf': 2.778315685204409e-40, 'model_score': 0.00039057714312440206, 'model_gain_score': 0.9981572501193582, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.00319276113690449, 'predict_macd_len': 2, 'predict_action': 1.5000488758087158, 'predict_vol': 0.0, 'MACD_gain': 1.0034519477885406, 'MACD_perf': 2332099.9546219776}
after retrain
MACD Perf:          2023-05-10 08:54:34.513000-04:00 - 2023-05-10 10:58:06.264000-04:00   0.00023502508244545916   1.0034519477885406     2332099.9546219776
{'model_run_date': '2023-05-10-18-07-44', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.00023502508244545916, 'model_gain': 1.001861820255231, 'model_perf': 2736.482247119929, 'buy_and_hold_gain': 0.9788210410365471, 'buy_and_hold_perf': 2.778315685204409e-40, 'model_score': 9.849428780511665e+42, 'model_gain_score': 1.0235393174571363, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.00319276113690449, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.0034519477885406, 'MACD_perf': 2332099.9546219776}

training - 10sec data 8-11 3/7/19
before retrain
MACD Perf:          2023-05-10 08:50:25.883000-04:00 - 2023-05-10 10:58:06.264000-04:00   0.00024290908802638254   0.9996287775526177     0.21685640570461
{'model_run_date': '2023-05-10-18-12-22', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.00024290908802638254, 'model_gain': 0.9797818251180049, 'model_perf': 3.031968984889306e-37, 'buy_and_hold_gain': 0.977186092179739, 'buy_and_hold_perf': 5.4801260241851544e-42, 'model_score': 55326.628831316564, 'model_gain_score': 1.0026563343042223, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.04159160716778575, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.1093452125787735, 'MACD_gain': 0.9996287775526177, 'MACD_perf': 0.21685640570461}
after retrain
MACD Perf:          2023-05-10 08:50:25.883000-04:00 - 2023-05-10 10:58:06.264000-04:00   0.00024290908802638254   0.9996287775526177     0.21685640570461
{'model_run_date': '2023-05-10-18-14-08', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.00024290908802638254, 'model_gain': 0.9900117399869751, 'model_perf': 1.1280204067490175e-18, 'buy_and_hold_gain': 0.977186092179739, 'buy_and_hold_perf': 5.4801260241851544e-42, 'model_score': 2.05838406228394e+23, 'model_gain_score': 1.0131250822232098, 'predict_date': '2023-05-10', 'predict_macd_accum': -0.04159160716778575, 'predict_macd_len': 2, 'predict_action': 1.2198697328567505, 'predict_vol': 0.0, 'MACD_gain': 0.9996287775526177, 'MACD_perf': 0.21685640570461}

10sec data 10-15 12/26/9
before retrain
MACD Perf:          2023-05-10 10:23:25.940000-04:00 - 2023-05-10 14:55:28.381000-04:00   0.0005175812087772705   0.9878491861985506     5.520638031677221e-11
{'model_run_date': '2023-05-10-18-17-26', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005175812087772705, 'model_gain': 0.9746411587876223, 'model_perf': 2.801165542897083e-22, 'buy_and_hold_gain': 0.9722895739521995, 'buy_and_hold_perf': 2.6325350193377656e-24, 'model_score': 106.40563268182993, 'model_gain_score': 1.002418605422111, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.3475410001950977, 'predict_macd_len': 14, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 0.9878491861985506, 'MACD_perf': 5.520638031677221e-11}
after retrain
MACD Perf:          2023-05-10 10:23:25.940000-04:00 - 2023-05-10 14:55:28.381000-04:00   0.0005175812087772705   0.9878491861985506     5.520638031677221e-11
{'model_run_date': '2023-05-10-18-20-10', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005175812087772705, 'model_gain': 0.9832518218344191, 'model_perf': 6.727391713379602e-15, 'buy_and_hold_gain': 0.9722895739521995, 'buy_and_hold_perf': 2.6325350193377656e-24, 'model_score': 2555480426.266819, 'model_gain_score': 1.0112746738995255, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.3475410001950977, 'predict_macd_len': 14, 'predict_action': 0.0, 'predict_vol': 0.8041440844535828, 'MACD_gain': 0.9878491861985506, 'MACD_perf': 5.520638031677221e-11}

10sec data 10-15 6/13/9
before retrain
MACD Perf:          2023-05-10 10:10:38.596000-04:00 - 2023-05-10 14:55:28.381000-04:00   0.0005419135273972603   0.9916133645450745     1.7804544352970618e-07
{'model_run_date': '2023-05-10-18-23-23', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005419135273972603, 'model_gain': 0.9678424069252504, 'model_perf': 6.384589432753297e-27, 'buy_and_hold_gain': 0.9671528655105088, 'buy_and_hold_perf': 1.7138143483227636e-27, 'model_score': 3.7253681759646953, 'model_gain_score': 1.0007129601114066, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.28736319231827, 'predict_macd_len': 11, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9916133645450745, 'MACD_perf': 1.7804544352970618e-07}
after retrain
MACD Perf:          2023-05-10 10:10:38.596000-04:00 - 2023-05-10 14:55:28.381000-04:00   0.0005419135273972603   0.9916133645450745     1.7804544352970618e-07
{'model_run_date': '2023-05-10-18-25-09', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005419135273972603, 'model_gain': 0.9647228008399463, 'model_perf': 1.6512471808420568e-29, 'buy_and_hold_gain': 0.9671528655105088, 'buy_and_hold_perf': 1.7138143483227636e-27, 'model_score': 0.00963492447392602, 'model_gain_score': 0.9974874037422411, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.28736319231827, 'predict_macd_len': 11, 'predict_action': 0.8041156530380249, 'predict_vol': 0.0, 'MACD_gain': 0.9916133645450745, 'MACD_perf': 1.7804544352970618e-07}

10sec data 10-15 3/7/19
before retrain
MACD Perf:          2023-05-10 10:08:33.587000-04:00 - 2023-05-10 14:57:01.237000-04:00   0.0005488219812278032   0.9954076791589935     0.0002278395780483348
{'model_run_date': '2023-05-10-18-28-06', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005488219812278032, 'model_gain': 0.9852846098523788, 'model_perf': 1.857257552303979e-12, 'buy_and_hold_gain': 0.9693889271766597, 'buy_and_hold_perf': 2.5021616481032043e-25, 'model_score': 7422612179000.893, 'model_gain_score': 1.0163976317761492, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.0041699390855706245, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9954076791589935, 'MACD_perf': 0.0002278395780483348}
after retrain
MACD Perf:          2023-05-10 10:08:33.587000-04:00 - 2023-05-10 14:57:01.237000-04:00   0.0005488219812278032   0.9954076791589935     0.0002278395780483348
{'model_run_date': '2023-05-10-18-29-56', 'start_date': '2023-05-10', 'end_date': '2023-05-10', 'duration': 0.0005488219812278032, 'model_gain': 0.9711732777911345, 'model_perf': 7.137703357529937e-24, 'buy_and_hold_gain': 0.9693889271766597, 'buy_and_hold_perf': 2.5021616481032043e-25, 'model_score': 28.526148032605185, 'model_gain_score': 1.0018406963030533, 'predict_date': '2023-05-10', 'predict_macd_accum': 0.0041699390855706245, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9954076791589935, 'MACD_perf': 0.0002278395780483348}

training - 10sec data 8-11 12/26/9
before retrain
MACD Perf:          2023-05-11 08:11:03.024000-04:00 - 2023-05-11 10:58:40.369000-04:00   0.00031891631785895485   0.9883489037375315     1.0979780185492677e-16
{'model_run_date': '2023-05-11-18-17-29', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.00031891631785895485, 'model_gain': 0.9991567799501391, 'model_perf': 0.07099598116809491, 'buy_and_hold_gain': 0.9989943803608399, 'buy_and_hold_perf': 0.04264580434922888, 'model_score': 1.6647823215316764, 'model_gain_score': 1.0001625630659108, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.0008232218758121163, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 0.9883489037375315, 'MACD_perf': 1.0979780185492677e-16}
after retrain
MACD Perf:          2023-05-11 08:11:03.024000-04:00 - 2023-05-11 10:58:40.369000-04:00   0.00031891631785895485   0.9883489037375315     1.0979780185492677e-16
{'model_run_date': '2023-05-11-18-19-29', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.00031891631785895485, 'model_gain': 0.9994132038210737, 'model_perf': 0.15873657977888878, 'buy_and_hold_gain': 0.9989943803608399, 'buy_and_hold_perf': 0.04264580434922888, 'model_score': 3.7222086017884912, 'model_gain_score': 1.000419245061301, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.0008232218758121163, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9883489037375315, 'MACD_perf': 1.0979780185492677e-16}

training - 10sec data 8-11 6/13/9
before retrain
MACD Perf:          2023-05-11 08:10:17.680000-04:00 - 2023-05-11 10:58:30.371000-04:00   0.000320037132166413   0.9801820593927423     6.866623708859422e-28
{'model_run_date': '2023-05-11-18-23-55', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.000320037132166413, 'model_gain': 0.9962936110385283, 'model_perf': 9.141949482452452e-06, 'buy_and_hold_gain': 0.9987077008608429, 'buy_and_hold_perf': 0.01758731047982336, 'model_score': 0.0005198037239940891, 'model_gain_score': 0.9975827864146499, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.002666972526774232, 'predict_macd_len': 3, 'predict_action': 0.02610548585653305, 'predict_vol': 0.0, 'MACD_gain': 0.9801820593927423, 'MACD_perf': 6.866623708859422e-28}
after retrain
MACD Perf:          2023-05-11 08:10:17.680000-04:00 - 2023-05-11 10:58:30.371000-04:00   0.000320037132166413   0.9801820593927423     6.866623708859422e-28
{'model_run_date': '2023-05-11-18-26-09', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.000320037132166413, 'model_gain': 1.0057903173701916, 'model_perf': 68371224.85187677, 'buy_and_hold_gain': 0.9987077008608429, 'buy_and_hold_perf': 0.01758731047982336, 'model_score': 3887531577.40145, 'model_gain_score': 1.0070917812121043, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.002666972526774232, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9801820593927423, 'MACD_perf': 6.866623708859422e-28}

training - 10sec data 8-11 3/7/19
before retrain
MACD Perf:          2023-05-11 08:02:19.189000-04:00 - 2023-05-11 10:58:30.371000-04:00   0.0003352099822425165   0.9848351852283738     1.5926843110170622e-20
{'model_run_date': '2023-05-11-18-29-31', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0003352099822425165, 'model_gain': 1.0124385015773585, 'model_perf': 1.037024796894592e+16, 'buy_and_hold_gain': 0.9966946051233622, 'buy_and_hold_perf': 5.134195573628437e-05, 'model_score': 2.0198389056724346e+20, 'model_gain_score': 1.0157961088311978, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.006280659795689848, 'predict_macd_len': 2, 'predict_action': 0.5652894973754883, 'predict_vol': 0.32727932929992676, 'MACD_gain': 0.9848351852283738, 'MACD_perf': 1.5926843110170622e-20}
after retrain
MACD Perf:          2023-05-11 08:02:19.189000-04:00 - 2023-05-11 10:58:30.371000-04:00   0.0003352099822425165   0.9848351852283738     1.5926843110170622e-20
{'model_run_date': '2023-05-11-18-31-59', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0003352099822425165, 'model_gain': 1.011625917385996, 'model_perf': 945214283000450.1, 'buy_and_hold_gain': 0.9966946051233622, 'buy_and_hold_perf': 5.134195573628437e-05, 'model_score': 1.8410172916970682e+19, 'model_gain_score': 1.0149808298207712, 'predict_date': '2023-05-11', 'predict_macd_accum': 0.006280659795689848, 'predict_macd_len': 2, 'predict_action': 0.4692407548427582, 'predict_vol': 0.0, 'MACD_gain': 0.9848351852283738, 'MACD_perf': 1.5926843110170622e-20}

10sec data 10-15 12/26/9
before retrain
MACD Perf:          2023-05-11 10:16:43.634000-04:00 - 2023-05-11 14:59:06.096000-04:00   0.0005372419457128361   1.0024444285186522     94.10455482181963
{'model_run_date': '2023-05-11-18-36-47', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005372419457128361, 'model_gain': 1.0032139485003582, 'model_perf': 392.57135327497423, 'buy_and_hold_gain': 1.0025373222399245, 'buy_and_hold_perf': 111.81943330037186, 'model_score': 3.5107614274921275, 'model_gain_score': 1.0006749137866726, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.008948982540628021, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.01045122742652893, 'MACD_gain': 1.0024444285186522, 'MACD_perf': 94.10455482181963}
after retrain
MACD Perf:          2023-05-11 10:16:43.634000-04:00 - 2023-05-11 14:59:06.096000-04:00   0.0005372419457128361   1.0024444285186522     94.10455482181963
{'model_run_date': '2023-05-11-18-38-28', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005372419457128361, 'model_gain': 1.0152650218633115, 'model_perf': 1764690443757.1213, 'buy_and_hold_gain': 1.0025373222399245, 'buy_and_hold_perf': 111.81943330037186, 'model_score': 15781607826.76094, 'model_gain_score': 1.012695487081668, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.008948982540628021, 'predict_macd_len': 4, 'predict_action': 0.44634342193603516, 'predict_vol': 0.6112312078475952, 'MACD_gain': 1.0024444285186522, 'MACD_perf': 94.10455482181963}

10sec data 10-15 6/13/9
before retrain
MACD Perf:          2023-05-11 10:09:21.809000-04:00 - 2023-05-11 14:58:04.909000-04:00   0.0005493118975139523   0.9906702061076641     3.882357625655601e-08
{'model_run_date': '2023-05-11-18-41-15', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005493118975139523, 'model_gain': 1.0115699203953206, 'model_perf': 1244072125.7128298, 'buy_and_hold_gain': 1.0076516993890503, 'buy_and_hold_perf': 1062978.77682672, 'model_score': 1170.3640306222505, 'model_gain_score': 1.0038884676209507, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.05615336772790947, 'predict_macd_len': 10, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9906702061076641, 'MACD_perf': 3.882357625655601e-08}
after retrain
MACD Perf:          2023-05-11 10:09:21.809000-04:00 - 2023-05-11 14:58:04.909000-04:00   0.0005493118975139523   0.9906702061076641     3.882357625655601e-08
{'model_run_date': '2023-05-11-18-44-25', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005493118975139523, 'model_gain': 0.9999415457834353, 'model_perf': 0.8990499920812446, 'buy_and_hold_gain': 1.0076516993890503, 'buy_and_hold_perf': 1062978.77682672, 'model_score': 8.457835769451134e-07, 'model_gain_score': 0.9923483941819482, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.05615336772790947, 'predict_macd_len': 10, 'predict_action': 0.8933435082435608, 'predict_vol': 0.0, 'MACD_gain': 0.9906702061076641, 'MACD_perf': 3.882357625655601e-08}

10sec data 10-15 3/7/19
before retrain
MACD Perf:          2023-05-11 10:08:40.599000-04:00 - 2023-05-11 14:57:53.759000-04:00   0.0005502650938609843   0.9933533834953855     5.4534825217359e-06
{'model_run_date': '2023-05-11-18-46-56', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005502650938609843, 'model_gain': 1.0053852690889242, 'model_perf': 17333.971821339048, 'buy_and_hold_gain': 1.0076790796963948, 'buy_and_hold_perf': 1090261.2052388098, 'model_score': 0.015898916459695756, 'model_gain_score': 0.9977236695157334, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.08857974345505043, 'predict_macd_len': 11, 'predict_action': 0.38277938961982727, 'predict_vol': 0.1408877670764923, 'MACD_gain': 0.9933533834953855, 'MACD_perf': 5.4534825217359e-06}
after retrain
MACD Perf:          2023-05-11 10:08:40.599000-04:00 - 2023-05-11 14:57:53.759000-04:00   0.0005502650938609843   0.9933533834953855     5.4534825217359e-06
{'model_run_date': '2023-05-11-18-48-29', 'start_date': '2023-05-11', 'end_date': '2023-05-11', 'duration': 0.0005502650938609843, 'model_gain': 1.0089039691423987, 'model_perf': 9915619.532064946, 'buy_and_hold_gain': 1.0076790796963948, 'buy_and_hold_perf': 1090261.2052388098, 'model_score': 9.094719214459289, 'model_gain_score': 1.001215555101504, 'predict_date': '2023-05-11', 'predict_macd_accum': -0.08857974345505043, 'predict_macd_len': 11, 'predict_action': 0.2995300889015198, 'predict_vol': 0.04961057007312775, 'MACD_gain': 0.9933533834953855, 'MACD_perf': 5.4534825217359e-06}

training - 10sec data 8-11 12/26/9
before retrain
2023-05-12 08:13:27.271000-04:00 2023-05-12 10:57:01.690000-04:00 0.9856410696446105 0.988427853876071 0.9791879904469463
after retrain
2023-05-12 08:13:27.271000-04:00 2023-05-12 10:57:01.690000-04:00 0.9947405040394461 0.988427853876071 0.9791879904469463

training - 10sec data 8-11 6/13/9
before retrain
2023-05-12 08:05:20.693000-04:00 2023-05-12 10:56:50.808000-04:00 0.9734266046586657 0.9996865265013826 0.9822502065585914
after retrain
2023-05-12 08:05:20.693000-04:00 2023-05-12 10:56:50.808000-04:00 0.9851949215925302 0.9996865265013826 0.9822502065585914

training - 10sec data 8-11 3/7/19
before retrain
2023-05-12 08:04:40.517000-04:00 2023-05-12 10:56:50.808000-04:00 0.9800007867623258 0.9958373633728651 0.9827822120866591
after retrain
2023-05-12 08:04:40.517000-04:00 2023-05-12 10:56:50.808000-04:00 1.0100991261140064 0.9958373633728651 0.9827822120866591

10sec data 10-15 12/26/9
before retrain
2023-05-12 10:14:37.960000-04:00 2023-05-12 14:54:46.016000-04:00 0.9815212340492816 0.9819391729076802 0.9626082468314503
after retrain
2023-05-12 10:14:37.960000-04:00 2023-05-12 14:54:46.016000-04:00 0.9985872969089258 0.9819391729076802 0.9626082468314503

10sec data 10-15 6/13/9
before retrain
2023-05-12 10:11:10.988000-04:00 2023-05-12 14:59:03.962000-04:00 0.9698445542960292 0.9760509854116478 0.9622002982677527
after retrain
2023-05-12 10:11:10.988000-04:00 2023-05-12 14:59:03.962000-04:00 0.966350639705215 0.9760509854116478 0.9622002982677527

10sec data 10-15 3/7/19
before retrain
2023-05-12 10:10:50.693000-04:00 2023-05-12 14:58:33.870000-04:00 0.9695831879695146 0.9723038392892835 0.9625315584117512
after retrain
2023-05-12 10:10:50.693000-04:00 2023-05-12 14:58:33.870000-04:00 0.9657440814854751 0.9723038392892835 0.9625315584117512

2023_05_08
2023-05-08 09:25:26.648000-04:00 2023-05-08 10:56:13.938000-04:00 0.9990659229462319 0.9848782947508387 0.9814193548387098
2023-05-08 10:13:11.277000-04:00 2023-05-08 14:56:21.254000-04:00 1.0036141761474575 0.9977302669443312 1.0012261341741109
2023_05_09
2023-05-09 09:39:27.801000-04:00 2023-05-09 10:57:35.689000-04:00 0.9970692375875277 0.9894451482668384 0.9955081667542774
2023-05-09 10:18:55.027000-04:00 2023-05-09 14:50:38.387000-04:00 1.0072103838833104 0.9914048055256153 1.0011825528880438
2023_05_10
2023-05-10 09:01:53.661000-04:00 2023-05-10 10:54:17.209000-04:00 0.9977192232300227 0.994680384096493 0.9836918806384456
2023-05-10 10:23:25.940000-04:00 2023-05-10 14:55:28.381000-04:00 0.9934658688231025 0.9878491861985506 0.9722895739521995
2023_05_11
2023-05-11 08:11:03.024000-04:00 2023-05-11 10:58:40.369000-04:00 0.9953803073380767 0.9883489037375315 0.9989943803608399
2023-05-11 10:16:43.634000-04:00 2023-05-11 14:59:06.096000-04:00 1.0107069256270729 1.0024444285186522 1.0025373222399245
2023_05_12
2023-05-12 08:13:27.271000-04:00 2023-05-12 10:57:01.690000-04:00 1.0024047445005773 0.988427853876071 0.9791879904469463
2023-05-12 10:14:37.960000-04:00 2023-05-12 14:54:46.016000-04:00 1.0101449176738566 0.9819391729076802 0.9626082468314503
1.0167374457586211 0.884257723961703 0.9107785810766711

2023_05_08
2023-05-08 09:25:26.648000-04:00 2023-05-08 10:56:13.938000-04:00 1.012272358267146 0.9848782947508387 0.9814193548387098
2023-05-08 10:13:11.277000-04:00 2023-05-08 14:56:21.254000-04:00 1.0366168001085636 0.9977302669443312 1.0012261341741109
2023_05_09
2023-05-09 09:39:27.801000-04:00 2023-05-09 10:57:35.689000-04:00 1.0076780791160254 0.9894451482668384 0.9955081667542774
2023-05-09 10:18:55.027000-04:00 2023-05-09 14:50:38.387000-04:00 1.0207533156675037 0.9914048055256153 1.0011825528880438
2023_05_10
2023-05-10 09:01:53.661000-04:00 2023-05-10 10:54:17.209000-04:00 1.0023761287034634 0.994680384096493 0.9836918806384456
2023-05-10 10:23:25.940000-04:00 2023-05-10 14:55:28.381000-04:00 1.004468213392571 0.9878491861985506 0.9722895739521995
2023_05_11
2023-05-11 08:11:03.024000-04:00 2023-05-11 10:58:40.369000-04:00 1.0068344222930292 0.9883489037375315 0.9989943803608399
2023-05-11 10:16:43.634000-04:00 2023-05-11 14:59:06.096000-04:00 1.0150688900509421 1.0024444285186522 1.0025373222399245
2023_05_12
2023-05-12 08:13:27.271000-04:00 2023-05-12 10:57:01.690000-04:00 1.0035093623550444 0.988427853876071 0.9791879904469463
2023-05-12 10:14:37.960000-04:00 2023-05-12 14:54:46.016000-04:00 1.0169316909178638 0.9819391729076802 0.9626082468314503
1.1334227557779417 0.884257723961703 0.9107785810766711

2023_05_08
2023-05-08 09:25:26.648000-04:00 2023-05-08 10:56:13.938000-04:00 1.003419764082337 0.9848782947508387 0.9814193548387098
2023-05-08 10:13:11.277000-04:00 2023-05-08 14:56:21.254000-04:00 1.0205797585273368 0.9977302669443312 1.0012261341741109
2023_05_09
2023-05-09 09:39:27.801000-04:00 2023-05-09 10:57:35.689000-04:00 1.0014048457138574 0.9894451482668384 0.9955081667542774
2023-05-09 10:18:55.027000-04:00 2023-05-09 14:50:38.387000-04:00 1.0052366280822858 0.9914048055256153 1.0011825528880438
2023_05_10
2023-05-10 09:01:53.661000-04:00 2023-05-10 10:54:17.209000-04:00 1.0040641674016024 0.994680384096493 0.9836918806384456
2023-05-10 10:23:25.940000-04:00 2023-05-10 14:55:28.381000-04:00 1.0045268109397596 0.9878491861985506 0.9722895739521995
2023_05_11
2023-05-11 08:11:03.024000-04:00 2023-05-11 10:58:40.369000-04:00 1.0004383084984672 0.9883489037375315 0.9989943803608399
2023-05-11 10:16:43.634000-04:00 2023-05-11 14:59:06.096000-04:00 1.010394894141983 1.0024444285186522 1.0025373222399245
2023_05_12
2023-05-12 08:13:27.271000-04:00 2023-05-12 10:57:01.690000-04:00 1.0073335944218198 0.988427853876071 0.9791879904469463
2023-05-12 10:14:37.960000-04:00 2023-05-12 14:54:46.016000-04:00 1.0267622478430523 0.9819391729076802 0.9626082468314503
1.0870643715339623 0.884257723961703 0.9107785810766711

performance is much worse with retrain every day, test next day.

2023_05_15
10sec data 8-11 12/26/9 before retrain
2023-05-15 08:13:18.920000-04:00 2023-05-15 10:54:08.565000-04:00 0.9941589749226193 1.0011080563853298 0.9895816721213925
10sec data 8-11 12/26/9 after retrain
2023-05-15 08:13:18.920000-04:00 2023-05-15 10:54:08.565000-04:00 0.998635645585679 1.0011080563853298 0.9895816721213925
10sec data 8-11 6/13/9 before retrain
2023-05-15 08:13:18.920000-04:00 2023-05-15 10:52:13.313000-04:00 1.0010776111599382 0.9906933706963873 0.9890508777149658
10sec data 8-11 6/13/9 after retrain
2023-05-15 08:13:18.920000-04:00 2023-05-15 10:52:13.313000-04:00 1.0283589009381908 0.9906933706963873 0.9890508777149658
10sec data 8-11 3/7/19 before retrain
2023-05-15 08:11:40.475000-04:00 2023-05-15 10:54:08.565000-04:00 0.9865872911929988 0.9834870730739033 0.9898761904761906
10sec data 8-11 3/7/19 after retrain
2023-05-15 08:11:40.475000-04:00 2023-05-15 10:54:08.565000-04:00 1.0304657887562472 0.9834870730739033 0.9898761904761906
10sec data 10-15 12/26/9 before retrain
2023-05-15 10:17:38.549000-04:00 2023-05-15 14:54:04.879000-04:00 0.9950122106960471 1.0010720711872731 1.0021066570362347
10sec data 10-15 12/26/9 after retrain
2023-05-15 10:17:38.549000-04:00 2023-05-15 14:54:04.879000-04:00 1.024199771706315 1.0010720711872731 1.0021066570362347
10sec data 10-15 6/13/9 before retrain
2023-05-15 10:13:52.777000-04:00 2023-05-15 14:57:51.006000-04:00 1.0027114882723975 0.9926478275912273 1.0024679467886595
10sec data 10-15 6/13/9 after retrain
2023-05-15 10:13:52.777000-04:00 2023-05-15 14:57:51.006000-04:00 1.0304830077055345 0.9926478275912273 1.0024679467886595
10sec data 10-15 3/7/19 before retrain
2023-05-15 10:08:26.552000-04:00 2023-05-15 14:57:51.006000-04:00 1.0158505171533685 0.9959678424251931 1.0048935310054365
10sec data 10-15 3/7/19 after retrain
2023-05-15 10:08:26.552000-04:00 2023-05-15 14:57:51.006000-04:00 1.0303869108578405 0.9959678424251931 1.0048935310054365

2023_05_17
10sec data 8-11 12/26/9 before retrain
2023-05-17 08:14:54.246000-04:00 2023-05-17 10:52:01.016000-04:00 1.0202551703648468 1.0023239560556279 1.0281748056725806
10sec data 8-11 12/26/9 after retrain
2023-05-17 08:14:54.246000-04:00 2023-05-17 10:52:01.016000-04:00 1.032938282924282 1.0023239560556279 1.0281748056725806
10sec data 8-11 6/13/9 before retrain
2023-05-17 08:03:35.345000-04:00 2023-05-17 10:58:12.529000-04:00 1.024110113660706 1.007282480063116 1.0313446126447017
10sec data 8-11 6/13/9 after retrain
2023-05-17 08:03:35.345000-04:00 2023-05-17 10:58:12.529000-04:00 1.0358797333643803 1.007282480063116 1.0313446126447017
10sec data 8-11 3/7/19 before retrain
2023-05-17 08:03:35.345000-04:00 2023-05-17 10:57:50.753000-04:00 1.0275527641414106 0.99800731735184 1.0316117542297418
10sec data 8-11 3/7/19 after retrain
2023-05-17 08:03:35.345000-04:00 2023-05-17 10:57:50.753000-04:00 1.0327043186832885 0.99800731735184 1.0316117542297418
10sec data 10-15 12/26/9 before retrain
2023-05-17 10:18:37.934000-04:00 2023-05-17 14:56:24.924000-04:00 0.9968560823139461 1.0056937153792074 1.009541540609728
10sec data 10-15 12/26/9 after retrain
2023-05-17 10:18:37.934000-04:00 2023-05-17 14:56:24.924000-04:00 1.0026891254358004 1.0056937153792074 1.009541540609728
10sec data 10-15 6/13/9 before retrain
2023-05-17 10:18:06.626000-04:00 2023-05-17 14:58:10.344000-04:00 1.0116140920866845 1.0084527886382133 1.0114781798053953
10sec data 10-15 6/13/9 after retrain
2023-05-17 10:18:06.626000-04:00 2023-05-17 14:58:10.344000-04:00 1.015329439180395 1.0084527886382133 1.0114781798053953
10sec data 10-15 3/7/19 before retrain
2023-05-17 10:06:55.669000-04:00 2023-05-17 14:58:10.344000-04:00 1.0077967652556947 1.0078979736326101 1.0161554671037227
10sec data 10-15 3/7/19 after retrain
2023-05-17 10:06:55.669000-04:00 2023-05-17 14:58:10.344000-04:00 1.0116571175519937 1.0078979736326101 1.0161554671037227

2023_05_18
10sec data 8-11 12/26/9 before retrain
2023-05-18 08:28:37.399000-04:00 2023-05-18 10:58:38.082000-04:00 0.9855231949968578 0.9840252275131645 0.9920161841805335
10sec data 8-11 12/26/9 after retrain
2023-05-18 08:28:37.399000-04:00 2023-05-18 10:58:38.082000-04:00 0.9905852472148731 0.9840252275131645 0.9920161841805335
10sec data 8-11 6/13/9 before retrain
2023-05-18 08:13:42.294000-04:00 2023-05-18 10:58:17.167000-04:00 0.9960302986848146 0.9911468422114061 0.9928697735440077
10sec data 8-11 6/13/9 after retrain
2023-05-18 08:13:42.294000-04:00 2023-05-18 10:58:17.167000-04:00 1.0198968928820766 0.9911468422114061 0.9928697735440077
10sec data 8-11 3/7/19 before retrain
2023-05-18 08:12:06.952000-04:00 2023-05-18 10:58:07.095000-04:00 0.996717439549964 0.997447262593242 0.9928989020390704
10sec data 8-11 3/7/19 after retrain
2023-05-18 08:12:06.952000-04:00 2023-05-18 10:58:07.095000-04:00 0.9957563633439342 0.997447262593242 0.9928989020390704
10sec data 10-15 12/26/9 before retrain
2023-05-18 10:20:41.892000-04:00 2023-05-18 14:52:57.439000-04:00 0.9876416081459206 1.0011252066033647 1.0033567994505495
10sec data 10-15 12/26/9 after retrain
2023-05-18 10:20:41.892000-04:00 2023-05-18 14:52:57.439000-04:00 0.9902152788125255 1.0011252066033647 1.0033567994505495
10sec data 10-15 6/13/9 before retrain
2023-05-18 10:14:45.952000-04:00 2023-05-18 14:58:48.732000-04:00 1.008692009411271 1.0126782329002963 1.009105414746544
10sec data 10-15 6/13/9 after retrain
2023-05-18 10:14:45.952000-04:00 2023-05-18 14:58:48.732000-04:00 1.009512612271858 1.0126782329002963 1.009105414746544
10sec data 10-15 3/7/19 before retrain
2023-05-18 10:12:55.243000-04:00 2023-05-18 14:58:38.186000-04:00 1.0220309622510007 1.010814778831188 1.009161962907499
10sec data 10-15 3/7/19 after retrain
2023-05-18 10:12:55.243000-04:00 2023-05-18 14:58:38.186000-04:00 1.0224932697608264 1.010814778831188 1.009161962907499

2023_05_19
10sec data 8-11 12/26/9 before retrain
2023-05-19 08:18:05.647000-04:00 2023-05-19 10:56:51.673000-04:00 1.0110990137075293 0.9959775924831076 1.0141544532130777
10sec data 8-11 12/26/9 after retrain
2023-05-19 08:18:05.647000-04:00 2023-05-19 10:56:51.673000-04:00 1.0110816626016346 0.9959775924831076 1.0141544532130777
10sec data 8-11 6/13/9 before retrain
2023-05-19 08:06:35.942000-04:00 2023-05-19 10:56:32.429000-04:00 1.0126649274487178 0.9990991323674773 1.014071822582461
10sec data 8-11 6/13/9 after retrain
2023-05-19 08:06:35.942000-04:00 2023-05-19 10:56:32.429000-04:00 1.0230655156706001 0.9990991323674773 1.014071822582461
10sec data 8-11 3/7/19 before retrain
2023-05-19 08:04:20.094000-04:00 2023-05-19 10:58:03.643000-04:00 1.01157871747545 0.9983260997661295 1.0123804164321892
10sec data 8-11 3/7/19 after retrain
2023-05-19 08:04:20.094000-04:00 2023-05-19 10:58:03.643000-04:00 1.0175741147429964 0.9983260997661295 1.0123804164321892
10sec data 10-15 12/26/9 before retrain
2023-05-19 10:13:19.686000-04:00 2023-05-19 14:55:08.805000-04:00 1.0117370333678504 0.9984748626382236 0.9975525745813812
10sec data 10-15 12/26/9 after retrain
2023-05-19 10:13:19.686000-04:00 2023-05-19 14:55:08.805000-04:00 1.0185864283807502 0.9984748626382236 0.9975525745813812
10sec data 10-15 6/13/9 before retrain
2023-05-19 10:07:40.642000-04:00 2023-05-19 14:56:41.484000-04:00 0.995770759294764 0.9994253443480405 1.0012839120241153
10sec data 10-15 6/13/9 after retrain
2023-05-19 10:07:40.642000-04:00 2023-05-19 14:56:41.484000-04:00 1.0080534341829708 0.9994253443480405 1.0012839120241153
10sec data 10-15 3/7/19 before retrain
2023-05-19 10:05:26.803000-04:00 2023-05-19 14:57:21.991000-04:00 1.0037497401832123 1.0024144587202715 1.0029623211091234
10sec data 10-15 3/7/19 after retrain
2023-05-19 10:05:26.803000-04:00 2023-05-19 14:57:21.991000-04:00 1.005466985338463 1.0024144587202715 1.0029623211091234

macd - 6/13/9
2023_05_08
2023-05-08 09:18:21.180000-04:00 2023-05-08 10:56:24.015000-04:00 0.9880122810079793 0.9954235421306844 0.9871098265895955
2023-05-08 10:09:06.780000-04:00 2023-05-08 14:58:23.386000-04:00 0.9946744354650997 1.001474451047177 0.9990392173988993
2023_05_09
2023-05-09 09:38:55.960000-04:00 2023-05-09 10:58:39.036000-04:00 1.0064377159739102 1.0002726314874326 0.9970809808473454
2023-05-09 10:12:51.388000-04:00 2023-05-09 14:58:55.771000-04:00 1.0017662763380857 0.9899048482016729 0.9997263045159756
2023_05_10
2023-05-10 08:54:34.513000-04:00 2023-05-10 10:58:06.264000-04:00 0.9869362052201003 1.0034519477885406 0.9788210410365471
2023-05-10 10:10:38.596000-04:00 2023-05-10 14:55:28.381000-04:00 0.9770701398638851 0.9916133645450745 0.9671528655105088
2023_05_11
2023-05-11 08:10:17.680000-04:00 2023-05-11 10:58:30.371000-04:00 1.0049802834195232 0.9801820593927423 0.9987077008608429
2023-05-11 10:09:21.809000-04:00 2023-05-11 14:58:04.909000-04:00 1.015134166357183 0.9906702061076641 1.0076516993890503
2023_05_12
2023-05-12 08:05:20.693000-04:00 2023-05-12 10:56:50.808000-04:00 0.9818568900944554 0.9996865265013826 0.9822502065585914
2023-05-12 10:11:10.988000-04:00 2023-05-12 14:59:03.962000-04:00 0.975269520898577 0.9760509854116478 0.9622002982677527
2023_05_15
2023-05-15 08:13:18.920000-04:00 2023-05-15 10:52:13.313000-04:00 1.018982389636024 0.9906933706963873 0.9890508777149658
2023-05-15 10:13:52.777000-04:00 2023-05-15 14:57:51.006000-04:00 1.026747858773574 0.9926478275912273 1.0024679467886595
2023_05_16
2023-05-16 08:12:33.018000-04:00 2023-05-16 10:53:15.497000-04:00 1.0122544343265376 1.00676448864859 1.0086336111277654
2023-05-16 10:17:46.549000-04:00 2023-05-16 14:56:53.336000-04:00 1.0145452543211015 1.014835389358234 1.0062225695905729
2023_05_17
2023-05-17 08:03:35.345000-04:00 2023-05-17 10:58:12.529000-04:00 1.0206531771808058 1.007282480063116 1.0313446126447017
2023-05-17 10:18:06.626000-04:00 2023-05-17 14:58:10.344000-04:00 1.0136196263853559 1.0084527886382133 1.0114781798053953
2023_05_18
2023-05-18 08:13:42.294000-04:00 2023-05-18 10:58:17.167000-04:00 1.0100720394899685 0.9911468422114061 0.9928697735440077
2023-05-18 10:14:45.952000-04:00 2023-05-18 14:58:48.732000-04:00 1.011922694209018 1.0126782329002963 1.009105414746544
2023_05_19
2023-05-19 08:06:35.942000-04:00 2023-05-19 10:56:32.429000-04:00 1.0217285634586188 0.9990991323674773 1.014071822582461
2023-05-19 10:07:40.642000-04:00 2023-05-19 14:56:41.484000-04:00 1.0101841440270454 0.9994253443480405 1.0012839120241153
1.0945757663470272 0.9452053263191085 0.951927732653615

2023_05_22
10sec data 8-11 12/26/9 before retrain
2023-05-22 08:18:48.218000-04:00 2023-05-22 10:56:55.063000-04:00 1.0088482079676988 0.9990413868878222 1.0182837718328543
10sec data 8-11 12/26/9 after retrain
2023-05-22 08:18:48.218000-04:00 2023-05-22 10:56:55.063000-04:00 1.0105757155218236 0.9990413868878222 1.0182837718328543
10sec data 8-11 6/13/9 before retrain
2023-05-22 08:17:46.224000-04:00 2023-05-22 10:57:36.232000-04:00 1.0212830784224967 1.0002123378511951 1.0174658007461654
10sec data 8-11 6/13/9 after retrain
2023-05-22 08:17:46.224000-04:00 2023-05-22 10:57:36.232000-04:00 1.0243248328210974 1.0002123378511951 1.0174658007461654
10sec data 8-11 3/7/19 before retrain
2023-05-22 08:10:35.207000-04:00 2023-05-22 10:57:36.232000-04:00 1.0257616948807042 0.9888464707710108 1.018450899031812
10sec data 8-11 3/7/19 after retrain
2023-05-22 08:10:35.207000-04:00 2023-05-22 10:57:36.232000-04:00 1.0345165097160223 0.9888464707710108 1.018450899031812
10sec data 10-15 12/26/9 before retrain
2023-05-22 10:14:23.805000-04:00 2023-05-22 14:52:27.646000-04:00 1.0144601157728252 1.0018132760395584 1.0289513926815947
10sec data 10-15 12/26/9 after retrain
2023-05-22 10:14:23.805000-04:00 2023-05-22 14:52:27.646000-04:00 1.0201615337799248 1.0018132760395584 1.0289513926815947
10sec data 10-15 6/13/9 before retrain
2023-05-22 10:12:20.006000-04:00 2023-05-22 14:51:35.537000-04:00 1.0269250759860635 1.0103234191634995 1.0283286984689668
10sec data 10-15 6/13/9 after retrain
2023-05-22 10:12:20.006000-04:00 2023-05-22 14:51:35.537000-04:00 1.0353413645500087 1.0103234191634995 1.0283286984689668
10sec data 10-15 3/7/19 before retrain
2023-05-22 10:05:57.527000-04:00 2023-05-22 14:55:55.768000-04:00 1.013926057996725 1.004199734333011 1.0202645842693456
10sec data 10-15 3/7/19 after retrain
2023-05-22 10:05:57.527000-04:00 2023-05-22 14:55:55.768000-04:00 1.0269625718378301 1.004199734333011 1.0202645842693456

2023_05_23
10sec data 8-11 12/26/9 before retrain
2023-05-23 08:09:24.136000-04:00 2023-05-23 10:55:59.352000-04:00 0.998805656175241 1.0144152993995217 1.0193280443000905
10sec data 8-11 12/26/9 after retrain
2023-05-23 08:09:24.136000-04:00 2023-05-23 10:55:59.352000-04:00 1.0024004006639078 1.0144152993995217 1.0193280443000905
10sec data 8-11 6/13/9 before retrain
2023-05-23 08:11:03.368000-04:00 2023-05-23 10:58:14.090000-04:00 1.015516197477289 1.0096313325164985 1.0206569770537188
10sec data 8-11 6/13/9 after retrain
2023-05-23 08:11:03.368000-04:00 2023-05-23 10:58:14.090000-04:00 1.032500723543737 1.0096313325164985 1.0206569770537188
10sec data 8-11 3/7/19 before retrain
2023-05-23 08:10:41.946000-04:00 2023-05-23 10:58:14.090000-04:00 1.0077382696326571 1.012188848214634 1.0204396657263002
10sec data 8-11 3/7/19 after retrain
2023-05-23 08:10:41.946000-04:00 2023-05-23 10:58:14.090000-04:00 1.0088159210054786 1.012188848214634 1.0204396657263002
10sec data 10-15 12/26/9 before retrain
2023-05-23 10:16:53.756000-04:00 2023-05-23 14:56:18.975000-04:00 0.9765137330641417 1.0035479262132214 0.980676828208544
10sec data 10-15 12/26/9 after retrain
2023-05-23 10:16:53.756000-04:00 2023-05-23 14:56:18.975000-04:00 0.9795962969734673 1.0035479262132214 0.980676828208544
10sec data 10-15 6/13/9 before retrain
2023-05-23 10:07:48.178000-04:00 2023-05-23 14:56:18.975000-04:00 0.9758024547066674 0.9997016240940975 0.979571499750872
10sec data 10-15 6/13/9 after retrain
2023-05-23 10:07:48.178000-04:00 2023-05-23 14:56:18.975000-04:00 0.9950378103940093 0.9997016240940975 0.979571499750872
10sec data 10-15 3/7/19 before retrain
2023-05-23 10:07:48.178000-04:00 2023-05-23 14:59:15.770000-04:00 0.9787203327665249 1.006219010656635 0.9797283193034905
10sec data 10-15 3/7/19 after retrain
2023-05-23 10:07:48.178000-04:00 2023-05-23 14:59:15.770000-04:00 0.9986484331123002 1.006219010656635 0.9797283193034905

2023_05_24
10sec data 8-11 12/26/9 before retrain
2023-05-24 08:24:29.925000-04:00 2023-05-24 10:54:24.456000-04:00 0.9805828914202201 0.9638216260355492 0.9731733914940021
10sec data 8-11 12/26/9 after retrain
2023-05-24 08:24:29.925000-04:00 2023-05-24 10:54:24.456000-04:00 0.9897671320914041 0.9638216260355492 0.9731733914940021
10sec data 8-11 6/13/9 before retrain
2023-05-24 08:09:31.801000-04:00 2023-05-24 10:52:41.005000-04:00 0.9889227281316779 0.9755376897346432 0.9760214114048502
10sec data 8-11 6/13/9 after retrain
2023-05-24 08:09:31.801000-04:00 2023-05-24 10:52:41.005000-04:00 1.002062285372595 0.9755376897346432 0.9760214114048502
10sec data 8-11 3/7/19 before retrain
2023-05-24 08:09:31.801000-04:00 2023-05-24 10:54:35.151000-04:00 0.9875546559665903 0.9778796517269414 0.975780533100284
10sec data 8-11 3/7/19 after retrain
2023-05-24 08:09:31.801000-04:00 2023-05-24 10:54:35.151000-04:00 0.9962540497432781 0.9778796517269414 0.975780533100284
10sec data 10-15 12/26/9 before retrain
2023-05-24 10:11:07.137000-04:00 2023-05-24 14:54:41.247000-04:00 1.0173582150748333 1.0005937097030078 1.0197876895728635
10sec data 10-15 12/26/9 after retrain
2023-05-24 10:11:07.137000-04:00 2023-05-24 14:54:41.247000-04:00 1.0328646723708075 1.0005937097030078 1.0197876895728635
10sec data 10-15 6/13/9 before retrain
2023-05-24 10:04:48.424000-04:00 2023-05-24 14:54:31.199000-04:00 1.0165822310789168 1.0120764686114225 1.0193746510329424
10sec data 10-15 6/13/9 after retrain
2023-05-24 10:04:48.424000-04:00 2023-05-24 14:54:31.199000-04:00 1.0245885425239096 1.0120764686114225 1.0193746510329424
10sec data 10-15 3/7/19 before retrain
2023-05-24 10:04:38.721000-04:00 2023-05-24 14:57:37.532000-04:00 1.0124793207151224 1.0088233967258224 1.0161962230416808
10sec data 10-15 3/7/19 after retrain
2023-05-24 10:04:38.721000-04:00 2023-05-24 14:57:37.532000-04:00 1.0192549837083564 1.0088233967258224 1.0161962230416808

2023_05_25
10sec data 8-11 12/26/9 before retrain
2023-05-25 08:14:31.532000-04:00 2023-05-25 10:57:09.797000-04:00 0.9893983623991921 0.9978039342992523 0.9857528667881256
10sec data 8-11 12/26/9 after retrain
2023-05-25 08:14:31.532000-04:00 2023-05-25 10:57:09.797000-04:00 0.9914493803682604 0.9978039342992523 0.9857528667881256
10sec data 8-11 6/13/9 before retrain
2023-05-25 08:05:56.428000-04:00 2023-05-25 10:56:59.997000-04:00 0.9906310685828822 0.9800557874135 0.986073915372255
10sec data 8-11 6/13/9 after retrain
2023-05-25 08:05:56.428000-04:00 2023-05-25 10:56:59.997000-04:00 1.0085531914365384 0.9800557874135 0.986073915372255
10sec data 8-11 3/7/19 before retrain
2023-05-25 08:02:46.436000-04:00 2023-05-25 10:56:48.809000-04:00 0.9933713602538439 0.9799432159334889 0.9873954087105772
10sec data 8-11 3/7/19 after retrain
2023-05-25 08:02:46.436000-04:00 2023-05-25 10:56:48.809000-04:00 1.0034764796067255 0.9799432159334889 0.9873954087105772
10sec data 10-15 12/26/9 before retrain
2023-05-25 10:15:53.489000-04:00 2023-05-25 14:52:44.956000-04:00 1.0059212005421476 0.9889001998909327 1.014606400309247
10sec data 10-15 12/26/9 after retrain
2023-05-25 10:15:53.489000-04:00 2023-05-25 14:52:44.956000-04:00 1.0144411677181844 0.9889001998909327 1.014606400309247
10sec data 10-15 6/13/9 before retrain
2023-05-25 10:12:06.172000-04:00 2023-05-25 14:57:22.427000-04:00 1.0066768115279472 1.0033499740895502 1.0067804985176239
10sec data 10-15 6/13/9 after retrain
2023-05-25 10:12:06.172000-04:00 2023-05-25 14:57:22.427000-04:00 1.0209661048650853 1.0033499740895502 1.0067804985176239
10sec data 10-15 3/7/19 before retrain
2023-05-25 10:05:10.516000-04:00 2023-05-25 14:59:20.096000-04:00 1.014503936166366 0.9993806582813339 0.9993989399486368
10sec data 10-15 3/7/19 after retrain
2023-05-25 10:05:10.516000-04:00 2023-05-25 14:59:20.096000-04:00 1.0174303955513462 0.9993806582813339 0.9993989399486368


2023_05_26
10sec data 8-11 12/26/9 before retrain
2023-05-26 08:19:59.047000-04:00 2023-05-26 10:56:11.999000-04:00 1.0305620375160713 1.0201416305348725 1.0297222521842304
10sec data 8-11 12/26/9 after retrain
2023-05-26 08:19:59.047000-04:00 2023-05-26 10:56:11.999000-04:00 1.0306173158087846 1.0201416305348725 1.0297222521842304
10sec data 8-11 6/13/9 before retrain
2023-05-26 08:13:23.492000-04:00 2023-05-26 10:56:11.999000-04:00 1.005328867727503 1.0076608494454595 1.0283440648252127
10sec data 8-11 6/13/9 after retrain
2023-05-26 08:13:23.492000-04:00 2023-05-26 10:56:11.999000-04:00 1.0330620038455094 1.0076608494454595 1.0283440648252127
10sec data 8-11 3/7/19 before retrain
2023-05-26 08:10:56.447000-04:00 2023-05-26 10:57:33.340000-04:00 1.0399199272801822 1.0008975776764508 1.0308455565142365
10sec data 8-11 3/7/19 after retrain
2023-05-26 08:10:56.447000-04:00 2023-05-26 10:57:33.340000-04:00 1.043288786845299 1.0008975776764508 1.0308455565142365
10sec data 10-15 12/26/9 before retrain
2023-05-26 10:20:48.368000-04:00 2023-05-26 14:54:45.552000-04:00 1.0155153812656332 1.0160044448362102 1.0325607064017661
10sec data 10-15 12/26/9 after retrain
2023-05-26 10:20:48.368000-04:00 2023-05-26 14:54:45.552000-04:00 1.0286922789679789 1.0160044448362102 1.0325607064017661
10sec data 10-15 6/13/9 before retrain
2023-05-26 10:11:18.897000-04:00 2023-05-26 14:56:35.787000-04:00 1.0435863543629966 1.0185007437179179 1.0364737202804577
10sec data 10-15 6/13/9 after retrain
2023-05-26 10:11:18.897000-04:00 2023-05-26 14:56:35.787000-04:00 1.0547605908714757 1.0185007437179179 1.0364737202804577
10sec data 10-15 3/7/19 before retrain
2023-05-26 10:05:45.866000-04:00 2023-05-26 14:59:00.212000-04:00 1.0274788797419339 1.025367591215039 1.0343818565400844
10sec data 10-15 3/7/19 after retrain
2023-05-26 10:05:45.866000-04:00 2023-05-26 14:59:00.212000-04:00 1.0426824239279646 1.025367591215039 1.0343818565400844


'''
