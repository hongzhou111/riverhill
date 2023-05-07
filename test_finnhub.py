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

def run(short, long, signal, act='before'):
    today = datetime.now().strftime("%Y_%m_%d")
    #fname = './finnhub_data/TSLA_history_finnhub_' + today + '.csv'
    fname = './finnhub_data/TSLA_history_finnhub_2023_05_05.csv'

    #df = odo(fname, pd.DataFrame)
    if os.stat(fname).st_size >0:
        df = pd.read_csv(fname)
        print(df)
        df1 = df[df['Open'].isnull()]
        df1['Date'] = pd.to_datetime(df1['Date'])
    else:
        df1 = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    print(df1)
    print(len(df1.loc[: 'Date']))

    ticker = 'TSLA'
    ss = StockStats(ticker, interval='no')
    ss.stock = df1.copy()
    ss.stock = Sdf.retype(ss.stock)
    ss.macd(short, long, signal)
    #ss.stock = ss.stock.reset_index()

    hday = datetime.now().strftime('%Y-%m-%d')
    #ss.stock = ss.stock.loc[ss.stock['date'] >= pd.to_datetime('2023-04-20 09:30:00-04:00')]
    #ss.stock = ss.stock.loc[ss.stock['date'] <= pd.to_datetime(hday + ' 15:00:00-04:00')]
    #print(ss.stock)
    #print(ss.stock.index.inferred_type)

    rl = StockRL(ticker, 0, short, long, signal, save_loc='./rl_min/test_rl_', interval='no')
    rl.stock_env.ss = ss.stock
    print(rl.stock_env.ss)
    rl.stock_env.c2 = ss.macd_crossing_by_threshold_min_len()
    print(rl.stock_env.c2)

    if act == 'before':
        rl.reload()
        re = rl.run('screen')
        rl.run_macd('screen')
        print(re)
    elif act == 'after':
        file_path = rl.save_loc + ticker + '.zip'
        rl.retrain(save=True) if os.path.exists(file_path) else rl.train(save=True)
        re = rl.run('screen')
        rl.run_macd('screen')
        print(re)

#run(3,7,19,act='before')
run(3,7,19,act='after')
#run(6,13,9,act='before')
#run(6,13,9,act='after')

