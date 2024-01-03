import networkx as nx
import random
import ipaddress
import math

class Service:

    def __init__(self, name, host_ip, port, version):
        self.name = name
        self.host_ip = host_ip
        self.port = port 
        self.version = version

class Host:
    
    def __init__(self, host_name, subnet_name, host_type, os, services, ipaddress):
        self.host_name = host_name 
        self.subnet_name = subnet_name
        self.type = host_type
        self.os = os 
        self.services = services
        self.ipaddress = ipaddress
        self.target = False
        self.is_compromised = False

class Network:
    
    def __init__(self, number_subnets, hosts_per_subnet, number_targets):

        self.graph = nx.Graph()
        self.hosts = {}

        services = ["web_server", "ssh", "tcp", "rdp", "ftp"]

        subnets = self.generate_subnets(number_subnets, hosts_per_subnet)

        for i in range(0,number_subnets): 

            subnet = subnets[i]
            subnet_name = "subnet" + str(i)

            network = ipaddress.IPv4Network(subnet, strict=False)

            for n in range(0,hosts_per_subnet): 
                host_name = subnet_name + "host" + str(n)

                self.graph.add_node(host_name)

                host = Host(host_name, subnet_name, "user", "Windows", random.sample(services, 3), network[n])

                self.hosts[host_name] = host
        
        # frequently need to map host name to observation space index
        self.host_to_index = {}
        index = 0
        for key in self.hosts.keys():
            self.host_to_index[key] = index
            index += 1

        # Connect all nodes on same subnet
        edges = [(node1, node2) for node1 in self.hosts.keys() for node2 in self.hosts.keys() if self.hosts[node1].subnet_name == self.hosts[node2].subnet_name]
        self.graph.add_edges_from(edges)

        # With some probability, connect nodes between subnets
        edges = [(node1, node2) for node1 in self.hosts.keys() for node2 in self.hosts.keys() if self.hosts[node1].subnet_name != self.hosts[node2].subnet_name and random.random() < .01]
        print(edges)
        self.graph.add_edges_from(edges)

        # Randomly assign 1 host where red agent starts
        self.source = random.choice(list(self.hosts.keys()))

        # Compute the shortest path lengths from source to all reachable nodes
        length = nx.single_source_shortest_path_length(self.graph, self.source)

        # Set the target to one of the nodes that is furthest away
        self.target = self.source
        for node in length:
            if length[node] > length[self.target]:
                self.target = node 

        self.hosts[self.target].target = True

    '''
    Create a set of subnets to draw from - currently it generates many more than actually needed 
    '''
    def generate_subnets(self, number_subnets, number_hosts):
        
        network = ipaddress.IPv4Network('192.168.0.0/16')

        bits = math.ceil(math.log2(number_hosts + 2))
        prefix_length = 32 - bits

        subnets = list(network.subnets(new_prefix=prefix_length))

        return subnets



