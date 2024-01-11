class Service:
    def __init__(self, port, version, name, protocol='tcp', vulnerabilities=[]):
        self.port = port
        self.protocol = protocol # i.e. tcp or udp
        self.version = version
        self.name = name
        self.vulnerabilities = vulnerabilities
