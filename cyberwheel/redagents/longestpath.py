import networkx as nx
import numpy as np
import random
from .red_agent_base import *

"""
Selects a random host as the starting point and then chooses as target the host that is furthest away
"""


class LongestPathRedAgent(RedAgent):

    def __init__(self, network):
        super().__init__()
        self.network = network
        self.source = self.network.get_random_host()
        self.target = self.network.find_host_with_longest_path(self.source)

    def act(self):
        # update this in case network object has been modified
        path = self.network.find_path_between_hosts(self.source, self.target)

        for node in path:
            if not self.network.check_compromised_status(node):
                self.network.update_host_compromised_status(
                    node, True
                )  # Set is_compromised to True
                break

        # return (
        #    "owned"
        #    if all(self.network.check_compromised_status(n) for n in path)
        #    else None
        # )
