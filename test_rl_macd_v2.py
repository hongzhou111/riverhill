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
from test_stockstats import StockStats
import json
from test_mongo import MongoExplorer
#from test_yahoo import QuoteExplorer
#from test_g20_v2 import StockScore

import warnings
warnings.filterwarnings("ignore")

class StockTradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, ticker, short=12, long=26, signal=9, aaod=datetime.now().strftime("%Y-%m-%d"), macd_threshold=0, macd_min_len=0):
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

        #short = 12
        #long = 26
        #signal = 9
        ss = StockStats(ticker, aaod)
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
            next_date_index = self.c2.loc[self.current_step, "index"] + 1
            #print(self.c2.loc[self.current_step], next_date_index, self.ss.iloc[next_date_index])
            buy_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["low"])

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
            next_date_index = self.c2.loc[self.current_step, "index"] + 1
            sell_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["high"])

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
            next_date_index = self.c2.loc[reward_target, "index"] + 1
            reward_buy_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["low"])
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
            next_date_index = self.c2.loc[reward_target, "index"] + 1
            reward_sell_price = random.uniform(self.ss.iloc[next_date_index]["open"], self.ss.iloc[next_date_index]["high"])
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

            total_possible = int(self.balance / current_price)
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
                shares_bought = int(self.balance / current_price)

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
            5, len(self.c2.loc[:, 'open'].values) - 10)

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

            total_possible = int(self.balance / current_price)
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
    def __init__(self, ticker, vb=0, short=12, long=26, signal=9, save_loc='./rl/test_rl_', aaod=datetime.now().strftime("%Y-%m-%d"), macd_threshold=0, macd_min_len=0):           #vb = verboss is 1 or 0
        self.ticker = ticker
        self.vb = vb
        # The algorithms require a vectorized environment to run
        self.stock_env = StockTradingEnv(ticker, short, long, signal, aaod, macd_threshold, macd_min_len)
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
        self.stock_env.current_step = 10
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
        dur = (end_date - start_date).days / 365
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
            'predict_date': self.stock_env.c2.loc[self.stock_env.current_step, 'date'].strftime("%Y-%m-%d"),
            'predict_macd_accum':  self.stock_env.c2.loc[self.stock_env.current_step, 'accum'],
            'predict_macd_len':  int(self.stock_env.c2.loc[self.stock_env.current_step, 'len']),
            'predict_action': float(action[0]),
            'predict_vol': float(action[1])
        }
        #print(result)

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

        if save_flag == 'stock_rl_macd_perf_results':
            result['symbol'] = self.ticker
            result['run_id'] = run_id
            result['short'] = self.short
            result['long'] = self.long
            result['signal'] = self.signal
            result['macd_threshold'] = self.macd_threshold
            result['macd_min_len'] = self.macd_min_len

            #print(result)
            mongo = MongoExplorer()
            mongo.mongoDB['stock_rl_macd_perf_results'].replace_one({'symbol': self.ticker, 'run_id': run_id}, result, upsert=True)

            r = {
                'symbol': self.ticker,
                'run_id': run_id,
                'short': self.short,
                'long': self.long,
                'signal': self.signal,
                'macd_threshold': self.macd_threshold,
                'macd_min_len': self.macd_min_len,
                'model_score': model_perf / buy_and_hold_perf,
                'model_run_date': self.stock_env.run_date,
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'duration': dur,
                'model_gain': model_gain,
                'model_perf': model_perf,
                'buy_and_hold_gain': buy_and_hold_gain,
                'buy_and_hold_perf': buy_and_hold_perf
                }
            result = pd.DataFrame.from_records([r])

        return result

