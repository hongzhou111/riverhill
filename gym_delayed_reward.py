#https://towardsdatascience.com/creating-a-custom-openai-gym-environment-for-stock-trading-be532be3910e

import gym
from gym.utils import seeding
import numpy as np


class myEnv(gym.Env):
    def __init__(self, *args, **kwargs):
        """
            Define all the necessary stuff here
        """
        self.env = gym.make('CartPole-v1')  # add stuff here to define game params
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.past_actions = []
        self.delay = 2  # to have a delay of two timesteps

    def reset(self):
        """
            Define the reset
        """
        self.observation = self.env.reset()
        return self.observation

    def step(self, action):
        """
            Add the delay of actions here
        """
        self.past_actions.append(action)  # to keep track of actions
        reward = 0;
        done = 0;
        info = {}  # reward, done and info are 0,0,{} for first two timesteps
        if len(self.past_actions) > self.delay:
            present_action = self.past_actions.pop(0)
            # change observation, reward, done, info
            # according to the action 'delay' timesteps ago
            self.observation, reward, done, info = self.env.step(present_action)
        return self.observation, reward, done, info

    def seed(self, seed=0):
        """
            Define seed method here
        """
        self.np_random, seed = seeding.np_random(seed)
        return self.env.seed(seed=seed)

    def render(self, mode="human", *args, **kwargs):
        """
            Define rendering method here
        """
        return self.env.render(*args, **kwargs)

    def close(self):
        """
            Define close method here
        """
        return self.env.close()
