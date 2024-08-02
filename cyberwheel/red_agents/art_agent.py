from typing import Type, Any, Dict, Tuple, List
from cyberwheel.red_actions.actions.art_killchain_phases import ARTDiscovery, ARTImpact, ARTKillChainPhase, ARTLateralMovement, ARTPingSweep, ARTPortScan, ARTPrivilegeEscalation
from cyberwheel.red_agents.red_agent_base import KnownSubnetInfo, RedAgent, AgentHistory, KnownHostInfo, RedActionResults, HybridSetList
from cyberwheel.red_agents.strategies import RedStrategy, ServerDowntime
from cyberwheel.network.network_base import Network, Host
from cyberwheel.red_actions import art_techniques

from cyberwheel.reward import RewardMap


class ARTAgent(RedAgent):
    def __init__(
        self,
        entry_host: Host,
        network: Network = Network(),
        name: str = "ARTAgent",
        killchain: List[
            Type[ARTKillChainPhase]
        ] = [
            ARTDiscovery,  # Count reconnaissance techniques (only 1) under Discovery
            ARTPrivilegeEscalation,  # Use previous exploit to elevate privilege level
            ARTImpact,  # Perform big attack
        ],
        red_strategy: RedStrategy = ServerDowntime,
        service_mapping: dict = {}
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
        self.killchain: List[Type[ARTKillChainPhase]] = (
            killchain  # NOTE: Look into having variable killchains depending on target host????
        )
        self.current_host: Host = entry_host  # Initialize the current host
        self.history: AgentHistory = AgentHistory(initial_host=entry_host)
        self.network = network
        self.initial_host_names = set(self.network.get_host_names())
        self.unimpacted_servers = HybridSetList()
        self.unknowns = HybridSetList()
        self.strategy = red_strategy
        self.all_kcps = killchain + [ARTLateralMovement]
        if service_mapping == {}:
            self.services_map = {}
            self.tracked_hosts = set()
            for host in self.network.get_all_hosts():
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
            self.tracked_hosts = set(service_mapping.keys())
    
    @classmethod
    def get_service_map(cls, network: Network):
        """
        Class function to get the service mapping based on host attributes.
        """
        killchain = [ARTDiscovery, ARTPrivilegeEscalation, ARTImpact, ARTLateralMovement]
        service_mapping = {}
        for host in network.get_all_hosts():
            service_mapping[host.name] = {}
            for kcp in killchain:
                service_mapping[host.name][kcp] = []
                kcp_valid_techniques = kcp.validity_mapping[host.os][kcp.get_name()]
                for mid in kcp_valid_techniques:
                    technique = art_techniques.technique_mapping[mid]
                    if len(host.host_type.cve_list & technique.cve_list) > 0:
                        service_mapping[host.name][kcp].append(mid)
        return service_mapping

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
        Does a 'check' at every step to initialize any newly added decoys to view.
        """
        current_hosts = set(self.network.get_host_names())

        new_hosts = current_hosts - self.tracked_hosts

        new_host = None
        network_change = False
        for host_name in new_hosts:
            h: Host = self.network.get_node_from_name(host_name)
            self.services_map[h.name] = self.get_valid_techniques_by_host(
                h, self.all_kcps
            )
            scanned_subnets = [
                self.history.mapping[s]
                for s, v in self.history.subnets.items()
                if v.is_scanned()
            ]
            if h.subnet in scanned_subnets:
                network_change = True
                new_host = h
            self.tracked_hosts.add(h.name)
        if (
            network_change and new_host != None
        ):  # Add the new host to self.history if the subnet is scanned. Else do nothing.
            self.history.mapping[new_host.name] = new_host
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
        if not self.history.hosts[target_host.name].ping_sweeped:
            # print("Time to Ping Sweep")
            action_results = ARTPingSweep(self.current_host, target_host).sim_execute()
            if action_results.attack_success:
                for h in target_host.subnet.connected_hosts:
                    # Create Red Agent History for host if not in there
                    if h.name not in self.history.hosts:
                        self.history.hosts[h.name] = KnownHostInfo(sweeped=True)
                        self.unknowns.add(h.name)
                    else:
                        self.history.hosts[h.name].ping_sweeped = True
                    if h.name not in self.history.mapping:
                        self.history.mapping[h.name] = h
            return action_results, ARTPingSweep
        elif not self.history.hosts[target_host.name].ports_scanned:
            # print("Time to Port Scan")
            action_results = ARTPortScan(self.current_host, target_host).sim_execute()
            if action_results.attack_success:
                self.history.hosts[target_host.name].ports_scanned = True
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

    def act(self) -> type[ARTKillChainPhase]:
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
            for h_name in action_results.metadata.keys():
                self.add_host_info(h_name, action_results.metadata[h_name])
            if action == ARTImpact:
                self.history.hosts[target_host.name].impacted = True
                if self.history.hosts[target_host.name].type == "Server":
                    self.unimpacted_servers.remove(target_host.name)
            #elif action == ARTPrivilegeEscalation:
            #    target_host.restored = False

        #print(f"{action.get_name()} - from {source_host.name} to {target_host.name}")
        self.history.update_step(action, action_results)
        return action

    def add_host_info(self, host_name: str, metadata: Dict[str, Any]) -> None:
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
        for k, v in metadata.items():
            if k == "type":
                host_type = v
                known_type = "Unknown"
                if "server" in host_type.lower():
                    known_type = "Server"
                    self.unimpacted_servers.add(host_name)
                    self.unknowns.remove(host_name)
                elif "workstation" in host_type.lower():
                    known_type = "User"
                    self.unknowns.remove(host_name)
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
                        self.unknowns.add(h.name)
            elif k == "ip_address":
                if host_name not in self.history.hosts.keys():
                    self.history.hosts[host_name] = KnownHostInfo(
                        ip_address=v.ip_address
                    )
                    self.unknowns.add(host_name)
                    self.history.mapping[host_name] = v

    def get_reward_map(self) -> RewardMap:
        """
        Get the reward mapping for the red agent. This is defined in the Red Strategy.
        It dictates which actions have the greater costs, for example Impact having -8
        while Discovery has -2.
        """
        return self.strategy.get_reward_map()

    def reset(self, entry_host: Host, network: Network):
        """
        Resets the red agent back to blank slate.
        """
        self.network = network
        self.current_host = entry_host
        self.history: AgentHistory = AgentHistory(initial_host=entry_host)
        self.initial_host_names = set(self.network.get_host_names())
        self.unimpacted_servers = HybridSetList()
        self.unknowns = HybridSetList()
