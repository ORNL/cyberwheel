import ipaddress
from .network_object import NetworkObject


class Subnet(NetworkObject):
    def __init__(self, name, default_route, ip_range, firewall_rules=[]):
        '''
        :param str name: name of router
        :param str default_route: name of router that provides default route
        :param str ip_range: cidr IP range (i.e. 192.168.0.0/24)
        :param list[dict] firewall_rules: list offirewall rules (emtpy rules = allow all)
                Example:
                [
                    {
                        'name': 'https',
                        'src': 'some_subnet'
                        'port': 443,
                        'proto': 'tcp',
                        'desc': 'Allow all src to all dest on dest port 443'
                    },
                    {
                        'name': 'foo'
                        'src': 'some_host'
                        'port': 3128,
                        'proto': 'tcp',
                        'desc': 'Allow some_host to use foo service'
                    }
                ]
        '''
        super().__init__(name, firewall_rules)
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
