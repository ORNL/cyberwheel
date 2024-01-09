import ipaddress

class Host:
    def __init__(self, name, host_type, services, ip_address, os):
        self.name = name
        self.host_type = host_type
        self.services = services
        self.ip_address = ipaddress.IPv4Address(ip_address)
        self.os = os 
        self.value = 1
        self.is_compromised = False


