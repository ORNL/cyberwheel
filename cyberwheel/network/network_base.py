from importlib.resources import files
import ipaddress as ipa
import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from os import PathLike
from pathlib import PosixPath
import random
from typing import Union, List, Type
import yaml

from .host import Host, HostType
from .network_object import NetworkObject, FirewallRule, Route
from .router import Router
from .service import Service
from .subnet import Subnet


class Network:

    def __init__(self, name=""):
        self.graph = nx.Graph(name=name)
        self.name = name
        self.decoys = []
        self.disconnected_nodes = []
        self.isolated_hosts: List[Host] = []

    def __iter__(self):
        return iter(self.graph)

    def __len__(self):
        return len(self.graph)

    def get_decoys(self):
        return self.decoys
    
    def num_decoys(self):
        return len(self.decoys)
    
    def get_disconnected(self):
        return self.disconnected_nodes
    
    def get_connected(self):
        return [
            host for _, host in self.graph.nodes(data="data") if isinstance(host, Host) and not host.disconnected 
        ] 

    def num_disconnected(self):
        return len(self.disconnected_nodes)


    # TODO: remove these in favor of self.add_node()
    def add_subnet(self, subnet):
        self.add_node(subnet)
        # self.graph.add_node(subnet.name, data=subnet)

    def add_router(self, router):
        self.add_node(router)
        # self.graph.add_node(router.name, data=router)

    def add_host(self, host):
        self.add_node(host)
        # self.graph.add_node(host.name, data=host)

    def add_node(self, node) -> None:
        self.graph.add_node(node.name, data=node)

    def remove_node(self, node: NetworkObject) -> None:
        try:
            self.graph.remove_node(node.name)
        except nx.NetworkXError as e:
            # TODO: raise custom exception?
            raise e

    def connect_nodes(self, node1, node2):
        self.graph.add_edge(node1, node2)

    def isolate_host(self, host: Host, subnet: Subnet):
        # print(host.name, subnet.name)
        host.isolated = True
        # self.isolated_hosts.append(host)
        self.disconnect_nodes(host.name, subnet.name)

    def disconnect_nodes(self, node1, node2):
        self.graph.remove_edge(node1, node2)
        self.disconnected_nodes.append((node1, node2))
    # def define_routing_rules(self, router, routes):
    #    if router.name in self.graph.nodes:
    #        data_object = self.graph.nodes[router.name]['data']
    #        if isinstance(data_object, Router):
    #            data_object.routes = routes

    # def define_firewall_rules(self, router, firewall_rules):
    #    if router.name in self.graph.nodes:
    #        data_object = self.graph.nodes[router.name]['data']
    #        if isinstance(data_object, Router):
    #            data_object.firewall_rules = firewall_rules

    # def define_host_firewall_rules(self, host, firewall_rules):
    #    if host.name in self.graph.nodes:
    #        data_object = self.graph.nodes[host.name]['data']
    #        if isinstance(data_object, Host):
    #            data_object.firewall_rules = firewall_rules

    def is_subnet_reachable(self, subnet1, subnet2):
        return nx.has_path(self.graph, subnet1.name, subnet2.name)

    def get_random_host(self):
        all_hosts = self.get_all_hosts()
        return random.choice(all_hosts)

    def get_random_user_host(self):
        hosts = self.get_hosts()
        user_hosts = []
        for h in hosts:
            if h.host_type != None and "workstation" in h.host_type.name.lower():
                user_hosts.append(h)
        random_host = random.choice(user_hosts)
        return random_host

    def get_hosts(self) -> list[Host]:
        return [
            host for _, host in self.graph.nodes(data="data") if isinstance(host, Host)
        ]  # type:ignore

    def get_host_names(self) -> list[str]:
        return [
            host.name
            for _, host in self.graph.nodes(data="data")
            if isinstance(host, Host)
        ]

    def get_nondecoy_hosts(self) -> List[Host]:
        return [
            host
            for _, host in self.graph.nodes(data="data")
            if isinstance(host, Host) and not host.decoy
        ]

    def update_host_compromised_status(self, host: str, is_compromised: bool):
        try:
            host_obj = self.get_node_from_name(host)
            host_obj.is_compromised = is_compromised
        except KeyError:
            return None  # return None if host not found

    def check_compromised_status(self, host_name: str) -> bool | None:
        try:
            host_obj = self.get_node_from_name(host_name)
            return host_obj.is_compromised
        except KeyError:
            return None  # return None if host not found

    # TODO - This method is not working properly
    def find_path_between_hosts(self, source_host, target_host):
        if source_host not in self.graph or target_host not in self.graph:
            return None  # Source or target not found in the network

        try:
            return nx.shortest_path(self.graph, source=source_host, target=target_host)
            # shortest_path = nx.shortest_path(self.graph, source=source_host, target=target_host)
            ##shortest_path = [item for item in shortest_path if "Router" not in item]

            ## Replace subnet names with host names on those subnets
            # new_path = []

            # for node in shortest_path:
            #    if isinstance(self.graph.nodes[node]['data'], Subnet):
            #    #if node.startswith('Subnet'):
            #        subnet_name = node
            #        # Try to find a connected node that starts with 'Host'
            #        connected_host = None
            #        for neighbor in self.graph.neighbors(subnet_name):
            #            if neighbor.startswith('Host'):
            #                connected_host = neighbor
            #                break

            #        if connected_host:
            #            new_path.append(connected_host)  # Replace subnet with connected host
            #        else:
            #            new_path.append(node)  # If no connected host found, keep the subnet
            #    else:
            #        # Keep non-subnet nodes unchanged
            #        new_path.append(node)

            # return new_path
        except:
            return None

    def find_host_with_longest_path(self, source_host):
        all_hosts = self.get_all_hosts()

        all_hosts.remove(source_host)  # Remove the source host from the list
        if not all_hosts:
            return None  # No other hosts in the network

        longest_path_length = -1
        target_host = None

        for host in all_hosts:
            path = self.find_path_between_hosts(source_host, host)
            if path is not None and len(path) > longest_path_length:
                longest_path_length = len(path)
                target_host = host

        return target_host

    # def generate_observation_vector(self):
    #     all_hosts = self.get_all_hosts()
    #     num_hosts = len(all_hosts)
    #     observation_vector = np.zeros(num_hosts, dtype=np.int8)

    #     index = 0
    #     for data_object in all_hosts:
    #         is_compromised = data_object.is_compromised
    #         observation_vector[index] = 1 if is_compromised else 0
    #         index += 1

    def get_action_space_size(self):
        return len(self.get_hosts())

    # TODO: still need to test this
    def is_any_subnet_fully_compromised(self):
        all_subnets = self.get_all_subnets()
        for subnet in all_subnets:
            subnet_hosts = self.get_all_hosts_on_subnet(subnet)
            if all(host.is_compromised for host in subnet_hosts):
                return True
        return False

    # TODO: still need to test this
    def set_host_compromised(self, host_id: str, compromised: bool):
        host_to_modify = self.get_node_from_name(host_id)
        host_to_modify.is_compromised = compromised

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
            config_dir = files("cyberwheel.network")
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

        conf_dir = files("cyberwheel.resources.metadata")
        # TODO: use create_host_type_from_yaml() instead?
        # conf_file = conf_dir.joinpath('host_definitions.json')
        # type = network.create_host_type_from_json(type_str, conf_file) #type: ignore
        conf_file = conf_dir.joinpath(host_config)
        with open(conf_file) as f:
            type_config = yaml.safe_load(f)
        types = type_config["host_types"]

        ## parse topology
        # parse routers
        for key, val in config["routers"].items():
            router = Router(
                key,
                # val.get('routes', []),
                val.get("firewall", []),
            )
            # add router to network graph
            network.add_router(router)

            # instantiate subnets for this router
            for key, val in config["subnets"].items():
                if not val.get("router") == router.name:
                    continue
                subnet = Subnet(
                    key,
                    val.get("ip_range", ""),
                    router,
                    val.get("firewall", []),
                    dns_server=val.get("dns_server"),
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

                # instantiate hosts for this subnet
                for key, val in config["hosts"].items():

                    # is host attached to this subnet?
                    if val["subnet"] != subnet.name:
                        continue

                    # instantiate firewall rules, if defined
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

                    # TODO: wip
                    # instantiate HostType if defined
                    if type_str := val.get("type"):
                        type = network.create_host_type_from_yaml(type_str, conf_file, types)  # type: ignore
                    else:
                        type = None

                    # instantiate Services in network config file
                    if services_dict := val.get("services"):
                        services = [service for service in services_dict]
                        for service in services_dict.items():
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
                    else:
                        services = []
                    # TODO: Maybe integrate with routers instead
                    interfaces = []
                    if key in list(config["interfaces"].keys()):
                        interfaces = config["interfaces"][key]
                    # instantiate host
                    host = network.add_host_to_subnet(
                        name=key,
                        subnet=subnet,
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
            # TODO: raise custom exception? return None?
            print(f"{node} not found in {self.name}")
            raise e

    def get_all_hosts(self) -> list:
        nodes_tuple = self.graph.nodes(data="data")  # type: ignore
        hosts = [obj for _, obj in nodes_tuple if isinstance(obj, Host)]

        return hosts

    def get_all_subnets(self) -> list:
        nodes_tuple = self.graph.nodes(data="data")  # type: ignore
        subnets = [obj for _, obj in nodes_tuple if isinstance(obj, Subnet)]

        return subnets

    def get_all_routers(self) -> list:
        nodes_tuple = self.graph.nodes(data="data")  # type: ignore
        routers = [obj for _, obj in nodes_tuple if isinstance(obj, Router)]

        return routers

    def get_all_hosts_on_subnet(self, subnet: Subnet) -> list:
        return subnet.get_connected_hosts()

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

    # TODO: should this be defined in the red actions?
    def scan_subnet(self, src: Host, subnet: Subnet) -> dict:
        """
        Scans a given subnet and returns found IPs and open ports

        """
        all_hosts = self.get_all_hosts_on_subnet(subnet)
        for host in all_hosts:
            pass
        found_hosts = {}
        return found_hosts

    # TODO: should this be defined in the red actions?
    def scan_host(self, src: Host, ip: str) -> list:
        """
        Scans a given host and returns open ports
        """
        open_ports = []
        return open_ports

    def ping_sweep_subnet(self, src: Host, subnet: Subnet) -> list:
        """
        Attempts to ping all hosts on a subnet

        Hosts are only visible to ping if ICMP is allowed by the firewall(s).
        """
        subnet_hosts = self.get_all_hosts_on_subnet(subnet)
        found_ips = []
        for host in subnet_hosts:
            if self.is_traffic_allowed(src, host, None, "icmp"):
                found_ips.append(host.ip_address)
        return found_ips

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

            # TODO: catch any common exceptions (KeyError, etc.)
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
        host = Host(
            name,
            subnet,
            host_type,
            firewall_rules=kwargs.get("firewall_rules", []),
            services=kwargs.get("services"),
        )
        # add host to graph
        self.add_node(host)
        # connect node to parent subnet
        self.connect_nodes(host.name, subnet.name)
        # assign IP, DNS, route for subnet, and default route
        host.get_dhcp_lease()
        # set decoy status
        host.decoy = kwargs.get("decoy", False)
        host.interfaces = kwargs.get("interfaces", [])
        return host

    def initialize_interfacing(self):
        h_names = [h.name for h in self.get_all_hosts() if len(h.interfaces) > 0]
        for h in h_names:
            host = self.get_node_from_name(h)
            interface_hosts = []
            for i in host.interfaces:
                interface_hosts.append(self.get_node_from_name(i))
            host.interfaces = interface_hosts

    def remove_host_from_subnet(self, host: Host) -> None:
        # release DHCP lease
        if host.ip_address is not None:
            ip: ipa.IPv4Address | ipa.IPv6Address = host.ip_address
            host.subnet.available_ips.append(ip)
        if host in self.get_hosts():
            self.remove_node(host)
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
        self.decoys.append(host)
        return host
    
    def remove_decoy_host(self, host: Host) -> None:
        for _, h in self.graph.nodes(data="data"):
            if not isinstance(h, Host):
                continue
            if h.name == host.name:
                self.remove_host_from_subnet(host)
                break
        for i in range(len(self.decoys)):
            if self.decoys[i].name == host.name:
                break
        self.decoys.remove(i)
        
    def reset(self):
        for decoy in self.decoys:
            self.remove_host_from_subnet(decoy)
        self.decoys = []

        for edge in self.disconnected_nodes:
            self.connect_nodes(edge[0], edge[1])
        self.disconnected_nodes = []

        for host in self.isolated_hosts:
            host.isolated = False
        self.isolated_hosts = []

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
            # debug
            print(f"{service=}")
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

        # print(config_file)

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
        config_dir = files("cyberwheel.resources.configs")
        config_file_path: PosixPath = config_dir.joinpath(
            "windows_exploitable_services.yaml"
        )  # type:ignore
        with open(config_file_path, "r") as f:
            windows_services = yaml.safe_load(f)

        running_services = []
        for service in services_list:
            # print(service)
            running_services.append(
                Service.create_service_from_yaml(windows_services, service)
            )
        decoy: bool = host_type.get("decoy", False)
        os: str = host_type.get("os", "")

        host_type = HostType(
            name=host_type_name, services=running_services, decoy=decoy, os=os
        )

        return host_type


class HostTypeNotFoundError(Exception):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)
