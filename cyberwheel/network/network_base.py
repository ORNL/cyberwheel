import json
import random
import yaml
import ipaddress as ipa
import matplotlib.pyplot as plt
import networkx as nx

from importlib.resources import files
from os import PathLike
from pathlib import PosixPath
from typing import Union, List
from tqdm import tqdm

from cyberwheel.network.host import Host, HostType
from cyberwheel.network.network_object import NetworkObject, FirewallRule
from cyberwheel.network.router import Router
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet
from cyberwheel.utils.hybrid_set_list import HybridSetList

class Network:

    def __init__(
        self,
        name: str = "Network",
        graph: nx.Graph = None,
    ):
        self.graph : nx.DiGraph = graph if graph else nx.DiGraph(name=name)
        self.name : str = name
        
        self.disconnected_nodes: list[Host] = []
        self.isolated_hosts: list[Host] = []

        self.hosts : dict[str, Host] = {name:host for name, host in self if isinstance(host, Host)}
        self.subnets : dict[str, Subnet] = {name:subnet for name, subnet in self if isinstance(subnet, Subnet)}
        self.decoys : dict[str, Host] = {hn:host for hn, host in self.hosts if host.decoy}

        self.user_hosts : HybridSetList = HybridSetList({hn for hn, host in self.hosts if "workstation" in host.host_type.name.lower() or "user" in host.host_type.name.lower()})
        self.server_hosts : HybridSetList = HybridSetList({hn for hn, host in self.hosts if "server" in host.host_type.name.lower()})

    def __iter__(self):
        #print(self.graph.nodes.items())
        #return iter(self.graph.nodes("data").items())
        return iter(self.graph.nodes.items())

    def __len__(self):
        return len(self.graph)
    
    def get_num_hosts(self) -> int:
        """
        Returns the number of Host objects in the Network.
        """
        return len(self.hosts)

    def get_num_decoys(self) -> int:
        """
        Returns the number of Decoy Hosts in the Network.
        """
        return len(self.decoys)

    def copy(self) -> 'Network':
        """
        Returns a copy of the Network.
        """
        return Network(name=self.name, graph=self.graph.copy())

    def get_all_hosts_on_subnet(self, subnet: Subnet) -> set[Host]:
        """
        Returns a list of all Hosts within the given Subnet
        """
        return list(subnet.get_connected_hosts())

    def add_subnet(self, subnet: Subnet):
        """
        Adds a Subnet to the Network.
        """
        self.add_node(subnet)
        self.subnets[subnet.name] = subnet

    def add_router(self, router: Router):
        """
        Adds a Router to the Network.
        """
        self.add_node(router)

    def add_host(self, host: Host):
        """
        Adds a Host to the Network.
        """
        self.add_node(host)
        self.hosts[host.name] = host
        if host.decoy:
            return
        host_type = host.host_type.name.lower()
        if "server" in host_type:
            self.server_hosts.add(host.name)
        else:
            self.user_hosts.add(host.name)


    def add_node(self, node: Host | Subnet | Router) -> None:
        """
        Adds a Node to the Network.
        """
        self.graph.add_node(node.name, data=node)

    def remove_host(self, host: Host) -> Host:
        """
        Removes a Host from the Network
        """
        try:
            self.graph.remove_node(host.name)
            self.decoys.pop(host.name, None)
            return self.hosts.pop(host.name, None)
        except nx.NetworkXError as e:
            raise e

    def connect_nodes(self, node1, node2):
        """
        Connects two Nodes together in the Network.
        """
        self.graph.add_edge(node1, node2)

    def isolate_host(self, host: Host, subnet: Subnet):
        """
        Isolates a Host from the Network, while keeping its data accessible
        """
        host.isolated = True
        self.disconnect_nodes(host.name, subnet.name)

    def disconnect_nodes(self, node1, node2):
        self.graph.remove_edge(node1, node2)
        self.disconnected_nodes.append((node1, node2))

    def is_subnet_reachable(self, subnet1, subnet2):
        return nx.has_path(self.graph, subnet1.name, subnet2.name)

    def get_random_host(self): # Does not support determinism yet
        return self.hosts[random.choice(list(self.hosts.keys()))]

    def get_random_user_host(self):
        return self.hosts[self.user_hosts.get_random()]

    def get_random_server_host(self):
        return self.hosts[self.server_hosts.get_random()]

    def update_host_compromised_status(self, host: str, is_compromised: bool):
        try:
            host_obj = self.hosts[host]
            host_obj.is_compromised = is_compromised
        except KeyError:
            return None  # return None if host not found

    def check_compromised_status(self, host_name: str) -> bool | None:
        try:
            host_obj = self.hosts[host_name]
            return host_obj.is_compromised
        except KeyError:
            return None  # return None if host not found

    def get_num_hosts(self):
        return len(self.hosts)
    
    def get_num_subnets(self):
        return len(self.subnets)

    # For debugging to view the network being generated
    def draw(self, **kwargs):
        labels: bool = kwargs.get("labels", False)
        filename: str = kwargs.get("filename", "networkx_graph.png")
        colors = []
        for _, node in self.graph.nodes(data="data"):
            if isinstance(node, Host):
                if node.decoy:
                    colors.append("blue")
                elif node.host_type.name == "workstation":
                    colors.append("green")
                elif "server" in node.host_type.name:
                    colors.append("red")
                else:
                    colors.append("black")
            elif isinstance(node, Subnet):
                colors.append("cyan")
            elif isinstance(node, Router):
                colors.append("orange")
            else:
                colors.append("black")

        plt.clf()  # clear
        nx.draw(
            self.graph,
            with_labels=labels,
            node_color=colors,
            node_size=30,
            font_size=12,
            font_color="black",
            font_weight="bold",
            edge_color="black",
        )

        # Display the graph
        if filename != "":
            plt.savefig(filename, format="png")
        else:
            plt.show()

    @classmethod
    def create_network_from_yaml(cls, network_config=None, host_config="host_defs_services.yaml"):  # type: ignore
        if network_config is None:
            config_dir = files("cyberwheel.data.configs.network")
            network_config: PosixPath = config_dir.joinpath(
                "example_config.yaml"
            )  # type:ignore
            print(
                "Using default network config file ({})".format(
                    network_config.absolute()
                )
            )

        # Load the YAML config file
        with open(network_config, "r") as yaml_file:
            config = yaml.safe_load(yaml_file)

        # Create an instance of the Network class
        network = cls(name=config["network"].get("name"))

        conf_dir = files("cyberwheel.data.configs.host_definitions")
        conf_file = conf_dir.joinpath(host_config)
        with open(conf_file) as f:
            type_config = yaml.safe_load(f)
        types = type_config["host_types"]

        ## parse topology
        # parse routers
        routers = tqdm(config["routers"])
        routers.set_description("Building Routers")
        for r in routers:
            routers.set_description(f"Building Routers: {r}", refresh=True)
            router = Router(
                r,
                # val.get('routes', []),
                config["routers"][r].get("firewall", []),
            )
            # add router to network graph
            network.add_router(router)
        subnets = tqdm(config["subnets"])
        subnets.set_description("Building Subnets")
        for s in subnets:
            subnets.set_description(f"Building Subnets: {s}", refresh=True)
            router = network.get_node_from_name(config["subnets"][s]["router"])
            subnet = Subnet(
                s,
                config["subnets"][s].get("ip_range", ""),
                router,
                config["subnets"][s].get("firewall", []),
                dns_server=config["subnets"][s].get("dns_server"),
            )
            # add subnet to network graph
            network.add_subnet(subnet)
            network.connect_nodes(subnet.name, router.name)

            # add subnet interface to router
            router.add_subnet_interface(subnet)

            # set default route to router interface for this subnet
            subnet.set_default_route()

            # assign router first available IP on each subnet
            # routers have one interface for each connected subnet
            router.set_interface_ip(subnet.name, subnet.available_ips.pop(0))

            # ensure subnet.dns_server is defined
            # default to router IP if it's still None
            router_interface_ip = router.get_interface_ip(subnet.name)
            if subnet.dns_server is None and router_interface_ip is not None:
                subnet.set_dns_server(router_interface_ip)
        hosts = tqdm(config["hosts"])
        hosts.set_description("Building Hosts")
        for h in hosts:
            # hosts.set_description(f"Building Hosts: {h}", refresh=True)
            # instantiate firewall rules, if defined
            val = config["hosts"][h]
            fw_rules = []
            if rules := val.get("firewall_rules"):
                for rule in rules:
                    fw_rules.append(
                        FirewallRule(
                            rule("name"),  # type: ignore
                            rule.get("src"),
                            rule.get("port"),
                            rule.get("proto"),
                            rule.get("desc"),
                        )
                    )
            else:
                # if not fw_rules defined insert 'allow all' rule
                fw_rules.append(FirewallRule())

            # instantiate HostType if defined
            if type_str := val.get("type"):
                type = network.create_host_type_from_yaml(type_str, conf_file, types)  # type: ignore
            else:
                type = None

            # instantiate Services in network config file
            services = []
            if services_dict := val.get("services"):
                for service in services_dict:
                    service = services_dict[service]
                    services.append(
                        Service(
                            name=service["name"],
                            port=service["port"],
                            protocol=service.get("protocol"),
                            version=service.get("version"),
                            vulns=service.get("vulns"),
                            description=service.get("descscription"),
                            decoy=service.get("decoy"),
                        )
                    )
            interfaces = []
            if h in config["interfaces"]:
                interfaces = config["interfaces"][h]
            # instantiate host
            host = network.add_host_to_subnet(
                name=h,
                subnet=network.subnets[val["subnet"]],
                host_type=type,
                firewall_rules=fw_rules,
                services=services,
                interfaces=interfaces,
            )

            if routes := val.get("routes"):
                host.add_routes_from_dict(routes)
        network.initialize_interfacing()
        return network

    def get_node_from_name(self, node: str) -> NetworkObject | Host | Subnet | Router:
        """
        Return network object by name

        :param str node: node.name of object
        :returns NetworkObject:
        """
        try:
            return self.graph.nodes[node]["data"]
        except KeyError as e:
            print(f"{node} not found in {self.name}")
            raise e

    def _is_valid_port_number(self, port) -> bool:
        """
        Validates port number
        """
        if isinstance(port, str):
            if port.lower() == "all":
                return True
            port = int(port)
        if port > 65535 or port < 1:
            return False
        return True

    def is_traffic_allowed(
        self,
        src: NetworkObject,
        dest: NetworkObject,
        port: Union[str, int, None],
        proto: str = "tcp",
    ) -> bool:
        """
        Checks firewall to see if network traffic should be allowed

        :param str NetworkObject: source subnet or host of traffic
        :param str NetworkObject: destination subnet or host of traffic
        :param int port: destination port
        :param str proto: protocol (i.e. tcp/udp/icmp, default = tcp)
        """
        # ICMP doesn't use ports (it's considered layer 3)
        if proto.lower() == "icmp":
            pass
        elif not self._is_valid_port_number(port):
            raise ValueError(f"{port} is not a valid port number")

        def _does_src_match(src, rule: dict, type) -> bool:
            if src.name == rule["src"] or rule["src"] == "all":
                return True
            if type == "host":
                if (
                    src.subnet.router.name == rule["src"]
                    or src.subnet.name == rule["src"]
                ):
                    return True
            elif type == "subnet":
                if src.router.name == rule["src"]:
                    return True
            return False

        def _does_dest_match(dest, rule: dict, type) -> bool:
            if dest.name == rule["dest"] or rule["dest"] == "all":
                return True
            if type == "host":
                if (
                    dest.subnet.router.name == rule["dest"]
                    or dest.subnet.name == rule["dest"]
                ):
                    return True
            elif type == "subnet":
                if dest.router.name == rule["dest"]:
                    return True
            return False

        def _does_port_match(port: str, rule: dict) -> bool:
            if str(rule["port"]) == port or str(rule["port"]) == "all":
                return True
            return False

        def _does_proto_match(proto: str, rule: dict) -> bool:
            if rule["proto"] == proto or rule["proto"] == "all":
                return True
            return False

        def _check_rules(src, dest, port, proto, type):

            # default to 'allow all' if no rules defined
            ### this is antithetical to how firewalls work in the real world,
            ### but seemed pragmatic in our case
            # try:
            #    if not dest.firewall_rules:
            #        return True
            # except NameError:
            #    return True

            # loop over each rule/element in firewall_rules
            for rule in dest.firewall_rules:
                # break if src doesn't match
                if not _does_src_match(src, rule, type):
                    break

                # break if dest doesn't match
                if not _does_dest_match(dest, rule, type):
                    break

                # break if port doesn't match
                if not _does_port_match(str(port), rule):
                    break

                # break if proto doesn't match
                if not _does_proto_match(proto, rule):
                    break

                # matching rule found
                return True
            return False

        if isinstance(dest, Host):
            subnet = dest.subnet
            router = subnet.router
            # check router fw
            if not _check_rules(src, router, port, proto, "host"):
                return False
            # check subnet fw
            if not _check_rules(src, subnet, port, proto, "host"):
                return False
            # check host fw
            if not _check_rules(src, dest, port, proto, "host"):
                return False
            return True
        elif isinstance(dest, Subnet):
            router = dest.router
            # check router fw
            if not _check_rules(src, router, port, proto, "subnet"):
                return False
            # check subnet fw
            if not _check_rules(src, dest, port, proto, "subnet"):
                return False
            return True
        elif isinstance(dest, Router):
            # check router fw
            if not _check_rules(src, dest, port, proto, "router"):
                return False
            return True

        return False

    def add_host_to_subnet(
        self, name: str, subnet: Subnet, host_type: HostType | None, **kwargs
    ) -> Host:
        """
        Create host and add it to parent subnet and self.graph

        This method also requests a DHCP lease which includes setting IP, DNS,
        default route, and route for subnet.

        :param str name:
        :param Subnet subnet:
        :param HostType type:
        :param list[FirewallRule] **firewall_rules:
        :param list[Service] **services:
        """
        #print(name)
        #print(subnet)
        host = Host(
            name,
            subnet,
            host_type,
            firewall_rules=kwargs.get("firewall_rules", []),
            services=kwargs.get("services"),
        )
        # add host to graph
        self.add_host(host)
        # connect node to parent subnet
        self.connect_nodes(host.name, subnet.name)
        # assign IP, DNS, route for subnet, and default route
        host.get_dhcp_lease()
        # set decoy status
        host.decoy = kwargs.get("decoy", False)
        host.interfaces = kwargs.get("interfaces", [])
        return host

    def initialize_interfacing(self):
        for h in self.hosts:
            host = self.hosts[h]
            if len(host.interfaces) <= 0:
                continue
            interface_hosts = []
            for i in host.interfaces:
                interface_hosts.append(self.hosts[i])
            host.interfaces = interface_hosts

    def remove_host_from_subnet(self, host: Host) -> None:
        # release DHCP lease
        if host.ip_address is not None:
            ip: ipa.IPv4Address | ipa.IPv6Address = host.ip_address
            host.subnet.available_ips.append(ip)
        self.remove_host(host)
        host.subnet.remove_connected_host(host)
        # TODO
        pass

    def create_decoy_host(self, *args, **kwargs) -> Host:
        """
        Create decoy host and add it to subnet and self.graph

        :param str *name:
        :param Subnet *subnet:
        :param str *type:
        :param list[Service] **services:
        :param IPv4Address | IPv6Address **dns_server:
        """
        host = self.add_host_to_subnet(*args, decoy=True, **kwargs)
        self.decoys[host.name] = host
        return host

    def remove_decoy_host(self, host: Host) -> None:
        self.remove_host_from_subnet(host)
        self.decoys.pop(host.name, None)
        #for _, h in self.graph.nodes(data="data"):
        #    if not isinstance(h, Host):
        #        continue
        #    if h.name == host.name:
        #        self.remove_host_from_subnet(host)
        #        break
        #for i in range(len(self.decoys)):
        #    if self.decoys[i].name == host.name:
        #        break
        #self.decoys.remove(i)

    def reset(self):
        for decoy in list(self.decoys.values()):
            self.remove_host_from_subnet(decoy)
        self.decoys = {}

        for edge in self.disconnected_nodes:
            self.connect_nodes(edge[0], edge[1])
        self.disconnected_nodes = []

        self.isolated_hosts = []

        for _, host in self.hosts.items():
            host.command_history = []
            host.is_compromised = False
            host.isolated = False  # For isolate action
            host.restored = False

    @staticmethod
    def create_host_type_from_json(name: str, config_file: PathLike) -> HostType:
        """
        Return a matching HostType object from json file

        :param str name: host type name to match against
        :param str config_file: JSON config file path
        :raises HostTypeNotFoundError:
        :returns HostType:
        """
        with open(config_file) as f:
            config = json.load(f)
        types: list = config["host_types"]

        host_type = [t for t in types if t["type"].lower() == name.lower()]
        if not host_type:
            msg = f"Host type ({name}) not found in config file ({config_file})"
            raise HostTypeNotFoundError(value=name, message=msg)

        services_list = host_type[0]["services"]
        service_objects = []
        for service in services_list:
            service_objects.append(
                Service(
                    name=name,
                    port=service.get("port"),
                    protocol=service.get("protocol"),
                    version=service.get("version"),
                    vulns=service.get("vulns"),
                    description=service.get("description"),
                    decoy=service.get("decoy"),
                )
            )

        decoy = host_type[0].get("decoy", False)
        os = host_type[0].get("os")

        return HostType(name=name, services=service_objects, decoy=decoy, os=os)

    @staticmethod
    def create_host_type_from_yaml(name: str, config_file: PathLike, types) -> HostType:
        """
        Return a matching HostType object from yaml file

        :param str name: host type name to match against
        :param str config_file: YAML config file path
        :raises HostTypeNotFoundError:
        :returns HostType:
        """
        # match name to defined host_type name
        host_type = {}
        host_type_name = ""
        for k, v in types.items():
            if k == name.lower():
                host_type_name = k
                host_type = v

        if "host_type" not in locals():
            msg = f"Host type ({name}) not found in config file ({config_file})"
            raise HostTypeNotFoundError(value=name, message=msg)

        services_list = host_type.get("services", [])

        windows_services = {}
        config_dir = files("cyberwheel.data.configs.services")
        config_file_path: PosixPath = config_dir.joinpath(
            "windows_exploitable_services.yaml"
        )  # type:ignore
        with open(config_file_path, "r") as f:
            windows_services = yaml.safe_load(f)

        cve_list = set()
        running_services = []
        for service in services_list:
            temp_service = Service.create_service_from_yaml(windows_services, service)
            running_services.append(temp_service)
            cve_list.update(temp_service.vulns)
        decoy: bool = host_type.get("decoy", False)
        os: str = host_type.get("os", "")

        host_type = HostType(
            name=host_type_name,
            services=running_services,
            decoy=decoy,
            os=os,
            cve_list=cve_list,
        )

        return host_type


class HostTypeNotFoundError(Exception):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)
