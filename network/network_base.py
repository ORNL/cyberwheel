import networkx as nx
import random
import ipaddress
import math
import numpy as np
import matplotlib.pyplot as plt
import yaml

from .subnet import Subnet
from .host import Host
from .router import Router

class Network:
    
    def __init__(self):
        self.graph = nx.Graph()

    def add_subnet(self, subnet):
        self.graph.add_node(subnet.name, data=subnet)

    def add_router(self, router):
        self.graph.add_node(router.name, data=router)

    def add_host(self, host):
        self.graph.add_node(host.name, data=host)

    def connect_nodes(self, node1, node2):
        self.graph.add_edge(node1.name, node2.name)

    def define_routing_rules(self, router, routes):
        if router.name in self.graph.nodes:
            data_object = self.graph.nodes[router.name]['data']
            if isinstance(data_object, Router):
                data_object.routes = routes

    def define_firewall_rules(self, router, firewall_rules):
        if router.name in self.graph.nodes:
            data_object = self.graph.nodes[router.name]['data']
            if isinstance(data_object, Router):
                data_object.firewall_rules = firewall_rules

    def define_subnet_routing_rules(self, subnet, routes):
        if subnet.name in self.graph.nodes:
            data_object = self.graph.nodes[subnet.name]['data']
            if isinstance(data_object, Subnet):
                data_object.routes = routes

    def define_subnet_firewall_rules(self, subnet, firewall_rules):
        if subnet.name in self.graph.nodes:
            data_object = self.graph.nodes[subnet.name]['data']
            if isinstance(data_object, Subnet):
                data_object.firewall_rules = firewall_rules

    def define_host_firewall_rules(self, host, firewall_rules):
        if host.name in self.graph.nodes:
            data_object = self.graph.nodes[host.name]['data']
            if isinstance(data_object, Host):
                data_object.firewall_rules = firewall_rules

    def is_subnet_reachable(self, subnet1, subnet2):
        return nx.has_path(self.graph, subnet1.name, subnet2.name)

    def get_random_host(self):
        all_hosts = [node_name for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]

        return random.choice(all_hosts)

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
            shortest_path = [item for item in shortest_path if "Router" not in item]

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

    @classmethod
    def create_network_from_yaml(cls, config_file_path):
        # Create an instance of the Network class
        network = cls()

        # Define dictionaries to store created instances for quick access
        subnets_dict = {}
        routers_dict = {}
        hosts_dict = {}

        # Load the YAML config file
        with open(config_file_path, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file)

        # Parse routers
        for router_config in config['routers']:
            router = Router(router_config['name'], router_config['default_route'])
            routers_dict[router.name] = router
            network.add_router(router)

        # Parse subnets
        for subnet_config in config['subnets']:
            subnet = Subnet(subnet_config['name'], subnet_config['default_route'], subnet_config['ip_range'])
            subnets_dict[subnet.name] = subnet
            network.add_subnet(subnet)

        # Parse hosts
        for host_config in config['hosts']:
            host = Host(host_config['name'], host_config['type'], subnets_dict[host_config['subnet']])
            hosts_dict[host.name] = host
            network.add_host(host)

        # Parse topology
        for router_name, router_config in config['topology'][0].items():
            for item in router_config:
                if isinstance(item, dict):
                    if any("Router" in key for key in item):
                        for child_router_name, subnets in item.items():
                            network.connect_nodes(routers_dict[router_name], routers_dict[child_router_name])
                            for subnet in subnets:
                                if isinstance(subnet, dict):
                                    for subnet_name, hosts in subnet.items():
                                        network.connect_nodes(routers_dict[child_router_name], subnets_dict[subnet_name])
                                        for host_name in hosts: 
                                            network.connect_nodes(hosts_dict[host_name], subnets_dict[subnet_name])
                                else: 
                                    network.connect_nodes(routers_dict[router_name], subnets_dict[subnet])
                    else:
                        if isinstance(item, dict):
                            for subnet_name, hosts in item.items():
                                network.connect_nodes(routers_dict[router_name], subnets_dict[subnet_name])
                                for host_name in hosts: 
                                    network.connect_nodes(hosts_dict[host_name], subnets_dict[subnet_name])
                else: 
                    network.connect_nodes(routers_dict[router_name], subnets_dict[item])

        return network



