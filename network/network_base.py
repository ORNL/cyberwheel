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

    def __iter__(self):
        return iter(self.graph)

    def __len__(self):
        return len(self.graph)

    def add_subnet(self, subnet):
        self.graph.add_node(subnet.name, data=subnet)

    def add_router(self, router):
        self.graph.add_node(router.name, data=router)

    def add_host(self, host):
        self.graph.add_node(host.name, data=host)

    def connect_nodes(self, node1, node2):
        self.graph.add_edge(node1, node2)

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

    # TODO - This method is not working properly
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

    def is_any_subnet_fully_compromised(self):
        # Iterate over all nodes in the graph
        for node_name, data_object in self.graph.nodes(data='data'):
            # Check if the node is a Subnet
            if isinstance(data_object, Subnet):
                # Get all hosts connected to the subnet
                hosts = [self.graph.nodes[neighbor]['data'] for neighbor in self.graph.neighbors(node_name) if isinstance(self.graph.nodes[neighbor]['data'], Host)]
                # Check if all hosts are compromised
                if all(host.is_compromised for host in hosts):
                    return True
                    
        return False

    def set_host_compromised(self, host_id, compromised):
        hosts = [data_object for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]
        host_to_modify = hosts[host_id]  # Adjust the index to match the list
        current_state = host_to_modify.is_compromised 
        host_to_modify.is_compromised = compromised  # Set is_compromised to False for the selected host
        
        return current_state

    # For debugging to view the network being generated
    def draw(self, **kwargs):
        labels: bool = kwargs.get('labels', False)
        filename: str = kwargs.get('filename', 'networkx_graph.png')

        plt.clf() # clear
        nx.draw(self.graph, with_labels=labels, node_color='skyblue', node_size=30, font_size=12, font_color='black', font_weight='bold', edge_color='black')

        # Display the graph
        plt.savefig(filename, format="png")

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
        for key, val in config['routers'].items():
            router = Router(key,
                            # using '.get()' here in case default_route isn't defined
                            val.get('default_route'),
                            val['routes'],
                            val.get('firewall', None))
            routers_dict[router.name] = router
            network.add_router(router)

        # Parse subnets
        for key, val in config['subnets'].items():
            subnet = Subnet(key,
                            val['default_route'],
                            val['ip_range'])
            subnets_dict[subnet.name] = subnet
            network.add_subnet(subnet)

        # Parse hosts
        for key, val in config['hosts'].items():
            host = Host(key,
                        val['type'],
                        val['subnet'],
                        val.get('firewall', None))
            hosts_dict[host.name] = host
            network.add_host(host)

        # Parse topology
        for node, data in network.graph.nodes(data='data'):

            # Connect all hosts to their parent subnets
            if isinstance(data, Host):
                parent_subnet = config['hosts'][node].get('subnet')
                network.connect_nodes(node, parent_subnet)

            # Connect all subnets to their parent routers
            if isinstance(data, Subnet):
                parent_router = config['subnets'][node].get('default_route')
                network.connect_nodes(node, parent_router)

            # Connect all routers that have an upstream default route
            if isinstance(data, Router):
                parent_router = config['routers'][node].get('default_route', None)
                if parent_router:
                    network.connect_nodes(node, parent_router)

        return network



