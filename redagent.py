import networkx as nx
import numpy as np

class RedAgent:
    def __init__(self, observation_space, network_graph, source, target_host, host_to_index):
        self.observation_space = observation_space
        self.network_graph = network_graph
        self.path = []
        self.source = source
        self.target_host = target_host
        self.host_to_index = host_to_index
        self.calculate_path()

    def calculate_path(self):
        # Calculate the most efficient path through the network using networkx
        self.path = nx.shortest_path(self.network_graph, source=self.source, target=self.target_host)

    def act(self, observation_space):
        self.observation_space = observation_space

        node_captured = False 
        for node in self.path:
            if self.observation_space[self.host_to_index[node]] != 1:
                self.observation_space[self.host_to_index[node]] == 1
                node_captured = True
                return node 
        
        if not node_captured:
            return "owned"