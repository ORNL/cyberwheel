import networkx as nx
import numpy as np
import random
from .redbase import *

class ShortestPathRedAgent(RedAgentBase):

    def __init__(self, network):
        super().__init__()
        self.network = network
        self.source = self.network.get_random_host()
        self.target = self.get_target()
        self.path = nx.shortest_path(self.network, source=self.source, target=self.target)

    def get_target(self): 

        # Compute the shortest path lengths from source to all reachable nodes
        length = self.network.single_source_shortest_path_length(self.graph, self.source)

        # Set the target to one of the nodes that is furthest away
        target = self.source
        for node in length:
            if length[node] > length[target]:
                target = node 

        return target

    def act(self, observation_space):

        node_captured = False 
        for node in self.path:
            if observation_space[self.host_to_index[node]] != 1:
                observation_space[self.host_to_index[node]] == 1
                node_captured = True
                return node 
        
        if not node_captured:
            return "owned"