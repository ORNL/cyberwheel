import os
import uuid
import yaml 

from typing import List, Tuple

# Helper functions to handle the check if a key is None and convert it to the right value
def _none_to_dict(dict_, key):
    if dict_[key] is None: dict_[key] = {}

def _none_to_list(dict_, key):
    if dict_[key] is None: dict_[key] = []  

def make_firewall(name="", src="", dest="", port=0, protocol=""):
    return (name, src, dest, port, protocol)


class NetworkYAMLGenerator():
    # https://stackoverflow.com/a/37445121
    yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', ''))

    def __init__(self, network_name=f'network-{uuid.uuid4().hex}', desc="default description"):
        self.data = {
            "network": 
                {"name": network_name, 
                 "desc": desc},
            "routers": None,
            "subnets": None,
            "host_type_config": None,
            "hosts": None,
            "interfaces": None,
            "topology": None,
                }

        self.file_name = f"{network_name}.yaml"

    def router(self, router_name: str, default_route: str):
        _none_to_dict(self.data, "routers")
        if router_name in self.data["routers"]:
            raise KeyError(f"key '{router_name}' already exists")
        self.data["routers"][router_name] = {}
        self.data["routers"][router_name]["default_route"] = default_route
        self.data["routers"][router_name]["routes_by_name"] = None
        self.data["routers"][router_name]["routes"] = None
        self.data["routers"][router_name]["firewall"] = None
    
    def add_route_to_router(self, router_name: str, dest: str, via: str):
        if not self.data["routers"][router_name]:
            raise KeyError(f"key '{router_name}' not found")
        self._add_route("routers", router_name, dest, via)

    def add_route_by_name(self, router_name: str, name: str):
        if not self.data["routers"][router_name]:
            raise KeyError(f"key '{router_name}' not found")
        _none_to_list(self.data["routers"][router_name], "routes_by_name")
        self.data["routers"][router_name]["routes_by_name"].append(name)

    def add_firewall_to_router(self, router_name: str, name="", src="", dest="", port=0, protocol=""):
        if not self.data["routers"][router_name]:
            raise KeyError(f"key '{router_name}' not found")
        self._add_firewall_entry("routers", router_name, name, src, dest, port, protocol)

    def add_firewalls_to_router(self, router_name: str, firewalls: List[Tuple[str, str, str, int, str]]):
        for firewall in firewalls:
            self.add_firewall_to_router(router_name, name=firewall[0], src=firewall[1], dest=firewall[2], port=firewall[3], protocol=firewall[4])

    def add_firewall_to_routers(self, routers: List[str], name="", src="", dest="", port=0, protocol=""):
        for router_name in routers:
            self.add_firewall_to_router(router_name, name, src, dest, port, protocol)

    def add_firewalls_to_routers(self, routers: List[str], firewalls: List[Tuple[str, str, str, int, str]]):
        for router_name in routers:
            self.add_firewalls_to_router(router_name, firewalls)

    def subnet(self, subnet_name: str, router_name="", ip_range="", dns_server="", default_route=""):
        _none_to_dict(self.data, "subnets")
        if subnet_name in self.data["subnets"]:
            raise KeyError(f"key '{subnet_name}' already exists")
        self.data["subnets"][subnet_name] = {}
        if router_name:
            self.data["subnets"][subnet_name]["router"] = router_name
        if ip_range:
            self.data["subnets"][subnet_name]["ip_range"] = ip_range
        if dns_server:
            self.data["subnets"][subnet_name]["dns_server"] = dns_server
        if default_route:
            self.data["subnets"][subnet_name]["default_route"] = default_route
        self.data["subnets"][subnet_name]["firewall"] = None

    def add_firewall_to_subnet(self, subnet_name: str, name="", src="", dest="", port=0, protocol=""):
        if not self.data["subnets"][subnet_name]:
            raise KeyError(f"key '{subnet_name}' not found")
        self._add_firewall_entry("subnets", subnet_name, name, src, dest, port, protocol)

    def add_firewalls_to_subnet(self, subnet_name: str, firewalls: List[Tuple[str, str, str, int, str]]):
        for firewall in firewalls:
            self.add_firewall_to_subnet(subnet_name, name=firewall[0], src=firewall[1], dest=firewall[2], port=firewall[3], protocol=firewall[4])

    def add_firewall_to_subnets(self, subnets: List[str], name="", src="", dest="", port=0, protocol=""):
        for subnet_name in subnets:
            self.add_firewall_to_subnet(subnet_name, name, src, dest, port, protocol)

    def add_firewalls_to_subnets(self, subnets: List[str], firewalls: List[Tuple[str, str, str, int, str]]):
        for subnet_name in subnets:
            self.add_firewalls_to_subnet(subnet_name, firewalls)

    def host(self, host_name: str, subnet: str, type_: str):
        _none_to_dict(self.data, "hosts")
        if host_name in self.data["hosts"]:
            raise KeyError(f"key '{host_name}' already exists")
        
        self.data["hosts"][host_name] = {}
        self.data["hosts"][host_name]["subnet"] = subnet
        self.data["hosts"][host_name]["type"] = type_
        self.data["hosts"][host_name]["firewall"] = None
        self.data["hosts"][host_name]["routes"] = None
    
    def add_route_to_host(self, host_name: str, dest: str, via: str):
        if not self.data["hosts"][host_name]:
            raise KeyError(f"key '{host_name}' not found")
        self._add_route("hosts", host_name, dest, via)

    def add_firewall_to_host(self, host_name: str, name="", src="", dest="", port=0, protocol=""):
        if not self.data["hosts"][host_name]:
            raise KeyError(f"key '{host_name}' not found")
        self._add_firewall_entry("hosts", host_name, name, src, dest, port, protocol)

    def add_firewalls_to_host(self, host_name: str, firewalls: List[Tuple[str, str, str, int, str]]):
        for firewall in firewalls:
            self.add_firewall_to_host(host_name, name=firewall[0], src=firewall[1], dest=firewall[2], port=firewall[3], protocol=firewall[4])

    def add_firewall_to_hosts(self, hosts: List[str], name="", src="", dest="", port=0, protocol=""):
        for host_name in hosts:
            self.add_firewall_to_host(host_name, name, src, dest, port, protocol)

    def add_firewalls_to_hosts(self, hosts: List[str], firewalls: List[Tuple[str, str, str, int, str]]):
        for host_name in hosts:
            self.add_firewalls_to_host(host_name, firewalls)

    def set_host_type_config(self, path: str):
        self.data["host_type_config"] = path

    def interface(self, src: str, dest: str):
        _none_to_dict(self.data, "interfaces")
        if src not in self.data["interfaces"]:
            self.data["interfaces"][src] = []
        self.data["interfaces"][src].append(dest)

    def _add_route(self, index: str, index2: str, dest: str, via: str):
        if not self.data[index]:
            raise KeyError(f"key '{index}' not found")
        if not self.data[index][index2]:
            raise KeyError(f"key '{index2}' not found")
        _none_to_list(self.data[index][index2], "routes")
        self.data[index][index2]["routes"].append({"dest": dest, "via": via})
    
    def _add_firewall_entry(self, index: str, index2: str, name="", src="", dest="", port=0, protocol=""):
        firewall_object = {}
        if name: 
            firewall_object["name"] = name
        if src: 
            firewall_object["src"] = name
        if dest: 
            firewall_object["dest"] = dest
        if port: 
            firewall_object["port"] = port
        if protocol: 
            firewall_object["proto"] = protocol
        _none_to_list(self.data[index][index2], "firewall")
        self.data[index][index2]["firewall"].append(firewall_object)
    
    def topology(self):
        # TODO These two for loops can probably be compressed into one somehow, though this isn't really important right now
        topology = {}
        for router in self.data["routers"]:
            topology[router] = None
            for subnet, s_data in self.data["subnets"].items():
                    if "router" not in s_data: continue
                    if s_data["router"] != router: continue
                    
                    if not topology[router]: topology[router]={}
                    topology[router][subnet] = None

                    for host, h_data in self.data["hosts"]. items():
                        if h_data["subnet"] != subnet: continue
                        if not topology[router][subnet]: topology[router][subnet] = []
                        topology[router][subnet].append(host)

        for subnet, s_data in self.data["subnets"].items():
            if "router" in s_data: continue
            if "no_router" not in topology:
                topology["no_router"] = {}
            topology["no_router"][subnet] = None

            for host, h_data in self.data["hosts"]. items():
                    if h_data["subnet"] != subnet: continue
                    if not topology["no_router"][subnet]: topology["no_router"][subnet] = []
                    topology["no_router"][subnet].append(host)

        self.data["topology"] = topology

    def _debug_output(self):
        print(self.data)

    def output(self, path= "."):
        self.topology()
        path = os.path.join(path, self.file_name)
        with open(path, "w") as w:
            yaml.safe_dump(self.data, w)

