import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from test_mongo import MongoExplorer

class StockLvl2Env(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, symbol, day, hr, depth=1, spread_cost=.02, render_mode="human"):
        self.symbol = symbol
        self.day = day  # YYYY-MM-DD
        self.hr = hr    # UTC time, time frame is HH:00:00-HH:59:50
        if self.hr == 9:    # 09:30:00-9:59:50
            self.length = 180   # num data points
        else:
            self.length = 360 
        self.depth = depth  # number of bids/asks to consider

        self.mongo = MongoExplorer()
        # lvl2 - [time step, bids/asks, dif/size] = (length, 2*depth, 2)
        # prices - [time step, last/buy/sell] = (length, 3)
        self.lvl2, self.prices = self._get_mongo()  
        self.spread_cost = spread_cost  # avg spread cost (buy-last) or (last-sell): .018 rounded to .02
        
        self.time = 0
        self.pos = 0    # current position: 0-none, 1-long, 2-short
        self.balance = 0
        self.last_action_price = 0

        self.observation_space = spaces.Dict(
            {
                # lvl 2 highest {depth} bids and lowest {depth} asks
                # bids: [0,depth/2] high to low, asks: [depth/2,depth] low to high
                # each bid/ask: ((price-last)*100, size/100)
                # price truncated within [last-$5,last+$5], size truncated within [0,50000]
                "lvl2": spaces.Box(low=np.array([[-500., 0.]]*2*self.depth), 
                                    high=np.array([[500., 500.]]*2*self.depth), 
                                    shape=(2*self.depth, 2), dtype=np.float32),
                
                # current position: 0-none, 1-long, 2-short
                "pos": spaces.Discrete(3)
            }
        )
        
        # action: [0,1,2] : 0-hold, 1-buy, 2-sell
        # if not in any position, 0 does nothing, 1 buys stock, 2 short sells
        # if currently long, 0/1 does nothing, 2 sells
        # if currently short, 0/2 does nothing, 1 buys back
        self.action_space = spaces.Discrete(3)

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

    def _get_mongo(self):
        collection_1 = f"{self.symbol}_10sec_ts_lvl1"
        collection_2 = f"{self.symbol}_10sec_ts_lvl2"
        if self.hr == 9:
            start = f"{self.day}T{self.hr}:30:00"
        else:
            start = f"{self.day}T{self.hr}:00:00"
        end = f"{self.day}T{self.hr}:59:50"
        query = {'$and': [{'CurTime': {'$gte': start}}, {'CurTime': {'$lte': end}}]}
        
        df_1 = pd.DataFrame(list(self.mongo.mongoDB[collection_1].find(query)))
        last_prices = df_1["Last"].to_numpy()
        assert len(last_prices.shape) == self.length
        prices = np.stack((last_prices, last_prices+self.spread_cost, last_prices-self.spread_cost), axis=1)
        
        df_2 = pd.DataFrame(list(self.mongo.mongoDB[collection_2].find(query)))
        df = pd.merge(df_1, df_2, on='CurTime')
        df["Dif"] = (df["Price"] - df["Last"]) * 100
        df["Size"] = df["TotalSize"] / 100
        bids = df[df["Side"] == "Bid"].groupby("CurTime").head(self.depth)
        bids = bids[["Dif", "Size"]].to_numpy().reshape(self.length, self.depth, 2)
        asks = df[df["Side"] == "Ask"].groupby("CurTime").head(self.depth)
        asks = asks[["Dif", "Size"]].to_numpy().reshape(self.length, self.depth, 2)
        return np.concatenate((bids, asks), axis=1), prices

    def step(self, action):
        reward = 0
        if self.pos == 0:
            if action == 1:
                self.pos = 1
                self.last_action_price = -self.prices[self.time, 1]
                self.balance -= self.prices[self.time, 1]
            elif action == 2:
                self.pos = 2
                self.last_action_price = self.prices[self.time, 2]
                self.balance += self.prices[self.time, 2]
        elif self.pos == 1 and action == 2:
            self.pos = 0
            reward = self.last_action_price + self.prices[self.time, 2]
            self.last_action_price = 0
            self.balance += self.prices[self.time, 2]
        elif self.pos == 2 and action == 1:
            self.pos = 0
            reward = self.last_action_price - self.prices[self.time, 1]
            self.last_action_price = 0
            self.balance -= self.prices[self.time, 1]
        
        if self.render_mode == "human":
            self.render()
        
        self.time += 1

        # observation, reward, done, truncated(False), info(None)
        return  {"lvl2": self.lvl2[self.time], "pos": self.pos}, reward, self.time == self.length, False, None

    def reset(self):
        self.time = 0
        self.balance = 0
        self.pos = 0
        return {"lvl2": self.lvl2[self.time], "pos": self.pos}, None    # observation, info
    
    def render(self):
        if self.time == 0:
            print(f"Date: {self.day}, Hr: {self.hr}, Open Price: {self.prices[self.time, 0]}")
            print(f"--------------------STARTING ENVIRONMENT--------------------")
        
        if self.hr == 9:
            minute = 30 + int(self.time / 6)
        else:
            minute = int(self.time / 6)
        line = f"{self.day}T{self.hr}:{minute}:{self.time % 6} - "
        if self.pos == 0:
            line += "None  - "
        elif self.pos == 1:
            line += "Long  - "
        elif self.pos == 2:
            line += "Short - "
        line += f"Balance: {self.balance}, "
        line = f"Last: {self.prices[self.time, 0]}, Bids: ["
        for i in range(self.depth - 1):
            line += f"({self.lvl2[self.time, i, 0]}, {self.lvl2[self.time, i, 1]}), "
        line += f"({self.lvl2[self.time, i, 0]}, {self.lvl2[self.time, i, 1]})], Asks: ["
        for i in range(self.depth, 2 * self.depth - 1):
            line += f"({self.lvl2[self.time, i, 0]}, {self.lvl2[self.time, i, 1]}), "
        line += f"({self.lvl2[self.time, i, 0]}, {self.lvl2[self.time, i, 1]})]"
        print(line)
        return