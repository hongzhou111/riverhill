'''
https://github.com/notadamking/Stock-Trading-Environment

setup:
1. pip install tensorflow=1.15
2. pip install stable_baseline3

History
2022/12/02 - change to stable_baseline3
  pip install stable_baseline3
2022/12/05 -
    1. create new funcs:  get_buy_price, get_sell_price, get_reward_buy_price, get_reward_sell_price
        get_buy_price:  if macd is normal,  price = next 2 day between open and low
                        if macd is threshold, price = next 1 dday between open and low
        get_sell_price: if macd is normal,  price = next 2 day between open and high
                        if macd is threshold, price = next 1 dday between open and high
        get_reward_buy_price:  if macd is normal,  price = next 2 day between open and low from the next reverse crossing
                        if macd is threshold, price = next 1 dday between open and low from the next reverse crossing
        get_reward_sell_price:  if macd is normal,  price = next 2 day between open and high from the next reverse crossing
                        if macd is threshold, price = next 1 dday between open and high from the next reverse crossing
    2. test run these params:
        macd (3,7,19), (6,13,9), (12.26,9), (24,52,9)
        threshold (0,0.2, 0.5)
        min_len (0, 6)
        save results to mongodb

        add two params to StockTradingEnv:
            macd_threshhold = 0.2
            macd_min_len = 6
    3. Ignore volume predictor
    4. recaculate reward
      buy - reward = shares_held * (reward_price - current_price)
      sell - reward = shares_seld * (current_price - reward_price)
      hold - if shares_held > 0 reward = shares_held * (reward_price - current_price)
             else reward = (balance / current_price) * (reward_price - current_price)
2023/03/26  import from test_rl_macd_v2, use minute data
'''

#import warnings
#warnings.filterwarnings("ignore")
#import os
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
#import tensorflow as tf
#tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from datetime import datetime
import random
#import json
import gym
from gym import spaces
#import pandas as pd
import numpy as np
import pandas as pd
#import datetime as datetime
#from stable_baselines.common.policies import MlpPolicy
#from stable_baselines.common.vec_env import DummyVecEnv
#from stable_baselines import PPO2
#from stable_baselines3.common.policies import MlpPolicy
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3 import PPO
#import yfinance as yf
from test_stockstats_v2 import StockStats
import json
from test_mongo import MongoExplorer
#from test_yahoo import QuoteExplorer
#from test_g20_v2 import StockScore
import os.path

import warnings
warnings.filterwarnings("ignore")

class StockTradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, ticker, short=12, long=26, signal=9, aaod=datetime.now().strftime("%Y-%m-%d"), macd_threshold=0, macd_min_len=0, interval='1m'):
        super(StockTradingEnv, self).__init__()

        #self.MAX_ACCOUNT_BALANCE = 2147483647
        #self.MAX_NUM_SHARES = 2147483647
        self.MAX_SHARE_PRICE = 10000
        #self.MAX_MACD = 1
        # self.MAX_OPEN_POSITIONS = 5
        self.MAX_STEPS = 200000
        self.MAX_REWARD = 100000  # 2147483647

        # self.INITIAL_ACCOUNT_BALANCE_MIN = 100000
        # self.INITIAL_ACCOUNT_BALANCE_MAX = 1000000
        # self.REWARD_PERIOD = 200
        # self.BUY_REWARD_LOOK_FORWARD = 200
        # self.SELL_REWARD_LOOK_FORWARD = 200
        # self.HOLD_REWARD_LOOK_FORWARD = 200

        if interval == 'no':
            self.ss = None
            self.c2 = None
        else:
            #short = 12
            #long = 26
            #signal = 9
            ss = StockStats(ticker, aaod, interval)
            ss.macd(short, long, signal)
            self.ss = ss.stock
            #self.c = ss.macd_crossing()
            #self.c = ss.macd_crossing_by_threshold()
            #self.c2 = ss.macd_crossing_by_threshold()
            self.c2 = ss.macd_crossing_by_threshold_min_len(threshold=macd_threshold, min_len=macd_min_len)


        #pd.set_option('display.max_rows', None)
        #pd.set_option('display.max_columns', None)
        #pd.set_option('display.width', None)
        #pd.set_option('display.max_colwidth', None)
        #print(self.c2)
        #ss.rsi()
        #ss.bollinger()

        #df = yf.Ticker(ticker).history(period="max")
        ## df = stock.history(start="2015-09-11", end="2020-09-11")
        #df = df.reset_index()
        #df = df.sort_values('Date')

        #self.df = df
        #self.df = ss.stock
        #self.df = self.df.reset_index()
        #self.df = self.df.sort_values('date')
        #self.df = self.df.fillna(0)

        #self.reward_range = (0, MAX_ACCOUNT_BALANCE)

        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)

        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(2, 5), dtype=np.float16)

        self.ticker = ticker
        #self.run_date = datetime.now().strftime("%Y-%m-%d")
        self.run_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        self.render_list = []

    def _next_observation(self):
        # Get the stock data points for the last 00 days and scale to between 0-1
        frame = np.array([
            #self.df.loc[self.current_step - 59: self.current_step, 'open'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'high'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'low'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'close'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'volume'].values / MAX_NUM_SHARES,
            self.c2.loc[self.current_step - 4: self.current_step, 'accum'].values,
            self.c2.loc[self.current_step - 4: self.current_step, 'len'].values,
            #self.c.loc[self.current_step - 4: self.current_step, 'accum'].values,
            #self.c.loc[self.current_step - 4: self.current_step, 'len'].values,
            #self.df.loc[self.current_step - 59: self.current_step, 'h_s'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'rsi_14'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'bb_value'].values,
        ])

        # Append additional data and scale each value to between 0-1
        #obs = np.append(frame, [[
        #    self.balance / MAX_ACCOUNT_BALANCE,
        #    self.max_net_worth / MAX_ACCOUNT_BALANCE,
        #    self.shares_held / MAX_NUM_SHARES,
        #    self.cost_basis / MAX_SHARE_PRICE,
        #    self.total_shares_sold / MAX_NUM_SHARES,
        #    self.total_sales_value / (MAX_NUM_SHARES * MAX_SHARE_PRICE),
        #]], axis=0)

        #return obs
        #print(self.current_step)
        #print(frame)
        return frame

    def get_buy_price(self):
        #if macd is normal, price = next 2 day between open and low
        #if macd is threshold, price = next 1 dday between open and low
        if self.c2.loc[self.current_step, 'cross_type'] == 'threshold':
            buy_price = random.uniform(self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_low"])
        else:
            #next_date_index = self.c2.loc[self.current_step, "index"] + 2
            next_date_index = self.c2.loc[self.current_step, "index"] + 1
            #print(self.c2.loc[self.current_step], next_date_index, self.ss.iloc[next_date_index])
            #buy_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["low"])
            buy_price = self.ss.iloc[next_date_index]["close"]      #, self.ss.iloc[next_date_index]["low"])

        #print(self.current_step, buy_price)

        # self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
        # self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
        # self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
        return buy_price

    def get_sell_price(self):
        #if macd is normal, price = next 2 day between open and high
        #if macd is threshold, price = next 1 dday between open and high
        if self.c2.loc[self.current_step, 'cross_type'] == 'threshold':
            sell_price = random.uniform(self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_high"])
        else:
            #next_date_index = self.c2.loc[self.current_step, "index"] + 2
            #sell_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["high"])
            next_date_index = self.c2.loc[self.current_step, "index"] + 1
            sell_price = self.ss.iloc[next_date_index]["close"]     #, self.ss.iloc[next_date_index]["high"])

        return sell_price

    def get_reward_buy_price(self):
        #if macd is normal, price = next 2 day between open and low from the next reverse crossing
        #if macd is threshold, price = next 1 dday between open and low from the next reverse crossing
        current_macd_sign = self.c2.loc[self.current_step, "macd_sign"]
        reward_target = self.current_step + 1
        reward_macd_sign = self.c2.loc[reward_target, "macd_sign"]
        while reward_macd_sign == current_macd_sign and reward_target < len(self.c2.loc[:, 'close'].values)-1:
            reward_target = reward_target + 1
            reward_macd_sign = self.c2.loc[reward_target, "macd_sign"]

        if self.c2.loc[reward_target, 'cross_type'] == 'threshold':
            reward_buy_price = random.uniform(self.c2.loc[reward_target, "next_open"], self.c2.loc[reward_target, "next_low"])
        else:
            #next_date_index = self.c2.loc[reward_target, "index"] + 2
            #reward_buy_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["low"])
            next_date_index = self.c2.loc[reward_target, "index"] + 1
            reward_buy_price = self.ss.iloc[next_date_index]["close"]       #, self.ss.iloc[next_date_index]["low"])
            #print(self.current_step, 'buy', reward_target, next_date_index, reward_buy_price)

        return reward_buy_price

    def get_reward_sell_price(self):
        #if macd is normal, price = next 2 day between open and high from the next reverse crossing
        #if macd is threshold, price = next 1 dday between open and high from the next reverse crossing
        current_macd_sign = self.c2.loc[self.current_step, "macd_sign"]
        reward_target = self.current_step + 1
        reward_macd_sign = self.c2.loc[reward_target, "macd_sign"]
        while reward_macd_sign == current_macd_sign and reward_target < len(self.c2.loc[:, 'close'].values)-1:
            reward_target = reward_target + 1
            reward_macd_sign = self.c2.loc[reward_target, "macd_sign"]

        if self.c2.loc[reward_target, 'cross_type'] == 'threshold':
            reward_sell_price = random.uniform(self.c2.loc[reward_target, "next_open"],self.c2.loc[reward_target, "next_high"])
        else:
            #next_date_index = self.c2.loc[reward_target, "index"] + 2
            #reward_sell_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["high"])
            next_date_index = self.c2.loc[reward_target, "index"] + 1
            reward_sell_price = self.ss.iloc[next_date_index]["close"]      #, self.ss.iloc[next_date_index]["high"])
            #print(self.current_step, 'sell', reward_target, next_date_index, reward_sell_price)

        return reward_sell_price

    def _take_action(self, action):
        # Set the current price to a random price within the time step
        #current_price = random.uniform(
            #self.c.loc[self.current_step, "next_open"], self.c.loc[self.current_step, "next_close"])
            #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
            #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
            #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
        #self.current_price = current_price
        reward = 0

        action_type = action[0]
        amount = action[1]
        if amount != amount: amount = 0  #check if amount is NaN

        #if self.c.loc[self.current_step, 'len'] < 5:
        #    action_type = 3
        #    return reward

        #print('current_step:', self.current_step)
        if action_type < 1:
            # Buy amount % of balance in shares
            #current_price = random.uniform(
            #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_low"])
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
            current_price = self.get_buy_price()
            self.current_price = current_price

            total_possible = self.balance / current_price
            #total_possible = int(self.balance / current_price)
            #shares_bought = int(total_possible * amount)
            shares_bought = total_possible
            prev_cost = self.cost_basis * self.shares_held
            additional_cost = shares_bought * current_price

            self.balance -= additional_cost
            if self.shares_held + shares_bought > 0:
                self.cost_basis = (prev_cost + additional_cost) / (self.shares_held + shares_bought)
            self.shares_held += shares_bought

            #reward_target = self.current_step + BUY_REWARD_LOOK_FORWARD if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / BUY_REWARD_LOOK_FORWARD
            #reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            #if reward_target < len(self.c2.loc[:, 'close'].values):
            #    reward_price = self.c2.loc[reward_target, "close"]
            #else:
            #    reward_price = current_price
            reward_price = self.get_reward_sell_price()
            #reward_price = self.c.loc[reward_target, "next_close"]
            #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
            #reward = reward_look_forward_adjuster * shares_bought * (reward_price - current_price) / self.MAX_REWARD
            reward = reward_look_forward_adjuster * self.shares_held * (reward_price - current_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster  * (reward_price - current_price) / self.MAX_REWARD

        elif action_type < 2:
            # Sell amount % of shares held
            #current_price = random.uniform(
            #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
            current_price = self.get_sell_price()
            self.current_price = current_price

            #shares_sold = int(self.shares_held * amount)
            shares_sold = self.shares_held
            self.balance += shares_sold * current_price
            self.shares_held -= shares_sold
            self.total_shares_sold += shares_sold
            self.total_sales_value += shares_sold * current_price

            #reward_target = self.current_step + SELL_REWARD_LOOK_FORWARD if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / SELL_REWARD_LOOK_FORWARD
            #reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            #reward_price = self.c.loc[reward_target, "close"]
            #reward_price = self.c.loc[reward_target, "next_close"]
            #if reward_target < len(self.c2.loc[:, 'close'].values):
            #    reward_price = self.c2.loc[reward_target, "close"]
            #else:
            #    reward_price = current_price
            reward_price = self.get_reward_buy_price()
            #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
            reward = reward_look_forward_adjuster * shares_sold * (current_price - reward_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster * (current_price - reward_price) / self.MAX_REWARD
            # if shares_sold > 0:
            #    reward = (shares_sold * current_price + self.balance - self.net_worth) / (self.cost_basis * MAX_REWARD)
        else:
            # hold
            #reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            #reward_price = self.c.loc[reward_target, "close"]
            #if reward_target < len(self.c2.loc[:, 'close'].values):
            #    reward_price = self.c2.loc[reward_target, "close"]
            #else:
            #    reward_price = current_price
            #reward_price = self.c.loc[reward_target, "next_close"]

            if self.shares_held > 0:
                #current_price = random.uniform(self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_high"])
                current_price = self.get_sell_price()
                # self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                # self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
                self.current_price = current_price

                #total_possible = int(self.balance / current_price)
                #shares_bought = int(total_possible * amount)

                reward_price = self.get_reward_buy_price()
                #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
                #reward = reward_look_forward_adjuster * shares_bought * (reward_price - current_price) / self.MAX_REWARD
                reward = reward_look_forward_adjuster * self.shares_held * (reward_price - current_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster * 100 * (reward_price - current_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (reward_price - current_price) / self.MAX_REWARD
            else:
                #current_price = random.uniform(self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_low"])
                current_price = self.get_buy_price()
                # self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                # self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
                self.current_price = current_price

                #shares_sold = int(self.shares_held * amount)
                shares_bought = self.balance / current_price
                #shares_bought = int(self.balance / current_price)

                reward_price = self.get_reward_sell_price()
                #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
                #reward = reward_look_forward_adjuster * shares_sold * (current_price - reward_price) / self.MAX_REWARD
                reward = reward_look_forward_adjuster * shares_bought * (current_price - reward_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster * 100 * (current_price - reward_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (current_price - reward_price) / self.MAX_REWARD

            #reward = (reward_price - current_price) / MAX_REWARD

        self.net_worth = self.balance + self.shares_held * current_price

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.shares_held == 0:
            self.cost_basis = 0

        #print(self.current_step, action, self.balance, self.shares_held, self.net_worth, current_price, reward_price, reward)
        return reward

    def step(self, action):
        # Execute one time step within the environment
        reward = self._take_action(action)

        self.current_step += 1

        #delay_modifier = (self.current_step / MAX_STEPS)
        #reward = self.balance * delay_modifier

        done = self.net_worth <= 0

        if self.current_step >= len(self.c2.loc[:, 'open'].values) - 2:
            #self.current_step = 100
            #self.current_step = random.randint(100, len(self.df.loc[:, 'open'].values) - 1)
            done = True

        obs = self._next_observation()
        #print(self.current_step, reward, done)
        return obs, reward, done, {'step': self.current_step}

    def reset(self):
        # Reset the state of the environment to an initial state
        #self.initial_account_balance = random.randint(INITIAL_ACCOUNT_BALANCE_MIN, INITIAL_ACCOUNT_BALANCE_MAX)
        self.initial_account_balance = 100000

        self.balance = self.initial_account_balance
        self.net_worth = self.initial_account_balance
        self.max_net_worth = self.initial_account_balance
        self.shares_held = 0
        self.cost_basis = 0
        self.total_shares_sold = 0
        self.total_sales_value = 0
        self.render_list = []

        # Set the current step to a random point within the data frame
        self.current_step = random.randint(
            #60, 400)
            #5, len(self.c2.loc[:, 'open'].values) - 10)
            5, len(self.c2.loc[:, 'open'].values) - 2)

        #print('reset', self.current_step)

        return self._next_observation()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        #profit = self.net_worth - INITIAL_ACCOUNT_BALANCE
        profit = self.net_worth - self.initial_account_balance
        print(f'Step: {self.current_step-1}')
        print(f'Balance: {self.balance}')
        print(
            f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})')
        print(
            f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})')
        print(
            f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})')
        print(f'Profit: {profit}')

        #print(f'State: {self.c.loc[self.current_step-1]}')
        print(f'date: {self.c2.loc[self.current_step - 1]["date"]}')
        print(f'close: {self.c2.loc[self.current_step - 1]["close"]}')
        print(f'current_price: {self.current_price}')
        print(f'accum: {self.c2.loc[self.current_step - 1]["accum"]}')
        print(f'len: {self.c2.loc[self.current_step - 1]["len"]}')
        #print(f'Date: {self.c.loc[self.current_step-1, "date"]}')
        #print(f'Close: {self.c.loc[self.current_step-1, "close"]}')

    def _next_observation_test(self):
        # Get the stock data points for the last 00 days and scale to between 0-1
        frame = np.array([
            #self.df.loc[self.current_step - 59: self.current_step, 'open'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'high'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'low'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'close'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'volume'].values / MAX_NUM_SHARES,
            self.c2.loc[self.current_step - 4: self.current_step, 'accum'].values,
            self.c2.loc[self.current_step - 4: self.current_step, 'len'].values,
            #self.df.loc[self.current_step - 59: self.current_step, 'h_s'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'rsi_14'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'bb_value'].values,
        ])

        # Append additional data and scale each value to between 0-1
        #obs = np.append(frame, [[
        #    self.balance / MAX_ACCOUNT_BALANCE,
        #    self.max_net_worth / MAX_ACCOUNT_BALANCE,
        #    self.shares_held / MAX_NUM_SHARES,
        #    self.cost_basis / MAX_SHARE_PRICE,
        #    self.total_shares_sold / MAX_NUM_SHARES,
        #    self.total_sales_value / (MAX_NUM_SHARES * MAX_SHARE_PRICE),
        #]], axis=0)

        #return obs
        return frame

    def _take_test(self, action):
        # Set the current price to a random price within the time step
        #current_price = random.uniform(
            #self.c.loc[self.current_step, "next_open"], self.c.loc[self.current_step, "next_close"])
            #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
            #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
            #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
        #self.current_price = current_price
        #reward = 0      # for hold, reward = 0

        action_type = action[0]
        amount = action[1]

        #if self.c.loc[self.current_step, 'len'] < 5:
        #    action_type = 3
        #    return reward

        if action_type < 1:
            # Buy amount % of balance in shares
            #current_price = random.uniform(
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
            #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_low"])
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
            current_price = self.get_buy_price()
            self.current_price = current_price

            total_possible = self.balance / current_price
            #total_possible = int(self.balance / current_price)
            #shares_bought = int(total_possible * amount)
            shares_bought = total_possible
            prev_cost = self.cost_basis * self.shares_held
            additional_cost = shares_bought * current_price

            self.balance -= additional_cost
            if self.shares_held + shares_bought > 0:
                self.cost_basis = (prev_cost + additional_cost) / (self.shares_held + shares_bought)
            self.shares_held += shares_bought

            #reward_target = self.current_step + BUY_REWARD_LOOK_FORWARD if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / BUY_REWARD_LOOK_FORWARD
            #reward_target = self.current_step + 1
            #reward_look_forward_adjuster = 1
            #reward_price = self.c.loc[reward_target, "close"]
            #reward_price = self.c.loc[reward_target, "next_close"]
            #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
            #reward = reward_look_forward_adjuster * shares_bought * (reward_price - current_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster  * (reward_price - current_price) / self.MAX_REWARD

        elif action_type < 2:
            # Sell amount % of shares held
            #current_price = random.uniform(
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_close"])
            #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
            current_price = self.get_sell_price()
            self.current_price = current_price

            #shares_sold = int(self.shares_held * amount)
            shares_sold = self.shares_held
            self.balance += shares_sold * current_price
            self.shares_held -= shares_sold
            self.total_shares_sold += shares_sold
            self.total_sales_value += shares_sold * current_price

            #reward_target = self.current_step + SELL_REWARD_LOOK_FORWARD if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / SELL_REWARD_LOOK_FORWARD
            #reward_target = self.current_step + 1
            #reward_look_forward_adjuster = 1
            #reward_price = self.c.loc[reward_target, "close"]
            #reward_price = self.c.loc[reward_target, "next_close"]
            #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
            #reward = reward_look_forward_adjuster * shares_sold * (current_price - reward_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster * (current_price - reward_price) / self.MAX_REWARD
            # if shares_sold > 0:
            #    reward = (shares_sold * current_price + self.balance - self.net_worth) / (self.cost_basis * MAX_REWARD)
        else:
            # hold
            #reward_target = self.current_step + 1
            #reward_look_forward_adjuster = 1
            #reward_price = self.c.loc[reward_target, "close"]
            #reward_price = self.c.loc[reward_target, "next_close"]
            if self.shares_held > 0:
                #current_price = random.uniform(
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_close"])
                #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_high"])
                # self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                # self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                # self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
                current_price = self.get_sell_price()
                self.current_price = current_price

                #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
                #reward = reward_look_forward_adjuster * 100 * (reward_price - current_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (reward_price - current_price) / self.MAX_REWARD
            else:
                #current_price = random.uniform(
                #self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                #self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_close"])
                #    self.c2.loc[self.current_step, "next_open"], self.c2.loc[self.current_step, "next_low"])
                # self.c.loc[self.current_step, "next_low"], self.c.loc[self.current_step, "next_high"])
                # self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
                # self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
                current_price = self.get_buy_price()
                self.current_price = current_price

                #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
            #    reward = reward_look_forward_adjuster * 100 * (current_price - reward_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (current_price - reward_price) / self.MAX_REWARD

            #reward = (reward_price - current_price) / MAX_REWARD

        self.net_worth = self.balance + self.shares_held * current_price

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.shares_held == 0:
            self.cost_basis = 0

        #print(action, self.balance, self.shares_held, reward)
        #return reward

    def render_to_screen(self, action=None):
        # Render the environment to the screen
        #profit = self.net_worth - INITIAL_ACCOUNT_BALANCE
        profit = self.net_worth - self.initial_account_balance
        print(f'Step: {self.current_step-1}')
        print(f'Balance: {self.balance}')
        print(
            f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})')
        print(
            f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})')
        print(
            f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})')
        print(f'Profit: {profit}')

        #print(f'State: {self.c.loc[self.current_step-1]}')
        print(f'date: {self.c2.loc[self.current_step - 1]["date"]}')
        print(f'close: {self.c2.loc[self.current_step - 1]["close"]}')
        print(f'current_price: {self.current_price}')
        print(f'accum: {self.c2.loc[self.current_step - 1]["accum"]}')
        print(f'len: {self.c2.loc[self.current_step - 1]["len"]}')
        #print(f'Date: {self.c.loc[self.current_step-1, "date"]}')
        #print(f'Close: {self.c.loc[self.current_step-1, "close"]}')

    def render_to_file(self, action=None):
        # Render the environment to the file
        f = open(self.save_loc + self.ticker + ".txt", "a")

        # profit = self.net_worth - INITIAL_ACCOUNT_BALANCE
        profit = self.net_worth - self.initial_account_balance
        f.write(f'Step: {self.current_step - 1}\n')
        f.write(f'Balance: {self.balance}\n')
        f.write(f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})\n')
        f.write(f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})\n')
        f.write(f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})\n')
        f.write(f'Profit: {profit}\n')
        f.write(f'date: {self.c2.loc[self.current_step - 1]["date"]}\n')
        f.write(f'close: {self.c2.loc[self.current_step - 1]["close"]}\n')
        f.write(f'current_price: {self.current_price}\n')
        f.write(f'accum: {self.c2.loc[self.current_step - 1]["accum"]}\n')
        f.write(f'len: {self.c2.loc[self.current_step - 1]["len"]}\n')
        f.write(str(action) + '\n')
        f.close()
        # print(f'Date: {self.c.loc[self.current_step-1, "date"]}')
        # print(f'Close: {self.c.loc[self.current_step-1, "close"]}')

    def render_to_db(self, action=None):
        # Render the environment to the file
        step_result = {
            'symbol':  self.ticker,
            'run_date': self.run_date,
            'step': self.current_step - 1,
            'balance': self.balance,
            'shares_held': self.shares_held,
            'Net worth':  self.net_worth,
            'date': self.c2.loc[self.current_step - 1]["date"],
            'close': self.c2.loc[self.current_step - 1]["close"],
            'current_price': self.current_price,
            'accum': self.c2.loc[self.current_step - 1]["accum"],
            'len': self.c2.loc[self.current_step - 1]["len"],
            'action': float(action[0]),
            'vol': float(action[1])
        }
        mongo = MongoExplorer()
        mongo.mongoDB['stock_rl_steps'].replace_one({'symbol': self.ticker, 'run_date': self.run_date, 'step': self.current_step-1}, step_result, upsert=True)
        #print(step_result)


    def render_to_df(self, action=None):
        # Render the environment to the file
        step_result = {
            'symbol': self.ticker,
            'run_date': self.run_date,
            'step': self.current_step - 1,
            'balance': self.balance,
            'shares_held': self.shares_held,
            'net_worth': self.net_worth,
            'date': self.c2.loc[self.current_step - 1]["date"],
            'close': self.c2.loc[self.current_step - 1]["close"],
            'current_price': self.current_price,
            #'next_close': self.c2.loc[self.current_step - 1]["next_close"],
            'accum': self.c2.loc[self.current_step - 1]["accum"],
            'len': self.c2.loc[self.current_step - 1]["len"],
            'r': self.c2.loc[self.current_step-1]["r"],
            'action': float(action[0]),
            'vol': float(action[1])
        }
        self.render_list.append(step_result)

