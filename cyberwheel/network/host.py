from __future__ import annotations

import ipaddress as ipa
from pydantic import BaseModel
import random
import json
from typing import Union, List, Type
from .network_object import NetworkObject
from .service import Service
from .subnet import Subnet
from .process import Process
from .command import Command


class HostType(BaseModel):
    name: str | None = None
    services: set[Service] = set()
    processes: list[Process] = []
    cve_list: set[str] = set()
    decoy: bool = False
    os: str = ""


# not using this yet
class ArpEntry(BaseModel):
    mac: str
    ip: ipa.IPv4Network | ipa.IPv6Network


# not using this yet
class ArpTable(BaseModel):
    table: list[ArpEntry]


class Host(NetworkObject):
    def __init__(self, name: str, subnet: Subnet, host_type: HostType | None, **kwargs):
        """
        :param str name: name of host
        :param Subnet subnet: subnet to be connected to
        :param str host_type: type of host
        :param list[FirewallRule] | list[None] **firewall_rules: list of FirewallRules
        :param list[Service] | list[None] **services: list of services
        """
        super().__init__(name, kwargs.get("firewall_rules", []))
        self.subnet: Subnet = subnet
        self.host_type: HostType | None = host_type
        self.services: list[Service] = kwargs.get("services", [])
        self.is_compromised: bool = False  # Default to not compromised
        self.mac_address = self._generate_mac_address()
        self.default_route = None
        self.routes = set()
        self.decoy = False
        self.os = "windows"  # 'windows', 'macos', or 'linux'
        self.isolated = False  # For isolate action
        self.interfaces = []
        self.restored = False
        # apply any HostType details
        if self.host_type:
            self._apply_host_type(self.host_type)
        self.vulnerabilities = []
        self.processes = []
        self.command_history = []
        self.dns_server = None

    def __str__(self) -> str:
        str = f'Host(name="{self.name}", subnet="{self.subnet.name}", '
        str += f' host_type="{self.host_type}"'
        return str

    def __repr__(self) -> str:
        str = f"Host(name={self.name!r}, subnet={self.subnet!r}, "
        str += f"host_type={self.host_type!r}, firewall_rules={self.firewall_rules!r}, "
        str += f"services={self.services!r}, dns_server={self.dns_server!r}"
        return str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Host):
            return False
        return self.name == other.name

    def _apply_host_type(self, host_type: HostType) -> None:
        """
        Override/update Host attributes from defined HostType

        For example, this allows the flexibility to use services defined in
        the HostType as well as custom defined services elsewhere (i.e. the
        network config file).

        :param HostType host_type: Host type to apply to self
        """
        # using sets to join and dedup
        deduped_services = []
        if self.services:
            host_type_services = set(host_type.services)
            host_services = set(self.services)
            deduped_services = list(host_services.union(host_type_services))

        self.services: list[Service] = deduped_services
        self.decoy: bool = host_type.decoy

    def _generate_mac_address(self) -> str:
        """Generates a random MAC address"""

        def _generate_hextet() -> str:
            return "{:02x}".format(random.randint(0, 255))

        # TODO: should we randomly generate all 6 hextets?
        mac_prefix = "46:6f:6f"
        return mac_prefix + ":{}:{}:{}".format(
            _generate_hextet(), _generate_hextet(), _generate_hextet()
        )

    def set_ip(self, ip: ipa.IPv4Address | ipa.IPv6Address):
        """
        Manually set IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        """
        self.ip_address = ip

    def set_ip_from_str(self, ip: str) -> None:
        """
        Manually set IP address of host from a given str

        :param str ip: IP
        :raises ValueError:
        """
        ip_obj = self.generate_ip_object(ip)
        self.ip_address = ip_obj

    def set_dns(self, ip: ipa.IPv4Address | ipa.IPv6Address):
        """
        Manually set DNS IP address of host

        :param (IPv4Address | IPv6Address) ip: IP object
        """
        self.dns_server = ip

    def set_dns_from_str(self, ip: str) -> None:
        """
        Manually set DNS IP address of host from a given str

        :param str ip: IP
        :raises ValueError:
        """
        ip_obj = self.generate_ip_object(ip)
        self.dns_server = ip_obj

    def get_dhcp_lease(self):
        self.subnet.assign_dhcp_lease(self)

    def define_services(self, services: List[Service]):
        self.services = services

    def get_services(self) -> Union[List[Service], list]:
        return self.services

    def add_service(self, name: str, port: int, **kwargs) -> None:
        """
        Adds a service to the defined services for a host

        :param str name: name of service
        :param int port: port service is listening on
        :param str **protocol: optional, default='tcp'
        :param str **version: optional, default=''
        :param list **vulns: optional, default=[]
        :param str **description: optional, default=''
        :param bool **decoy: optional, default=False
        """
        service = Service(
            name=name,
            port=port,
            protocol=kwargs.get("protocol", "tcp"),
            version=kwargs.get("version", ""),
            vulns=kwargs.get("vulns", []),
            description=kwargs.get("desc", ""),
            decoy=kwargs.get("decoy", False),
        )
        if service not in self.services:
            self.services.append(service)
        else:
            # update existing service if it already exists
            for existing_service in self.services:
                if service == existing_service:
                    existing_service = service

    def remove_service(self, service_name: str) -> None:
        """
        Removes an existing service from defined services for host

        :param str service_name: name of existing fw rule (case insensitive)
        """
        if self.services is None:
            return
        # iterate over existing services and discard if service.name equals
        # the service_name param
        updated_services = [
            service
            for service in self.services
            if service.name.lower() != service_name.lower()
        ]

        # update services
        self.services = updated_services

    def add_process(self, process_name: str, process_privilege_level: str):
        self.processes.append(
            Process(name=process_name, privilege=process_privilege_level)
        )
    
    def run_command(self, command_executor, command_content, privilege):
        self.command_history.append(Command(command_executor, command_content, privilege))

    def remove_process(self, process_name: str):
        new_processes = [p for p in self.processes if p.name != process_name]
        self.processes = new_processes

    def kill_malicious_processes(self):
        self.processes = []
