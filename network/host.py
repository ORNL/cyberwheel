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

class Host:
    def __init__(self, name, type, subnet):
        self.name = name
        self.type = type
        self.subnet = subnet
        self.firewall_rules = []  # List of firewall rules specific to this host
        self.is_compromised = False  # Default to not compromised

    def add_firewall_rule(self, rule):
        self.firewall_rules.append(rule)


