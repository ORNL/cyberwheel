from ipaddress import IPv4Address, IPv6Address
from typing import List, Dict, Union
from copy import deepcopy
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service

IPAddress = Union[IPv4Address, IPv6Address, None]

# TODO Needs to be updated as the network implementation changes.
class Alert:
    FIELD_NAMES = set(["src_host", "dst_hosts", "services"])

    def __init__(
        self,
        src_host: Host | None = None,
        dst_hosts: List[Host] = [],
        services: List[Service] = [],
    ):
        self.src_host: Host | None = src_host
        self.dst_hosts: List[Host] = dst_hosts
        self.services: List[Service] = services

        self.src_ip: IPAddress = src_host.ip_address
        self.dst_ips: List[IPAddress] = [h.ip_address for h in dst_hosts]
        self.dst_ports: List[str] = [s.port for s in services]

        self.techniques = techniques # Use to determine probabilty of detection
        

    def add_dst_host(self, host: Host) -> None:
        self.dst_hosts.append(host)
        self.dst_ips.append(host.ip_address)

    def add_src_host(self, host: Host) -> None:
        self.src_host = host

    def add_service(self, service: Service) -> None:
        self.services.append(service)
        self.dst_ports.append(service.port)

    def remove_src_host(self) -> None:
        self.src_host = None

    def remove_dst_host(self, host: Host) -> None:
        if host in self.dst_hosts:
            self.dst_hosts.remove(host)

    def remove_service(self, service: Service) -> None:
        if service in self.services:
            self.services.remove(service)

    def to_dict(self) -> Dict:
        d = deepcopy(self.__dict__)
        for k in self.__dict__.keys():
            if k not in self.FIELD_NAMES:
                d.pop(k)
        return d

    def __eq__(self, __value: object) -> bool:
        assert isinstance(__value, Alert)
        src_host = True if self.src_host == __value.src_host else False
        dst_hosts = True if len(self.dst_hosts) == len(__value.dst_hosts) else False
        if dst_hosts:
            for host in self.dst_hosts:
                if host not in __value.dst_hosts:
                    dst_hosts = False
        services = True if len(self.services) == len(__value.services) else False
        if services:
            for service in self.services:
                if service not in __value.services:
                    services = False
        if src_host and dst_hosts and services:
            return True
        return False

    def __str__(self) -> str:
        return f"Alert: dst_hst: {[str(h) for h in self.dst_hosts]}, services: {[str(s) for s in self.services]}"
