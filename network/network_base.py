import networkx as nx
import random
import ipaddress
import math
from .host import Host

class Network:
    
    def __init__(self, ):

class Network:
    def __init__(self):
        self.graph = nx.Graph()

    def add_subnet(self, subnet):
        self.graph.add_node(subnet)

    def add_host(self, host):
        self.graph.add_node(host)

    def connect_subnets(self, subnet1, subnet2):
        self.graph.add_edge(subnet1, subnet2)

    def connect_host_to_subnet(self, host, subnet):
        self.graph.add_edge(host, subnet)

    def is_subnet_reachable(self, subnet1, subnet2):
        return nx.has_path(self.graph, subnet1, subnet2)

    def get_random_host(self):
        all_hosts = [node for node in random_net.graph.nodes if isinstance(node, Host)]
        return random.choice(all_hosts)

    def find_path_between_hosts(self, source_host, target_host):

        if source_host not in self.graph or target_host not in self.graph:
            return None  # Source or target not found in the network

        shortest_path = nx.shortest_path(self.graph, source=source_host, target=target_host)
        filtered_path = [node for node in shortest_path if isinstance(node, Host)]
        return filtered_path

    def generate_observation_vector(self):
        
        observation_vector = []
        for node in self.graph.nodes:
            if isinstance(node, Host):
                is_compromised = node.is_compromised
                observation_vector.append(1 if is_compromised else 0)

        return observation_vector



