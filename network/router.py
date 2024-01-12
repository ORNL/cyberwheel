class Router:
    def __init__(self, name, default_route):
        self.name = name
        self.default_route = default_route
        self.routes = []  # List of routes to other subnets or routers
        self.firewall_rules = []  # List of firewall rules specific to this router
