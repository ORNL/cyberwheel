from ipaddress import IPv4Address, IPv6Address
from typing import Union
from .network_object import NetworkObject
from .subnet import Subnet


class Host(NetworkObject):
    def __init__(self, name, type, subnet: Subnet, firewall_rules=[]):
        '''
        :param str name: name of host
        :param str type: type of host
        :param Subnet subnet: subnet to be connected to
        :param list[dict] firewall_rules: list of firewall rules (emtpy rules = allow all)
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
        self.type = type
        self.subnet = subnet
        self.is_compromised = False  # Default to not compromised


    def set_ip(self, ip: Union[IPv4Address, IPv6Address]):
        self.ip_address = ip

