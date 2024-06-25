from typing import Type, Any, Dict, Tuple, List
from cyberwheel.red_actions.actions.art_killchain_phases import *
from cyberwheel.red_agents.red_agent_base import (
    KnownSubnetInfo,
    RedAgent,
    AgentHistory,
    KnownHostInfo,
    RedActionResults,
)
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
        # print("----------------------------------------------------------")
        self.name: str = name
        self.killchain: List[Type[ARTKillChainPhase]] = (
            killchain  # NOTE: Look into having variable killchains depending on target host????
        )
        self.current_host: Host = entry_host  # Initialize the current host
        self.history: AgentHistory = AgentHistory(initial_host=entry_host)
        self.network = network
        self.initial_host_names = set(self.network.get_host_names())

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

    def select_next_target(self) -> tuple[Host, bool]:
        """
        Should select next taget to be itself always.
        """
        return self.current_host, False

    def move_to_host(self) -> bool:
        """
        This agent should move to another Host once it has impacted its current host, for now.
        """
        if self.history.hosts[self.current_host.name].last_step == len(self.killchain):
            unimpacted_hosts = [
                h
                for h, info in self.history.hosts.items()
                if info.last_step != len(self.killchain)
            ]
            if len(unimpacted_hosts) > 0:
                target_host_name = random.choice(unimpacted_hosts)
                target_host = self.history.mapping[target_host_name]
                action_results = ARTLateralMovement(
                    self.current_host, target_host
                ).sim_execute()
                success = target_host in action_results.attack_success
                self.history.update_step(
                    (ARTLateralMovement, self.current_host, target_host),
                    success,
                    action_results,
                )
                if (
                    success
                ):  # NOTE: Currently, this code assumes success. Does not handle stochsticity yet.
                    self.current_host = target_host
                    return True

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

        action = self.killchain[step]
        return (
            action(self.current_host, target_host).sim_execute(),
            action,
        )

    def act(self) -> type[ARTKillChainPhase]:
        self.handle_network_change()

        # Decide whether to use LateralMovement to jump to another Host.
        do_lateral_movement = self.move_to_host()
        if do_lateral_movement:
            return ARTLateralMovement

        target_host, do_lateral_movement = self.select_next_target()
        if do_lateral_movement:
            return ARTLateralMovement

        action_results, action = self.run_action(target_host)
        success = target_host in action_results.attack_success
        if success:
            self.history.hosts[target_host.name].update_killchain_step()

        print(
            f"\n{self.current_host.name} ---{action.get_name()}--> {target_host.name}"
        )
        print(
            f"{action_results.metadata['mitre_id']} - {action_results.metadata['technique'].name}"
        )
        # print(action_results.metadata['technique'].description)
        for p in action_results.metadata["commands"]:
            print(f"\t{p}")

        self.history.update_step(
            (action, self.current_host, target_host), success, action_results
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
            if k == "vulnerabilities":
                self.history.hosts[host_name].vulnerabilites = v
            elif k == "services":
                self.history.hosts[host_name].services = v
            elif k == "type":
                host_type = v
                known_type = "Unknown"
                if "server" in host_type.lower():
                    known_type = "Server"
                elif "workstation" in host_type.lower():
                    known_type = "User"
                self.history.hosts[host_name].type = known_type
            elif (
                k == "subnet_scanned"
            ):  # TODO: This should have the subnet object as a value, would be easier
                if v.name not in self.history.subnets.keys():
                    self.history.mapping[v.name] = v
                    self.history.subnets[v.name] = KnownSubnetInfo(scanned=True)
                    self.history.subnets[v.name].connected_hosts = v.connected_hosts
                    self.history.subnets[v].available_ips = v.available_ips
                    self.history.subnets[v].scan()
                elif v.name not in self.history.mapping.keys():
                    self.history.mapping[v.name] = v
                    self.history.subnets[v.name] = KnownSubnetInfo(scanned=False)

                for h in v.connected_hosts:
                    if h.name not in self.history.hosts.keys():
                        self.history.mapping[h.name] = h
                        self.history.hosts[h.name] = KnownHostInfo()
            elif k == "interfaces":
                for interfaced_host in v:
                    if interfaced_host.name in self.history.hosts.keys():
                        continue
                    self.history.hosts[interfaced_host.name] = KnownHostInfo()
                    self.history.mapping[interfaced_host.name] = interfaced_host

    def get_reward_map(self) -> RewardMap:
        return {
            "pingsweep": (-1, 0),
            "portscan": (-1, 0),
            "discovery": (-2, 0),
            "lateral-movement": (-4, 0),
            "privilege-escalation": (-6, 0),
            "impact": (-8, 0),
        }
