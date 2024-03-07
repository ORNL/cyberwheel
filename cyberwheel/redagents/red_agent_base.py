from ipaddress import IPv4Address, IPv6Address
import networkx as nx
import numpy as np
from abc import ABC, abstractmethod
from typing import Type, List

from ray import init
from red_actions.red_base import RedAction
from network.network_base import Host, Subnet
from network.service import Service


class RedAgent(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def act(self):
        pass


class KnownHostInfo:
    def __init__(
        self,
        last_step: int = -1,
        scanned: bool = False,
        ip_address: IPv4Address | IPv6Address | None = None,
        type: str = "Unknown",
        services: List[Service] = [],
        vulnerabilities: List[str] = [],
    ):
        self.last_step = last_step
        self.ports_scanned = scanned
        self.ip_address = ip_address
        self.services = services
        self.vulnerabilities = vulnerabilities
        self.type = type

    def scan(self):
        self.ports_scanned = True

    def is_scanned(self):
        return self.ports_scanned

    def update_killchain_step(self):
        self.last_step += 1

    def get_next_step(self) -> int:
        return self.last_step + 1


class KnownSubnetInfo:
    def __init__(self, scanned: bool = False):
        self.scanned = scanned
        self.connected_hosts = []
        self.available_ips = []

    def scan(self):
        self.scanned = True

    def is_scanned(self):
        return self.scanned


class StepInfo:
    def __init__(self, step: int, action: Type[RedAction], success: bool):
        self.step = step
        self.action = action
        self.success = success


class AgentHistory:
    def __init__(self, initial_host: Host):
        self.history = []  # List of StepInfo objects detailing step information by step
        self.hosts = (
            {}
        )  # Hosts discovered, and whether or not they've been scanned successfully yet
        self.subnets = (
            {}
        )  # Subnets discovered, and last killchainstep performed on them (by index)
        self.step = -1

        self.hosts[initial_host] = KnownHostInfo(
            last_step=2,
            scanned=True,
            ip_address=initial_host.ip_address,
            type=initial_host.type,
            services=initial_host.services,
            vulnerabilities=initial_host.cves,
        )
        self.hosts[initial_host].ip_address = initial_host.ip_address
        self.subnets[initial_host.subnet] = KnownSubnetInfo()

    def update_step(self, action: Type[RedAction], success: bool):
        self.step += 1
        self.history.append(StepInfo(self.step, action=action, success=success))
