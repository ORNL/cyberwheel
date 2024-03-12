import ipaddress as ipa
from .network_object import NetworkObject, Route
#from .subnet import Subnet


class Router(NetworkObject):
    def __init__(self, name, firewall_rules=[], **kwargs):
        """
        :param str name: name of router
        :param (ip_address | None) default_route: IP object of default route
        :param list[str] routes: additional routes in the routing table
                (abstracted to router or subnet names)
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
        """
        super().__init__(name, firewall_rules)
        # TODO
        self.default_route = None
        # TODO: set routes after init?
        #self.routes = routes  # List of routes to other subnets or routers
        self.interfaces = {}

    def __str__(self) -> str:
        str = f'Router(name="{self.name}", default_route="{self.default_route}", '
        str += f'routes="{self.routes}"'
        return str


    def __repr__(self) -> str:
        str = f'Router(name={self.name!r}, default_route={self.default_route!r}, '
        str += f'routes={self.routes!r}, firewall_rules={self.firewall_rules!r}'
        return str

    
    def set_interface_ip(self, interface_name: str, ip: ipa.IPv4Address |ipa.IPv6Address):
        self.interfaces.update({interface_name: ip})


    #def get_interface_ip(self, interface_name: str) -> ipa.IPv4Address | ipa.IPv6Address:
    def get_interface_ip(self, interface_name: str):
        try:
            return self.interfaces.get(interface_name)
        except KeyError as e:
            # TODO
            raise e


    def add_subnet_interface(self, subnet) -> None:
        ip = subnet.available_ips.pop(0)
        self.set_interface_ip(subnet.name, ip)
