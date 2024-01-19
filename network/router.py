class Router:
    def __init__(self, name, default_route, routes=[], firewall_rules={}):
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
        self.name = name
        self.default_route = default_route
        self.routes = routes  # List of routes to other subnets or routers
        self.firewall_rules = firewall_rules  # dict of firewall rules specific to this router


    def get_default_route(self) -> str:
        return self.default_route


    def get_routes(self) -> list[str]:
        # should the default route be preppended to this list??
        return self.routes.append(self.default_route)


    def add_firewall_rule(self, rule):
        '''
        Adds new firewall rule(s)

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
        # if a new rule is added that has overlapping keys (i.e. service name)
        # with an existing rule it will overwrite the previous existing rule
        self.firewall_rules.update(rule)


    def remove_firewall_rule(self, rule_name: str):
        '''
        Removes an existing firewall rule

        :param str rule_name: service name of existing fw rule
        '''
        try:
            self.firewall_rules.pop(rule_name)
        except KeyError as e:
            # TODO: raise custom exception here?
            raise e
