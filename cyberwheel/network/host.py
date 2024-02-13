import ipaddress as ipa
import json
import random
from typing import Union
from .network_object import NetworkObject
from .service import Service
from .subnet import Subnet
#from .router import Router

class Host(NetworkObject):
    def __init__(self, name, type, subnet: Subnet, firewall_rules=[], **kwargs):
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
        :param list[Service] **services: list of services
        :param (IPv4Address | IPv6Address) **dns_server: IP of DNS server
        '''
        super().__init__(name, firewall_rules)
        self.type = type
        self.subnet = subnet
        self.ip_address = None
        self.is_compromised = False  # Default to not compromised
        self.services = kwargs.get('services', [])
        self.dns_server = kwargs.get('dns_server')
        self.mac_address = self._generate_mac_address()


    def _generate_mac_address(self):
        def _generate_hextet() -> str:
            return '{:02x}'.format(random.randint(0,255))
        mac_prefix = '46:6f:6f'
        return mac_prefix + ':{}:{}:{}'.format(_generate_hextet(),
                                               _generate_hextet(),
                                               _generate_hextet())

    def set_ip(self, ip: Union[ipa.IPv4Address, ipa.IPv6Address]):
        '''
        Manually set IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        '''
        self.ip_address = ip

    def set_dns(self, ip: Union[ipa.IPv4Address, ipa.IPv6Address]):
        '''
        Manually set IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        '''
        self.dns_server = ip


    def get_dhcp_lease(self):
        # this also assigns the host's DNS server
        self.subnet.assign_dhcp_lease(self)


    def define_services(self, services: list[Service]):
        self.services = services


    def define_services_from_host_type(self, host_types_file=None):
        # TODO: not sure the best way to handle relative files here...
        if host_types_file is None:
            host_types_file = 'resources/metadata/host_definitions.json'
        # load host type definitions
        with open(host_types_file) as f:
            data = json.load(f)

        # create instace of each Service()
        for host_type in data.get('host_types'):
            defined_type = host_type.get('type')
            if self.type == defined_type.lower():
                for service in defined_type.get('services'):
                    self.services.append(Service(service.get('name'),
                                         service.get('port'),
                                         service.get('protocol'),
                                         service.get('version'),
                                         service.get('vulnerabilities'))
                                        )


    def get_services(self) -> Union[list[Service], list]:
        return self.services


    def add_service(self, name: str, port: int, protocol='tcp', version=None, vulns=[]):
        '''
        Adds a service to the defined services list for a host
        '''
        service = Service(name, port, protocol, version, vulns)
        self.services.append(service)


    def remove_service(self, service_name: str):
        '''
        Removes an existing service from defined services for host

        :param str service_name: name of existing fw rule
        '''
        # iterate over existing services and discard if service.name equals
        # the service_name param
        updated_services = [service for service in self.services if 
                service.name != service_name]
        
        # update services
        self.services = updated_services

    def __eq__(self, __value: object) -> bool:
        if self.name == __value.name:
            return True
        return False

    def get_routes(self):
        pass
