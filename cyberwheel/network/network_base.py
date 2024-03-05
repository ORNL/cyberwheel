import networkx as nx
import random
import ipaddress as ipa
import numpy as np
import matplotlib.pyplot as plt
import yaml

from .network_object import NetworkObject, FirewallRule, Route
from .service import Service
from .subnet import Subnet
from .host import Host, HostType
from .router import Router


class Network:

    def __init__(self, name=""):
        self.graph = nx.Graph(name=name)
        self.name = name

    def __iter__(self):
        return iter(self.graph)

    def __len__(self):
        return len(self.graph)

    # TODO: remove these in favor of self.add_node()
    def add_subnet(self, subnet):
        self.add_node(subnet)
        #self.graph.add_node(subnet.name, data=subnet)
    def add_router(self, router):
        self.add_node(router)
        #self.graph.add_node(router.name, data=router)
    def add_host(self, host):
        self.add_node(host)
        #self.graph.add_node(host.name, data=host)


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

    def get_hosts(self):
        return [
            data_object
            for node_name, data_object in self.graph.nodes(data="data")
            if isinstance(data_object, Host)
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

    def generate_observation_vector(self):
        all_hosts = self.get_all_hosts()
        num_hosts = len(all_hosts)
        observation_vector = np.zeros(num_hosts, dtype=np.int8)

        index = 0
        for data_object in all_hosts:
            is_compromised = data_object.is_compromised
            observation_vector[index] = 1 if is_compromised else 0
            index += 1

    def get_action_space_size(self):
        # TODO: could we just `return len(self.get_all_hosts())` here?
        n = 1  # do nothing action
        for _, data_object in self.graph.nodes(data="data"):
            if isinstance(data_object, Host):
                n += 1
        return n

    # TODO: still need to test this
    def is_any_subnet_fully_compromised(self):
        ## Iterate over all nodes in the graph
        # for node_name, data_object in self.graph.nodes(data='data'):
        #    # Check if the node is a Subnet
        #    if isinstance(data_object, Subnet):
        #        # Get all hosts connected to the subnet
        #        hosts = [self.graph.nodes[neighbor]['data'] for neighbor in self.graph.neighbors(node_name) if isinstance(self.graph.nodes[neighbor]['data'], Host)]
        #        # Check if all hosts are compromised
        #        if all(host.is_compromised for host in hosts):
        #            return True

        all_subnets = self.get_all_subnets()
        for subnet in all_subnets:
            subnet_hosts = self.get_all_hosts_on_subnet(subnet)
            if all(host.is_compromised for host in subnet_hosts):
                return True

        return False

    # TODO: still need to test this
    def set_host_compromised(self, host_id, compromised):
        # hosts = [data_object for node_name, data_object in self.graph.nodes(data='data') if isinstance(data_object, Host)]
        host_to_modify = self.get_host_from_name(host_id)
        # host_to_modify = hosts[host_id]  # Adjust the index to match the list
        current_state = host_to_modify.is_compromised
        host_to_modify.is_compromised = (
            compromised  # Set is_compromised to False for the selected host
        )

        host = self.get_host_from_name(host_id)

        return current_state

    # For debugging to view the network being generated
    def draw(self, **kwargs):
        labels: bool = kwargs.get("labels", False)
        filename: str = kwargs.get("filename", "networkx_graph.png")

        plt.clf()  # clear
        nx.draw(
            self.graph,
            with_labels=labels,
            node_color="skyblue",
            node_size=30,
            font_size=12,
            font_color="black",
            font_weight="bold",
            edge_color="black",
        )

        # Display the graph
        plt.savefig(filename, format="png")

    @classmethod
    def create_network_from_yaml(cls, config_file_path):
        # TODO: should this just be a module-level function instead of static method??
        @staticmethod
        def create_host_type_from_yaml(name: str, config_file: str) -> HostType:
            with open(config_file) as f:
                config = yaml.safe_load(f)

            services = config[name].get('services')
            decoy: bool = config[name].get('decoy', False)

            return HostType(name=name, services=services, decoy=decoy)

        # Load the YAML config file
        with open(config_file_path, "r") as yaml_file:
            config = yaml.safe_load(yaml_file)

        # Create an instance of the Network class
        network = cls(name=config["network"].get("name"))

        ## parse topology
        # parse routers
        for key, val in config["routers"].items():
            router = Router(
                key,
                # using '.get()' here in case default_route isn't defined
                val.get("default_route"),
                val.get("routes", []),
                val.get("firewall", []),
            )
            # add router to network graph
            network.add_router(router)

            # instantiate subnets for this router
            for key, val in config["subnets"].items():
                subnet = Subnet(
                    key,
                    val.get("default_route", None),
                    val.get("ip_range", ""),
                    router,
                    val.get("firewall", []),
                    dns_server=val.get("dns_server"),
                )
                # add subnet to network graph
                network.add_subnet(subnet)
                network.connect_nodes(subnet.name, router.name)

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
                    if val['subnet'] == subnet.name:
                        # instantiate firewall rules
                        fw_rules = []
                        if rules := val.get('firewall_rules'):
                            for rule in rules:
                                fw_rules.append(FirewallRule(rule('name'), # type: ignore
                                                             rule.get('src'),
                                                             rule.get('port'),
                                                             rule.get('proto'),
                                                             rule.get('desc')))
                        # TODO: wip
                        # instantiate host type
                        if type_str := val.get('type'):
                            type = create_host_type_from_yaml(type_str, 'file.yml')
                        else:
                            type = HostType()

                        # instantiate services
                        if services_dict := val.get('services'):
                            services = [service for service in services_dict]
                            for service in services_dict.items():
                                services.append(Service(name=service['name'],
                                                        port=service['port'],
                                                        protocol=service.get('protocol'),
                                                        version=service.get('version'),
                                                        vulns=service.get('vulns'),
                                                        description=service.get('descscription'),
                                                        decoy=service.get('decoy')))
                        else:
                            services = []

                        # instantiate dns server
                        host = Host(key,
                                    subnet,
                                    type,
                                    firewall_rules=fw_rules,
                                    services=services,
                                    )

                        # add host to network graph
                        network.add_host(host)
                        network.connect_nodes(host.name, subnet.name)

                        # get IP from subnet
                        #host.set_ip(subnet.get_dhcp_lease())
                        host.get_dhcp_lease()
                        if routes := val.get('routes'):
                            for route in routes:
                                dest = route['dest']
                                via = route['via']
                                host.add_route(dest, via)

        return network

    def get_node_from_name(self, node: str) -> NetworkObject:
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
        nodes_tuple = self.graph.nodes(data="data")
        hosts = [obj for _, obj in nodes_tuple if isinstance(obj, Host)]

        return hosts

    def get_all_subnets(self) -> list:
        nodes_tuple = self.graph.nodes(data="data")
        subnets = [obj for _, obj in nodes_tuple if isinstance(obj, Subnet)]

        return subnets

    def get_all_routers(self) -> list:
        nodes_tuple = self.graph.nodes(data="data")
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


    def add_host_to_subnet(self, name: str, subnet: Subnet, type: HostType, **kwargs) -> Host:
        '''
        Create host and add it to parent subnet and self.graph

        :param str *name:
        :param Subnet *subnet:
        :param str *type:
        :param list[Service] **services:
        :param IPv4Address | IPv6Address **dns_server:
        '''
        host = Host(name,
                    subnet,
                    type,
                    firewall_rules=[],
                    #services=kwargs.get('services'),
                    #dns_server=kwargs.get('dns_server'),
                    )
        # add host to graph
        self.add_node(host)
        # connect node to parent subnet
        self.connect_nodes(host.name, subnet.name)
        # assign IP, DNS, route for subnet, and default route
        host.get_dhcp_lease()
        return host


    def remove_host_from_subnet(self, host: Host) -> None:
        # release DHCP lease
        if host.ip_address is not None:
            ip: ipa.IPv4Address | ipa.IPv6Address = host.ip_address
            host.subnet.available_ips.append(ip)
        self.remove_node(host)
        host.subnet.remove_connected_host(host)
        pass

        
    def create_decoy_host(self, *args, **kwargs) -> Host:
        '''
        Create decoy host and add it to subnet and self.graph

        :param str *name:
        :param Subnet *subnet:
        :param str *type:
        :param list[Service] **services:
        :param IPv4Address | IPv6Address **dns_server:
        '''
        host = self.add_host_to_subnet(*args, decoy=True, **kwargs)
        host.decoy = True
        return host
