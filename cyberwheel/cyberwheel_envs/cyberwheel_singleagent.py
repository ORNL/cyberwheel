import gymnasium as gym
from gymnasium import spaces
from network.network_base import Network
from .cyberwheel import Cyberwheel
from redagents.longestpath import LongestPathRedAgent

# import numpy as np
import yaml


class SingleAgentCyberwheel(gym.Env, Cyberwheel):

    metadata = {"render.modes": ["human"]}

    # def __init__(self, number_hosts, number_subnets, connect_subnets_probability, **kwargs):
    def __init__(self, **kwargs):
        # super(SingleAgentCyberwheel, self).__init__()
        # use config_file_path kwarg if supplied, otherwise use default
        config_file_path = kwargs.get("config_file_path", "network/config.yaml")
        super().__init__(config_file_path=config_file_path)
        ## Define action and observation space
        ## They must be gym.spaces objects
        # self.number_hosts = number_hosts
        # self.number_subnets = number_subnets
        # self.connect_subnets_probability = connect_subnets_probability

        self.max_steps = 100

        ## self.network is now instantiated in the Cyberwheel class
        ##self.network = RandomNetwork(number_hosts,number_subnets,connect_subnets_probability)
        # self.network = Network.create_network_from_yaml('network/config.yaml')
        # self.network.draw()

        # Action space: 0 for no action, 1 to N for restore action on the corresponding host
        self.action_space = spaces.Discrete(self.network.get_action_space_size())

        # Observation space: Binary vector indicating whether each host is compromised or not
        self.observation_space = spaces.MultiBinary(
            self.network.get_action_space_size() - 1
        )

        self.current_step = 0

        self.red_agent = LongestPathRedAgent(self.network)

    ## private method that converts state into observation
    ## convert the dictionary of Host objects into the observation vector
    # def _get_obs(self):
    #    return self.network.generate_observation_vector()

    def step(self, action):

        reward = 0

        # Example logic: If the action is to restore a host, set the corresponding element in the state to 1
        if action > 0:

            if self.network.set_host_compromised(action - 1, False):
                reward = 10

        flag = self.red_agent.act()

        if flag == "owned":
            done = True
            reward = -100
        elif self.current_step >= self.max_steps:  # Maximal number of steps
            done = True
        else:
            done = False

        self.current_step += 1

        return self._get_obs(), reward, done, False, {}

    def reset(self, seed=None, options=None):

        self.current_step = 0

        # self.network = RandomNetwork(self.number_hosts,self.number_subnets,self.connect_subnets_probability)
        self.network = Network.create_network_from_yaml(self.config_file_path)
        self.red_agent = LongestPathRedAgent(self.network)

        return self._get_obs(), {}  # observation, info

    # can implement existing GUI here???
    def render(self, mode="human"):
        pass

    # if you open any other processes close them here
    def close(self):
        pass
