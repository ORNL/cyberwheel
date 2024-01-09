import networkx as nx
import random
import ipaddress
import math
import numpy as np
from .host import Host
import matplotlib.pyplot as plt

class Network:
    
    def __init__(self):
        pass

class Network:
    def __init__(self):
        self.graph = nx.Graph()

    def add_subnet(self, subnet):
        self.graph.add_node(subnet.name, data = subnet)

    def add_host(self, host):
        self.graph.add_node(host.name, data = host)

    def connect_subnets(self, subnet1, subnet2):
        self.graph.add_edge(subnet1, subnet2)

    def connect_host_to_subnet(self, host, subnet):
        self.graph.add_edge(host, subnet)

    def is_subnet_reachable(self, subnet1, subnet2):
        return nx.has_path(self.graph, subnet1.name, subnet2.name)

    def get_random_host(self):
        all_hosts = [node_name for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]

        return random.choice(all_hosts)

    def update_host_compromised_status(self, host, is_compromised):
        if host in self.graph.nodes:
            host.is_compromised = is_compromised

    def update_host_compromised_status(self, host, is_compromised):
        if host in self.graph.nodes:
            data_object = self.graph.nodes[host]['data']
            if isinstance(data_object, Host):
                data_object.is_compromised = is_compromised

    def check_compromised_status(self, host_name):
        if host_name in self.graph.nodes:
            data_object = self.graph.nodes[host_name]['data']
            if isinstance(data_object, Host):
                return data_object.is_compromised
        return None  # Return None if host not found or not an instance of Host

    def find_path_between_hosts(self, source_host, target_host):

        if source_host not in self.graph or target_host not in self.graph:
            return None  # Source or target not found in the network

        try:
            shortest_path = nx.shortest_path(self.graph, source=source_host, target=target_host)

            # Replace subnet names with host names on those subnets
            new_path = []

            for node in shortest_path:
                if node.startswith('Subnet'):
                    subnet_name = node
                    # Try to find a connected node that starts with 'Host'
                    connected_host = None
                    for neighbor in self.graph.neighbors(subnet_name):
                        if neighbor.startswith('Host'):
                            connected_host = neighbor
                            break

                    if connected_host:
                        new_path.append(connected_host)  # Replace subnet with connected host
                    else:
                        new_path.append(node)  # If no connected host found, keep the subnet
                else:
                    # Keep non-subnet nodes unchanged
                    new_path.append(node)

            return new_path
        except: 
            return None
    
    def find_host_with_longest_path(self, source_host):
        all_hosts = [node_name for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]
        all_hosts.remove(source_host)  # Remove the source host from the list
        if not all_hosts:
            return None  # No other hosts in the network

        longest_path_length = -1
        target_host = None

        for host in all_hosts:
            path = self.find_path_between_hosts(source_host, host)
            if path is not None and len(path) > longest_path_length:
                longest_path_length = len(path)
                target_host = host

        return target_host

    def generate_observation_vector(self):
        num_hosts = sum(isinstance(data_object, Host) for _, data_object in self.graph.nodes(data='data'))
        observation_vector = np.zeros(num_hosts, dtype=np.int8)

        index = 0
        for _, data_object in self.graph.nodes(data='data'):
            if isinstance(data_object, Host):
                is_compromised = data_object.is_compromised
                observation_vector[index] = 1 if is_compromised else 0
                index += 1

        return observation_vector

    def get_action_space_size(self):
        n = 1  # do nothing action
        for _, data_object in self.graph.nodes(data='data'):
            if isinstance(data_object, Host):
                n += 1
        return n

    def take_action(self, action):
        hosts = [data_object for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]
        if action >= 1 and action <= len(hosts):
            host_to_modify = hosts[action - 1]  # Adjust the index to match the list
            current_state = host_to_modify.is_compromised 
            host_to_modify.is_compromised = False  # Set is_compromised to False for the selected host
            
            return current_state

    # For debugging to view the network being generated
    def draw(self):

        plt.clf() # clear
        nx.draw(self.graph, with_labels=False, node_color='skyblue', node_size=30, font_size=12, font_color='black', font_weight='bold', edge_color='black')

        # Display the graph
        plt.savefig("networkx_graph.png", format="png")



