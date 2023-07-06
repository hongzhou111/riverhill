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
    def __init__(self, buy_threshold_range, sell_threshold_range, size_threshold):
        self.mongo = MongoExplorer()
        self.buy_threshold_range = buy_threshold_range
        self.sell_threshold_range = sell_threshold_range
        self.size_threshold = size_threshold

        buy_thresholds = {13: 0.06, 14: 0.105, 15: 0.075, 16: 0.04, 17: 0.03, 18: 0.025, 19: 0.02}
        sell_thresholds = {13: -0.215, 14: -0.085, 15: -0.18, 16: -0.07, 17: -0.065, 18: -0.205, 19: -0.065}
        buy_to_cover_thresholds = {13: 0.055, 14: 0.145, 15: 0.08, 16: 0.065, 17: 0.1, 18: 0.08, 19: 0.02}
        sell_short_thresholds = {13: -0.215, 14: -0.12, 15: -0.18, 16: -0.075, 17: -0.105, 18: -0.1, 19: -0.065}
        self.ts_trader = TS_Trader(buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, trade_stop_loss=.2, quantity="40")

    def calc_gain_long(self, df, buy_threshold, sell_threshold, size_threshold):
        last_sell = df.iloc[len(df) - 1, df.columns.get_loc("SELL")]
        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= buy_threshold))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= sell_threshold))]
        df.loc[df["Side"] == "Bid", "Multiplier"] = df.loc[df["Side"] == "Bid", "Dif"] - buy_threshold
        df.loc[df["Side"] == "Ask", "Multiplier"] = df.loc[df["Side"] == "Ask", "Dif"] - sell_threshold
        df["VolumeSum"] = df["TotalSize"] * df["Multiplier"]
        df = df[["Time", "VolumeSum", "BUY", "SELL"]]
        df = df.groupby("Time").agg({"VolumeSum": "sum", "BUY": "first", "SELL": "first"})
        df = df[(df["VolumeSum"] > size_threshold) | (df["VolumeSum"] < -size_threshold)].reset_index()
        df["Long"] = df["VolumeSum"] > size_threshold
        df["Short"] = df["VolumeSum"] < -size_threshold
        if len(df) < 2:
            return 0, None

        df["Buy Action"] = df["Long"] & df["Short"].shift()
        if df.iloc[0, df.columns.get_loc("Long")]:
            df.iloc[0, df.columns.get_loc("Buy Action")] = True
        df["Sell Action"] = df["Short"] & df["Long"].shift()
        df.loc[df["Buy Action"], "Gain"] = -pd.to_numeric(df.loc[df["Buy Action"], "BUY"]) 
        df.loc[df["Sell Action"], "Gain"] = pd.to_numeric(df.loc[df["Sell Action"], "SELL"])

        if df.iloc[len(df) - 1, df.columns.get_loc("Long")]:
            df.loc[len(df)] = [0, 0, 0, 0, 0, 0, 0, 0, last_sell]
        return df["Gain"].sum(), df

    def calc_gain_short(self, df, buy_to_cover_threshold, sell_short_threshold, size_threshold):
        last_buy_to_cover = df.iloc[len(df) - 1, df.columns.get_loc("BUY")]
        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] >= buy_to_cover_threshold))
                    | ((df["Side"] == "Ask") & (df["Dif"] <= sell_short_threshold)) ]
        df.loc[df["Side"] == "Bid", "Multiplier"] = df.loc[df["Side"] == "Bid", "Dif"] - buy_to_cover_threshold
        df.loc[df["Side"] == "Ask", "Multiplier"] = df.loc[df["Side"] == "Ask", "Dif"] - sell_short_threshold
        df["VolumeSum"] = df["TotalSize"] * df["Multiplier"]
        df = df[["Time", "VolumeSum", "BUY", "SELL"]]
        df = df.groupby("Time").agg({"VolumeSum": "sum", "BUY": "first", "SELL": "first"})
        df = df[(df["VolumeSum"] > size_threshold) | (df["VolumeSum"] < -size_threshold)].reset_index()
        df["Long"] = df["VolumeSum"] > size_threshold
        df["Short"] = df["VolumeSum"] < -size_threshold
        if len(df) < 2:
            return 0, None

        df["Sell Action"] = df["Short"] & df["Long"].shift()
        if df.iloc[0, df.columns.get_loc("Short")]:
            df.iloc[0, df.columns.get_loc("Sell Action")] = True
        df["Buy Action"] = df["Long"] & df["Short"].shift()
        df.loc[df["Buy Action"], "Gain"] = -pd.to_numeric(df.loc[df["Buy Action"], "BUY"]) 
        df.loc[df["Sell Action"], "Gain"] = pd.to_numeric(df.loc[df["Sell Action"], "SELL"])

        if df.iloc[len(df) - 1, df.columns.get_loc("Short")]:
            df.loc[len(df)] = [0, 0, 0, 0, 0, 0, 0, 0, -last_buy_to_cover]
        return df["Gain"].sum(), df

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
        df = df[df["BUY"].notna() & df["SELL"].notna()]

        buy_arr = np.repeat(self.buy_threshold_range, len(self.sell_threshold_range))
        sell_arr = np.tile(self.sell_threshold_range, len(self.buy_threshold_range))
        long_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        short_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        for i in range(len(long_arr)):
            buy_threshold, sell_threshold = buy_arr[i], sell_arr[i]
            long_arr[i], _ = self.calc_gain_long(df.copy(), buy_threshold, sell_threshold, size_threshold)
            short_arr[i], _ = self.calc_gain_short(df.copy(), buy_threshold, sell_threshold, size_threshold)
        long_df[date] = long_arr
        long_df["Sum"] = long_df[dates].sum(axis=1)
        long_df = long_df[["Buy Threshold", "Sell Threshold"]+dates+["Sum"]]
        long_df = long_df.round(3)
        long_df.to_csv(f"tradestation_data/{symbol}_{hour}_thresholds_long.csv", index=False, date_format="%Y-%m-%d")
        long_df = long_df.sort_values(by=["Sum"], ascending=False)
        short_df[date] = long_arr
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
            date = datetime.utcnow().strftime("%Y-%m-%d")
            f.write(f"{date}\n----------PREVIOUS THRESHOLDS----------\n")
            f.write(f"{self.ts_trader.buy_thresholds}\n{self.ts_trader.sell_thresholds}\n")
            f.write(f"{self.ts_trader.buy_to_cover_thresholds}\n{self.ts_trader.sell_short_thresholds}\n")
            for hour in range(13, 20):
                long_row, short_row = self.update_thresholds(symbol, date, hour)
                prev_long_row, prev_short_row = self.test_thresholds(symbol, hour, \
                    self.ts_trader.buy_thresholds[hour], self.ts_trader.sell_thresholds[hour], \
                        self.ts_trader.buy_to_cover_thresholds[hour], self.ts_trader.sell_short_thresholds[hour])
                f.write(f"Previous Long {hour}: {prev_long_row}\nPrevious Short {hour}: {prev_short_row}\n")
                f.write(f"Long {hour}: {long_row}\nShort {hour}: {short_row}\n")
                self.ts_trader.buy_thresholds[hour] = long_row[0]
                self.ts_trader.sell_thresholds[hour] = long_row[1]
                self.ts_trader.buy_to_cover_thresholds[hour] = short_row[0]
                self.ts_trader.sell_short_thresholds[hour] = short_row[1]
            f.write("----------NEW THRESHOLDS----------\n")
            f.write(f"Buy Thresholds: {self.ts_trader.buy_thresholds}\nSell Thresholds: {self.ts_trader.sell_thresholds}\n")
            f.write(f"Buy to Cover Thresholds: {self.ts_trader.buy_to_cover_thresholds}\nSell Short Thresholds: {self.ts_trader.sell_short_thresholds}\n")
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
                day_of_week='mon-fri', hour="20", minute="35")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    symbols = ["TSLA"]
    buy_threshold_range = (-np.arange(50) / 200) + .25
    sell_threshold_range = (-np.arange(50) / 200)
    size_threshold = 0
    lvl2_trader = Lvl2Trader(buy_threshold_range, sell_threshold_range, size_threshold)
    lvl2_trader.start_scheduler(symbols)
    