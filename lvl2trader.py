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

        buy_thresholds = {13: 4.0, 14: 78.0, 15: 2.0, 16: 8.0, 17: 0.0, 18: 6.0, 19: 44.0}
        sell_thresholds = {13: -225.0, 14: -43.0, 15: -68.0, 16: -69.0, 17: -267.0, 18: -70.0, 19: -499.0}
        buy_to_cover_thresholds = {13: 16.0, 14: 252.0, 15: 0.0, 16: 14.0, 17: 41.0, 18: 35.0, 19: 111.0}
        sell_short_thresholds = {13: -64.0, 14: -8.0, 15: -72.0, 16: -68.0, 17: -39.0, 18: -70.0, 19: 0.0}
        self.ts_trader = TS_Trader(self.account_id, buy_thresholds, sell_thresholds, buy_to_cover_thresholds, sell_short_thresholds, stop_loss=100, quantity=40)

    def calc_gain_long(self, hour, buy_threshold, sell_threshold, last_sell):
        df = pd.read_csv(f"tradestation_data/TSLA_{hour}_test.csv")
        df = df[(df["VolumeSum"] >= buy_threshold) | (df["VolumeSum"] <= sell_threshold)].reset_index(drop=True)
        df["Long"] = df["VolumeSum"] >= buy_threshold
        df["Short"] = df["VolumeSum"] <= sell_threshold
        if len(df) < 1:
            return 0, None

        df["Buy Action"] = df["Long"] & df["Short"].shift()
        if df.iloc[0, df.columns.get_loc("Long")]:
            df.iloc[0, df.columns.get_loc("Buy Action")] = True
        df["Sell Action"] = df["Short"] & df["Long"].shift()
        df.loc[df["Buy Action"], "Gain"] = -pd.to_numeric(df.loc[df["Buy Action"], "BUY"]) 
        df.loc[df["Sell Action"], "Gain"] = pd.to_numeric(df.loc[df["Sell Action"], "SELL"])

        if df.iloc[len(df) - 1, df.columns.get_loc("Long")]:
            df.loc[len(df)] = [0, 0, 0, 0, 0, 0, 0, 0, last_sell]
        df = df.round(3)
        return df["Gain"].sum(), df

    def calc_gain_short(self, hour, buy_to_cover_threshold, sell_short_threshold, last_buy_to_cover):
        df = pd.read_csv(f"tradestation_data/TSLA_{hour}_test.csv")
        df = df[(df["VolumeSum"] >= buy_to_cover_threshold) | (df["VolumeSum"] <= sell_short_threshold)].reset_index(drop=True)
        df["Long"] = df["VolumeSum"] >= buy_to_cover_threshold
        df["Short"] = df["VolumeSum"] <= sell_short_threshold
        if len(df) < 1:
            return 0, None

        df["Sell Action"] = df["Short"] & df["Long"].shift()
        if df.iloc[0, df.columns.get_loc("Short")]:
            df.iloc[0, df.columns.get_loc("Sell Action")] = True
        df["Buy Action"] = df["Long"] & df["Short"].shift()
        df.loc[df["Buy Action"], "Gain"] = -pd.to_numeric(df.loc[df["Buy Action"], "BUY"]) 
        df.loc[df["Sell Action"], "Gain"] = pd.to_numeric(df.loc[df["Sell Action"], "SELL"])

        if df.iloc[len(df) - 1, df.columns.get_loc("Short")]:
            df.loc[len(df)] = [0, 0, 0, 0, 0, 0, 0, 0, -last_buy_to_cover]
        df = df.round(3)
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
        df = df[df["BUY"].notna() & df["SELL"].notna()].reset_index(drop=True)

        last_sell = df.iloc[len(df) - 1, df.columns.get_loc("SELL")]
        last_buy_to_cover = df.iloc[len(df) - 1, df.columns.get_loc("BUY")]

        df = df.loc[((df["Side"] == "Bid") & (df["Dif"] > 0))
                    | ((df["Side"] == "Ask") & (df["Dif"] < 0))]
        df["VolumeSum"] = df["TotalSize"] * df["Dif"]
        df = df[["Time", "VolumeSum", "BUY", "SELL"]]
        df = df.groupby("Time").agg({"VolumeSum": "sum", "BUY": "first", "SELL": "first"})
        df.to_csv(f"tradestation_data/TSLA_{hour}_test.csv")

        buy_arr = np.repeat(self.buy_threshold_range, len(self.sell_threshold_range))
        sell_arr = np.tile(self.sell_threshold_range, len(self.buy_threshold_range))
        long_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        short_arr = np.zeros(len(self.buy_threshold_range) * len(self.sell_threshold_range))
        for i in range(len(long_arr)):
            buy_threshold, sell_threshold = buy_arr[i], sell_arr[i]
            long_arr[i], _ = self.calc_gain_long(hour, buy_threshold, sell_threshold, last_sell)
            short_arr[i], _ = self.calc_gain_short(hour, buy_threshold, sell_threshold, last_buy_to_cover)
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
            self.ts_trader.boh_balance[symbol] = 0
            self.ts_trader.hourly_stop_loss_hit[symbol] = False
            scheduler.add_job(self.ts_trader.reset_bod, 'cron', args=[symbol],
                day_of_week='mon-fri', hour="13", minute="25")
            scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, 13, True], 
                day_of_week='mon-fri', hour="13", minute="30-59", second="*/10")
            scheduler.add_job(self.ts_trader.close_eoh, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="13", minute="59", second="55")
            scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, 14, False],
                    day_of_week='mon-fri', hour="14", second="*/10")
            scheduler.add_job(self.ts_trader.close_eoh, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="14", minute="59", second="55")
            for hr in range(15, 19):
                scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, hr, True],
                    day_of_week='mon-fri', hour=hr, second="*/10")
                scheduler.add_job(self.ts_trader.close_eoh, 'cron', args=[symbol], 
                    day_of_week='mon-fri', hour=hr, minute="59", second="55")
            scheduler.add_job(self.ts_trader.trade, 'cron', args=[symbol, 19, False],
                day_of_week='mon-fri', hour="19", minute="0-54", second="*/10")
            scheduler.add_job(self.ts_trader.close_eod, 'cron', args=[symbol], day_of_week='mon-fri', hour="19", minute="55")
            scheduler.add_job(self.update_all_thresholds, 'cron', args=[symbol], 
                day_of_week='mon-fri', hour="20", minute="5")
        scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(filename="tradestation_data/trading_exceptions.log", format='%(asctime)s %(message)s')
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    symbols = ["TSLA"]
    account_id="11655345"
    buy_threshold_range = np.arange(500)
    sell_threshold_range = -np.arange(500)
    lvl2_trader = Lvl2Trader(account_id, buy_threshold_range, sell_threshold_range)
    lvl2_trader.start_scheduler(symbols)
    