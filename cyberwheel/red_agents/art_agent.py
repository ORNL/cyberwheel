import importlib
import yaml

from typing import Type, Any, Dict, Tuple
from importlib.resources import files

from cyberwheel.reward import RewardMap
from cyberwheel.red_agents import strategies
from cyberwheel.network.network_base import Network, Host
from cyberwheel.red_actions import art_techniques
from cyberwheel.red_actions.actions import (
    ARTDiscovery,
    ARTImpact,
    ARTKillChainPhase,
    ARTLateralMovement,
    ARTPingSweep,
    ARTPortScan,
    ARTPrivilegeEscalation,
)
from cyberwheel.red_agents.red_agent_base import (
    KnownSubnetInfo,
    RedAgent,
    AgentHistory,
    KnownHostInfo,
    RedActionResults,
    RedAgentResult
)
from cyberwheel.utils import HybridSetList


class ARTAgent(RedAgent):
    def __init__(
        self,
        network: Network,
        args, 
        name: str = "ARTAgent",
        service_mapping: dict = {},
        map_services: bool = True
    ):
        """
        An Atomic Red Team (ART) Red Agent that uses a defined Killchain to attack hosts in a particular order.

        Before going down the killchain on a host, the agent must Pingsweep the host's subnet and Portscan the host.
        These actions are defined to specific ART Techniques, and always succeed. After portscanning, the agent can start
        attacking down the killchain on a host.
        The KillChain in this case:
        1. ARTDiscovery - Chooses a 'discovery' Atomic Red Team technique to attack the host. Also exposes the Host's CVEs to the attacker.
        2. ARTPrivilegeEscalation - Chooses a 'privilege-escalation' Atomic Red Team technique to attack the host. Also escalates its privileges to 'root'
        3. ARTImpact - Chooses an 'impact' Atomic Red Team technique to attack the host.

        General Logic:
        - The agent will start on a given Host, with its CVEs, ports, subnet, and vulnerabilities already scanned.
        - At each step the agent will
            - Determine which Host is its target_host with its given red strategy (ServerDowntime by default)
            - Run a Pingsweep on the target_host's subnet if not already scanned
            - Run a Portscan on target_host, revealing services and vulnerabilities, if not already scanned
            - Run LateralMovement to hack into target_host if not already physically on target_host
            - On target_host, the agent will run the next step of the Killchain.
                - For example, if it has already run Discovery on the target_host, it will run PrivilegeEscalation

        Important member variables:

        * `entry_host`: required
            - The host for the red agent to start on. The agent will have info on the Host's ports, subnet (list of other hosts in subnet), and CVEs.
            - NOTE: This will be used as the initial value of the class variable `current_host`. This will track which Host the red agent is currently on.

        * `name`: optional
            - Name of the Agent.
            - Default: 'ARTAgent'

        * `network`: required
            - The network that the red agent will explore.

        * `killchain`: optional
            - The sequence of Actions the Red Agent will take on a given Host.
            - Default: [ARTDiscovery, ARTPrivilegeEscalation, ARTImpact]
            - NOTE: This is currently only tested with the default Killchain.

        * `red_strategy`: optional
            - The logic that the red agent will use to select it's next target.
            - This is implemented as separate class to allow modularity in red agent implementations.
            - Default: ServerDowntime

        * `service_mapping`: optional
            - A mapping that is initialized with a network, dictating with a bool, whether a given Technique will be valid on a given Host.
            - This is generated and passed before initialization to avoid checking for CVEs for every environment if running parallel.
            - Default: {} (if empty, will generate during __init__())
        """
        self.name: str = name
        self.network = network
        self.config = files("cyberwheel.data.configs.red_agent").joinpath(
            args.red_agent
        )

        self.from_yaml()

        self.history: AgentHistory = AgentHistory(initial_host=self.current_host)
        self.unimpacted_servers = HybridSetList()
        self.unimpacted_hosts = HybridSetList()
        self.unknowns = HybridSetList()
        self.campaign = args.campaign if hasattr(args, 'campaign') else False
        service_mapping = args.service_mapping if hasattr(args, 'service_mapping') else {}

        if service_mapping == {} and not self.campaign and map_services:
            self.services_map = {}
            self.tracked_hosts = HybridSetList()
            for _, host in self.network.hosts.items():
                self.tracked_hosts.add(host.name)
                self.services_map[host.name] = {}
                for kcp in self.all_kcps:
                    self.services_map[host.name][kcp] = []
                    kcp_valid_techniques = kcp.validity_mapping[host.os][kcp.get_name()]
                    for mid in kcp_valid_techniques:
                        technique = art_techniques.technique_mapping[mid]
                        if len(host.host_type.cve_list & technique.cve_list) > 0:
                            self.services_map[host.name][kcp].append(mid)
        else:
            self.services_map = service_mapping
            self.tracked_hosts = HybridSetList(service_mapping.keys())
    
    def from_yaml(self) -> None:
        with open(self.config, "r") as r:
            contents = yaml.safe_load(r)

        self.killchain = []
        self.all_kcps = []
        self.reward_map = {}

        self.entry_host: Host = contents["entry_host"]
        self.current_host: Host = self.network.hosts[self.entry_host] if self.entry_host.lower() != "random" else self.network.get_random_user_host()

        for k, v in contents['actions'].items():
            self.reward_map[k] = (v["reward"]["immediate"], v["reward"]["recurring"])
            kcp = getattr(importlib.import_module("cyberwheel.red_actions.actions"), v["class"])
            if kcp == ARTPingSweep or kcp == ARTPortScan:
                pass
            elif kcp == ARTLateralMovement:
                self.all_kcps.append(kcp)
            else:
                self.all_kcps.append(kcp)
                self.killchain.append(kcp)

        self.strategy = getattr(strategies, contents["strategy"])

        self.leader: Host = contents.get("leader", "random")
        self.leader_host: Host = self.network.hosts[self.leader] if self.leader.lower() != "random" else self.network.get_random_server_host()

    def get_valid_techniques_by_host(self, host, all_kcps):
        """
        Returns service mapping for a given host and killchain phases.
        """
        valid_techniques = {}
        for kcp in all_kcps:
            valid_techniques[kcp] = []
            kcp_valid_techniques = kcp.validity_mapping[host.os][kcp.get_name()]
            for mid in kcp_valid_techniques:
                technique = art_techniques.technique_mapping[mid]
                if len(host.host_type.cve_list & technique.cve_list) > 0:
                    valid_techniques[kcp].append(mid)
        return valid_techniques

    def handle_network_change(self):
        """
        Does a 'check' at every step to initialize any newly added decoys to view or remove any removed decoys
        """
        current_hosts = self.network.hosts.keys()

        new_hosts = current_hosts - self.tracked_hosts.data_set

        removed_hosts = (self.unknowns.data_set | self.unimpacted_hosts.data_set | self.unimpacted_servers.data_set) - self.network.hosts.keys()
        #print(removed_hosts)
        
        if len(removed_hosts) > 0:
            removed_host = removed_hosts.pop()
            self.unknowns.remove(removed_host)
            self.unimpacted_hosts.remove(removed_host)
            self.unimpacted_servers.remove(removed_host)

        new_host = None
        network_change = False
        for host_name in new_hosts:
            h: Host = self.network.hosts[host_name]
            if not self.campaign:
                self.services_map[host_name] = self.get_valid_techniques_by_host(
                    h, self.all_kcps
                )
            scanned_subnets = [
                s
                for s, v in self.history.subnets.items()
                if v.is_scanned()
            ]
            if h.subnet.name in scanned_subnets:
                network_change = True
                new_host = h
            self.tracked_hosts.add(host_name)
        if (
            network_change and new_host != None
        ):  # Add the new host to self.history if the subnet is scanned. Else do nothing.
            self.history.hosts[new_host.name] = KnownHostInfo()
            self.unknowns.add(new_host.name)
        

    def select_next_target(self) -> Host:
        """
        Logic to determine which host the agent targets.
        """
        return self.strategy.select_target(self)

    def run_action(
        self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """
        Helper function to run the appropriate action given the target Host's place in the Killchain.

        Parameters:

        * `target_host`: required
            - The target Host of the attack
        """
        # print(target_host.name)
        step = self.history.hosts[target_host.name].get_next_step()
        if step > len(self.killchain) - 1:
            step = len(self.killchain) - 1
        if not self.history.hosts[target_host.name].sweeped:
            action_results = ARTPingSweep(self.current_host, target_host).sim_execute()
            if action_results.attack_success:
                for h in action_results.metadata["sweeped_hosts"]:
                    # Create Red Agent History for host if not in there
                    if h.name not in self.history.hosts:
                        sweeped = h.subnet.name == target_host.subnet.name
                        self.history.hosts[h.name] = KnownHostInfo(sweeped=sweeped, ip_address=h.ip_address)
                        if h.subnet.name not in self.history.subnets:
                            self.history.subnets[h.subnet.name] = KnownSubnetInfo()
                        self.unknowns.add(h.name)
                    else:
                        self.history.hosts[h.name].sweeped = True
            return action_results, ARTPingSweep
        elif not self.history.hosts[target_host.name].scanned:
            action_results = ARTPortScan(self.current_host, target_host).sim_execute()
            if action_results.attack_success:
                self.history.hosts[target_host.name].scanned = True
            return action_results, ARTPortScan
        elif self.current_host.name != target_host.name:
            # do lateral movement to target host
            # print("Time to Lateral Move")
            action_results = ARTLateralMovement(
                self.current_host,
                target_host,
                self.services_map[target_host.name][ARTLateralMovement],
            ).sim_execute()
            success = action_results.attack_success
            if success:
                self.history.hosts[self.current_host.name].on_host = False
                self.history.hosts[target_host.name].on_host = True
                self.current_host = target_host

            return action_results, ARTLateralMovement

        action = self.killchain[step]
        return (
            action(
                self.current_host,
                target_host,
                self.services_map[target_host.name][action],
            ).sim_execute(),
            action,
        )

    def act(self, policy_action=None) -> RedAgentResult:
        """
        This defines the red agent's action at each step of the simulation.
        It will
            *   handle any newly added hosts
            *   Select the next target
            *   Run an action on the target
            *   Handle any additional metadata and update history
        """
        self.handle_network_change()

        target_host = self.select_next_target()
        source_host = self.current_host
        action_results, action = self.run_action(target_host)
        success = action_results.attack_success
        no_update = [ARTLateralMovement, ARTPingSweep, ARTPortScan]
        if success:
            if action not in no_update:
                self.history.hosts[target_host.name].update_killchain_step()
                self.add_host_info(action_results.metadata)
            if action == ARTImpact:
                self.history.hosts[target_host.name].impacted = True
                self.unimpacted_hosts.remove(target_host.name)
                if self.history.hosts[target_host.name].type == "Server":
                    self.unimpacted_servers.remove(target_host.name)
            elif action == ARTPrivilegeEscalation:
                self.history.hosts[target_host.name].escalated = True
            # elif action == ARTPrivilegeEscalation:
            #    target_host.restored = False
        self.history.update_step(action, action_results)
        return RedAgentResult(
            action, 
            source_host, 
            target_host, 
            success,
            action_results=action_results
        )  # Returns what ARTAgent act() should, probably. Or the observation space?

    def add_host_info(self, all_metadata: Dict[str, Any]) -> None:
        """
        Helper function to add metadata to the Red Agent's history/knowledge. Metadata is in JSON object representation, with key-value pairs.

        Metadata Keys Supported:
        * `ip_address` : str
            - Adds newly found Host with IP address to Red Agent view

        * `type` : str
            - Adds the Host type to history.hosts[Host].type

        * `subnet_scanned` : Subnet
            - If True, adds the list of Hosts on a subnet to history.subnets[Subnet].connected_hosts,
            and the available IPS of a Subnet to history.subnets[Subnet].available_ips
        """
        for host_name, host_metadata in all_metadata.items():
            for k, metadata in host_metadata.items():
                if k == "type":
                    host_type = metadata
                    known_type = "Unknown"
                    if "server" in host_type.lower():
                        known_type = "Server"
                        self.unimpacted_servers.add(host_name)
                        self.unknowns.remove(host_name)
                    elif "workstation" in host_type.lower():
                        known_type = "User"
                        self.unknowns.remove(host_name)
                    self.history.hosts[host_name].type = known_type
                    self.history.hosts[host_name].discovered = known_type != "Unknown"
                    self.history.hosts[host_name].is_leader = self.leader_host.name == host_name if self.leader_host else False
                elif k == "subnet_scanned":
                    if metadata.name not in self.history.subnets.keys():
                        subnet_data = KnownSubnetInfo(scanned=True)
                        subnet_data.connected_hosts = metadata.connected_hosts
                        subnet_data.available_ips = metadata.available_ips
                        subnet_data.scan()
                        self.history.subnets[metadata.name] = subnet_data

                    for h in metadata.connected_hosts:
                        if h.name not in self.history.hosts.keys():
                            self.history.hosts[h.name] = KnownHostInfo()
                            self.unknowns.add(h.name)
                            self.unimpacted_hosts.add(h.name)
                elif k == "ip_address":
                    if host_name not in self.history.hosts.keys():
                        self.history.hosts[host_name] = KnownHostInfo(
                            ip_address=metadata.ip_address
                        )
                        self.unknowns.add(host_name)

    def get_reward_map(self) -> RewardMap:
        """
        Get the reward mapping for the red agent. This is defined in the Red Strategy.
        It dictates which actions have the greater costs, for example Impact having -8
        while Discovery has -2.
        """
        return self.reward_map

    def reset(self):
        """
        Resets the red agent back to blank slate.
        """
        self.current_host : Host = self.network.hosts[self.entry_host] if self.entry_host.lower() != "random" else self.network.get_random_user_host()
        self.history: AgentHistory = AgentHistory(initial_host=self.current_host)
        self.unimpacted_servers.reset()
        self.unimpacted_hosts.reset()
        self.unknowns.reset()
        self.leader_host: Host = self.network.hosts[self.leader] if self.leader.lower() != "random" else self.network.get_random_server_host()
