import ipaddress

class Subnet:
    def __init__(self, name, default_route, ip_range):
        self.name = name
        self.default_route = default_route
        self.network = ipaddress.IPv4Network(f"{ip_range}", strict=False)
        ## not sure if subnets should have routes at this point
        #self.routes = []  # List of routes to other subnets or routers
        ## currently I think only routers and hosts should have ACLs
        #self.firewall_rules = {}  # List of firewall rules specific to this subnet

    def get_network_address(self) -> str:
        '''
        Returns the network address of the subnet
            i.e. '192.168.0.0'
        '''
        return str(self.network.network_address)

    def get_prefix_length(self) -> int:
        return self.network.prefixlen


    def get_max_num_hosts(self) -> int:
        '''
        Returns number of usable IP address in subnet.
        '''
        return self.network.num_addresses - 2
