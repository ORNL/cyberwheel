from ipaddress import IPv4Address, IPv6Address
import networkx as nx
import numpy as np
from abc import ABC, abstractmethod
from typing import Type, List, Tuple

from ray import init
from cyberwheel.red_actions.red_base import RedAction
from cyberwheel.network.network_base import Host, Subnet
from cyberwheel.network.service import Service
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.reward.reward import RewardMap


class RedAgent(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def act(self) -> str:
        pass
    
    @abstractmethod
    def get_reward_map(self) -> RewardMap:
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
        self.vulnerabilities = vulnerabilities  # TODO: Service-level host
        self.type = type
        self.routes = None  # TODO: If route not set, defaults to Router and local Subnet-level network

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
    def __init__(
        self, step: int, action: Tuple[Type[RedAction], Host, Host], success: bool
    ):
        self.step = step
        self.action = action
        self.success = success
        self.info = f"{action[0].__name__} from {action[1].name} to {action[2].name} - {'Succeeded' if success else 'Failed'}"


class AgentHistory:
    def __init__(self, initial_host: Host):
        self.history: List[StepInfo] = (
            []
        )  # List of StepInfo objects detailing step information by step
        self.red_action_history: List[RedActionResults] = []
        self.mapping = {}
        self.hosts = (
            {}
        )  # Hosts discovered, and whether or not they've been scanned successfully yet
        self.subnets = (
            {}
        )  # Subnets discovered, and last killchainstep performed on them (by index)
        self.step = -1

        self.hosts[initial_host.name] = KnownHostInfo(
            last_step=1,
            scanned=True,
            ip_address=initial_host.ip_address,
            type=initial_host.host_type,
            services=initial_host.services,
            vulnerabilities=initial_host.cves,
        )
        self.hosts[initial_host.name].ip_address = initial_host.ip_address
        self.subnets[initial_host.subnet.name] = KnownSubnetInfo()

        for h in initial_host.subnet.connected_hosts:
            self.hosts[initial_host.name] = KnownHostInfo()
            self.mapping[initial_host.name] = initial_host

        self.mapping[initial_host.name] = initial_host
        self.mapping[initial_host.subnet.name] = initial_host.subnet

    def update_step(
        self,
        action: Tuple[Type[RedAction], Host, Host],
        success: bool,
        red_action_results: RedActionResults,
    ):
        self.step += 1
        self.history.append(StepInfo(self.step, action=action, success=success))
        self.red_action_history.append(red_action_results)

    def recent_history(self) -> RedActionResults:
        return self.red_action_history[-1]
