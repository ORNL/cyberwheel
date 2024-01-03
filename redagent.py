import networkx as nx
import numpy as np

class RedAgent:
    def __init__(self, observation_space, network_graph, source, target_host, host_to_index):
        self.observation_space = observation_space
        self.network_graph = network_graph
        self.path = None
        self.source = source
        self.target_host = target_host
        self.host_to_index = host_to_index
        self.calculate_path()

    def calculate_path(self):
        # Calculate the most efficient path through the network using networkx
        self.path = nx.shortest_path(self.network_graph, source=self.source, target=self.target_host)

    def compromise_furthest_host(self):
        # Find the furthest host along the path with observation 0
        furthest_host = None
        for host_id in reversed(self.path):
            if self.observation_space[self.host_to_index[host_id]] == 0:
                furthest_host = host_id
                break

        if furthest_host is not None:
            # Compromise the furthest host by changing its observation from 0 to 1
            print(f"Compromising host {furthest_host} along the path.")
            self.observation_space[self.host_to_index[furthest_host]] = 1

        return furthest_host

    def act(self, observation_space):
        self.observation_space = observation_space

        if self.path is None:
            print("Calculate the path first.")
            return None

        # Compromise the furthest host along the path with observation 0
        furthest_host = self.compromise_furthest_host()

        # Check if the red agent reached its target
        print(self.path)
        if self.path and self.path[-1] == self.target_host:
            print("Red agent reached its target. End game signal sent.")
            return "owned"

        return furthest_host