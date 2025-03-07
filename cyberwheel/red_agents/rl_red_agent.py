import importlib
import yaml
import numpy as np

from typing import Iterable

from cyberwheel.network.network_base import Network, Host
from cyberwheel.observation import RedObservation
from cyberwheel.red_actions.actions import (
    ARTKillChainPhase,
    ARTPingSweep,
    ARTPortScan,
    ARTDiscovery,
    ARTLateralMovement,
    ARTPrivilegeEscalation,
    ARTImpact
)
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.red_agents import ARTAgent
from cyberwheel.red_agents.red_agent_base import RedAgentResult
from cyberwheel.reward.reward_base import RewardMap


class RLRedAgent(ARTAgent):
    """
    RL Red Agent environment. Tracks hosts that it has discovered, to build its observation space.
    The action space is defined by the number of actions in the killchain and the number of hosts 
    it has in its view. Depending on configuration, can be trained to attack servers, users, all hosts,
    or just explore quietly.
    """

    def __init__(self, network: Network, args) -> None:
        super().__init__(network, args, service_mapping=args.service_mapping)
        self.tracked_hosts = self.network.hosts.keys()
        self.observation = RedObservation(len(self.network.hosts) * 7 * 2)
        self.observation.add_host(self.current_host.name, on_host=True)
    
    def from_yaml(self) -> None:
        with open(self.config, "r") as f:
            contents = yaml.safe_load(f)

        # Get module import path
        self.killchain = [
            ARTPingSweep,
            ARTPortScan,
            ARTDiscovery,
            ARTLateralMovement,
            ARTPrivilegeEscalation,
            ARTImpact,
        ]

        

        self.reward_map = {}

        self.entry_host: Host = contents["entry_host"]
        self.current_host : Host = self.network.hosts[self.entry_host] if self.entry_host.lower() != "random" else self.network.get_random_user_host()

        # Initialize the action space
        as_class = contents['action_space']
        asm = importlib.import_module("cyberwheel.red_agents.action_space")
        self.action_space = getattr(asm, as_class)(self.killchain, self.current_host.name)

        for k, v in contents['actions'].items():
            self.reward_map[k] = (v["reward"]["immediate"], v["reward"]["recurring"])

    def act(self, action: int) -> RedAgentResult:
        art_action, target_host_name = self.action_space.select_action(
            action
        )  # Selects ART Action, should include the action and target host
        source_host = self.current_host
        target_host = self.network.hosts[target_host_name]
        success = False
        if self.validate_action(art_action, target_host_name):
            if art_action == ARTPingSweep or art_action == ARTPortScan:
                result = art_action(
                    self.current_host, target_host
                ).sim_execute()  # Executes the ART Action, returns results
            else:
                result = art_action(
                    self.current_host,
                    target_host,
                    self.services_map[target_host_name][art_action],
                ).sim_execute()  # Executes the ART Action, returns results
            success = result.attack_success
            self.handle_action(result)
        else:
            result = RedActionResults(source_host, target_host)
        
        return RedAgentResult(
            art_action, 
            source_host, 
            target_host, 
            success, 
            self.get_observation_space(),
            result
        )  # Returns what ARTAgent act() should, probably. Or the observation space?

    def handle_action(self, result: RedActionResults) -> None:
        if not result.attack_success:
            return
        action = result.action
        src_host = result.src_host.name
        target_host = result.target_host.name
        if action == ARTPingSweep:  # Adds pingsweeped hosts to obs
            self.observation.update_host(target_host, sweeped=True)
            hosts = result.metadata["sweeped_hosts"]
            for h in hosts:
                h_name = h.name
                if h_name in self.observation.obs.keys():
                    continue
                sweeped = h.subnet.name == result.target_host.subnet.name
                self.observation.add_host(h_name, sweeped=sweeped)
                self.action_space.add_host(h_name)
        elif action == ARTPortScan:  # Scans target host
            self.observation.update_host(target_host, scanned=True)
        elif action == ARTDiscovery:  # Discovers host type
            self.observation.update_host(target_host, discovered=True, type=result.target_host.host_type.name)
        elif action == ARTLateralMovement:  # Moves to target host
            self.observation.update_host(target_host, on_host=True)
            self.observation.update_host(src_host, on_host=False)
            self.current_host = result.target_host
        elif action == ARTPrivilegeEscalation:
            self.observation.update_host(target_host, escalated=True)
        elif action == ARTImpact:
            self.observation.update_host(target_host, impacted=True)

    def handle_network_change(self):
        current_hosts = self.network.hosts.keys()
        new_hosts = current_hosts - self.tracked_hosts
        for h in new_hosts:
            host = self.network.hosts[h]
            self.services_map[h] = self.get_valid_techniques_by_host(
                host, self.all_kcps
            )
            self.observation.add_host(h, sweeped=True)
            self.action_space.add_host(h)
        self.tracked_hosts = current_hosts

    def validate_action(self, action: ARTKillChainPhase, target_host: str) -> bool:
        host_view = self.observation.obs[target_host]
        if action == ARTPingSweep:  # valid if host.sweeped == False
            return not host_view.sweeped
        elif (
            action == ARTPortScan
        ):  # valid if host.scanned == False and host.sweeped == True
            return host_view.sweeped and not host_view.scanned
        elif (
            action == ARTDiscovery
        ):  # valid if host.scanned && host.sweeped && !host.discovered
            return host_view.sweeped and host_view.scanned and not host_view.discovered
        elif (
            action == ARTLateralMovement
        ):  # valid if host.scanned && host.sweeped && host.discovered && !host.on_target
            return (
                host_view.sweeped
                and host_view.scanned
                and host_view.discovered
                and not host_view.on_host
            )
        elif (
            action == ARTPrivilegeEscalation
        ):  # valid if host.scanned && host.sweeped && host.discovered && host.on_target && !host.escalated
            return (
                host_view.sweeped
                and host_view.scanned
                and host_view.discovered
                and host_view.on_host
                and not host_view.escalated
            )
        elif (
            action == ARTImpact
        ):  # valid if host.scanned && host.sweeped && host.discovered && host.on_target && host.escalated
            return (
                host_view.sweeped
                and host_view.scanned
                and host_view.discovered
                and host_view.on_host
                and host_view.escalated
                and not host_view.impacted
            )
        else:
            return False

    def get_reward_map(self) -> RewardMap:
        return self.reward_map

    def get_action_space_shape(self) -> tuple[int, ...]:
        return self.action_space.get_shape()

    def get_observation_space(self):
        """
        Takes red agent view of network and transforms it into the obs vector.
        """
        return np.array(self.observation.obs_vec, dtype=np.int64)

    def reset(self) -> Iterable:
        self.current_host : Host = self.network.hosts[self.entry_host] if self.entry_host.lower() != "random" else self.network.get_random_user_host()

        self.action_space.reset(self.current_host.name)
        return self.observation.reset(self.current_host.name)
