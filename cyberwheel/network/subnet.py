import ipaddress as ipa
from typing import Union
from .network_object import NetworkObject

# from .host import Host  # this is causing circular import issues
from .router import Router


class Subnet(NetworkObject):
    def __init__(
        self, name, default_route, ip_range, router: Router, firewall_rules=[], **kwargs
    ):
        """
        :param str name: name of router
        :param str default_route: name of router that provides default route
        :param str ip_range: cidr IP range (i.e. 192.168.0.0/24)
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
        :param (IPv4Address | IPv6Address] **dns_server: default DNS server for subnet
        """
        super().__init__(name, firewall_rules)
        # default route
        try:
            if default_route is not None:
                self.default_route = ipa.ip_address(default_route)
        except ValueError as e:
            print(
                f"default route ({default_route}) does not represent a valid IP address"
            )
            raise e

        # ip range of subnet
        try:
            # this should allow IPv4 or IPv6
            self.ip_network = ipa.ip_network(f"{ip_range}", strict=False)
        except ValueError as e:
            print("ip_range does not represent a valid IPv4 or IPv6 address")
            raise e
        self.available_ips = [ip for ip in self.ip_network.hosts()]
        self.connected_hosts = []
        self.router = router

        dns_server = kwargs.get("dns_server")
        if dns_server:
            try:
                self.dns_server = ipa.ip_address(dns_server)
            except ValueError as e:
                print(f"{dns_server} does not represent a valid IPv4 or IPv6 address")
                raise e
        else:
            self.dns_server = None

    def set_dns_server(self, ip: Union[ipa.IPv4Address, ipa.IPv6Address]):
        self.dns_server = ip

    def get_network_address(self) -> str:
        """
        Returns the network address of the subnet
            i.e. '192.168.0.0'
        """
        return str(self.ip_network.network_address)

    def get_prefix_length(self) -> int:
        return self.ip_network.prefixlen

    def get_max_num_hosts(self) -> int:
        """
        Returns number of usable IP address in subnet.
        """
        return self.ip_network.num_addresses - 2

    def get_unassigned_ips(self) -> list:
        return self.available_ips

    def get_num_unassigned_ips(self) -> int:
        return len(self.available_ips)

    def assign_dhcp_lease(self, host_obj):
        # get next available IP
        ip_lease = self.available_ips.pop(0)
        # update connected hosts
        self.connected_hosts.append(host_obj)
        # assign IP and DNS server
        host_obj.set_ip(ip_lease)
        host_obj.set_dns(self.dns_server)
        # assign default route if not already set
        if host_obj.default_route is None:
            host_obj.default_route = self.default_route

    def get_connected_hosts(self) -> list:
        return self.connected_hosts

    def get_connected_hostnames(self) -> list[str]:
        return [host.name for host in self.connected_hosts]
