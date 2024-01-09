import networkx as nx
import random
import ipaddress
from .host import Host
from .subnet import Subnet
from .service import Service
from .network_base import Network

class RandomNetwork(Network):
    def __init__(self, number_subnets, hosts_per_subnet, connect_subnets_probability=0.5):
        super().__init__()
        self.number_subnets = number_subnets
        self.hosts_per_subnet = hosts_per_subnet
        self.connect_subnets_probability = connect_subnets_probability
        self.generate_random_network()

    def generate_random_network(self):
        subnets = []
        for subnet_id in range(1, self.number_subnets + 1):
            subnet_name = f"Subnet{subnet_id}"
            subnet_network = f"192.168.{subnet_id}.0"  # Example network address
            subnet_prefix_length = random.randint(24, 30)  # Random prefix length
            subnet = Subnet(subnet_name, subnet_network, subnet_prefix_length)
            subnets.append(subnet)
            self.add_subnet(subnet)

            for host_id in range(1, self.hosts_per_subnet + 1):
                host_name = f"Host{subnet_id}-{host_id}"
                host_type = random.choice(["Server", "Client"])
                host_ip = str(subnet.network.network_address + host_id)  # Assign IP addresses sequentially
                services = self.generate_random_services()
                host = Host(host_name, host_type, services, host_ip, "Windows")
                self.add_host(host)
                self.connect_host_to_subnet(host.name, subnet.name)

        # Connect subnets randomly
        for i in range(0, len(subnets)-1):
                #if subnet1 != subnet2 and random.random() < self.connect_subnets_probability:
            self.connect_subnets(subnets[i].name, subnets[i+1].name)

        self.draw()

    def generate_random_services(self):
        num_services = random.randint(1, 5)  # Generate a random number of services
        services = []
        for _ in range(num_services):
            port = random.randint(1, 65535)
            version = f"Version-{random.randint(1, 10)}"
            service_name = f"Service-{random.randint(100, 999)}"
            vulnerabilities = [f"CVE-{random.randint(1000, 9999)}" for _ in range(random.randint(0, 3))]
            service = Service(port, version, service_name, vulnerabilities)
            services.append(service)
        return services

# Example usage
#random_net = RandomNetwork(number_subnets=3, hosts_per_subnet=4, connect_subnets_probability=0.4)






