'''
https://github.com/notadamking/Stock-Trading-Environment
'''
import random
#import json
import gym
from gym import spaces
#import pandas as pd
import numpy as np
import datetime as datetime

from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2

#import yfinance as yf

from test_stockstats import StockStats

MAX_ACCOUNT_BALANCE = 2147483647
MAX_NUM_SHARES = 2147483647
MAX_SHARE_PRICE = 10000
MAX_OPEN_POSITIONS = 5
MAX_STEPS = 200000
MAX_REWARD = 10000      #2147483647

INITIAL_ACCOUNT_BALANCE_MIN = 100000
INITIAL_ACCOUNT_BALANCE_MAX = 1000000
REWARD_PERIOD = 200
BUY_REWARD_LOOK_FORWARD = 200
SELL_REWARD_LOOK_FORWARD = 200
HOLD_REWARD_LOOK_FORWARD = 200

class StockTradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, ticker):

        super(StockTradingEnv, self).__init__()
        ss = StockStats(ticker)
        MACD_EMA_SHORT = 40
        MACD_EMA_LONG = 80
        MACD_EMA_SIGNAL = 9
        ss.macd(MACD_EMA_SHORT, MACD_EMA_LONG, MACD_EMA_SIGNAL)
        ss.rsi()
        #ss.bollinger()

        #df = yf.Ticker(ticker).history(period="max")
        ## df = stock.history(start="2015-09-11", end="2020-09-11")
        #df = df.reset_index()
        #df = df.sort_values('Date')

        #self.df = df
        self.df = ss.stock
        self.df = self.df.reset_index()
        self.df = self.df.sort_values('date')
        self.df = self.df.fillna(0)

        #self.reward_range = (0, MAX_ACCOUNT_BALANCE)

        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)

        # Prices contains the OHCL values for the last five prices
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(2, 60), dtype=np.float16)

    def _next_observation(self):
        # Get the stock data points for the last 00 days and scale to between 0-1
        frame = np.array([
            #self.df.loc[self.current_step - 59: self.current_step, 'open'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'high'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'low'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'close'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'volume'].values / MAX_NUM_SHARES,
            self.df.loc[self.current_step - 59: self.current_step, 'h_s'].values / MAX_SHARE_PRICE,
            self.df.loc[self.current_step - 59: self.current_step, 'rsi_14'].values / MAX_SHARE_PRICE,
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

    def _take_action(self, action):
        # Set the current price to a random price within the time step
        current_price = random.uniform(
            self.df.loc[self.current_step, "open"], self.df.loc[self.current_step, "close"])
        reward = 0      # for hold, reward = 0

        action_type = action[0]
        amount = action[1]

        if action_type < 1:
            # Buy amount % of balance in shares
            total_possible = int(self.balance / current_price)
            shares_bought = int(total_possible * amount)
            prev_cost = self.cost_basis * self.shares_held
            additional_cost = shares_bought * current_price

            self.balance -= additional_cost
            if self.shares_held + shares_bought > 0:
                self.cost_basis = (prev_cost + additional_cost) / (self.shares_held + shares_bought)
            self.shares_held += shares_bought

            reward_target = self.current_step + BUY_REWARD_LOOK_FORWARD if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            reward_look_forward_adjuster = 1 if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / BUY_REWARD_LOOK_FORWARD
            reward_price = self.df.loc[reward_target, "close"]
            #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
            reward = reward_look_forward_adjuster * shares_bought * (reward_price - current_price) / MAX_REWARD

        elif action_type < 2:
            # Sell amount % of shares held
            shares_sold = int(self.shares_held * amount)
            self.balance += shares_sold * current_price
            self.shares_held -= shares_sold
            self.total_shares_sold += shares_sold
            self.total_sales_value += shares_sold * current_price

            reward_target = self.current_step + SELL_REWARD_LOOK_FORWARD if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            reward_look_forward_adjuster = 1 if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / SELL_REWARD_LOOK_FORWARD
            reward_price = self.df.loc[reward_target, "close"]
            #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
            reward = reward_look_forward_adjuster * shares_sold * (current_price - reward_price) / MAX_REWARD
            # if shares_sold > 0:
            #    reward = (shares_sold * current_price + self.balance - self.net_worth) / (self.cost_basis * MAX_REWARD)
        else:
            # hold
            reward_target = self.current_step + HOLD_REWARD_LOOK_FORWARD if self.current_step + HOLD_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            reward_look_forward_adjuster = 1 if self.current_step + HOLD_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / HOLD_REWARD_LOOK_FORWARD
            reward_price = self.df.loc[reward_target, "close"]
            if self.shares_held > 0:
                #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
                reward = reward_look_forward_adjuster * 100 * (reward_price - current_price) / MAX_REWARD
            else:
                #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
                reward = reward_look_forward_adjuster * 100 * (current_price - reward_price) / MAX_REWARD

            #reward = (reward_price - current_price) / MAX_REWARD

        self.net_worth = self.balance + self.shares_held * current_price

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.shares_held == 0:
            self.cost_basis = 0

        #print(action, self.balance, self.shares_held, reward)
        return reward

    def step(self, action):
        # Execute one time step within the environment
        reward = self._take_action(action)

        self.current_step += 1

        #delay_modifier = (self.current_step / MAX_STEPS)
        #reward = self.balance * delay_modifier

        done = self.net_worth <= 0

        if self.current_step >= len(self.df.loc[:, 'open'].values) - 1:
            #self.current_step = 100
            #self.current_step = random.randint(100, len(self.df.loc[:, 'open'].values) - 1)
            done = True

        obs = self._next_observation()

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

        # Set the current step to a random point within the data frame
        self.current_step = random.randint(
            #60, 400)
            60, len(self.df.loc[:, 'open'].values) - 1)

        print('reset', self.current_step)

        return self._next_observation()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        #profit = self.net_worth - INITIAL_ACCOUNT_BALANCE
        profit = self.net_worth - self.initial_account_balance
        print(f'Step: {self.current_step}')
        print(f'Balance: {self.balance}')
        print(
            f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})')
        print(
            f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})')
        print(
            f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})')
        print(f'Profit: {profit}')

        print(f'Date: {self.df.loc[self.current_step-1, "date"]}')
        print(f'Close: {self.df.loc[self.current_step-1, "close"]}')

