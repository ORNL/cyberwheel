from typing import Type, Any, Dict, Tuple, List, Callable
from cyberwheel.red_actions.actions.art_killchain_phases import *
from cyberwheel.red_agents.red_agent_base import (
    KnownSubnetInfo,
    RedAgent,
    AgentHistory,
    KnownHostInfo,
    RedActionResults,
)
from cyberwheel.red_agents.red_strategies import impact_all_servers, dfs_impact
from cyberwheel.red_agents.red_rewards import STATIC_IMPACT, RECURRING_IMPACT
from cyberwheel.red_actions.actions.art_killchain_phases import ARTKillChainPhase
from cyberwheel.network.network_base import Network

from copy import deepcopy
import networkx as nx

from cyberwheel.reward import RewardMap


class ARTAgent(RedAgent):
    def __init__(
        self,
        entry_host: Host,
        name: str = "ARTAgent",
        killchain: List[
            Type[ARTKillChainPhase]
        ] = [  # Need to fill this out more accurately, currently defined as an example
            ARTDiscovery,  # Count reconnaissance techniques (only 1) under Discovery
            ARTPrivilegeEscalation,  # Use previous exploit to elevate privilege level
            ARTImpact,  # Perform big attack
        ],
        network: Network = Network(),
        red_strategy: Callable = impact_all_servers,
        reward_map: RewardMap = RECURRING_IMPACT
    ):
        """
        An Atomic Red Team (ART) Red Agent that uses a defined Killchain to attack hosts in a particular order.

        The KillChain in this case:
        1. Discovery - PortScan and PingSweep a Host (two separate actions)
        2. Reconnaissance - Get List of CVEs associated with a host, and a host's type (user/server)
        3. PrivilegeEscalation - When an agent is physically on a Host, it can escalate it's privileges to 'root'
        4. Impact - When its privileges are escalated, it can compromise the Host

        Logic:
        - The agent will start on a given Host, with its CVEs, ports, subnet, and vulnerabilities already scanned.
        - After it has retrieved a list of vulnerabilties associated with a Host with Reconnaissance, it can use LateralMovement to get onto a Host.
        - From there, it will search for Hosts that haven't been portscanned and hosts with the type 'Server'
        - Its goal is to explore the netowrk to find, move to, and Impact Servers if reachable. If no servers are found, it will Impact any given Host.

        Important member variables:

        * `entry_host`: required
            - The host for the red agent to start on. The agent will have info on the Host's ports, subnet (list of other hosts in subnet), and CVEs.
            - The agent will also have a physical malware on the Host called 'malware.exe'. When using LateralMovement, this will jump from Host to Host.
            - NOTE: This will be used as the initial value of the class variable `current_host`. This will track which Host the red agent is currently on.

        * `name`: optional
            - Name of the Agent.
            - Default: 'KillChainAgent'

        * `killchain`: optional
            - The sequence of Actions the Red Agent will take on a given Host.
            - Default: [Discovery, Reconnaissance, PrivilegeEscalation, Impact]
            - NOTE: This is currently only functional with the default Killchain.
        """
        self.name: str = name
        self.killchain: List[Type[ARTKillChainPhase]] = (
            killchain  # NOTE: Look into having variable killchains depending on target host????
        )
        self.current_host: Host = entry_host  # Initialize the current host
        self.history: AgentHistory = AgentHistory(initial_host=entry_host)
        self.network = network
        self.initial_host_names = set(self.network.get_host_names())
        self.impacted_hosts = []
        self.strategy = red_strategy
        self.reward_map = reward_map
        self.temp_flag = False
        self.services_map = {k:{} for k in art_techniques.technique_mapping}
        for technique in self.services_map:
            for host in self.network.get_all_hosts():
                self.services_map[technique][host.name] = []
                for service in host.services:
                    for cve in technique.cve_list:
                        if cve in service.vulns:
                            self.services_map[technique][host.name].append(technique.mitre_id)


    def handle_network_change(self):
        """
        TODO: Add network handling info
        """
        current_hosts = set(self.network.get_host_names())
        new_hosts = current_hosts - (
            self.initial_host_names | set(self.history.hosts.keys())
        )
        new_host = None
        network_change = False
        for host_name in new_hosts:
            h: Host = self.network.get_node_from_name(host_name)
            scanned_subnets = [
                self.history.mapping[s]
                for s, v in self.history.subnets.items()
                if v.is_scanned()
            ]
            if h.subnet in scanned_subnets:
                network_change = True
                new_host = h
        if (
            network_change and new_host != None
        ):  # Add the new host to self.history if the subnet is scanned. Else do nothing.
            self.history.mapping[new_host.name] = new_host
            self.history.hosts[new_host.name] = KnownHostInfo()

    def handle_killchain(self, action, success, target_host) -> None:
        pass

    def select_next_target(self) -> Host:
        """
        Should select next target to be itself until impacted.
        """
        return self.strategy(self)

    def move_to_host(self) -> bool:
        """
        This agent should move to another Host once it has impacted its current host, for now.
        """
        return False

    def run_action(
        self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """
        Helper function to run the appropriate action given the target Host's place in the Killchain.

        Parameters:

        * `target_host`: required
            - The target Host of the attack
        """
        step = self.history.hosts[target_host.name].get_next_step()
        if step > len(self.killchain) - 1:
            step = len(self.killchain) - 1
        if not self.history.hosts[target_host.name].ping_sweeped:
            action_results = ARTPingSweep(self.current_host, target_host).sim_execute()
            if target_host in action_results.attack_success:
                for h in target_host.subnet.connected_hosts:
                    # Create Red Agent History for host if not in there
                    if h.name not in self.history.hosts:
                        self.history.hosts[h.name] = KnownHostInfo(sweeped=True)
                    else:
                        self.history.hosts[h.name].ping_sweeped = True
                    if h.name not in self.history.mapping:
                        self.history.mapping[h.name] = h
                return action_results, ARTPingSweep
        elif not self.history.hosts[target_host.name].ports_scanned:
            action_results = ARTPortScan(self.current_host, target_host).sim_execute()
            if target_host in action_results.attack_success:
                self.history.hosts[target_host.name].ports_scanned = True
                return action_results, ARTPortScan
        elif self.current_host.name != target_host.name:
            # do lateral movement to target host
            action_results = ARTLateralMovement(
                self.current_host, target_host
            ).sim_execute()
            success = target_host in action_results.attack_success
            if (
                success
            ):  # NOTE: Currently, this code assumes success. Does not handle stochsticity yet.
                self.current_host = target_host
                return action_results, ARTLateralMovement

        action = self.killchain[step]
        return (action(self.current_host, target_host).sim_execute(), action)

    def act(self) -> type[ARTKillChainPhase]:
        self.handle_network_change()

        target_host = self.select_next_target()
        source_host = self.current_host
        action_results, action = self.run_action(target_host)

        success = self.services_map[action_results.metadata[target_host.name]["mitre_id"]][target_host.name]
        
        no_update = [ARTLateralMovement, ARTPingSweep, ARTPortScan]
        if success:
            if action not in no_update:
                self.history.hosts[target_host.name].update_killchain_step()
            for h_name in action_results.metadata.keys():
                self.add_host_info(h_name, action_results.metadata[h_name])
            if action == ARTImpact:
                self.impacted_hosts.append(target_host.name)

        self.history.update_step(
            (action, source_host, target_host), success, action_results
        )

        return action

    def add_host_info(self, host_name: str, metadata: Dict[str, Any]) -> None:
        """
        Helper function to add metadata to the Red Agent's history/knowledge. Metadata is in JSON object representation, with key-value pairs.

        Metadata Keys Supported:

        * `vulnerabilities` : List[str]
            - Adds CVEs of Host to history.hosts[Host].vulnerabilities

        * `services` : List[Service]
            - Adds available services on Host to history.hosts[Host].services

        * `type` : str
            - Adds the Host type to history.hosts[Host].type

        * `subnet_scanned` : Subnet
            - If True, adds the list of Hosts on a subnet to history.subnets[Subnet].connected_hosts,
            and the available IPS of a Subnet to history.subnets[Subnet].available_ips
        """
        for k, v in metadata.items():
            if k == "type":
                host_type = v
                known_type = "Unknown"
                if "server" in host_type.lower():
                    known_type = "Server"
                elif "workstation" in host_type.lower():
                    known_type = "User"
                self.history.hosts[host_name].type = known_type
            elif k == "subnet_scanned":
                if v.name not in self.history.subnets.keys():
                    self.history.mapping[v.name] = v
                    self.history.subnets[v.name] = KnownSubnetInfo(scanned=True)
                    self.history.subnets[v.name].connected_hosts = v.connected_hosts
                    self.history.subnets[v.name].available_ips = v.available_ips
                    self.history.subnets[v.name].scan()
                elif v.name not in self.history.mapping.keys():
                    self.history.mapping[v.name] = v
                    self.history.subnets[v.name] = KnownSubnetInfo(scanned=False)

                for h in v.connected_hosts:
                    if h.name not in self.history.hosts.keys():
                        self.history.mapping[h.name] = h
                        self.history.hosts[h.name] = KnownHostInfo()
            elif k == "ip_address":
                if host_name not in self.history.hosts.keys():
                    self.history.hosts[host_name] = KnownHostInfo(ip_address=v.ip_address)
                    self.history.mapping[host_name] = v

    def get_reward_map(self) -> RewardMap:
        return self.reward_map
