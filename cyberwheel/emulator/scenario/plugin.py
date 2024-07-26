"""This plugin emulates the Cage 2 Challenge Scenario"""

import yaml
import os
from netaddr import IPNetwork
from base_objects import Switch


# from linux.ubuntu1604 import Ubuntu1604Server, Ubuntu1604Desktop
from linux.ubuntu1604cage import (
    Ubuntu1604Server,
    Ubuntu1604Desktop,
    Ubuntu1604DesktopSiem,
)
from vyos.helium118 import Helium118
from firewheel.control.experiment_graph import AbstractPlugin, Vertex

# Not working...
# from linux.ubuntu1804 import Ubuntu1804Server, Ubuntu1804Desktop
# from windows.windows_server_2008_r2 import WindowsServer2008R2

# Get network configuration file name from environment variable
network_config = os.environ["NETWORK_CONFIG"]


def read_config(name: str):
    """Read network config from YAML file"""
    cwd = os.getcwd()

    with open(f"{cwd}/configs/{name}", "r", encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.SafeLoader)
        return data


class Plugin(AbstractPlugin):
    """cage.topology plugin documentation."""

    def run(self):
        """Run method documentation."""

        # TODO - add check to ensure config exist
        config = read_config(network_config)

        # Create an external-facing network
        # self.external_network = IPNetwork("1.0.0.0/24")
        # Create an external-facing network iterator
        # external_network_iter = self.external_network.iter_hosts()

        # Create an internal facing network
        core_router = config.get("routers").get("core_router")
        core_router_networks = core_router.get("routes")[0].get("dest")
        internal_networks = IPNetwork(core_router_networks)  # e.g. 10.0.0.0/8

        # Break the internal network in to various subnets
        self.internal_subnets = internal_networks.subnet(24)

        # Create an internal switch
        internal_switch_name = "cyberwheel-internal-switch"
        internal_switch = Vertex(self.g, name=internal_switch_name)
        internal_switch.decorate(Switch)

        # Grab a subnet to use for connections to the internal switch
        internal_switch_network = next(self.internal_subnets)
        # Create a generator for the network
        internal_switch_network_iter = internal_switch_network.iter_hosts()
        print(
            f"\ncreated switch {internal_switch_name}, network: {core_router_networks}\n"
        )

        # Build Subnets
        subnets = config.get("subnets")
        for name, values in subnets.items():
            subnet_name = name.replace("_", "-")

            # Extract subnet's ip range
            subnet_ip = values.get("ip_range")
            subnet_network = IPNetwork(subnet_ip)

            # Break up subnet network into smaller subnets
            # internal_subnets = subnet_network.subnet(24)

            # Create subnets
            print(f"creating {subnet_name} with ip range {subnet_ip}...")
            subnet_router = self.build_subnet(subnet_name, subnet_network, num_hosts=2)
            print(f"finished creating {subnet_name}")

            # Connect subnet to internal switch
            subnet_router.ospf_connect(
                internal_switch,
                next(internal_switch_network_iter),
                internal_switch_network.netmask,
            )
            print(f"connected {subnet_name} router to {internal_switch_name}\n")

            # Connect all connected subnets together
            # subnet_router.redistribute_ospf_connected()

        # Create the Firewall and Enterprise Hosts subnet (Subnet 2)
        # enterprise_subnet_firewall = self.build_enterprise_subnet(
        #     "enterprise", next(self.internal_subnets), num_hosts=3
        # )

        # Connect firewall to internal switch
        # enterprise_subnet_firewall.ospf_connect(
        #     internal_switch,
        #     next(internal_switch_network_iter),
        #     internal_switch_network.netmask,
        # )

    def build_subnet(self, name: str, network: IPNetwork, num_hosts: int = 1):
        """Build subnet

        Args:
            name (str): the name of the user hosts subnet.
            network (netaddr.IPNetwork): the subnet for the user hosts.
            num_hosts (int): the number of hosts the subnet should have.

        Returns:
        vyos.Helium118: The subnet router.
        """

        # Create subnet router
        subnet_name = f"{name}.cyberwheel.com"
        subnet_router = Vertex(self.g, name=subnet_name)
        subnet_router.decorate(Helium118)

        # Create hosts switch
        subnet_switch_name = f"{name}-switch"
        subnet_switch = Vertex(self.g, name=subnet_switch_name)
        subnet_switch.decorate(Switch)

        # Create a network generator
        network_iter = network.iter_hosts()

        # Connet the router to the switch
        subnet_ip = next(network_iter)
        subnet_router.connect(subnet_switch, subnet_ip, network.netmask)
        print(
            f"connected {subnet_name} router to {subnet_switch_name}, {subnet_ip} {network.netmask}"
        )

        # Redistributes routes directly connected subnets to OSPF peers.
        subnet_router.redistribute_ospf_connected()

        # Create hosts
        for i in range(num_hosts):
            # Create a new host which are Ubuntu Desktops
            host_name = f"{name}-host-{i}.cyberwheel.com"
            host = Vertex(self.g, name=host_name)
            host.decorate(Ubuntu1604Desktop)

            # Connect the host ot the switch
            host_ip = next(network_iter)
            host.connect(subnet_switch, host_ip, network.netmask)
            print(
                f"connected {host_name} to {subnet_switch_name}, {host_ip} {network.netmask}"
            )

        return subnet_router
