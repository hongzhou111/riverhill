'''
https://github.com/notadamking/Stock-Trading-Environment
'''
from datetime import datetime
import random
#import json
import gym
from gym import spaces
#import pandas as pd
import numpy as np
#import datetime as datetime
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2
#import yfinance as yf
from test_stockstats import StockStats
import json
from test_mongo import MongoExplorer

class StockTradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, ticker, short=12, long=26, signal=9):
        super(StockTradingEnv, self).__init__()

        self.MAX_ACCOUNT_BALANCE = 2147483647
        self.MAX_NUM_SHARES = 2147483647
        self.MAX_SHARE_PRICE = 10000
        self.MAX_MACD = 1
        # self.MAX_OPEN_POSITIONS = 5
        self.MAX_STEPS = 200000
        self.MAX_REWARD = 10000  # 2147483647

        # self.INITIAL_ACCOUNT_BALANCE_MIN = 100000
        # self.INITIAL_ACCOUNT_BALANCE_MAX = 1000000
        # self.REWARD_PERIOD = 200
        # self.BUY_REWARD_LOOK_FORWARD = 200
        # self.SELL_REWARD_LOOK_FORWARD = 200
        # self.HOLD_REWARD_LOOK_FORWARD = 200

        #short = 12
        #long = 26
        #signal = 9
        ss = StockStats(ticker)
        ss.macd(short, long, signal)
        self.c = ss.macd_crossing()
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
        self.run_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    def _next_observation(self):
        # Get the stock data points for the last 00 days and scale to between 0-1
        frame = np.array([
            #self.df.loc[self.current_step - 59: self.current_step, 'open'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'high'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'low'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'close'].values / MAX_SHARE_PRICE,
            #self.df.loc[self.current_step - 59: self.current_step, 'volume'].values / MAX_NUM_SHARES,
            self.c.loc[self.current_step - 4: self.current_step, 'accum'].values,
            self.c.loc[self.current_step - 4: self.current_step, 'len'].values,
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

    def _take_action(self, action):
        # Set the current price to a random price within the time step
        current_price = random.uniform(
            self.c.loc[self.current_step, "low"], self.c.loc[self.current_step, "high"])
            #self.c.loc[self.current_step, "open"], self.c.loc[self.current_step, "close"])
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

            #reward_target = self.current_step + BUY_REWARD_LOOK_FORWARD if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + BUY_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / BUY_REWARD_LOOK_FORWARD
            reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            reward_price = self.c.loc[reward_target, "close"]
            #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
            reward = reward_look_forward_adjuster * shares_bought * (reward_price - current_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster  * (reward_price - current_price) / MAX_REWARD

        elif action_type < 2:
            # Sell amount % of shares held
            shares_sold = int(self.shares_held * amount)
            self.balance += shares_sold * current_price
            self.shares_held -= shares_sold
            self.total_shares_sold += shares_sold
            self.total_sales_value += shares_sold * current_price

            #reward_target = self.current_step + SELL_REWARD_LOOK_FORWARD if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else len(self.df.loc[:, 'open'].values) - 1
            #reward_look_forward_adjuster = 1 if self.current_step + SELL_REWARD_LOOK_FORWARD < len(self.df.loc[:, 'open'].values) else (len(self.df.loc[:, 'open'].values) - 1 - self.current_step) / SELL_REWARD_LOOK_FORWARD
            reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            reward_price = self.c.loc[reward_target, "close"]
            #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
            reward = reward_look_forward_adjuster * shares_sold * (current_price - reward_price) / self.MAX_REWARD
            #reward = reward_look_forward_adjuster * (current_price - reward_price) / MAX_REWARD
            # if shares_sold > 0:
            #    reward = (shares_sold * current_price + self.balance - self.net_worth) / (self.cost_basis * MAX_REWARD)
        else:
            # hold
            reward_target = self.current_step + 1
            reward_look_forward_adjuster = 1
            reward_price = self.c.loc[reward_target, "close"]
            if self.shares_held > 0:
                #reward = shares_bought * (reward_price - current_price) / MAX_REWARD
                reward = reward_look_forward_adjuster * 100 * (reward_price - current_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (reward_price - current_price) / MAX_REWARD
            else:
                #reward = shares_sold * (current_price - reward_price) / MAX_REWARD
                reward = reward_look_forward_adjuster * 100 * (current_price - reward_price) / self.MAX_REWARD
                #reward = reward_look_forward_adjuster  * (current_price - reward_price) / MAX_REWARD

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

        if self.current_step >= len(self.c.loc[:, 'open'].values) - 1:
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
            5, len(self.c.loc[:, 'open'].values) - 2)

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

        print(f'State: {self.c.loc[self.current_step-1]}')
        #print(f'Date: {self.c.loc[self.current_step-1, "date"]}')
        #print(f'Close: {self.c.loc[self.current_step-1, "close"]}')


    def render_to_file(self, action=None):
        # Render the environment to the file
        f = open("./rl/rl_" + self.ticker + ".txt", "a")

        # profit = self.net_worth - INITIAL_ACCOUNT_BALANCE
        profit = self.net_worth - self.initial_account_balance
        f.write(f'Step: {self.current_step - 1}\n')
        f.write(f'Balance: {self.balance}\n')
        f.write(f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})\n')
        f.write(f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})\n')
        f.write(f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})\n')
        f.write(f'Profit: {profit}\n')
        f.write(f'date: {self.c.loc[self.current_step - 1]["date"]}\n')
        f.write(f'close: {self.c.loc[self.current_step - 1]["close"]}\n')
        f.write(f'accum: {self.c.loc[self.current_step - 1]["accum"]}\n')
        f.write(f'len: {self.c.loc[self.current_step - 1]["len"]}\n')
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
            'date': self.c.loc[self.current_step - 1]["date"],
            'close': self.c.loc[self.current_step - 1]["close"],
            'accum': self.c.loc[self.current_step - 1]["accum"],
            'len': self.c.loc[self.current_step - 1]["len"],
            'action': float(action[0]),
            'vol': float(action[1])
        }
        mongo = MongoExplorer()
        mongo.mongoDB['stock_rl_steps'].replace_one({'symbol': self.ticker, 'run_date': self.run_date, 'step': self.current_step-1}, step_result, upsert=True)
        #print(step_result)

