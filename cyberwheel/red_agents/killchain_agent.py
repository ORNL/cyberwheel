from typing import Type, Any, Dict, Tuple, List
from cyberwheel.red_actions.actions.killchain_phases import *
from cyberwheel.red_agents.red_agent_base import (
    KnownSubnetInfo,
    RedAgent,
    AgentHistory,
    KnownHostInfo,
)
from cyberwheel.red_actions.actions.killchain_phases import KillChainPhase
from cyberwheel.network.network_base import Network

from copy import deepcopy
import networkx as nx

from cyberwheel.reward import RewardMap


class KillChainAgent(RedAgent):
    def __init__(
        self,
        entry_host: Host,
        name: str = "KillChainAgent",
        killchain: List[
            Type[KillChainPhase]
        ] = [  # Need to fill this out more accurately, currently defined as an example
            Discovery,
            Reconnaissance,  # Get CVEs on a host
            PrivilegeEscalation,  # Use previous exploit to elevate privilege level
            Impact,  # Perform big attack
        ],
        network: Network = Network(),
    ):
        """
        A basic Red Agent that uses a defined Killchain to attack hosts in a particular order.

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
        self.killchain: List[Type[KillChainPhase]] = (
            killchain  # NOTE: Look into having variable killchains depending on target host????
        )
        self.current_host: Host = entry_host  # Initialize the current host
        self.history: AgentHistory = AgentHistory(
            initial_host=entry_host
        )  # Tracks the Red Agent's available and known information of attacks, hosts, and subnets
        # self.initial_network = deepcopy(network)
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
        # If the agent has scanned the Host AND the Subnet it's a part of, advance from the Discover Step
        if all(
            [
                action == Discovery,
                success,
                target_host.subnet.name in self.history.subnets.keys(),
                self.history.subnets[target_host.subnet.name].is_scanned(),
                target_host.name in self.history.hosts.keys(),
                self.history.hosts[target_host.name].is_scanned(),
            ]
        ):
            # interfaced_non_subnet = [unsweeped_host for unsweeped_host in h.interfaces if unsweeped_host not in h.subnet.connected_hosts]
            # return PingSweep(self.src_host, self.target_service, )
            self.history.hosts[target_host.name].update_killchain_step()

        # If the attack was successful, update the killchain of the target Host
        elif success and action != Discovery:
            self.history.hosts[target_host.name].update_killchain_step()

    def select_next_target(self) -> tuple[Host, bool]:
        # If staying on current host, decide whether to
        # A. Further execute current host's killchain
        # OR
        # B. Get info on other Unknown host types (discovery, recon)

        # Get Host type of current Host
        current_host_type = self.history.hosts[self.current_host.name].type

        # Set default target to the Host with highest KillChain Step
        known_hosts = list(self.history.hosts.items())  # Host.name, KnownHostInfo
        max_host = 0
        for i in range(len(known_hosts)):
            if i == 0:
                continue
            k = known_hosts[i][0]
            v = known_hosts[i][1]
            if v.get_next_step() > known_hosts[max_host][1].get_next_step():
                max_host = i
        target_host_name = known_hosts[max_host][0]

        target_host = self.history.mapping[target_host_name]

        # print([f"{k}: {v.type}" for k, v in self.history.hosts.items()])

        # List of hosts with 'Unknown' host types
        unknown_host_types = [
            self.history.mapping[h]
            for h, v in self.history.hosts.items()
            if v.type == "Unknown"
        ]

        # If the current Host is a 'Server' or 'Unknown', keep advancing its killchain.
        # The agent wants to attack Server Hosts and gain more information on Unknown Hosts.
        if current_host_type == "Server" or current_host_type == "Unknown":
            target_host = self.current_host
            target_host_name = target_host.name
        elif (
            len(unknown_host_types) > 0
        ):  # Else If the current Host is a 'Printer' or 'Workstation', and there are 'Unknown' Hosts available to scan, target those.
            target_host = random.choice(unknown_host_types)
            target_host_name = target_host.name
        elif target_host != self.current_host:  # If not on best KC, move to it
            # Else If The current Host is a 'Printer' or 'Workstation' and there are no other 'Unknown' Hosts to scan, move to the Host furthest along in it's Killchain.
            # NOTE: Ideally, this shouldn't be the case. The Agent should be able to route to a Server from any entry Host on the network.
            action_results = LateralMovement(
                self.current_host,
                random.choice(self.history.hosts[target_host_name].services),
                [target_host],
            ).sim_execute()
            self.current_host = target_host
            success = target_host in action_results.attack_success
            self.history.update_step(
                (LateralMovement, self.current_host, target_host),
                success=success,
                red_action_results=action_results,
            )
            return target_host, True
        return target_host, False

    def act(self) -> type[KillChainPhase]:
        """
        TODO: Specify logic
        """
        # If network change, add new decoy host to self.history if subnet with host had already been pingsweeped.
        self.handle_network_change()

        # Decide whether to use LateralMovement to jump to another Host.
        do_lateral_movement = self.move_to_host()
        if do_lateral_movement:
            return LateralMovement

        target_host, do_lateral_movement = self.select_next_target()
        if do_lateral_movement:
            return LateralMovement

        # Run the appropriate action, given the target Host. Stores Results of action, and action type.
        action_results, action = self.run_action(target_host)

        # Store success value of action
        success = (
            target_host in action_results.attack_success
        )  # Successful if target Host was found in ActionResult.attack_success List.

        # Update the Overall Step History, regardless of action success
        self.history.update_step(
            (action, self.current_host, target_host), success, action_results
        )

        # Handle whether killchain advances depending on network state
        self.handle_killchain(action, success, target_host)

        # Store any new information of Hosts/Subnets as metadata in its History
        for h_name in action_results.metadata.keys():
            self.add_host_info(h_name, action_results.metadata[h_name])

        return action

    def select_service(
        self, target_host: Host, action: Type[KillChainPhase]
    ) -> Service:
        """
        Helper function to select the target Service to exploit, based on the given target Host.

        Parameters:

        * `target_host`: required
            - The target Host of the given Killchain Phase

        * `action`: required
            - The current action being taken
            - NOTE: This is not currently being utilized by the function. Currently, it just chooses a random Service on the Host to exploit.
        """
        # TODO: need to implement more intelligent Service selection using the action type
        # return random.choice(self.history.hosts[target_host.name].services)
        return Service(name="Placeholder")

    def run_action(
        self, target_host: Host
    ) -> Tuple[RedActionResults, Type[KillChainPhase]]:
        """
        Helper function to run the appropriate action given the target Host's place in the Killchain.

        Parameters:

        * `target_host`: required
            - The target Host of the attack
        """
        step = self.history.hosts[target_host.name].get_next_step()
        if step > len(self.killchain) - 1:
            step = len(self.killchain) - 1
        action = self.killchain[step]
        target_service = self.select_service(target_host, action)
        if (
            action == Discovery
        ):  # If it's a Discovery attack, need to pass some more metadata
            scanned_hosts = [
                self.history.mapping[h]
                for h, v in self.history.hosts.items()
                if v.is_scanned()
            ]
            scanned_subnets = [
                self.history.mapping[s]
                for s, v in self.history.subnets.items()
                if v.is_scanned()
            ]
            results = Discovery(
                src_host=self.current_host,
                target_hosts=[target_host],
                target_service=target_service,
                scanned_hosts=scanned_hosts,
                scanned_subnets=scanned_subnets,
            ).sim_execute()
            if target_host in results.attack_success:
                self.history.hosts[target_host.name].scan()
                if target_host.subnet.name in self.history.subnets:
                    self.history.subnets[target_host.subnet.name].scan()
                else:
                    self.history.subnets[target_host.subnet.name] = KnownSubnetInfo(
                        scanned=False
                    )

            return (results, Discovery)
        else:
            return (
                action(
                    src_host=self.current_host,
                    target_hosts=[target_host],
                    target_service=target_service,
                ).sim_execute(),
                action,
            )
        # NOTE: As different actions need to pass on more metadata, separate elif statements can be added to handle them if necessary

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

    def move_to_host(self) -> bool:
        """
        Helper function to handle logic of whether the Red Agent should move to another Host.

        If the agent is currently on a Server, do not use LateralMovement to move to another Host.
        If the agent is currently on a Printer or Workstation, use LateralMovement to move to another Host if it is a Server.

        """
        current_host_type = self.history.hosts[self.current_host.name].type
        # print(
        #    f"Current Host: {self.current_host.name}\nCurrent Host Type: {current_host_type}"
        # )

        # If the current host is a Server or Unknown (NOTE: This shouldn't happen), stay on it and continue attacking.
        if current_host_type == "Unknown" or current_host_type == "Server":
            return False

        # If the current host is a Printer or Workstation, use LateralMovement to move to a random known Server
        elif current_host_type == "User":
            servers = [
                self.history.mapping[k]
                for k, h in self.history.hosts.items()
                if h.type == "Server"
            ]
            server_names = [s.name for s in servers]
            # If there are no known Server hosts reachable, just keep attacking current Host
            if len(servers) == 0:
                return False
            # Choose a random server and move to it
            target_host = random.choice(servers)
            if self.history.hosts[target_host.name].services:
                target_service = random.choice(
                    self.history.hosts[target_host.name].services
                )
            else:
                target_service = Service(name="ssh")

            action_results = LateralMovement(
                self.current_host, target_service, [target_host]
            ).sim_execute()

            # Update the current host after doing this, assuming LateralMovement is successful
            success = target_host in action_results.attack_success
            self.history.update_step(
                (LateralMovement, self.current_host, target_host),
                success,
                action_results,
            )
            if (
                success
            ):  # NOTE: Currently, this code assumes success. Does not handle stochsticity yet.
                self.current_host = target_host
            return True
        else:
            return False

    def get_reward_map(self) -> RewardMap:
        return {
            "discovery": (-1, 0),
            "reconnaissance": (-2, 0),
            "lateral-movement": (-4, 0),
            "privilege-escalation": (-6, 0),
            "impact": (-8, 0),
        }
