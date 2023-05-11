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
    print(df1)
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
        if short == 12:
            save_loc = './rl_sec_8_11/test_rl_'
        else:
            save_loc = './rl_sec_8_11/test_rl_' + str(short) + '_' + str(long) + '_' + str(signal) + '_'
    elif period == 2:
        ss.stock = ss.stock.loc[ss.stock.index >= pd.to_datetime(dd + ' 10:00:00-04:00')]
        ss.stock = ss.stock.loc[ss.stock.index <= pd.to_datetime(dd + ' 15:00:00-04:00')]
        if short == 12:
            save_loc = './rl_sec_10_15/test_rl_'
        else:
            save_loc = './rl_sec_10_15/test_rl_' + str(short) + '_' + str(long) + '_' + str(signal) + '_'

    cc = ss.macd_crossing_by_threshold_min_len()
    print(cc)

    print(save_loc)
    rl = StockRL(ticker, 0, short, long, signal, save_loc=save_loc, interval='no')
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

ticker='TSLA'
today = datetime.now().strftime("%Y_%m_%d")
#today = '2023_05_08'
print(today)

#re1 = daily_run(ticker, 12, 26, 9, today, test=True, period=1)
#re1 = daily_run(ticker, 12, 26, 9, today, test=False, period=1)

#re1 = daily_run(ticker, 6, 13, 9, today, test=True, period=1)
#re1 = daily_run(ticker, 6, 13, 9, today, test=False, period=1)

#re1 = daily_run(ticker, 3, 7, 19, today, test=True, period=1)
#re1 = daily_run(ticker, 3, 7, 19, today, test=False, period=1)

#re2 = daily_run(ticker, 12, 26, 9, today, test=True, period=2)
#re2 = daily_run(ticker, 12, 26, 9, today, test=False, period=2)

#re2 = daily_run(ticker, 6, 13, 9, today, test=True, period=2)
#re2 = daily_run(ticker, 6, 13, 9, today, test=False, period=2)

#re2 = daily_run(ticker, 3, 7, 19, today, test=True, period=2)
re2 = daily_run(ticker, 3, 7, 19, today, test=False, period=2)

'''
model_gain = 1
buy_and_hold_gain = 1
macd_gain = 1

qDates = [
    '2023_05_08'
]

tDates = [
    '2023_05_08'
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

ticker='TSLA'
for q in qDates:
    print(q)

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

print(model_gain, buy_and_hold_gain, macd_gain)
'''
#test_date = '2023_05_05'
#daily_run(ticker, 3, 7, 19, test_date, test=True)

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


'''
