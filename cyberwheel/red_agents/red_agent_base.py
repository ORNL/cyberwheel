from abc import ABC, abstractmethod
from ipaddress import IPv4Address, IPv6Address
from typing import Type, List, Any, Iterable

from cyberwheel.red_actions.red_base import ARTAction
from cyberwheel.network.network_base import Host
from cyberwheel.network.service import Service
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.red_actions.actions import ARTKillChainPhase
from cyberwheel.red_actions.technique import Technique
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

class RedAgentResult:
    def __init__(
        self,
        action: ARTKillChainPhase | Technique,
        src_host: Host,
        target_host: Host,
        success: bool,
        obs: Iterable[int] = None,
        action_results: RedActionResults = None,
    ):
        """
        - `name`: name of the red action executed
        - `success`: whether this action successfully executed or not
        """
        self.action = action
        self.src_host = src_host
        self.target_host = target_host
        self.success = success
        self.obs = obs
        self.action_results = action_results

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
        leader=False,
        on_host=False
    ):
        self.last_step = last_step
        self.scanned = scanned
        self.sweeped = sweeped

        self.ip_address = ip_address
        self.services = services
        self.vulnerabilities = vulnerabilities
        self.type = type
        self.discovered = False
        self.escalated = False
        self.routes = None
        self.impacted = False
        self.is_leader = leader
        self.on_host = False

    def scan(self):
        self.scanned = True

    def is_scanned(self):
        return self.scanned

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

    def __init__(self, initial_host: Host = None):
        self.history: List[dict[str, Any]] = (
            []
        )  # List of StepInfo objects detailing step information by step
        self.red_action_history: List[RedActionResults] = []
        self.hosts = (
            {}
        )  # Hosts discovered, and whether or not they've been scanned successfully yet
        self.subnets = (
            {}
        )  # Subnets discovered, and last killchainstep performed on them (by index)
        self.step = -1
        if initial_host:
            self.hosts[initial_host.name] = KnownHostInfo(
                ip_address=initial_host.ip_address, on_host=True
            )
            self.subnets[initial_host.subnet.name] = KnownSubnetInfo()

    def update_step(
        self,
        action: Type[ARTAction],
        red_action_results: RedActionResults,
    ):
        """
        Updates the history of the red agent at a given step with action and RedActionResults metadata
        """
        self.step += 1
        target_host_metadata = red_action_results.metadata[
            red_action_results.target_host.name
        ]
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
                "success": red_action_results.attack_success,
            }
        )
        self.red_action_history.append(red_action_results)

    def recent_history(self) -> RedActionResults:
        return self.red_action_history[-1]
