from typing import List
from red_actions.actions.killchain_phases import *
from red_agent_base import KnownSubnetInfo, RedAgent, AgentHistory
from red_actions.actions.killchain_phases import KillChainPhase
from typing import Type, Any, Dict, Tuple


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
            Impact,  # Perform big attack (unknown atm)
        ],
    ):
        """
        A basic Red Agent that uses a defined Killchain to attack hosts in a particular order.

        The KillChain in this case:
        1. Discovery - PortScan and PingSweep a Host (two separate actions)
        2. Reconnaissance - Get List of CVEs associated with a host
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
        self.killchain: List[Type[KillChainPhase]] = (
            killchain  # NOTE: Look into having variable killchains depending on target host????
        )
        self.current_host: Host = entry_host  # Initialize the current host
        self.history: AgentHistory = AgentHistory(
            initial_host=entry_host
        )  # Tracks the Red Agent's available and known information of attacks, hosts, and subnets

    def act(self):
        # Decide whether to use LateralMovement to jump to another Host. This should only happen if there is a Server available to attack.
        do_lateral_movement = self.change_target()
        if do_lateral_movement:
            return

        # If staying on current host, decide whether to
        # A. Further execute current host's killchain
        # OR
        # B. Get info on other Unknown host types (discovery, recon)

        # Get Host type of current Host
        current_host_type = self.history.hosts[self.current_host].type

        # Set default target to the Host with highest KillChain Step
        known_hosts = list(self.history.hosts.items())
        max_host = 0
        for i in range(len(known_hosts)):
            if i == 0:
                continue
            k = known_hosts[i][0]
            v = known_hosts[i][1]
            if v.get_next_step() > known_hosts[max_host][1].get_next_step():
                max_host = i
        target_host = known_hosts[max_host][0]

        # List of hosts with 'Unknown' host types
        unknown_host_types = [
            h for h, v in self.history.hosts.items() if v.type == "Unknown"
        ]

        # If the current Host is a 'Server' or 'Unknown', keep advancing its killchain.
        # The agent wants to attack Server Hosts and gain more information on Unknown Hosts.
        if current_host_type == "Server" or current_host_type == "Unknown":
            target_host = self.current_host
        # Else If the current Host is a 'Printer' or 'Workstation', and there are 'Unknown' Hosts available to scan, target those.
        elif len(unknown_host_types) > 0:
            target_host = random.choice(unknown_host_types)
        # Else If The current Host is a 'Printer' or 'Workstation' and there are no other 'Unknown' Hosts to scan, move to the Host furthest along in it's Killchain.
        # NOTE: Ideally, this shouldn't be the case. The Agent should be able to route to a Server from any entry Host on the network.
        elif target_host != self.current_host:  # If not on best KC, move to it
            action_results = LateralMovement(
                self.current_host,
                random.choice(self.history.hosts[target_host].services),
                [target_host],
            ).sim_execute()
            self.current_host = target_host
            success = target_host in action_results.attack_success
            self.history.update_step(LateralMovement, success=success)
            return

        # Run the appropriate action, given the target Host. Stores Results of action, and action type.
        action_results, action = self.run_action(target_host)

        # Store success value of action
        success = (
            self.current_host in action_results.attack_success
        )  # Successful if target Host was found in ActionResult.attack_success List.

        # Update the Overall Step History, regardless of action success
        self.history.update_step(action, success=success)

        # If the agent has scanned the Host AND the Subnet it's a part of, advance from the Discover Step
        if all(
            [
                action == Discovery,
                success and target_host.subnet in self.history.subnets.keys(),
                self.history.subnets[target_host.subnet].is_scanned(),
                target_host in self.history.hosts.keys(),
                self.history.hosts[target_host].is_scanned(),
            ]
        ):
            self.history.hosts[target_host].update_killchain_step()

        # If the attack was successful, update the killchain of the target Host
        if success:
            self.history.hosts[target_host].update_killchain_step()

        # Store any new information of Hosts/Subnets as metadata in its History
        self.add_host_info(target_host, action_results.metadata[target_host])

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
        return random.choice(self.history.hosts[target_host].services)

    def run_action(
        self, target_host: Host
    ) -> Tuple[RedActionResults, Type[KillChainPhase]]:
        """
        Helper function to run the appropriate action given the target Host's place in the Killchain.

        Parameters:

        * `target_host`: required
            - The target Host of the attack
        """
        action = self.killchain[self.history.hosts[self.current_host].get_next_step()]
        target_service = self.select_service(target_host, action)
        if isinstance(
            action, Discovery
        ):  # If it's a Discovery attack, need to pass some more metadata
            scanned_hosts = [h for h, v in self.history.hosts.items() if v.is_scanned()]
            scanned_subnets = [
                s for s, v in self.history.subnets.items() if v.is_scanned()
            ]
            return (
                Discovery(
                    src_host=self.current_host,
                    target_hosts=[target_host],
                    target_service=target_service,
                    scanned_hosts=scanned_hosts,
                    scanned_subnets=scanned_subnets,
                ).sim_execute(),
                Discovery,
            )
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

    def add_host_info(self, host: Host, metadata: Dict[str, Any]) -> None:
        """
        Helper function to add metadata to the Red Agent's history/knowledge. Metadata is in JSON object representation, with key-value pairs.

        Metadata Keys Supported:

        * `vulnerabilities` : List[str]
            - Adds CVEs of Host to history.hosts[Host].vulnerabilities

        * `services` : List[Service]
            - Adds available services on Host to history.hosts[Host].services

        * `type` : str
            - Adds the Host type to history.hosts[Host].type

        * `subnet_scanned` : bool
            - If True, adds the list of Hosts on a subnet to history.subnets[Subnet].connected_hosts,
            and the available IPS of a Subnet to history.subnets[Subnet].available_ips
        """
        for k, v in metadata.items():
            if k == "vulnerabilities":
                self.history.hosts[host].vulnerabilites = v
            elif k == "services":
                self.history.hosts[host].services = v
            elif k == "type":
                self.history.hosts[host].type = v
            elif k == "subnet_scanned":
                self.history.subnets[v] = KnownSubnetInfo(scanned=True)
                self.history.subnets[v].connected_hosts = v.connected_hosts
                self.history.subnets[v].available_ips = v.available_ips

    def change_target(self) -> bool:
        """
        Helper function to handle logic of whether the Red Agent should move to another Host.

        If the agent is currently on a Server, do not use LateralMovement to move to another Host.
        If the agent is currently on a Printer or Workstation, use LateralMovement to move to another Host if it is a Server.

        """
        host_type = self.history.hosts[self.current_host].type

        # If the current host is a Server or Unknown (NOTE: This shouldn't happen), stay on it and continue attacking.
        if host_type == "Unknown" or host_type == "Server":
            return False

        # If the current host is a Printer or Workstation, use LateralMovement to move to a random known Server
        elif host_type == "Printer" or host_type == "Workstation":
            servers = [k for k, h in self.history.hosts.items() if h.type == "Server"]
            # If there are no known Server hosts reachable, just keep attacking current Host
            if len(servers) == 0:
                return False
            # Choose a random server and move to it
            target_host = random.choice(servers)
            target_service = random.choice(self.history.hosts[target_host].services)
            action_results = LateralMovement(
                self.current_host, target_service, [target_host]
            ).sim_execute()

            # Update the current host after doing this, assuming LateralMovement is successful
            success = target_host in action_results.attack_success
            self.history.update_step(LateralMovement, success=success)
            if (
                success
            ):  # NOTE: Currently, this code assumes success. Does not handle stochsticity yet.
                self.current_host = target_host
            return True
        else:
            return False
