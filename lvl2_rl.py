import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from test_mongo import MongoExplorer

class StockLvl2Env(gym.Env):
    def __init__(self, symbol, day, hr, depth=1):
        self.symbol = symbol
        self.day = day  # YYYY-MM-DD
        self.hr = hr    # UTC time, time frame is HH:00:00-HH:59:50
        self.depth = depth  # number of bids/asks to consider

        self.mongo = MongoExplorer()
        self._get_mongo()
        
        self.time = 0
        self.balance = 30000
        self.pos = 0    # current position: 0-none, 1-long, 2-short

        self.observation_space = spaces.Dict(
            {
                # lvl 2 highest {depth} bids and lowest {depth} asks
                # bids: [0,depth/2] high to low, asks: [depth/2,depth] low to high
                # each bid/ask: ((price-last)*100, size/100)
                # price truncated within [last-$5,last+$5], size truncated within [0,50000]
                "lvl2": spaces.Box(low=np.array([[-500., 0.]]*2*depth), 
                                    high=np.array([[500., 500.]]*2*depth), 
                                    shape=(2*depth, 2), dtype=np.float32),
                
                # current position: 0-none, 1-long, 2-short
                "pos": spaces.Discrete(3)
            }
        )
        
        # action: [0,1,2] : 0-hold, 1-buy, 2-sell
        # if not in any position, 0 does nothing, 1 buys stock, 2 short sells
        # if currently long, 0/1 does nothing, 2 sells
        # if currently short, 0/2 does nothing, 1 buys back
        self.action_space = spaces.Discrete(3)

    def _get_mongo(self):
        collection_1 = f"{self.symbol}_10sec_ts_lvl1"
        collection_2 = f"{self.symbol}_10sec_ts_lvl2"
        start = f"{self.day}T{self.hr}:00:00"
        end = f"{self.day}T{self.hr}:59:50"
        query = {'$and': [{'CurTime': {'$gte': start}}, {'CurTime': {'$lte': end}}]}
        df_1 = pd.DataFrame(list(self.mongo.mongoDB[collection_1].find(query)))
        df_2 = pd.DataFrame(list(self.mongo.mongoDB[collection_2].find(query)))
        df = pd.merge(df_1, df_2, on='CurTime')
    
    def _get_obs(self):
        return

    def _get_info(self):
        return

    def step(self, action):
        return

    def reset(self):
        self.balance = 30000
        self.cur_pos = 0
    
    def render(self):
        return