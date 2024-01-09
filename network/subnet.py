import ipaddress

class Subnet:
    def __init__(self, name, network_address, prefix_length):
        self.name = name
        self.network = ipaddress.IPv4Network(f"{network_address}/{prefix_length}", strict=False)
        self.hosts = []

    def get_network_address(self):
        return str(self.network.network_address)

    def get_prefix_length(self):
        return self.network.prefixlen