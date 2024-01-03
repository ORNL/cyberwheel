import networkx as nx
import numpy as np
from abc import ABC, abstractmethod

class RedAgentBase(ABC):
    def __init__(self, observation_space, network_graph, source, target_host, host_to_index):
        self.observation_space = observation_space
        self.network_graph = network_graph
        self.path = []
        self.source = source
        self.target_host = target_host
        self.host_to_index = host_to_index
        self.calculate_path()

    @abstractmethod
    def calculate_path(self):
        pass

    @abstractmethod
    def act(self, observation_space):
        pass