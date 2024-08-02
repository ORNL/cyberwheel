from ipaddress import IPv4Address, IPv6Address
import networkx as nx
import numpy as np
import random
from abc import ABC, abstractmethod
from typing import Type, List, Tuple, Any

from ray import init
from cyberwheel.red_actions.red_base import ARTAction
from cyberwheel.network.network_base import Host, Subnet
from cyberwheel.network.service import Service
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.red_actions.actions.art_killchain_phases import ARTKillChainPhase
from cyberwheel.reward import RewardMap


class RedAgent(ABC):
    """
    Base class for Red Agent. Defines structure for any additional red agents to be added.
    """
    def __init__(self):
        pass

    @abstractmethod
    def act(self) -> Type[ARTKillChainPhase]:
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
    """
    Defines red agent's knowledge of a given host.

    *   last_step - Index of the last step of the killchain that was executed on this host. Default is -1
    *   scanned - Whether the Host has been Portscanned
    *   sweeped - Whether the Host's subnet has been Pingsweeped
    *   ip_address - IP Address of the Host
    *   type - The known type of the Host. Options: Unknown | User | Server
    *   services - The known services on the Host.
    *   vulnerabilities - The known vulnerabilities on the Host.
    """
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
    """
    Defines red agent's knowledge of a given subnet.

    *   scanned - Whether the Subnet has been pingsweeped
    *   connected_hosts - List of hosts in the subnet
    *   available_ips - The IP Addresses available for the subnet to distribute
    """
    def __init__(self, scanned: bool = False):
        self.scanned = scanned
        self.connected_hosts = []
        self.available_ips = []

    def scan(self):
        self.scanned = True

    def is_scanned(self):
        return self.scanned

class AgentHistory:
    """
    Defines history of red agent throughout the game.
    *   initial_host (required) - sets the initial entry host for the red agent to have a foothold on the network.
    *   history - List of metadata detailing red agent actions. Grows with each step.
    *   red_action_history - List of action results for every given step.
    *   mapping - preserves a mapping from host/subnet name to Host/Subnet object to allow information gathering
    *   hosts - dict of hostnames mapped to KnownHostInfo.
    *   subnets - dict of subnets mapped to KnownSubnetInfo.
    *   step - the last step of the simulation
    """
    def __init__(self, initial_host: Host):
        self.history: List[dict[str, Any]] = [] # List of StepInfo objects detailing step information by step
        self.red_action_history: List[RedActionResults] = []
        self.mapping = {}
        self.hosts = {}  # Hosts discovered, and whether or not they've been scanned successfully yet
        self.subnets = {} # Subnets discovered, and last killchainstep performed on them (by index)
        self.step = -1

        self.hosts[initial_host.name] = KnownHostInfo(ip_address=initial_host.ip_address)
        self.subnets[initial_host.subnet.name] = KnownSubnetInfo()
        self.mapping[initial_host.name] = initial_host
        self.mapping[initial_host.subnet.name] = initial_host.subnet

    def update_step(
        self,
        action: Type[ARTAction],
        red_action_results: RedActionResults,
    ):
        """
        Updates the history of the red agent at a given step with action and RedActionResults metadata
        """
        self.step += 1
        target_host_metadata = red_action_results.metadata[red_action_results.target_host.name]
        techniques = {
            "mitre_id": target_host_metadata["mitre_id"],
            "technique": target_host_metadata["technique"],
            "commands": target_host_metadata["commands"],
        }
        self.history.append(
            {
                "step": self.step,
                "action": action.__name__,
                "src_host": red_action_results.src_host.name,
                "target_host": red_action_results.target_host.name,
                "techniques": techniques,
                "success": red_action_results.attack_success
            }
        )
        self.red_action_history.append(red_action_results)

    def recent_history(self) -> RedActionResults:
        return self.red_action_history[-1]

class HybridSetList:
    """
    Defines a Hybrid Set/List object. This allows us to take advantage of the O(1) time complexity for
    membership checking of sets, while taking advantage of the O(1) time complexity of random.choice()
    of lists.
    """
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
