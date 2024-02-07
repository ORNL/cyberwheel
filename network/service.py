class Service:
    def __init__(self, name, port, protocol='tcp', version=None, vulnerabilities=[]):
        self.name = name
        self.port = port
        self.protocol = protocol # i.e. tcp, udp, or icmp
        self.version = version
        self.vulnerabilities = vulnerabilities
