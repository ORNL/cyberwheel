class Service:
    def __init__(self, port, version, name, vulnerabilities=[]):
        self.port = port
        self.version = version
        self.name = name
        self.vulnerabilities = vulnerabilities