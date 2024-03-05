import ipaddress as ipa
import json
from pydantic import BaseModel
import random
from .network_object import NetworkObject, Route, FirewallRule
from .service import Service
from .subnet import Subnet

# from .router import Router



class HostType(BaseModel):
    name: str | None = None
    services: list[Service] = []
    decoy: bool = False


class Host(NetworkObject):
    def __init__(self, name: str, subnet: Subnet, type: HostType, **kwargs):
        '''
        :param str name: name of host
        :param Subnet subnet: subnet to be connected to
        :param str type: type of host
        :param list[FirewallRule] | list[None] **firewall_rules: list of FirewallRules
        :param list[Service] | list[None] **services: list of services
        '''
        super().__init__(name, kwargs.get('firewall_rules', []))
        self.subnet: Subnet = subnet
        self.type: HostType = type
        self.services: list[Service] | None = kwargs.get('services')
        self.is_compromised: bool = False  # Default to not compromised
        self.mac_address = self._generate_mac_address()
        self.default_route = None
        self.routes = set()
        self.decoy = False

    def __str__(self) -> str:
        str = f'Host(name="{self.name}", type="{self.type}", '
        str += f'subnet="{self.subnet.name}"'
        return str


    def __repr__(self) -> str:
        str = f'Host(name={self.name!r}, type={self.type!r}, '
        str += f'subnet={self.subnet!r}, firewall_rules={self.firewall_rules!r}, '
        str += f'services={self.services!r}, dns_server={self.dns_server!r}'
        return str


    def _generate_mac_address(self):
        def _generate_hextet() -> str:
            return "{:02x}".format(random.randint(0, 255))

        mac_prefix = "46:6f:6f"
        return mac_prefix + ":{}:{}:{}".format(
            _generate_hextet(), _generate_hextet(), _generate_hextet()
        )

    def set_ip(self, ip: ipa.IPv4Address | ipa.IPv6Address):
        '''
        Manually set IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        '''
        self.ip_address = ip


    def set_ip_from_str(self, ip: str) -> None:
        '''
        Manually set IP address of host from a given str

        :param str ip: IP
        '''
        ip_obj = self.generate_ip_object(ip)
        self.ip_address = ip_obj


    def set_dns(self, ip: ipa.IPv4Address | ipa.IPv6Address):
        '''
        Manually set DNS IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        '''
        self.dns_server = ip


    def set_dns_from_str(self, ip: str) -> None:
        '''
        Manually set DNS IP address of host from a given str

        :param str ip: IP
        '''
        ip_obj = self.generate_ip_object(ip)
        self.dns_server = ip_obj



    def get_dhcp_lease(self):
        # this also assigns the host's DNS server
        self.subnet.assign_dhcp_lease(self)

    def define_services(self, services: list[Service]):
        self.services = services


    #def define_services_from_host_type(self, host_types_file=None):
    #    # TODO: not sure the best way to handle relative files here...
    #    if host_types_file is None:
    #        host_types_file = 'resources/metadata/host_definitions.json'
    #    # load host type definitions
    #    with open(host_types_file) as f:
    #        data = json.load(f)

    #    # create instace of each Service()
    #    for host_type in data.get('host_types'):
    #        defined_type = host_type.get('type')
    #        if self.type == defined_type.lower():
    #            for service in defined_type.get('services'):
    #                self.services.append(Service(service.get('name'),
    #                                     service.get('port'),
    #                                     service.get('protocol'),
    #                                     service.get('version'),
    #                                     service.get('vulnerabilities'))
    #                                    )


    def get_services(self) -> list[Service] | list:
        return self.services

    def add_service(self, name: str, port: int, protocol="tcp", version=None, vulns=[]):
        """
        Adds a service to the defined services list for a host
        """
        service = Service(name, port, protocol, version, vulns)
        self.services.append(service)

    def remove_service(self, service_name: str):
        """
        Removes an existing service from defined services for host

        :param str service_name: name of existing fw rule
        """
        if self.services is None:
            return
        # iterate over existing services and discard if service.name equals
        # the service_name param
        updated_services = [
            service for service in self.services if service.name != service_name
        ]

        # update services
        self.services = updated_services

    # TODO: make this work for IPv6 as well
    def get_routing_table(self, ipv6: bool = False):
        routes = self.routes
        if ipv6:
            slash_zero_net = ipa.ip_network('::/0')
        else:
            slash_zero_net = ipa.ip_network('0.0.0.0/0')
        routes.add({'dest': slash_zero_net, 'via': self.default_route})
        return routes


    def add_route(self,
                  dest: ipa.IPv4Network | ipa.IPv6Network,
                  via: ipa.IPv4Address | ipa.IPv6Address):
        route = Route(dest=dest, via=via)
        self.routes.add(route)


    def add_routes_from_dict(self, routes: list[dict]):
        for route in routes:
            # make sure 'dest' is an ip_network object
            try:
                if not isinstance(route['dest'], ipa.IPv4Network | ipa.IPv6Network):
                    dest = self.generate_ip_network_object(route['dest'])
                else:
                    dest = route['dest']
            except ValueError as e:
                # TODO: custom exception here?
                raise e
            # make sure 'via' is an ip_address object
            try:
                if not isinstance(route['via'], ipa.IPv4Address | ipa.IPv6Address):
                    via = self.generate_ip_object(route['via'])
                else:
                    via = route['via']
            except ValueError as e:
                # TODO: custom exception here?
                raise e

            self.add_route(dest, via)


    def get_nexthop_from_routes(self,
                                dest_ip: ipa.IPv4Address | ipa.IPv6Address):
        '''
        Return most specific route that matches dest_ip

        :param (IPv4Address | IPv6Address) dest_ip: destination IP object
        :returns (IPv4Network | IPv6Network):
        '''
        # sort routes
        routes = sorted(self.routes)

        # reverse list because ipaddress' logical operators are weird
        # and sort by subnet mask bits instead of number of ips in subnet
        # i.e. this should give us a list with smallest subnets first
        routes.reverse()

        # find most specific match in routes
        for route in routes:
            if dest_ip in route['dest'].hosts():
                return route['via']

        # return default_route if no matche
        return self.default_route