class StockRL:
    def __init__(self, ticker, vb=0, short=12, long=26, signal=9, save_loc='./rl/test_rl_', aaod=datetime.now().strftime("%Y-%m-%d"), macd_threshold=0, macd_min_len=0, interval='1m'):           #vb = verboss is 1 or 0
        self.ticker = ticker
        self.vb = vb
        # The algorithms require a vectorized environment to run
        self.stock_env = StockTradingEnv(ticker, short, long, signal, aaod, macd_threshold, macd_min_len, interval)
        # self.env = DummyVecEnv([lambda: StockTradingEnv(ticker)])
        self.env = DummyVecEnv([lambda: self.stock_env])
        #self.model = PPO2(MlpPolicy, self.env, verbose=self.vb)
        self.model = PPO('MlpPolicy', self.env, verbose=self.vb)
        self.save_loc = save_loc

        self.short = short
        self.long = long
        self.signal = signal
        self.macd_threshold = macd_threshold
        self.macd_min_len = macd_min_len

    def train(self, save=False):
        self.model.learn(total_timesteps=20000)
        if save is True:
            self.model.save(self.save_loc+self.ticker)

    def retrain(self, save=False):
        #self.model = PPO2.load(self.save_loc+self.ticker, self.env)
        self.model = PPO.load(self.save_loc+self.ticker, self.env)
        #self.model.set_env(self.env)
        self.model.learn(total_timesteps=20000)
        if save is True:
            self.model.save(self.save_loc+self.ticker)

    def reload(self):
        #self.model = PPO2.load(self.save_loc + self.ticker, self.env)
        self.model = PPO.load(self.save_loc + self.ticker, self.env)
        #self.model.set_env(self.env)

    def run(self, save_flag=None, run_id=0):
        obs = self.stock_env.reset()
        #self.stock_env.current_step = 10
        self.stock_env.current_step = 6
        # info = [{'step': 0}]
        i = 1
        # while info[0]['step'] < len(stock_env.c.loc[:, 'open'].values) - 2:
        while self.stock_env.current_step < len(self.stock_env.c2.loc[:, 'open'].values) - 1:
            #print(self.stock_env.current_step)
            #obs = self.stock_env._next_observation()
            obs = self.stock_env._next_observation_test()
            action, _states = self.model.predict(obs)
            # obs, rewards, done, info = env.step(action)
            #reward = self.stock_env._take_action(action)
            self.stock_env._take_test(action)
            self.stock_env.current_step += 1

            if save_flag == 'screen':
                self.stock_env.render_to_screen()
                print(action)
            if save_flag == 'file':
                self.stock_env.render_to_file(action)
            if save_flag == 'db':
                self.stock_env.render_to_db(action)
            if save_flag == 'df':
                self.stock_env.render_to_df(action)

            if i < 2:
                start = self.stock_env.net_worth
                start_date = self.stock_env.c2.loc[self.stock_env.current_step - 1, "date"]
                start_price = self.stock_env.c2.loc[self.stock_env.current_step - 1, "close"]
            i += 1
        # env.render()
        end = self.stock_env.net_worth
        end_date = self.stock_env.c2.loc[self.stock_env.current_step - 1, "date"]
        end_price = self.stock_env.c2.loc[self.stock_env.current_step - 1, "close"]
        dur = (end_date - start_date).total_seconds() / (365 * 24 * 60 * 60)
        model_gain = end / start
        model_perf = 10 ** (np.log10(end / start) / dur)
        buy_and_hold_gain = end_price / start_price
        buy_and_hold_perf = 10 ** (np.log10(end_price / start_price) / dur)

        self.stock_env.current_step = len(self.stock_env.c2.loc[:, 'open'].values) - 1
        #print(self.stock_env.current_step, self.stock_env.c.loc[self.stock_env.current_step, "date"],
        #      self.model.predict(self.stock_env._next_observation()))
        #print('test rl', self.ticker)
        #print(self.stock_env.c)
        action, _states = self.model.predict(self.stock_env._next_observation_test())

        result = {
            'model_run_date': self.stock_env.run_date,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'duration': dur,
            'model_gain': model_gain,
            'model_perf': model_perf,
            'buy_and_hold_gain': buy_and_hold_gain,
            'buy_and_hold_perf': buy_and_hold_perf,
            'model_score': model_perf / buy_and_hold_perf,
            'model_gain_score': model_gain / buy_and_hold_gain,
            'predict_date': self.stock_env.c2.loc[self.stock_env.current_step, 'date'].strftime("%Y-%m-%d"),
            'predict_macd_accum':  self.stock_env.c2.loc[self.stock_env.current_step, 'accum'],
            'predict_macd_len':  int(self.stock_env.c2.loc[self.stock_env.current_step, 'len']),
            'predict_action': float(action[0]),
            'predict_vol': float(action[1])
        }
        #print(result)

        mr = self.run_macd()
        result['MACD_gain'] = mr['MACD_gain']
        result['MACD_perf'] = mr['MACD_perf']

        if save_flag == 'screen':
            # print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}')
            # print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}')
            print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}')
            print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}')
            #print(json.dumps(result))

        if save_flag == 'file':
            f = open(self.save_loc + self.ticker + ".txt", "a")
            f.write(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}\n')
            f.write(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}\n')
            f.write(json.dumps(result))
            f.write('\n\ns')
            f.close()

        if save_flag == 'df':
            return self.stock_env.render_list, result

        if save_flag == 'stock_min_rl_macd_perf_results':
            result['symbol'] = self.ticker
            result['run_id'] = run_id
            result['short'] = self.short
            result['long'] = self.long
            result['signal'] = self.signal
            result['macd_threshold'] = self.macd_threshold
            result['macd_min_len'] = self.macd_min_len

            #print(result)
            mongo = MongoExplorer()
            mongo.mongoDB['stock_min_rl_macd_perf_results'].replace_one({'symbol': self.ticker, 'run_id': run_id}, result, upsert=True)

            r = {
                'symbol': self.ticker,
                'run_id': run_id,
                'short': self.short,
                'long': self.long,
                'signal': self.signal,
                'macd_threshold': self.macd_threshold,
                'macd_min_len': self.macd_min_len,
                'model_score': model_perf / buy_and_hold_perf,
                'model_gain_score': model_gain / buy_and_hold_gain,
                'model_run_date': self.stock_env.run_date,
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'duration': dur,
                'model_gain': model_gain,
                'model_perf': model_perf,
                'buy_and_hold_gain': buy_and_hold_gain,
                'buy_and_hold_perf': buy_and_hold_perf,
                'macd_gain': mr['MACD_gain'],
                'macd_perf': mr['MACD_perf']
            }
            result = pd.DataFrame.from_records([r])

        return result

    def run_macd(self, save_flag=None, run_id=0):
        obs = self.stock_env.reset()
        #self.stock_env.current_step = 10
        self.stock_env.current_step = 6
        i = 1
        # while info[0]['step'] < len(stock_env.c.loc[:, 'open'].values) - 2:
        while self.stock_env.current_step < len(self.stock_env.c2.loc[:, 'open'].values) - 1:
            if self.stock_env.c2.loc[self.stock_env.current_step, "macd_sign"] == -1:
                action = [0,1]
            elif self.stock_env.c2.loc[self.stock_env.current_step, "macd_sign"] == 1:
                action = [1,1]
            else:
                action = [2,1]

            self.stock_env._take_test(action)
            self.stock_env.current_step += 1

            if save_flag == 'screen':
                self.stock_env.render_to_screen()
                print(action)

            if i < 2:
                start = self.stock_env.net_worth
                start_date = self.stock_env.c2.loc[self.stock_env.current_step - 1, "date"]
                start_price = self.stock_env.c2.loc[self.stock_env.current_step - 1, "close"]
            i += 1
        # env.render()
        end = self.stock_env.net_worth
        end_date = self.stock_env.c2.loc[self.stock_env.current_step - 1, "date"]
        end_price = self.stock_env.c2.loc[self.stock_env.current_step - 1, "close"]
        dur = (end_date - start_date).total_seconds() / (365 * 24 * 60 * 60)
        macd_gain = end / start
        macd_perf = 10 ** (np.log10(end / start) / dur)

        if save_flag == 'screen':
            print(f'MACD Perf:          {start_date} - {end_date}   {dur}   {end / start}     {macd_perf}')
            #print(json.dumps(result))

        result = {
            'MACD_run_date': self.stock_env.run_date,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'duration': dur,
            'MACD_gain': macd_gain,
            'MACD_perf': macd_perf,
        }
        return result

