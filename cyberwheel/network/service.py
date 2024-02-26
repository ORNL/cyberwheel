class Service:
    def __init__(self, name, port, protocol="tcp", version=None, vulnerabilities=[]):
        self.name = name
        self.port = port
        self.protocol = protocol  # i.e. tcp, udp, or icmp
        self.version = version
        self.vulnerabilities = vulnerabilities

    def __eq__(self, __value: object) -> bool:
        if self.name == __value.name:
            return True
        return False
