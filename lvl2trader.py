from re import S
import pandas as pd
from test_mongo import MongoExplorer
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
from datetime import datetime
from tradestation_trader import TS_Trader
import logging
import numpy as np

class Lvl2Trader:
    def __init__(self, account_id, buy_threshold_range, sell_threshold_range):
        self.mongo = MongoExplorer()
        self.account_id = account_id
        self.buy_threshold_range = buy_threshold_range
        self.sell_threshold_range = sell_threshold_range

        thresholds = {'TSLA': {'buy': {13: 189.0, 14: 94.0, 15: 2.0, 16: 8.0, 17: 0.0, 18: 6.0, 19: 42.0},
                'sell': {13: -224.0, 14: -43.0, 15: -68.0, 16: -69.0, 17: -47.0, 18: -70.0, 19: -498.0},
                'buy_to_cover': {13: 219.0, 14: 74.0, 15: 0.0, 16: 14.0, 17: 40.0, 18: 107.0, 19: 109.0},
                'sell_short':{13: -224.0, 14: -43.0, 15: -68.0, 16: -69.0, 17: -47.0, 18: -70.0, 19: -498.0}},
            'NVDA': {'buy': {13: 44.0, 14: 38.0, 15: 69.0, 16: 13.0, 17: 8.0, 18: 15.0, 19: 8.0},
                'sell': {13: -440.0, 14: -5.0, 15: -288.0, 16: 0.0, 17: -240.0, 18: -17.0, 19: -40.0},
                'buy_to_cover': {13: 34.0, 14: 28.0, 15: 69.0, 16: 9.0, 17: 8.0, 18: 15.0, 19: 27.0},
                'sell_short':{13: -440.0, 14: -5.0, 15: -288.0, 16: 0.0, 17: -240.0, 18: -17.0, 19: -40.0}}, 
            'AMZN': {'buy': {13: 29.0, 14: 46.0, 15: 41.0, 16: 34.0, 17: 71.0, 18: 41.0, 19: 23.0},
                'sell': {13: -76.0, 14: -59.0, 15: -358.0, 16: -33.0, 17: -57.0, 18: -45.0, 19: -85.0},
                'buy_to_cover': {13: 29.0, 14: 6.0, 15: 24.0, 16: 34.0, 17: 71.0, 18: 37.0, 19: 23.0},
                'sell_short':{13: -76.0, 14: -59.0, 15: -358.0, 16: -33.0, 17: -57.0, 18: -45.0, 19: -85.0}}, 
            'AAPL': {'buy': {13: 97.0, 14: 39.0, 15: 56.0, 16: 25.0, 17: 19.0, 18: 250.0, 19: 36.0},
                'sell': {13: -46.0, 14: -33.0, 15: -32.0, 16: -21.0, 17: -58.0, 18: -36.0, 19: -66.0},
                'buy_to_cover': {13: 94.0, 14: 39.0, 15: 479.0, 16: 5.0, 17: 19.0, 18: 135.0, 19: 11.0},
                'sell_short':{13: -46.0, 14: -33.0, 15: -32.0, 16: -21.0, 17: -58.0, 18: -36.0, 19: -66.0}}, 
            'GOOG': {'buy': {13: 6.0, 14: 20.0, 15: 34.0, 16: 19.0, 17: 46.0, 18: 53.0, 19: 39.0},
                'sell': {13: -337.0, 14: -33.0, 15: -475.0, 16: -28.0, 17: -40.0, 18: -10.0, 19: -446.0},
                'buy_to_cover': {13: 124.0, 14: 413.0, 15: 34.0, 16: 27.0, 17: 250.0, 18: 32.0, 19: 41.0},
                'sell_short':{13: -337.0, 14: -33.0, 15: -475.0, 16: -28.0, 17: -40.0, 18: -10.0, 19: -446.0}}}
        policy_long = {'TSLA': {13: True, 14: False, 15: True, 16: True, 17: True, 18: True, 19: False},
            'NVDA': {13: True, 14: True, 15: False, 16: True, 17: False, 18: False, 19: True}, 
            'AMZN': {13: False, 14: True, 15: True, 16: True, 17: False, 18: False, 19: False}, 
            'AAPL': {13: False, 14: False, 15: True, 16: True, 17: False, 18: False, 19: False}, 
            'GOOG': {13: True, 14: True, 15: True, 16: True, 17: False, 18: False, 19: False}}
        stop_losses = {'TSLA': 100, 'NVDA': 4.5, 'AMZN': 1.5, 'AAPL': 2.0, 'GOOG': 1.5}
        quantities = {'TSLA': 40, 'NVDA': 1, 'AMZN': 1, 'AAPL': 1, 'GOOG': 1}
        self.ts_trader = TS_Trader(self.account_id, thresholds, policy_long, stop_losses=stop_losses, quantities=quantities)

    def calc_gain_long(self, arr, buy_threshold, sell_threshold):
        # arr = [VolumeSum, Buy, Sell]
        arr = arr[(arr[:, 0] >= buy_threshold) | (arr[:, 0] <= sell_threshold) | (arr[:, 3] == 1)]
        if len(arr) < 2:
            return 0
        l = (arr[:, 0] >= buy_threshold) & (arr[:, 3] == 0)
        s = (arr[:, 0] <= sell_threshold) | (arr[:, 3] == 1)
        buy = l & np.roll(s, 1)
        sell = s & np.roll(l, 1)
        return arr[sell, 2].sum() - arr[buy, 1].sum() 

    def calc_gain_short(self, arr, buy_to_cover_threshold, sell_short_threshold):
        arr = arr[(arr[:, 0] >= buy_to_cover_threshold) | (arr[:, 0] <= sell_short_threshold) | (arr[:, 3] == 1)]
        if len(arr) < 2:
            return 0
        s = (arr[:, 0] <= sell_short_threshold) & (arr[:, 3] == 0)
        l = (arr[:, 0] >= buy_to_cover_threshold) | (arr[:, 3] == 1)
        sell = s & np.roll(l, 1)
        buy = l & np.roll(s, 1)
        return arr[sell, 2].sum() - arr[buy, 1].sum() 

    def update_thresholds(self, symbol, date, hour):
        collection_1 = f"{symbol}_10sec_ts_lvl1"
        collection_2 = f"{symbol}_10sec_ts_lvl2"
        collection_3 = f"{symbol}_ts_trade_prices"
        long_df = pd.read_csv(f"tradestation_data/{symbol}_{hour}_thresholds_long.csv")
        short_df = pd.read_csv(f"tradestation_data/{symbol}_{hour}_thresholds_short.csv")
        if date not in long_df.columns:
            dates = list(long_df.columns)[2:-1] + [date]
        else:
            dates = list(long_df.columns)[2:-1]
        start = f'{date}T{hour}:00:00Z'
        end = f'{date}T{hour+1}:00:00Z'
        query_1 = {'$and': [{'CurTime': {'$gte': start}}, {'CurTime': {'$lt': end}}]}
        df_1 = pd.DataFrame(list(self.mongo.mongoDB[collection_1].find(query_1)))
        df_2 = pd.DataFrame(list(self.mongo.mongoDB[collection_2].find(query_1)))
        df = pd.merge(df_1, df_2, on="CurTime")
        df["Dif"] = (df["Price"] - df["Last"])
        df = df.rename(columns={"CurTime": "Time"})
        query_3 = {'$and': [{'Time': {'$gte': start}}, {'Time': {'$lt': end}}]}
        df_3 = pd.DataFrame(list(self.mongo.mongoDB[collection_3].find(query_3)))
        df = pd.merge(df, df_3, on="Time")
        df = df[["Time", "Side", "TotalSize", "Dif", "BUY", "SELL"]]
        df = df[df["BUY"].notna() & df["SELL"].notna()].reset_index(drop=True)
        df["EoH"] = df["Time"] == f'{date}T{hour}:59:50Z'

        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] > 0))
                | ((df["Side"] == "Ask") & (df["Dif"] < 0))
                | df["EoH"]]
        df["VolumeSum"] = df["TotalSize"] * df["Dif"]
        df = df[["Time", "VolumeSum", "BUY", "SELL", "EoH"]]
        df = df.groupby("Time").agg({"VolumeSum": "sum", "BUY": "first", "SELL": "first", "EoH": "first"})
        arr = df.to_numpy().astype('float64')

        buy_arr = np.repeat(self.buy_threshold_range, len(self.sell_threshold_range))
        sell_arr = np.tile(self.sell_threshold_range, len(self.buy_threshold_range))
        long_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        short_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        for i in range(len(long_arr)):
            buy_threshold, sell_threshold = buy_arr[i], sell_arr[i]
            long_arr[i] = self.calc_gain_long(arr.copy(), buy_threshold, sell_threshold)
            short_arr[i] = self.calc_gain_short(arr.copy(), buy_threshold, sell_threshold)
        long_df[date] = long_arr
        long_df["Sum"] = long_df[dates].sum(axis=1)
        long_df = long_df[["Buy Threshold", "Sell Threshold"]+dates+["Sum"]]
        long_df = long_df.round(3)
        long_df.to_csv(f"tradestation_data/{symbol}_{hour}_thresholds_long.csv", index=False, date_format="%Y-%m-%d")
        long_df = long_df.sort_values(by=["Sum"], ascending=False)
        short_df[date] = short_arr
        short_df["Sum"] = short_df[dates].sum(axis=1)
        short_df = short_df.round(3)
        short_df = short_df[["Buy Threshold", "Sell Threshold"]+dates+["Sum"]]
        short_df.to_csv(f"tradestation_data/{symbol}_{hour}_thresholds_short.csv", index=False, date_format="%Y-%m-%d")
        short_df = short_df.sort_values(by=["Sum"], ascending=False)
        return long_df.iloc[0].tolist(), short_df.iloc[0].tolist()
    
    def test_thresholds(self, symbol, hour, buy_threshold, sell_threshold, buy_to_cover_threshold, sell_short_threshold):
        long_df = pd.read_csv(f"tradestation_data/{symbol}_{hour}_thresholds_long.csv")
        short_df = pd.read_csv(f"tradestation_data/{symbol}_{hour}_thresholds_short.csv")
        return long_df[(long_df["Buy Threshold"]==buy_threshold) & (long_df["Sell Threshold"]==sell_threshold)].iloc[0].tolist(), \
            short_df[(short_df["Buy Threshold"]==buy_to_cover_threshold) & (short_df["Sell Threshold"]==sell_short_threshold)].iloc[0].tolist()

    def update_all_thresholds(self, symbol):
        with open(f"tradestation_data/{symbol}_thresholds.log", 'a') as f:
            date = datetime.now().strftime("%Y-%m-%d")
            f.write(f"{date}\n----------PREVIOUS THRESHOLDS----------\n")
            f.write(f"'prev policy_long': {self.ts_trader.policy_long[symbol]}\n")
            f.write(f"{{'prev buy': {self.ts_trader.thresholds[symbol]['buy']},\n'prev sell': {self.ts_trader.thresholds[symbol]['sell']},\n")
            f.write(f"'prev buy_to_cover': {self.ts_trader.thresholds[symbol]['buy_to_cover']},\n'prev sell_short':{self.ts_trader.thresholds[symbol]['sell']}}}\n")
            for hour in range(13, 20):
                long_row, short_row = self.update_thresholds(symbol, date, hour)
                prev_long_row, prev_short_row = self.test_thresholds(symbol, hour, \
                    self.ts_trader.thresholds[symbol]['buy'][hour], self.ts_trader.thresholds[symbol]['sell'][hour], \
                        self.ts_trader.thresholds[symbol]['buy_to_cover'][hour], self.ts_trader.thresholds[symbol]['sell_short'][hour])
                f.write(f"Prev Long {hour}: {prev_long_row}\nPrev Short {hour}: {prev_short_row}\n")
                f.write(f"Long {hour}: {long_row}\nShort {hour}: {short_row}\n")
                self.ts_trader.thresholds[symbol]['buy'][hour] = long_row[0]
                self.ts_trader.thresholds[symbol]['sell'][hour] = long_row[1]
                self.ts_trader.thresholds[symbol]['buy_to_cover'][hour] = short_row[0]
                self.ts_trader.thresholds[symbol]['sell_short'][hour] = short_row[1]
                self.ts_trader.policy_long[symbol][hour] = long_row[-1] >= short_row[-1]
            f.write("----------NEW THRESHOLDS----------\n")
            f.write(f"'policy_long': {self.ts_trader.policy_long[symbol]}\n")
            f.write(f"{{'buy': {self.ts_trader.thresholds[symbol]['buy']},\n'sell': {self.ts_trader.thresholds[symbol]['sell']},\n")
            f.write(f"'buy_to_cover': {self.ts_trader.thresholds[symbol]['buy_to_cover']},\n'sell_short':{self.ts_trader.thresholds[symbol]['sell_short']}}}\n")
            f.write("\n")

    def start_scheduler(self, symbols):
        executors = {
            'default': ThreadPoolExecutor(100),
            'processpool': ProcessPoolExecutor(8)
        }
        scheduler = BlockingScheduler(executors=executors, timezone=utc)
        for symbol in symbols:
            self.ts_trader.holding_long[symbol] = False
            self.ts_trader.holding_short[symbol] = False
            self.ts_trader.balance[symbol] = 0
            self.ts_trader.boh_balance[symbol] = 0
            self.ts_trader.hourly_stop_loss_hit[symbol] = False
            scheduler.add_job(self.ts_trader.reset_bod, 'cron', args=[symbol],
                day_of_week='mon-fri', hour="13", minute="25")
            scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, 13], 
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.ts_trader.close_eoh, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="13", minute="59", second="55")
            for hr in range(14, 19):
                scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, hr],
                    day_of_week='mon-fri', hour=hr, second="*/10")
                scheduler.add_job(self.ts_trader.close_eoh, 'cron', args=[symbol], 
                    day_of_week='mon-fri', hour=hr, minute="59", second="55")
            scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, 19],
                day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
            scheduler.add_job(self.ts_trader.close_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
            scheduler.add_job(self.update_all_thresholds, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="20", minute="5")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    symbols = ["TSLA", 'NVDA', 'AMZN', 'AAPL', 'GOOG']
    account_id="11655345"
    buy_threshold_range = np.arange(500)
    sell_threshold_range = -np.arange(500)
    lvl2_trader = Lvl2Trader(account_id, buy_threshold_range, sell_threshold_range)
    for symbol in symbols:
        lvl2_trader.update_all_thresholds(symbol)
    lvl2_trader.start_scheduler(symbols)
    