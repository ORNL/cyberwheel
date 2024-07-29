from ipaddress import IPv4Address, IPv6Address
import networkx as nx
import numpy as np
from abc import ABC, abstractmethod
from typing import Type, List, Tuple, Any

from ray import init
from cyberwheel.red_actions.red_base import RedAction, ARTAction
from cyberwheel.network.network_base import Host, Subnet
from cyberwheel.network.service import Service
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.red_actions.actions.killchain_phases import KillChainPhase
from cyberwheel.reward import RewardMap


class RedAgent(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def act(self) -> Type[KillChainPhase]:
        pass

    @abstractmethod
    def handle_network_change(self) -> None:
        pass

    @abstractmethod
    def select_next_target(self) -> tuple[Host | None, bool]:
        pass

    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        pass

    @abstractmethod
    def run_action(self) -> None:
        pass

    @abstractmethod
    def add_host_info(self) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class KnownHostInfo:
    def __init__(
        self,
        last_step: int = -1,
        scanned: bool = False,
        sweeped: bool = False,
        ip_address: IPv4Address | IPv6Address | None = None,
        type: str = "Unknown",
        services: List[Service] = [],
        vulnerabilities: List[str] = [],
    ):
        self.last_step = last_step
        self.ports_scanned = scanned
        self.ping_sweeped = sweeped
        self.ip_address = ip_address
        self.services = services
        self.vulnerabilities = vulnerabilities
        self.type = type
        self.routes = None  # TODO: If route not set, defaults to Router and local Subnet-level network
        self.impacted = False

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
        self,
        step: int,
        action: Tuple[Type[RedAction], Host, Host],
        techniques: dict[str, Any],
        success: bool,
    ):
        self.step = step
        self.action = action
        self.success = success
        self.info = f"{action[0].__name__} from {action[1].name} to {action[2].name} - {'Succeeded' if success else 'Failed'}"
        self.techniques = techniques


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
            vulnerabilities=initial_host.host_type.cve_list,
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
        action: Tuple[Type[RedAction] | Type[ARTAction], Host, Host],
        success: bool,
        red_action_results: RedActionResults,
    ):
        self.step += 1
        # print(action[2].host_type.services)
        target_host_metadata = red_action_results.metadata[action[2].name]
        techniques = {
            "mitre_id": target_host_metadata["mitre_id"],
            "technique": target_host_metadata["technique"],
            "commands": target_host_metadata["commands"],
        }
        self.history.append(
            StepInfo(self.step, action=action, techniques=techniques, success=success)
        )
        self.red_action_history.append(red_action_results)

    def recent_history(self) -> RedActionResults:
        return self.red_action_history[-1]


import random


class HybridSetList:
    def __init__(self):
        self.data_set = set()
        self.data_list = []

    def add(self, value):
        if value not in self.data_set:
            self.data_set.add(value)
            self.data_list.append(value)

    def remove(self, value):
        if value in self.data_set:
            self.data_set.remove(value)
            self.data_list.remove(value)

    def get_random(self):
        return random.choice(self.data_list)

    def check_membership(self, value):
        return value in self.data_set

    def length(self):
        return len(self.data_set)