'''
TSLA - min 3,7,19
MACD Perf:          2023-04-14 11:54:27.564000-04:00 - 2023-04-14 15:49:32.714000-04:00   0.00044727137239979704   1.0083054192679979     107434872.07614592
{'model_run_date': '2023-04-16-21-38-15', 'start_date': '2023-04-14', 'end_date': '2023-04-14', 'duration': 0.00044727137239979704, 'model_gain': 1.012703753685852, 'model_perf': 1809171062995.0938, 'buy_and_hold_gain': 1.0103682914906247, 'buy_and_hold_perf': 10366644477.080454, 'model_score': 174.51848252295892, 'predict_date': '2023-04-14', 'predict_macd_accum': -0.48844454102081303, 'predict_macd_len': 32, 'predict_action': 2.4004642963409424, 'predict_vol': 1.0}

MACD Perf:          2023-04-17 13:06:16.181000-04:00 - 2023-04-17 19:55:15.963000-04:00   0.0007781513825469305   1.0028693607782688     39.7308017256014
{'model_run_date': '2023-04-17-23-03-18', 'start_date': '2023-04-17', 'end_date': '2023-04-17', 'duration': 0.0007781513825469305, 'model_gain': 1.0091038005725788, 'model_perf': 114271.65618912569, 'buy_and_hold_gain': 1.0085257427951448, 'buy_and_hold_perf': 54718.89942782848, 'model_score': 2.088339812825445, 'predict_date': '2023-04-17', 'predict_macd_accum': 0.000642849952203435, 'predict_macd_len': 1, 'predict_action': 0.37969690561294556, 'predict_vol': 0.4072553217411041}

before retrain with 2023_04_18 data
MACD Perf:          2023-04-18 07:30:52.334000-04:00 - 2023-04-18 19:48:41.843000-04:00   0.0014037769216133941   1.00283985899181     7.539424950169594
{'model_run_date': '2023-04-18-23-02-39', 'start_date': '2023-04-18', 'end_date': '2023-04-18', 'duration': 0.0014037769216133941, 'model_gain': 0.9760058654508436, 'model_perf': 3.06401037404876e-08, 'buy_and_hold_gain': 0.9769590146527926, 'buy_and_hold_perf': 6.141484676435594e-08, 'model_score': 0.4989038539500283, 'predict_date': '2023-04-18', 'predict_macd_accum': -0.02010252107789157, 'predict_macd_len': 6, 'predict_action': 0.0, 'predict_vol': 0.39019984006881714}
after retrain
MACD Perf:          2023-04-18 07:30:52.334000-04:00 - 2023-04-18 19:48:41.843000-04:00   0.0014037769216133941   1.00283985899181     7.539424950169594
{'model_run_date': '2023-04-18-23-04-15', 'start_date': '2023-04-18', 'end_date': '2023-04-18', 'duration': 0.0014037769216133941, 'model_gain': 0.9858562734280666, 'model_perf': 3.917735440852307e-05, 'buy_and_hold_gain': 0.9769590146527926, 'buy_and_hold_perf': 6.141484676435594e-08, 'model_score': 637.9134113749983, 'predict_date': '2023-04-18', 'predict_macd_accum': -0.02010252107789157, 'predict_macd_len': 6, 'predict_action': 0.0, 'predict_vol': 0.4384729862213135}

before retrain with 2023_04_19 data
MACD Perf:          2023-04-19 11:41:59.085000-04:00 - 2023-04-19 19:44:25.495000-04:00   0.000917884639776763   0.9747019979562337     7.521692485398539e-13
{'model_run_date': '2023-04-19-23-11-11', 'start_date': '2023-04-19', 'end_date': '2023-04-19', 'duration': 0.000917884639776763, 'model_gain': 0.9410878706809923, 'model_perf': 1.866772152161689e-29, 'buy_and_hold_gain': 0.9345135865071929, 'buy_and_hold_perf': 8.998382703551826e-33, 'model_score': 2074.5640785258443, 'predict_date': '2023-04-19', 'predict_macd_accum': -0.0014501275694409066, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}
after retrain
MACD Perf:          2023-04-19 11:41:59.085000-04:00 - 2023-04-19 19:44:25.495000-04:00   0.000917884639776763   0.9747019979562337     7.521692485398539e-13
{'model_run_date': '2023-04-19-23-12-43', 'start_date': '2023-04-19', 'end_date': '2023-04-19', 'duration': 0.000917884639776763, 'model_gain': 0.9583895195415313, 'model_perf': 7.776425304046146e-21, 'buy_and_hold_gain': 0.9345135865071929, 'buy_and_hold_perf': 8.998382703551826e-33, 'model_score': 864202552862.8217, 'predict_date': '2023-04-19', 'predict_macd_accum': -0.0014501275694409066, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}

before retrain with 2023_04_20 data
MACD Perf:          2023-04-20 05:08:48.502000-04:00 - 2023-04-20 14:48:37.488000-04:00   0.0011031515093860983   0.9477782628492079     7.670221969910399e-22
{'model_run_date': '2023-04-21-00-01-39', 'start_date': '2023-04-20', 'end_date': '2023-04-20', 'duration': 0.0011577667744799593, 'model_gain': 0.9599520457153294, 'model_perf': 4.659739019914198e-16, 'buy_and_hold_gain': 0.973973673138186, 'buy_and_hold_perf': 1.2819400173081937e-10, 'model_score': 3.6349118968129857e-06, 'predict_date': '2023-04-20', 'predict_macd_accum': -0.0032215398329362814, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}
after retrain
MACD Perf:          2023-04-20 05:08:48.502000-04:00 - 2023-04-20 14:48:37.488000-04:00   0.0011031515093860983   0.9477782628492079     7.670221969910399e-22
{'model_run_date': '2023-04-21-00-29-26', 'start_date': '2023-04-20', 'end_date': '2023-04-20', 'duration': 0.0011577667744799593, 'model_gain': 1.0174403528672546, 'model_perf': 3060033.3798302985, 'buy_and_hold_gain': 0.973973673138186, 'buy_and_hold_perf': 1.2819400173081937e-10, 'model_score': 2.3870331985233828e+16, 'predict_date': '2023-04-20', 'predict_macd_accum': -0.0032215398329362814, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}

before retrain with 2023_04_21 data
MACD Perf:          2023-04-21 04:53:55.408000-04:00 - 2023-04-21 14:51:04.157000-04:00   0.0011361221778285135   1.0081280174017262     1242.9680887363252
{'model_run_date': '2023-04-21-21-21-33', 'start_date': '2023-04-21', 'end_date': '2023-04-21', 'duration': 0.0011903324454591577, 'model_gain': 1.0279770193208586, 'model_perf': 11675530644.68139, 'buy_and_hold_gain': 0.9959570359642772, 'buy_and_hold_perf': 0.033260511422796166, 'model_score': 351032805727.6711, 'predict_date': '2023-04-21', 'predict_macd_accum': -0.19643556472239665, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0}
after retrain
MACD Perf:          2023-04-21 04:53:55.408000-04:00 - 2023-04-21 14:51:04.157000-04:00   0.0011361221778285135   1.0081280174017262     1242.9680887363252
{'model_run_date': '2023-04-21-21-22-28', 'start_date': '2023-04-21', 'end_date': '2023-04-21', 'duration': 0.0011903324454591577, 'model_gain': 1.0434473420933137, 'model_perf': 3289461655537952.0, 'buy_and_hold_gain': 0.9959570359642772, 'buy_and_hold_perf': 0.033260511422796166, 'model_score': 9.889991208263302e+16, 'predict_date': '2023-04-21', 'predict_macd_accum': -0.19643556472239665, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0}

before retrain with 2023_04_25 data
MACD Perf:          2023-04-25 05:06:19.503000-04:00 - 2023-04-25 19:55:09.808000-04:00   0.0016910928779807204   0.9858489046116573     0.00021870413347636013
{'model_run_date': '2023-04-25-21-02-30', 'start_date': '2023-04-25', 'end_date': '2023-04-25', 'duration': 0.001769210901826484, 'model_gain': 1.0198821689761757, 'model_perf': 68024.02750220361, 'buy_and_hold_gain': 1.0159527697525437, 'buy_and_hold_perf': 7674.956370260337, 'model_score': 8.863115856370166, 'predict_date': '2023-04-25', 'predict_macd_accum': 0.0023455663972533278, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}
after retrain
MACD Perf:          2023-04-25 05:06:19.503000-04:00 - 2023-04-25 19:55:09.808000-04:00   0.0016910928779807204   0.9858489046116573     0.00021870413347636013
{'model_run_date': '2023-04-25-21-04-15', 'start_date': '2023-04-25', 'end_date': '2023-04-25', 'duration': 0.001769210901826484, 'model_gain': 1.0577306741835015, 'model_perf': 59894179917365.03, 'buy_and_hold_gain': 1.0159527697525437, 'buy_and_hold_perf': 7674.956370260337, 'model_score': 7803846305.817293, 'predict_date': '2023-04-25', 'predict_macd_accum': 0.0023455663972533278, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 0.0}

before retrain with 2023_04_26 data
MACD Perf:          2023-04-26 11:07:50.730000-04:00 - 2023-04-26 19:52:59.260000-04:00   0.000999128932014206   0.997513557059013     0.08276833465492194
{'model_run_date': '2023-04-26-21-06-58', 'start_date': '2023-04-26', 'end_date': '2023-04-26', 'duration': 0.0010313330796549974, 'model_gain': 0.9798039299107718, 'model_perf': 2.5608196157073047e-09, 'buy_and_hold_gain': 0.988793075606369, 'buy_and_hold_perf': 1.795227521552358e-05, 'model_score': 0.00014264596464591455, 'predict_date': '2023-04-26', 'predict_macd_accum': -0.07473904463745451, 'predict_macd_len': 4, 'predict_action': 0.06753349304199219, 'predict_vol': 0.0}
after retrain
MACD Perf:          2023-04-26 10:50:55.140000-04:00 - 2023-04-26 19:52:59.260000-04:00   0.0010313330796549974   0.9960352190755033     0.02123790970453959
{'model_run_date': '2023-04-26-21-43-53', 'start_date': '2023-04-26', 'end_date': '2023-04-26', 'duration': 0.0010313330796549974, 'model_gain': 0.9931793944743009, 'model_perf': 0.00131220748568104, 'buy_and_hold_gain': 0.988793075606369, 'buy_and_hold_perf': 1.795227521552358e-05, 'model_score': 73.09421618861748, 'predict_date': '2023-04-26', 'predict_macd_accum': -0.07473904463745451, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9960352190755033, 'MACD_perf': 0.02123790970453959}

before retrain with 2023_04_27 data
MACD Perf:          2023-04-27 04:28:39.129000-04:00 - 2023-04-27 19:32:56.322000-04:00   0.001720484303652968   1.027537775489373     7198688.990381172
{'model_run_date': '2023-04-27-21-11-11', 'start_date': '2023-04-27', 'end_date': '2023-04-27', 'duration': 0.001720484303652968, 'model_gain': 1.019140463822955, 'model_perf': 61078.442563947305, 'buy_and_hold_gain': 1.024209167204648, 'buy_and_hold_perf': 1091987.440191705, 'model_score': 0.055933283035951964, 'model_gain_score': 0.995051105239053, 'predict_date': '2023-04-27', 'predict_macd_accum': 0.6329190377787023, 'predict_macd_len': 15, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.027537775489373, 'MACD_perf': 7198688.990381172}
after retrain
MACD Perf:          2023-04-27 04:28:39.129000-04:00 - 2023-04-27 19:32:56.322000-04:00   0.001720484303652968   1.027537775489373     7198688.990381172
{'model_run_date': '2023-04-27-21-12-35', 'start_date': '2023-04-27', 'end_date': '2023-04-27', 'duration': 0.001720484303652968, 'model_gain': 1.0225782067682927, 'model_perf': 432446.25612598215, 'buy_and_hold_gain': 1.024209167204648, 'buy_and_hold_perf': 1091987.440191705, 'model_score': 0.39601760991872176, 'model_gain_score': 0.9984075904721623, 'predict_date': '2023-04-27', 'predict_macd_accum': 0.6329190377787023, 'predict_macd_len': 15, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.027537775489373, 'MACD_perf': 7198688.990381172}

before retrain with 2023_04_28 data
MACD Perf:          2023-04-28 05:04:16.878000-04:00 - 2023-04-28 19:47:39.789000-04:00   0.001680711282343988   1.0427547263791959     65786721567.2074
{'model_run_date': '2023-04-30-20-01-15', 'start_date': '2023-04-28', 'end_date': '2023-04-28', 'duration': 0.001680711282343988, 'model_gain': 1.0336592827101594, 'model_perf': 358393287.3280847, 'buy_and_hold_gain': 1.0425288815538911, 'buy_and_hold_perf': 57831817238.743706, 'model_score': 0.00619716454436406, 'model_gain_score': 0.991492227217234, 'predict_date': '2023-04-28', 'predict_macd_accum': 0.029789387638273462, 'predict_macd_len': 6, 'predict_action': 0.42508524656295776, 'predict_vol': 0.5184339284896851, 'MACD_gain': 1.0427547263791959, 'MACD_perf': 65786721567.2074}
after retrain
MACD Perf:          2023-04-28 05:04:16.878000-04:00 - 2023-04-28 19:47:39.789000-04:00   0.001680711282343988   1.0427547263791959     65786721567.2074
{'model_run_date': '2023-04-30-20-02-20', 'start_date': '2023-04-28', 'end_date': '2023-04-28', 'duration': 0.001680711282343988, 'model_gain': 1.0353695446713456, 'model_perf': 958398741.1973795, 'buy_and_hold_gain': 1.0425288815538911, 'buy_and_hold_perf': 57831817238.743706, 'model_score': 0.016572170596695555, 'model_gain_score': 0.993132720820286, 'predict_date': '2023-04-28', 'predict_macd_accum': 0.029789387638273462, 'predict_macd_len': 6, 'predict_action': 0.0, 'predict_vol': 0.9027358293533325, 'MACD_gain': 1.0427547263791959, 'MACD_perf': 65786721567.2074}

before retrain with 2023_05_01 data
MACD Perf:          2023-05-01 05:05:33.254000-04:00 - 2023-05-01 19:49:03.461000-04:00   0.0016809426369863015   0.9818110054346766     1.8086770434512814e-05
{'model_run_date': '2023-05-01-21-04-25', 'start_date': '2023-05-01', 'end_date': '2023-05-01', 'duration': 0.0016809426369863015, 'model_gain': 0.9931609097958525, 'model_perf': 0.016863888884499002, 'buy_and_hold_gain': 0.9851797415640885, 'buy_and_hold_perf': 0.0001387800003063741, 'model_score': 121.51526767019652, 'model_gain_score': 1.008101230562347, 'predict_date': '2023-05-01', 'predict_macd_accum': -0.0214122395072455, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9818110054346766, 'MACD_perf': 1.8086770434512814e-05}
after retrain
MACD Perf:          2023-05-01 05:05:33.254000-04:00 - 2023-05-01 19:49:03.461000-04:00   0.0016809426369863015   0.9818110054346766     1.8086770434512814e-05
{'model_run_date': '2023-05-01-21-05-50', 'start_date': '2023-05-01', 'end_date': '2023-05-01', 'duration': 0.0016809426369863015, 'model_gain': 1.014010425936165, 'model_perf': 3932.437776816728, 'buy_and_hold_gain': 0.9851797415640885, 'buy_and_hold_perf': 0.0001387800003063741, 'model_score': 28335767.172037635, 'model_gain_score': 1.029264390197777, 'predict_date': '2023-05-01', 'predict_macd_accum': -0.0214122395072455, 'predict_macd_len': 4, 'predict_action': 1.9112415313720703, 'predict_vol': 0.4658159017562866, 'MACD_gain': 0.9818110054346766, 'MACD_perf': 1.8086770434512814e-05}

TSLA - min 6,13,9
before retrain with 2023_05_01 data
MACD Perf:          2023-05-01 05:23:57.626000-04:00 - 2023-05-01 19:50:11.576000-04:00   0.0016480831430745813   0.9852665733182424     0.00012264143342395457
{'model_run_date': '2023-05-01-21-13-08', 'start_date': '2023-05-01', 'end_date': '2023-05-01', 'duration': 0.0016480831430745813, 'model_gain': 0.9902832448699996, 'model_perf': 0.002672815877469839, 'buy_and_hold_gain': 0.9816306603197851, 'buy_and_hold_perf': 1.3013489364858927e-05, 'model_score': 205.3881017252296, 'model_gain_score': 1.0088145011153133, 'predict_date': '2023-05-01', 'predict_macd_accum': -0.008496648266839733, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9852665733182424, 'MACD_perf': 0.00012264143342395457}
after retrain
MACD Perf:          2023-05-01 05:23:57.626000-04:00 - 2023-05-01 19:50:11.576000-04:00   0.0016480831430745813   0.9852665733182424     0.00012264143342395457
{'model_run_date': '2023-05-01-21-14-43', 'start_date': '2023-05-01', 'end_date': '2023-05-01', 'duration': 0.0016480831430745813, 'model_gain': 0.9909472946482704, 'model_perf': 0.0040143370212119235, 'buy_and_hold_gain': 0.9816306603197851, 'buy_and_hold_perf': 1.3013489364858927e-05, 'model_score': 308.47506834347354, 'model_gain_score': 1.0094909773146759, 'predict_date': '2023-05-01', 'predict_macd_accum': -0.008496648266839733, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 1.0, 'MACD_gain': 0.9852665733182424, 'MACD_perf': 0.00012264143342395457}

TSLA - min 3,7,19
before retrain with 2023_05_02 data
MACD Perf:          2023-05-02 04:51:05.130000-04:00 - 2023-05-02 19:53:17.453000-04:00   0.0017165247019279553   1.006972848637157     57.28807496794537
{'model_run_date': '2023-05-02-22-13-19', 'start_date': '2023-05-02', 'end_date': '2023-05-02', 'duration': 0.0017165247019279553, 'model_gain': 1.0039889875313321, 'model_perf': 10.16806140619005, 'buy_and_hold_gain': 0.9850351028451779, 'buy_and_hold_perf': 0.000153159913410816, 'model_score': 66388.52934655677, 'model_gain_score': 1.0192418367948592, 'predict_date': '2023-05-02', 'predict_macd_accum': 0.029899870896987313, 'predict_macd_len': 5, 'predict_action': 0.9921914339065552, 'predict_vol': 0.06120339035987854, 'MACD_gain': 1.006972848637157, 'MACD_perf': 57.28807496794537}
after retrain
MACD Perf:          2023-05-02 04:51:05.130000-04:00 - 2023-05-02 19:53:17.453000-04:00   0.0017165247019279553   1.006972848637157     57.28807496794537
{'model_run_date': '2023-05-02-22-14-39', 'start_date': '2023-05-02', 'end_date': '2023-05-02', 'duration': 0.0017165247019279553, 'model_gain': 1.0018408346584917, 'model_perf': 2.9195622539813053, 'buy_and_hold_gain': 0.9850351028451779, 'buy_and_hold_perf': 0.000153159913410816, 'model_score': 19062.18271454787, 'model_gain_score': 1.0170610486517404, 'predict_date': '2023-05-02', 'predict_macd_accum': 0.029899870896987313, 'predict_macd_len': 5, 'predict_action': 0.8221617937088013, 'predict_vol': 0.0, 'MACD_gain': 1.006972848637157, 'MACD_perf': 57.28807496794537}

TSLA - min 6,13,9
before retrain with 2023_05_02 data
MACD Perf:          2023-05-02 04:52:11.421000-04:00 - 2023-05-02 19:53:17.453000-04:00   0.0017144226281075596   1.0102894715900705     391.9151595606211
{'model_run_date': '2023-05-02-22-19-08', 'start_date': '2023-05-02', 'end_date': '2023-05-02', 'duration': 0.0017144226281075596, 'model_gain': 0.994800195363574, 'model_perf': 0.04779233419590069, 'buy_and_hold_gain': 0.9852171234986141, 'buy_and_hold_perf': 0.00016876135278152095, 'model_score': 283.194780132942, 'model_gain_score': 1.0097268628776257, 'predict_date': '2023-05-02', 'predict_macd_accum': 0.019024897175947162, 'predict_macd_len': 5, 'predict_action': 0.3143615126609802, 'predict_vol': 1.0, 'MACD_gain': 1.0102894715900705, 'MACD_perf': 391.9151595606211}
after retrain
MACD Perf:          2023-05-02 04:52:11.421000-04:00 - 2023-05-02 19:53:17.453000-04:00   0.0017144226281075596   1.0102894715900705     391.9151595606211
{'model_run_date': '2023-05-02-22-20-11', 'start_date': '2023-05-02', 'end_date': '2023-05-02', 'duration': 0.0017144226281075596, 'model_gain': 1.033369481332182, 'model_perf': 206595487.8469935, 'buy_and_hold_gain': 0.9852171234986141, 'buy_and_hold_perf': 0.00016876135278152095, 'model_score': 1224187199509.1956, 'model_gain_score': 1.0488748689858065, 'predict_date': '2023-05-02', 'predict_macd_accum': 0.019024897175947162, 'predict_macd_len': 5, 'predict_action': 2.0377635955810547, 'predict_vol': 0.1803872436285019, 'MACD_gain': 1.0102894715900705, 'MACD_perf': 391.9151595606211}

TSLA - min 3,7,19
before retrain with 2023_05_03 data
MACD Perf:          2023-05-03 04:30:50.211000-04:00 - 2023-05-03 19:55:28.503000-04:00   0.001759205098934551   0.9879509287516649     0.0010171465360322856
{'model_run_date': '2023-05-03-21-05-05', 'start_date': '2023-05-03', 'end_date': '2023-05-03', 'duration': 0.001759205098934551, 'model_gain': 1.0194406083353664, 'model_perf': 56655.61565014044, 'buy_and_hold_gain': 1.0074836295603369, 'buy_and_hold_perf': 69.27921321034782, 'model_score': 817.7866494834576, 'model_gain_score': 1.0118681618481955, 'predict_date': '2023-05-03', 'predict_macd_accum': -0.0183958409101993, 'predict_macd_len': 2, 'predict_action': 0.48421311378479004, 'predict_vol': 0.42144283652305603, 'MACD_gain': 0.9879509287516649, 'MACD_perf': 0.0010171465360322856}
after retrain
MACD Perf:          2023-05-03 04:30:50.211000-04:00 - 2023-05-03 19:55:28.503000-04:00   0.001759205098934551   0.9879509287516649     0.0010171465360322856
{'model_run_date': '2023-05-03-21-09-12', 'start_date': '2023-05-03', 'end_date': '2023-05-03', 'duration': 0.001759205098934551, 'model_gain': 1.033694902367874, 'model_perf': 151768124.63784075, 'buy_and_hold_gain': 1.0074836295603369, 'buy_and_hold_perf': 69.27921321034782, 'model_score': 2190673.3290552446, 'model_gain_score': 1.0260165744022816, 'predict_date': '2023-05-03', 'predict_macd_accum': -0.0183958409101993, 'predict_macd_len': 2, 'predict_action': 0.31148597598075867, 'predict_vol': 0.0, 'MACD_gain': 0.9879509287516649, 'MACD_perf': 0.0010171465360322856}

TSLA - min 6,13,9
before retrain with 2023_05_03 data
MACD Perf:          2023-05-03 04:30:50.211000-04:00 - 2023-05-03 19:55:28.503000-04:00   0.001759205098934551   0.9947686919087844     0.05071758708544964
{'model_run_date': '2023-05-03-21-12-20', 'start_date': '2023-05-03', 'end_date': '2023-05-03', 'duration': 0.001759205098934551, 'model_gain': 1.0107517170674787, 'model_perf': 436.6223016569442, 'buy_and_hold_gain': 1.0074836295603369, 'buy_and_hold_perf': 69.27921321034782, 'model_score': 6.302356528375363, 'model_gain_score': 1.0032438120196236, 'predict_date': '2023-05-03', 'predict_macd_accum': -0.004113861176459205, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9947686919087844, 'MACD_perf': 0.05071758708544964}
after retrain
MACD Perf:          2023-05-03 04:30:50.211000-04:00 - 2023-05-03 19:55:28.503000-04:00   0.001759205098934551   0.9947686919087844     0.05071758708544964
{'model_run_date': '2023-05-03-21-14-08', 'start_date': '2023-05-03', 'end_date': '2023-05-03', 'duration': 0.001759205098934551, 'model_gain': 1.0252059103344038, 'model_perf': 1397805.4772724682, 'buy_and_hold_gain': 1.0074836295603369, 'buy_and_hold_perf': 69.27921321034782, 'model_score': 20176.405194273862, 'model_gain_score': 1.017590638948447, 'predict_date': '2023-05-03', 'predict_macd_accum': -0.004113861176459205, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9947686919087844, 'MACD_perf': 0.05071758708544964}

TSLA - min 3,7,19
before retrain with 2023_05_04 data
MACD Perf:          2023-05-04 05:08:22.187000-04:00 - 2023-05-04 19:41:55.912000-04:00   0.0016620283168442415   1.0019403754509624     3.2102318342994867
{'model_run_date': '2023-05-04-20-06-59', 'start_date': '2023-05-04', 'end_date': '2023-05-04', 'duration': 0.0016620283168442415, 'model_gain': 0.9876057690306256, 'model_perf': 0.000550936256655676, 'buy_and_hold_gain': 0.9956962803565939, 'buy_and_hold_perf': 0.07464390804232723, 'model_score': 0.007380860288602046, 'model_gain_score': 0.9918745188813292, 'predict_date': '2023-05-04', 'predict_macd_accum': -0.08872531016993636, 'predict_macd_len': 9, 'predict_action': 0.23671545088291168, 'predict_vol': 0.5209234952926636, 'MACD_gain': 1.0019403754509624, 'MACD_perf': 3.2102318342994867}
after retrain
MACD Perf:          2023-05-04 05:08:22.187000-04:00 - 2023-05-04 19:41:55.912000-04:00   0.0016620283168442415   1.0019403754509624     3.2102318342994867
{'model_run_date': '2023-05-04-20-08-04', 'start_date': '2023-05-04', 'end_date': '2023-05-04', 'duration': 0.0016620283168442415, 'model_gain': 1.0105938532789336, 'model_perf': 567.0937918434895, 'buy_and_hold_gain': 0.9956962803565939, 'buy_and_hold_perf': 0.07464390804232723, 'model_score': 7597.321827280478, 'model_gain_score': 1.0149619650251223, 'predict_date': '2023-05-04', 'predict_macd_accum': -0.08872531016993636, 'predict_macd_len': 9, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 1.0019403754509624, 'MACD_perf': 3.2102318342994867}

TSLA - min 6,13,9
before retrain with 2023_05_04 data
MACD Perf:          2023-05-04 04:51:33.498000-04:00 - 2023-05-04 19:41:55.912000-04:00   0.0016940136352105528   0.9932286019512367     0.018118059011546023
{'model_run_date': '2023-05-04-20-10-53', 'start_date': '2023-05-04', 'end_date': '2023-05-04', 'duration': 0.0016940136352105528, 'model_gain': 0.9864675061607469, 'model_perf': 0.00032135468271023973, 'buy_and_hold_gain': 0.9951456310679611, 'buy_and_hold_perf': 0.05655283312966875, 'model_score': 0.005682379907889188, 'model_gain_score': 0.9912795427761653, 'predict_date': '2023-05-04', 'predict_macd_accum': -0.06977938393070934, 'predict_macd_len': 9, 'predict_action': 0.0, 'predict_vol': 0.8805941343307495, 'MACD_gain': 0.9932286019512367, 'MACD_perf': 0.018118059011546023}
after retrain
MACD Perf:          2023-05-04 04:51:33.498000-04:00 - 2023-05-04 19:41:55.912000-04:00   0.0016940136352105528   0.9932286019512367     0.018118059011546023
{'model_run_date': '2023-05-04-20-11-48', 'start_date': '2023-05-04', 'end_date': '2023-05-04', 'duration': 0.0016940136352105528, 'model_gain': 1.0107683563554726, 'model_perf': 557.0916689088929, 'buy_and_hold_gain': 0.9951456310679611, 'buy_and_hold_perf': 0.05655283312966875, 'model_score': 9850.81804180437, 'model_gain_score': 1.0156989337035482, 'predict_date': '2023-05-04', 'predict_macd_accum': -0.06977938393070934, 'predict_macd_len': 9, 'predict_action': 0.0, 'predict_vol': 0.06870855391025543, 'MACD_gain': 0.9932286019512367, 'MACD_perf': 0.018118059011546023}

TSLA - min 3,7,19
before retrain with 2023_05_05 data
after retrain
MACD Perf:          2023-05-05 04:19:08.235000-04:00 - 2023-05-05 19:55:19.438000-04:00   0.0017811771626078134   1.0129592089977637     1378.7092279083004
{'model_run_date': '2023-05-07-13-26-34', 'start_date': '2023-05-05', 'end_date': '2023-05-05', 'duration': 0.0017811771626078134, 'model_gain': 1.0496960782759246, 'model_perf': 669342319206.5338, 'buy_and_hold_gain': 1.0478333230598533, 'buy_and_hold_perf': 246934255849.62537, 'model_score': 2.7106094166786674, 'model_gain_score': 1.001777720917132, 'predict_date': '2023-05-05', 'predict_macd_accum': -0.006855526625270782, 'predict_macd_len': 3, 'predict_action': 1.1018755435943604, 'predict_vol': 0.0, 'MACD_gain': 1.0129592089977637, 'MACD_perf': 1378.7092279083004}

'''
