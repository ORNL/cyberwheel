import ipaddress as ipa
from typing import Union
from .network_object import NetworkObject


class Router(NetworkObject):
    def __init__(self, name, default_route=None, routes=[], firewall_rules=[]):
        '''
        :param str name: name of router
        :param str default_route: name of router that provides default route
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
        '''
        super().__init__(name, firewall_rules)
        self.default_route = default_route
        self.routes = routes  # List of routes to other subnets or routers
        self.interfaces = {}


    def get_default_route(self):
        return self.default_route


    def get_routes(self):
        # should the default route be preppended to this list?
        routes = self.routes.append(self.default_route)
        return routes

    
    def set_interface_ip(self, interface_name: str, ip: Union[ipa.IPv4Address,ipa.IPv6Address]):
        self.interfaces.update({interface_name: ip})


    def get_interface_ip(self, interface_name: str) -> Union[ipa.IPv4Address, ipa.IPv6Address, None]:
        return self.interfaces.get(interface_name)

