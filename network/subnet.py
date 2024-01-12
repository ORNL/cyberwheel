import ipaddress

class Subnet:
    def __init__(self, name, default_route, ip_range):
        self.name = name
        self.default_route = default_route
        self.network = ipaddress.IPv4Network(f"{ip_range}", strict=False)
        self.routes = []  # List of routes to other subnets or routers
        self.firewall_rules = []  # List of firewall rules specific to this subnet

    def get_network_address(self):
        return str(self.network.network_address)

    def get_prefix_length(self):
        return self.network.prefixlen