if __name__ == '__main__':
    mongo = MongoExplorer()
    #com_query = {'status': 'active'}
    com_query = {'status': 'active', 'Yahoo_Symbol': 'AAPL'}
    com = mongo.mongoDB['etrade_companies'].find(com_query, no_cursor_timeout=True)
    aaod = datetime.now().strftime("%Y-%m-%d")

    index = 1
    restartIndex = 1
    stopIndex = 1000000

    for i in com:
        #ticker = 'TSLA'         #'ILIM'     #'AZO'     #'TCEHY'        #'AYX'      #'LYFT'     #'PUMP'     #'CDLX' #'APPN' #'EYE'  #'RNG'     #'GOOGL'     #'EVBG'     #'BAND'     #'NFLX' #'GRWG'     #'ACMR'     #'MDB'     #'RCM'     #'FB'     #'AAPL'     #'ANTM'     #'AMZN'     #'TSLA'   #'BAND'     #'ROKU'     #'SHOP'     #'TWLO'
        ticker = i['Yahoo_Symbol']
        print(str(index) + "	" + ticker)
        if index > stopIndex:
            break
        if index >= restartIndex:
            #try:
            #    q = QuoteExplorer()
            #    q.get_quotes(ticker, aaod)

            #    g20 = StockScore({'AAOD': aaod, 'symbol': ticker})
            #    if g20.run_fundamentals() == True:
            #        g20.run()
            #except Exception as error:
            #    # print(error)
            #    print(traceback.format_exc())

            #if g20.result.get('Recommendation') != '':
            if True:
                r = pd.DataFrame()

                macd_list = [[3,7,19],[6,13,9],[12,26,9]]     #, [6,13,9],[12,26,9]
                macd_threshold_list = [0,0.2,0.5,1]   #,0.2,0.5,1
                macd_min_len_list = [0,5]

                repeat = 10

                m_i = 0
                for m in macd_list:
                    m_i += 1
                    mtl_i = 0
                    for macd_threshold in macd_threshold_list:
                        mtl_i += 1
                        mmll_i = 0
                        for macd_min_len in macd_min_len_list:
                            mmll_i += 1
                            for i in range(repeat):
                                run_id = m_i * 10000 + mtl_i * 1000 + mmll_i * 100 + i
                                short = m[0]
                                long = m[1]
                                signal = m[2]

                                s = StockRL(ticker, 0, short=short, long=long, signal=signal, macd_threshold=macd_threshold, macd_min_len=macd_min_len)
                                #s = StockRL(ticker, 0, 12, 26, 9, aaod='2019-11-13')
                                #s = StockRL(ticker, 0, 6, 13, 9, aaod='2019-11-13')

                                s.train(save=False)
                                #s.train(save=True)
                                #s.retrain(save=False)
                                #s.retrain()
                                #s.reload()
                                #print(s.run())
                                #print(s.stock_env.c2)

                                rr = s.run(save_flag='stock_rl_macd_perf_results', run_id=run_id)
                                print(rr.to_string(header=False))
                                #print(s.run(save_flag='screen', run_id=run_id))
                                #print(s.run('db'))
                                #df, a = s.run('df')
                                #print(df)
                                #print(a)
                                #print(s.run('df'))
                                r = pd.concat([r, rr])

            if r.empty:
                mongo_query = {"symbol": ticker}
                r = pd.DataFrame(list(mongo.mongoDB['stock_rl_macd_perf_results'].find(mongo_query, no_cursor_timeout=True)))

            #print(r)
            print(r.to_csv().strip('\n').split('\n'))

            r['group'] = r['run_id'] / 100
            r['group'] = r['group'].astype(int)
            s = r.groupby('group').model_score.agg(['mean', 'std'])
            print(s)

            max_score = s['mean'].max()
            smax = s[s['mean'] == max_score]
            smax = smax.reset_index()
            macd_list_index = int(smax['group']/100) - 1
            macd_threshold_list_index = int((smax['group']%100)/10) - 1
            macd_min_len_list_index = int(smax['group']%10) - 1
            print(ticker, max_score, macd_list[macd_list_index], macd_threshold_list[macd_threshold_list_index], macd_min_len_list[macd_min_len_list_index])

        index += 1

