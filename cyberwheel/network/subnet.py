import ipaddress as ipa
import random
from .network_object import NetworkObject, Route
#from .host import Host  # this is causing circular import issues
from .router import Router


class Subnet(NetworkObject):
    def __init__(self, name, ip_range, router: Router, firewall_rules=[], **kwargs):
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
                self.dns_server = self.generate_ip_object(dns_server)
            except ValueError as e:
                print(f"{dns_server} does not represent a valid IPv4 or IPv6 address")
                raise e
        else:
            self.dns_server = None


    def __str__(self) -> str:
        return f'Subnet(name="{self.name}", ip_network="{self.ip_network}", router="{self.router.name}"'


    def __repr__(self) -> str:
        str = f'Subnet(name={self.name!r}, '
        str += f'default_route={self.default_route!r}, '
        str += f'ip_range={self.ip_network!r}, router={self.router!r}, '
        str += f'firewall_rules={self.firewall_rules!r}, '
        str += f'dns_server={self.dns_server!r}'
        return str


    def set_dns_server(self, ip: ipa.IPv4Address | ipa.IPv6Address):
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
        # get random IP from self.available_ips
        ip_lease = random.choice(self.available_ips)
        self.available_ips.remove(ip_lease)

        # update connected hosts
        self.connected_hosts.append(host_obj)

        # assign IP and DNS server
        host_obj.set_ip(ip_lease)
        host_obj.set_dns(self.dns_server)

        # assign route for subnet.ip_network
        host_ip = host_obj.ip_address
        host_obj.add_route(dest=self.ip_network, via=host_ip)

        # assign default route if not already set
        if host_obj.default_route is None:
            host_obj.default_route = self.default_route

    def get_connected_hosts(self) -> list:
        return self.connected_hosts


    def remove_connected_host(self, host) -> None:
        self.connected_hosts.remove(host)


    def get_connected_hostnames(self) -> list[str]:
        return [host.name for host in self.connected_hosts]


    def get_nexthop_from_routes(self):
        raise NotImplementedError()
