"""
Test class for genertaing topology.
"""

from pprint import pp
import yaml

class Plugin:
    """
    Mock Plugin class for Firesheel. Use for testing purposes.
    """
    def __init__(self):
        """Initialize class"""
        config = Plugin.read_config("configs/example_config.yaml")
        self.config = config


    def run(self):
        """Connect subnets and run network in emulator"""

    @classmethod
    def read_config(cls, config: str):
        """Read network config from YAML file"""

        with open(config, 'r', encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)
            print(f"loading {config}...")
            return data


    def build_subnet(self):
        """Create emulator subnet from config variables"""
        routers = self.config.get("routers")
        core_router = routers.get("core_router")
        core_router_networks = core_router.get("routes")[0].get("dest")
        print("\ncore router networks")
        pp(core_router_networks)
        print()

        subnets = self.config.get("subnets")
        for subnet_name, v in subnets.items():
            parent_router = v.get("router")
            subnet_ip = v.get("ip_range")
            subnet_network_lst = subnet_ip.split('/')[0].split('.')[0:3]
            subnet_network = '.'.join(subnet_network_lst)
            subnet_mask = subnet_ip.split('/')[1]

            hosts = self.config.get("hosts")
            num_hosts = sum(1 for _, hv in hosts.items() if hv.get("subnet") == subnet_name)

            print()
            print("subnet name: ", subnet_name)
            print("subnet ip range: ", subnet_ip)
            print("parent router: ", parent_router)
            print("subnet network: ", subnet_network)
            print("subnet mask: ", subnet_mask)
            print("number of hosts in subnet: ", num_hosts)


    def build_host(self):
        """Print hosts from config file"""
        hosts = self.config.get("hosts")

        for user, v in hosts.items():
            host_type = v.get("type")
            host_subnet = v.get("subnet")

            print()
            print(f"host name: {user}")
            print(f"host type: {host_type}")
            print(f"host subnet: {host_subnet}")


plugin = Plugin()
plugin.build_subnet()
plugin.build_host()