import gymnasium as gym
from gymnasium import spaces
from network.network_base import Network
from redagents.longestpath import LongestPathRedAgent
import numpy as np
import yaml

class Cyberwheel:

    def __init__(self, **kwargs):
        super().__init__()
        # use config_file_path kwarg if supplied
        self.config_file_path = kwargs.get('config_file_path', 'network/config.yaml')

        #self.network = RandomNetwork(number_hosts,number_subnets,connect_subnets_probability)
        self.network = Network.create_network_from_yaml(self.config_file_path)
        self.network.draw()


    # private method that converts state into observation 
    # convert the dictionary of Host objects into the observation vector
    def _get_obs(self):

        return self.network.generate_observation_vector()