class StockRL:
    def __init__(self, ticker, vb=0, short=12, long=26, signal=9):           #vb = verboss is 1 or 0
        self.ticker = ticker
        self.vb = vb
        # The algorithms require a vectorized environment to run
        self.stock_env = StockTradingEnv(ticker, short, long, signal)
        # self.env = DummyVecEnv([lambda: StockTradingEnv(ticker)])
        self.env = DummyVecEnv([lambda: self.stock_env])
        self.model = PPO2(MlpPolicy, self.env, verbose=self.vb)

    def train(self):
        self.model.learn(total_timesteps=20000)
        #self.model.save("./rl/test_rl_"+self.ticker)

    def retrain(self):
        self.model = PPO2.load("./rl/test_rl_"+self.ticker, self.env)
        #self.model.set_env(self.env)
        self.model.learn(total_timesteps=20000)
        #self.model.save("./rl/test_rl_"+self.ticker)

    def reload(self):
        self.model = PPO2.load("./rl/test_rl_" + self.ticker, self.env)
        #self.model.set_env(self.env)

    def run(self, save_flag=None):
        obs = self.stock_env.reset()
        self.stock_env.current_step = 10
        # info = [{'step': 0}]
        i = 1
        # while info[0]['step'] < len(stock_env.c.loc[:, 'open'].values) - 2:
        while self.stock_env.current_step < len(self.stock_env.c.loc[:, 'open'].values) - 1:
            obs = self.stock_env._next_observation()
            action, _states = self.model.predict(obs)
            # obs, rewards, done, info = env.step(action)
            reward = self.stock_env._take_action(action)
            self.stock_env.current_step += 1

            #self.stock_env.render()
            #print(action)
            if save_flag == 'file':
                self.stock_env.render_to_file(action)
            if save_flag == 'db':
                self.stock_env.render_to_db(action)

            if i < 2:
                start = self.stock_env.net_worth
                start_date = self.stock_env.c.loc[self.stock_env.current_step - 1, "date"]
                start_price = self.stock_env.c.loc[self.stock_env.current_step - 1, "close"]
            i += 1
        # env.render()
        end = self.stock_env.net_worth
        end_date = self.stock_env.c.loc[self.stock_env.current_step - 1, "date"]
        end_price = self.stock_env.c.loc[self.stock_env.current_step - 1, "close"]
        dur = (end_date - start_date).days / 365

        model_perf = 10 ** (np.log10(end / start) / dur)

        buy_and_hold_perf = 10 ** (np.log10(end_price / start_price) / dur)

        #print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}')
        #print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}')

        self.stock_env.current_step = len(self.stock_env.c.loc[:, 'open'].values) - 1
        #print(self.stock_env.current_step, self.stock_env.c.loc[self.stock_env.current_step, "date"],
        #      self.model.predict(self.stock_env._next_observation()))
        #print('test rl', self.ticker)
        #print(self.stock_env.c)

        result = {
            'model_run_date': self.stock_env.run_date,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'duration': dur,
            'model_perf': model_perf,
            'buy_hold': buy_and_hold_perf,
            'model_score': model_perf / buy_and_hold_perf,
            'predict_date': self.stock_env.c.loc[self.stock_env.current_step, 'date'].strftime("%Y-%m-%d"),
            'predict_macd_accum':  self.stock_env.c.loc[self.stock_env.current_step, 'accum'],
            'predict_macd_len':  int(self.stock_env.c.loc[self.stock_env.current_step, 'len']),
            'predict_action': float(self.model.predict(self.stock_env._next_observation())[0][0]),
            'predict_vol': float(self.model.predict(self.stock_env._next_observation())[0][1])
        }
        #print(result)

        if save_flag == 'screen':
            # print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}')
            # print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}')
            print(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}')
            print(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}')
            #print(json.dumps(result))

        if save_flag == 'file':
            f = open("./rl/rl_" + self.ticker + ".txt", "a")
            f.write(f'Model Perf:         {start_date} - {end_date}   {dur}   {end / start}     {model_perf}\n')
            f.write(f'Buy and Hold Perf:  {start_date} - {end_date}   {dur}   {end_price / start_price}    {buy_and_hold_perf}\n')
            f.write(json.dumps(result))
            f.write('\n\ns')
            f.close()

        return result
    def run_macd(self, save_flag=None, run_id=0):
        obs = self.stock_env.reset()
        self.stock_env.current_step = 10
        i = 1
        # while info[0]['step'] < len(stock_env.c.loc[:, 'open'].values) - 2:
        while self.stock_env.current_step < len(self.stock_env.c.loc[:, 'open'].values) - 1:
            if self.stock_env.c.loc[self.stock_env.current_step, "macd_sign"] == -1:
                action = [0,1]
            elif self.stock_env.c.loc[self.stock_env.current_step, "macd_sign"] == 1:
                action = [1,1]
            else:
                action = [2,1]

            self.stock_env._take_action(action)
            self.stock_env.current_step += 1

            if i < 2:
                start = self.stock_env.net_worth
                start_date = self.stock_env.c.loc[self.stock_env.current_step - 1, "date"]
                start_price = self.stock_env.c.loc[self.stock_env.current_step - 1, "close"]
            i += 1
        # env.render()
        end = self.stock_env.net_worth
        end_date = self.stock_env.c.loc[self.stock_env.current_step - 1, "date"]
        end_price = self.stock_env.c.loc[self.stock_env.current_step - 1, "close"]
        dur = (end_date - start_date).total_seconds() / (365 * 24 * 60 * 60)
        #macd_gain = end / start
        macd_perf = 10 ** (np.log10(end / start) / dur)

        if save_flag == 'screen':
            print(f'MACD Perf:          {start_date} - {end_date}   {dur}   {end / start}     {macd_perf}')
            #print(json.dumps(result))

if __name__ == '__main__':
    # get historical market data
    ticker = 'SHOP'     #'GOOGL'     #'EVBG'     #'BAND'     #'NFLX'         #'APPN'     #'GRWG'     #'ACMR'     #'MDB'     #'CDLX'       #'RCM'     #'FB'     #'AAPL'     #'ANTM'     #'AMZN'     #'TSLA'   #'BAND'     #'ROKU'     #'SHOP'     #'TWLO'

    s = StockRL(ticker, 0, 3, 7, 19)
    s.train()
    #s.retrain()
    #s.reload()
    #print(s.run())
    #print(s.run('db'))
    print(s.run('screen'))
    s.run_macd('screen')
