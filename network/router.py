from .network_object import NetworkObject


class Router(NetworkObject):
    def __init__(self, name, default_route=None, routes=[], firewall_rules=[]):
        '''
        :param str name: name of router
        :param str default_route: name of router that provides default route
        :param list[str] routes: additional routes in the routing table
                (abstracted to router or subnet names)
        :param dict: firewall_rules: firewall rules dict (emtpy rules = allow all)
                Example:
                {'service-name':
                    {'port': 443,
                     'proto': 'tcp',
                     'desc': 'Allow all src to all dest on dest port 443'},
                 'foo service':
                    {'port': 3128,
                     'proto': 'tcp',
                     'src': ['subnet_a', 'subnet_b'],
                     'desc': 'Allow only subnet_a and subnet_b to use foo service'
                     }
                }
        '''
        super().__init__(name, firewall_rules)
        self.default_route = default_route
        self.routes = routes  # List of routes to other subnets or routers


    def get_default_route(self):
        return self.default_route


    def get_routes(self) -> list[str]:
        # should the default route be preppended to this list?
        return self.routes.append(self.default_route)