# get historical market data
ticker = 'AAPL'     #APPN'     #'GRWG'     #'ACMR'     #'MDB'     #'CDLX'       #'RCM'     #'FB'     #'AAPL'     #'ANTM'     #'AMZN'     #'TSLA'   #'BAND'     #'ROKU'     #'SHOP'     #'TWLO'

# The algorithms require a vectorized environment to run
stock_env = StockTradingEnv(ticker)
#env = DummyVecEnv([lambda: StockTradingEnv(ticker)])
env = DummyVecEnv([lambda: stock_env])

model = PPO2(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=20000)
#model.save("test_rl_"+ticker)

#model = PPO2.load("test_rl_"+ticker)
#model.set_env(env)
#model.learn(total_timesteps=20000)

obs = env.reset()
info = [{'step': 0}]
i = 1
while info[0]['step'] < len(stock_env.df.loc[:, 'open'].values) - 2:
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    env.render()
    print(action)
    if i < 2:
        start = stock_env.net_worth
        start_date = stock_env.df.loc[stock_env.current_step-1, "date"]
        start_price = stock_env.df.loc[stock_env.current_step-1, "close"]
    i += 1
#env.render()
end = stock_env.net_worth
end_date = stock_env.df.loc[stock_env.current_step-1, "date"]
end_price = stock_env.df.loc[stock_env.current_step-1, "close"]
dur = (end_date - start_date).days / 365

model_perf =10 ** (np.log10(end/start)/dur)

buy_and_hold_perf = 10 ** (np.log10(end_price/start_price)/dur)

print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end/start}     {model_perf}')
print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price/start_price}    {buy_and_hold_perf}')

stock_env.current_step = len(stock_env.df.loc[:, 'open'].values)-1
print(stock_env.current_step, stock_env.df.loc[stock_env.current_step-1, "date"],  model.predict(stock_env._next_observation()))