if __name__ == '__main__':
    ticker = 'TSLA'     #'GOOGL'     #'EVBG'     #'BAND'     #'NFLX'         #'APPN'     #'GRWG'     #'ACMR'     #'MDB'     #'CDLX'       #'RCM'     #'FB'     #'AAPL'     #'ANTM'     #'AMZN'     #'TSLA'   #'BAND'     #'ROKU'     #'SHOP'     #'TWLO'

    #s = StockRL(ticker, 0, 3, 7, 19, interval='1d')
    #s = StockRL(ticker, 0, 3, 7, 19, save_loc='./rl_min/test_rl_', interval='1m')
    s = StockRL(ticker, 0, 6, 13, 9, save_loc='./rl_min/test_rl_', interval='1m')
    #s.train(save=True)
    #s.retrain(save=True)
    #s.reload()
    #print(s.run())
    #print(s.run('db'))
    file_path = s.save_loc + ticker + '.zip'
    #s.retrain(save=True) if os.path.exists(file_path) else s.train(save=True)
    s.train(save=True)

    re = s.run('screen')
    s.run_macd('screen')
    print(re)

'''
TSLA - min data 3,7,19
MACD Perf:          2023-03-28 10:36:00-04:00 - 2023-03-28 15:49:00-04:00   0.0005955098934550989   1.0019196278381348     25.038454920315033
{'model_run_date': '2023-03-28-16-19-06', 'start_date': '2023-03-28', 'end_date': '2023-03-28', 'duration': 0.0005955098934550989, 'model_gain': 1.0082538691711427, 'model_perf': 987848.0344487781, 'buy_and_hold_gain': 1.0034528867258263, 'buy_and_hold_perf': 326.4297727029072, 'model_score': 3026.219165822984, 'predict_date': '2023-03-28', 'predict_macd_accum': 0.25225727021455585, 'predict_macd_len': 5, 'predict_action': 1.4587864875793457, 'predict_vol': 0.05342584848403931}

MACD Perf:          2023-03-20 10:55:00-04:00 - 2023-03-28 15:49:00-04:00   0.02247716894977169   0.956352592010498     0.13731075044956736
{'model_run_date': '2023-03-28-16-28-44', 'start_date': '2023-03-20', 'end_date': '2023-03-28', 'duration': 0.02247716894977169, 'model_gain': 1.0306835731506347, 'model_perf': 3.836556669547518, 'buy_and_hold_gain': 1.0198159107812328, 'buy_and_hold_perf': 2.3940357808669512, 'model_score': 1.6025477564742945, 'predict_date': '2023-03-28', 'predict_macd_accum': 0.2522572702145559, 'predict_macd_len': 5, 'predict_action': 0.5496585369110107, 'predict_vol': 0.0}

MACD Perf:          2023-03-22 10:52:00-04:00 - 2023-03-30 15:49:00-04:00   0.022482876712328768   1.035139201965332     4.646426648190674
{'model_run_date': '2023-03-30-20-06-25', 'start_date': '2023-03-22', 'end_date': '2023-03-30', 'duration': 0.022482876712328768, 'model_gain': 1.057855281829834, 'model_perf': 12.202205096190822, 'buy_and_hold_gain': 0.9925508305934112, 'buy_and_hold_perf': 0.7170809364097084, 'model_score': 17.016496292991704, 'predict_date': '2023-03-30', 'predict_macd_accum': 0.06909375309380672, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.0}

MACD Perf:          2023-03-23 10:12:00-04:00 - 2023-03-31 15:52:00-04:00   0.02256468797564688   1.0459324089050293     7.317160093993148
{'model_run_date': '2023-04-01-14-14-24', 'start_date': '2023-03-23', 'end_date': '2023-03-31', 'duration': 0.02256468797564688, 'model_gain': 1.1346930830383302, 'model_perf': 270.4258115817643, 'buy_and_hold_gain': 1.0383725861161592, 'buy_and_hold_perf': 5.305494924864809, 'model_score': 50.970892520202554, 'predict_date': '2023-03-31', 'predict_macd_accum': -0.01875483469305945, 'predict_macd_len': 1, 'predict_action': 0.2607571482658386, 'predict_vol': 1.0}

MACD Perf:          2023-03-24 10:37:00-04:00 - 2023-04-03 15:53:00-04:00   0.02799847792998478   0.9667827163696289     0.2992284360982987
{'model_run_date': '2023-04-03-16-23-12', 'start_date': '2023-03-24', 'end_date': '2023-04-03', 'duration': 0.02799847792998478, 'model_gain': 1.1054613975524903, 'model_perf': 35.90975642855778, 'buy_and_hold_gain': 1.0196375585617923, 'buy_and_hold_perf': 2.0028710267812833, 'model_score': 17.929140692731774, 'predict_date': '2023-04-03', 'predict_macd_accum': 0.34727517881244596, 'predict_macd_len': 5, 'predict_action': 0.40438389778137207, 'predict_vol': 0.0}

MACD Perf:          2023-03-27 10:42:00-04:00 - 2023-04-04 15:44:00-04:00   0.022492389649923897   0.9822555549621582     0.45113342842917303
{'model_run_date': '2023-04-04-19-58-44', 'start_date': '2023-03-27', 'end_date': '2023-04-04', 'duration': 0.022492389649923897, 'model_gain': 1.1171802711486816, 'model_perf': 137.8907467865706, 'buy_and_hold_gain': 0.9857933530291569, 'buy_and_hold_perf': 0.5293265592828444, 'model_score': 260.5022256457171, 'predict_date': '2023-04-04', 'predict_macd_accum': -0.11946180559247808, 'predict_macd_len': 3, 'predict_action': 0.31994548439979553, 'predict_vol': 0.6549206972122192}

MACD Perf:          2023-03-28 10:36:00-04:00 - 2023-04-05 15:46:00-04:00   0.022507610350076104   0.9727125560676015     0.292522527287329
{'model_run_date': '2023-04-05-17-49-28', 'start_date': '2023-03-28', 'end_date': '2023-04-05', 'duration': 0.022507610350076104, 'model_gain': 1.0682699756762561, 'model_perf': 18.80533611169515, 'buy_and_hold_gain': 0.9880193132069512, 'buy_and_hold_perf': 0.5853711112016603, 'model_score': 32.12549398464714, 'predict_date': '2023-04-05', 'predict_macd_accum': 0.0019879559347803083, 'predict_macd_len': 1, 'predict_action': 0.32943400740623474, 'predict_vol': 0.0}

MACD Perf:          2023-03-29 11:06:00-04:00 - 2023-04-06 15:54:00-04:00   0.022465753424657533   0.9549847687262544     0.12870572212297665
{'model_run_date': '2023-04-07-01-57-55', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.022465753424657533, 'model_gain': 1.101016830165519, 'model_perf': 72.50046601789948, 'buy_and_hold_gain': 0.9662557112856056, 'buy_and_hold_perf': 0.2169778922785813, 'model_score': 334.1375716048297, 'predict_date': '2023-04-06', 'predict_macd_accum': 0.13488062730271955, 'predict_macd_len': 4, 'predict_action': 0.0, 'predict_vol': 0.4013793468475342}

MACD Perf:          2023-03-29 11:06:00-04:00 - 2023-04-06 15:54:00-04:00   0.022465753424657533   0.9549847687262544     0.12870572212297665
{'model_run_date': '2023-04-07-02-02-17', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.022465753424657533, 'model_gain': 1.1128038546339174, 'model_perf': 116.46481206490297, 'buy_and_hold_gain': 0.9662557112856056, 'buy_and_hold_perf': 0.2169778922785813, 'model_score': 536.7588874693832, 'predict_date': '2023-04-06', 'predict_macd_accum': 0.13488062730271955, 'predict_macd_len': 4, 'predict_action': 0.022090762853622437, 'predict_vol': 0.7236120700836182}

MACD Perf:          2023-03-29 11:06:00-04:00 - 2023-04-06 15:54:00-04:00   0.022465753424657533   0.9549847687262544     0.12870572212297665
{'model_run_date': '2023-04-07-02-06-23', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.022465753424657533, 'model_gain': 1.21862995626561, 'model_perf': 6642.698329144762, 'buy_and_hold_gain': 0.9662557112856056, 'buy_and_hold_perf': 0.2169778922785813, 'model_score': 30614.632022584577, 'predict_date': '2023-04-06', 'predict_macd_accum': 0.13488062730271955, 'predict_macd_len': 4, 'predict_action': 0.6575024724006653, 'predict_vol': 0.752621054649353}

MACD Perf:          2023-03-30 10:59:00-04:00 - 2023-04-10 15:57:00-04:00   0.030703957382039574   0.9808811462253195     0.5332775953061848
{'model_run_date': '2023-04-10-20-11-14', 'start_date': '2023-03-30', 'end_date': '2023-04-10', 'duration': 0.030703957382039574, 'model_gain': 1.2357057706297367, 'model_perf': 985.3499276936737, 'buy_and_hold_gain': 0.9417594985590176, 'buy_and_hold_perf': 0.14166082680786232, 'model_score': 6955.697985796211, 'predict_date': '2023-04-10', 'predict_macd_accum': -0.032321091048257755, 'predict_macd_len': 1, 'predict_action': 0.0, 'predict_vol': 1.0}

MACD Perf:          2023-03-31 10:38:00-04:00 - 2023-04-11 15:48:00-04:00   0.030726788432267883   0.9864574785246883     0.6416248581090379
{'model_run_date': '2023-04-11-20-17-01', 'start_date': '2023-03-31', 'end_date': '2023-04-11', 'duration': 0.030726788432267883, 'model_gain': 1.2241916379984974, 'model_perf': 722.8521645096223, 'buy_and_hold_gain': 0.9333448019157607, 'buy_and_hold_perf': 0.10593118170060564, 'model_score': 6823.790246696451, 'predict_date': '2023-04-11', 'predict_macd_accum': -0.18685786807515442, 'predict_macd_len': 5, 'predict_action': 0.0, 'predict_vol': 0.0}

MACD Perf:          2023-04-03 10:26:00-04:00 - 2023-04-12 15:38:00-04:00   0.025251141552511416   0.9995649458641382     0.9829147993315328
{'model_run_date': '2023-04-12-16-41-32', 'start_date': '2023-04-03', 'end_date': '2023-04-12', 'duration': 0.025251141552511416, 'model_gain': 1.1573564002595131, 'model_perf': 326.1636676552029, 'buy_and_hold_gain': 0.9146815144951561, 'buy_and_hold_perf': 0.029255268124053435, 'model_score': 11148.886630337662, 'predict_date': '2023-04-12', 'predict_macd_accum': 0.3655156975793187, 'predict_macd_len': 8, 'predict_action': 0.39430877566337585, 'predict_vol': 0.0}

MACD Perf:          2023-04-04 10:37:00-04:00 - 2023-04-13 15:50:00-04:00   0.02525304414003044   1.0218267271862778     2.351428553797802
{'model_run_date': '2023-04-13-17-22-26', 'start_date': '2023-04-04', 'end_date': '2023-04-13', 'duration': 0.02525304414003044, 'model_gain': 1.1550142128084535, 'model_perf': 300.8896700277288, 'buy_and_hold_gain': 0.9620919787112431, 'buy_and_hold_perf': 0.21646653774490318, 'model_score': 1390.0054630259517, 'predict_date': '2023-04-13', 'predict_macd_accum': 0.055528671040204966, 'predict_macd_len': 3, 'predict_action': 3.0, 'predict_vol': 0.0}

MACD Perf:          2023-04-05 10:21:00-04:00 - 2023-04-14 15:44:00-04:00   0.0252720700152207   1.056636292015487     8.845410351352786
{'model_run_date': '2023-04-16-19-50-47', 'start_date': '2023-04-05', 'end_date': '2023-04-14', 'duration': 0.0252720700152207, 'model_gain': 1.1495903305015402, 'model_perf': 248.6867672027813, 'buy_and_hold_gain': 0.9874440405299997, 'buy_and_hold_perf': 0.6065446609531681, 'model_score': 410.00569819867343, 'predict_date': '2023-04-14', 'predict_macd_accum': -0.5726386951022444, 'predict_macd_len': 13, 'predict_action': 1.4552509784698486, 'predict_vol': 1.0}

ALNY
MACD Perf:          2023-03-27 11:28:00-04:00 - 2023-04-04 15:44:00-04:00   0.022404870624048705   0.9908597253417969     0.6637596691942094
{'model_run_date': '2023-04-04-20-20-11', 'start_date': '2023-03-27', 'end_date': '2023-04-04', 'duration': 0.022404870624048705, 'model_gain': 1.0313541633605956, 'model_perf': 3.96673822963235, 'buy_and_hold_gain': 1.0684629124146745, 'buy_and_hold_perf': 19.214318836105733, 'model_score': 0.20644698693031108, 'predict_date': '2023-04-04', 'predict_macd_accum': -0.3259188885707272, 'predict_macd_len': 6, 'predict_action': 1.4263696670532227, 'predict_vol': 0.0}

MACD Perf:          2023-03-29 10:30:00-04:00 - 2023-04-06 15:57:00-04:00   0.022539954337899543   0.9886820197242411     0.603509884095659
{'model_run_date': '2023-04-08-12-16-41', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.022539954337899543, 'model_gain': 1.2308857379431297, 'model_perf': 10059.346313416303, 'buy_and_hold_gain': 1.0848915433628474, 'buy_and_hold_perf': 37.14819301855165, 'model_score': 270.7896534400127, 'predict_date': '2023-04-06', 'predict_macd_accum': -0.06666388684056734, 'predict_macd_len': 1, 'predict_action': 1.253609299659729, 'predict_vol': 0.04852983355522156}

MACD Perf:          2023-03-30 11:21:00-04:00 - 2023-04-10 15:49:00-04:00   0.0306468797564688   0.967428781214653     0.33943114903111193
{'model_run_date': '2023-04-10-20-52-56', 'start_date': '2023-03-30', 'end_date': '2023-04-10', 'duration': 0.0306468797564688, 'model_gain': 1.221546371655083, 'model_perf': 685.2517195592899, 'buy_and_hold_gain': 1.0642964401958044, 'buy_and_hold_perf': 7.639169775505323, 'model_score': 89.70238123997724, 'predict_date': '2023-04-10', 'predict_macd_accum': -0.8384782212997839, 'predict_macd_len': 9, 'predict_action': 0.0, 'predict_vol': 0.0}

MACD Perf:          2023-03-31 10:45:00-04:00 - 2023-04-11 15:37:00-04:00   0.03069254185692542   0.9704146674249745     0.37588484323334875
{'model_run_date': '2023-04-11-21-47-54', 'start_date': '2023-03-31', 'end_date': '2023-04-11', 'duration': 0.03069254185692542, 'model_gain': 1.1814386579436735, 'model_perf': 228.68802156626273, 'buy_and_hold_gain': 1.0286825630943959, 'buy_and_hold_perf': 2.5127084752699758, 'model_score': 91.01255629811634, 'predict_date': '2023-04-11', 'predict_macd_accum': -1.1069623297865592, 'predict_macd_len': 18, 'predict_action': 0.0, 'predict_vol': 0.0}

MACD Perf:          2023-04-03 11:02:00-04:00 - 2023-04-12 15:54:00-04:00   0.025213089802130897   0.9771595322991682     0.3999550760115418
{'model_run_date': '2023-04-12-17-04-26', 'start_date': '2023-04-03', 'end_date': '2023-04-12', 'duration': 0.025213089802130897, 'model_gain': 1.145453306125432, 'model_perf': 218.352202957411, 'buy_and_hold_gain': 1.0030154759533199, 'buy_and_hold_perf': 1.1268427060154218, 'model_score': 193.77345373207987, 'predict_date': '2023-04-12', 'predict_macd_accum': -0.026586228172983534, 'predict_macd_len': 1, 'predict_action': 2.0047707557678223, 'predict_vol': 0.47849661111831665}

MACD Perf:          2023-04-04 11:02:00-04:00 - 2023-04-13 15:41:00-04:00   0.02518835616438356   0.9959110489877685     0.849873498235627
{'model_run_date': '2023-04-13-17-06-28', 'start_date': '2023-04-04', 'end_date': '2023-04-13', 'duration': 0.02518835616438356, 'model_gain': 1.1535813261056855, 'model_perf': 290.64915003883317, 'buy_and_hold_gain': 1.0351692449800616, 'buy_and_hold_perf': 3.944248607413933, 'model_score': 73.68935859988775, 'predict_date': '2023-04-13', 'predict_macd_accum': -1.0271777888247817, 'predict_macd_len': 14, 'predict_action': 0.0, 'predict_vol': 0.0}

MACD Perf:          2023-04-05 11:22:00-04:00 - 2023-04-14 15:17:00-04:00   0.025104642313546425   0.9589615763356834     0.18840070782531443
{'model_run_date': '2023-04-16-19-59-54', 'start_date': '2023-04-05', 'end_date': '2023-04-14', 'duration': 0.025104642313546425, 'model_gain': 1.1213761989053146, 'model_perf': 95.88669045102439, 'buy_and_hold_gain': 1.0021498347655762, 'buy_and_hold_perf': 1.0893084335789032, 'model_score': 88.02528971155617, 'predict_date': '2023-04-14', 'predict_macd_accum': 1.7714833078275078, 'predict_macd_len': 17, 'predict_action': 0.0, 'predict_vol': 0.23773692548274994}

AMZN
MACD Perf:          2023-03-27 10:38:00-04:00 - 2023-04-04 15:25:00-04:00   0.02246385083713851   0.9925720292663575     0.7175608833594689
{'model_run_date': '2023-04-04-20-45-11', 'start_date': '2023-03-27', 'end_date': '2023-04-04', 'duration': 0.02246385083713851, 'model_gain': 1.0215531790924073, 'model_perf': 2.5838151935913722, 'buy_and_hold_gain': 1.0571437952738796, 'buy_and_hold_perf': 11.867280309382386, 'model_score': 0.2177259764858325, 'predict_date': '2023-04-04', 'predict_macd_accum': -0.6629738085107535, 'predict_macd_len': 23, 'predict_action': 0.0, 'predict_vol': 0.029092788696289062}

MACD Perf:          2023-03-29 10:12:00-04:00 - 2023-04-06 15:54:00-04:00   0.022568493150684932   0.9847760771312022     0.5067422412123772
{'model_run_date': '2023-04-08-14-42-48', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.022568493150684932, 'model_gain': 1.1187263008195951, 'model_perf': 144.18904868746074, 'buy_and_hold_gain': 1.0223741998209899, 'buy_and_hold_perf': 2.665689805335311, 'model_score': 54.09070792815803, 'predict_date': '2023-04-06', 'predict_macd_accum': 0.01297973198793207, 'predict_macd_len': 1, 'predict_action': 0.12370282411575317, 'predict_vol': 0.12099908292293549}

ELV
MACD Perf:          2023-03-27 10:44:00-04:00 - 2023-04-04 15:52:00-04:00   0.022503805175038052   1.0038528063964844     1.1863459071944173
{'model_run_date': '2023-04-04-20-48-25', 'start_date': '2023-03-27', 'end_date': '2023-04-04', 'duration': 0.022503805175038052, 'model_gain': 1.029215057373047, 'model_perf': 3.595291205513817, 'buy_and_hold_gain': 1.0270775457574073, 'buy_and_hold_perf': 3.2780239216646296, 'model_score': 1.0967861405014014, 'predict_date': '2023-04-04', 'predict_macd_accum': -0.7745373755141036, 'predict_macd_len': 6, 'predict_action': 0.9069832563400269, 'predict_vol': 0.0}

NIO
MACD Perf:          2023-03-29 10:18:00-04:00 - 2023-04-06 15:41:00-04:00   0.02253234398782344   0.9044015351143568     0.011568734708174074
{'model_run_date': '2023-04-08-14-07-50', 'start_date': '2023-03-29', 'end_date': '2023-04-06', 'duration': 0.02253234398782344, 'model_gain': 1.1542039507835054, 'model_perf': 580.9518559876794, 'buy_and_hold_gain': 0.9305813723122289, 'buy_and_hold_perf': 0.041048572702518146, 'model_score': 14152.790651160463, 'predict_date': '2023-04-06', 'predict_macd_accum': -0.008446593837671306, 'predict_macd_len': 15, 'predict_action': 0.0, 'predict_vol': 0.4694051742553711}

MACD Perf:          2023-04-20 10:05:00-04:00 - 2023-04-28 15:55:00-04:00   0.02258371385083714   0.9758949252914404     0.33944599993635455
{'model_run_date': '2023-04-30-19-56-09', 'start_date': '2023-04-20', 'end_date': '2023-04-28', 'duration': 0.02258371385083714, 'model_gain': 0.9967641739543609, 'model_perf': 0.8663089194985224, 'buy_and_hold_gain': 0.982830461199769, 'buy_and_hold_perf': 0.4644672047443816, 'model_score': 1.8651670357981323, 'model_gain_score': 1.0141771274951965, 'predict_date': '2023-04-28', 'predict_macd_accum': -0.03913161071462773, 'predict_macd_len': 3, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9758949252914404, 'MACD_perf': 0.33944599993635455}

TSLA - min data 6,13,9
MACD Perf:          2023-04-21 11:21:00-04:00 - 2023-05-01 15:56:00-04:00   0.02792047184170472   0.9690314692329074     0.32409875178874115
{'model_run_date': '2023-05-01-21-08-54', 'start_date': '2023-04-21', 'end_date': '2023-05-01', 'duration': 0.02792047184170472, 'model_gain': 0.9964665200055027, 'model_perf': 0.8809280844646317, 'buy_and_hold_gain': 0.9868348658152919, 'buy_and_hold_perf': 0.6221002857713832, 'model_score': 1.416054781862559, 'model_gain_score': 1.0097601478462697, 'predict_date': '2023-05-01', 'predict_macd_accum': 0.014170228700177062, 'predict_macd_len': 2, 'predict_action': 0.0, 'predict_vol': 0.0, 'MACD_gain': 0.9690314692329074, 'MACD_perf': 0.32409875178874115}

'''
