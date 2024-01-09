import gymnasium as gym
from gymnasium import spaces
from network.network_random import RandomNetwork
from redagents.shortestpath import ShortestPathRedAgent
import numpy as np

class Cyberwheel(gym.Env):

    metadata = {'render.modes': ['human']}

    def __init__(self, number_hosts, number_subnets,connect_subnets_probability):
        super(Cyberwheel, self).__init__()
        # Define action and observation space
        # They must be gym.spaces objects
        self.number_hosts = number_hosts
        self.number_subnets = number_subnets
        self.connect_subnets_probability = connect_subnets_probability

        self.network = RandomNetwork(number_hosts,number_subnets,connect_subnets_probability)

        # Action space: 0 for no action, 1 to N for restore action on the corresponding host
        self.action_space = spaces.Discrete(self.network.get_action_space_size())

        # Observation space: Binary vector indicating whether each host is compromised or not
        self.observation_space = spaces.MultiBinary(self.network.get_action_space_size()-1)

        self.red_agent = ShortestPathRedAgent(self.network)

    # private method that converts state into observation 
    # convert the dictionary of Host objects into the observation vector
    def _get_obs(self):

        return self.network.generate_observation_vector()

    def step(self, action):

        reward = 0

        # Example logic: If the action is to restore a host, set the corresponding element in the state to 1
        if action > 0:
            
            if self.network.take_action(action):
                reward = 10

        flag = self.red_agent.act()

        if flag == "owned":
            done = True
            reward = -100
        else: 
            done = False

        return self._get_obs(), reward, done, False, {}

    def reset(self, seed=None, options=None):

        self.network = RandomNetwork(self.number_hosts,self.number_subnets,self.connect_subnets_probability)
        self.red_agent = ShortestPathRedAgent(self.network)
        
        return self._get_obs(), {} # observation, info

    # can implement existing GUI here???
    def render(self, mode='human'):
        pass

    # if you open any other processes close them here
    def close (self):
        pass