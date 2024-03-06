from typing import List

from blue_actions.blue_base import BlueAction
from network.subnet import Subnet
from network.network_base import Network
from network.host import Host
from network.service import Service

class DecoyHost(BlueAction):
    def __init__(self, network: Network, subnet: Subnet, type: str) -> None:
        super().__init__()
        self.network: Network = network
        self.subnet: Subnet = subnet
        self.type: str = type

        self.host: Host = Host()

    def execute(self) -> any:
        self.host = self.network.create_decoy_host(self.name, self.subnet, self.type)
        


def decoy_from_yaml(path: str, network: Network, subnet: Subnet)-> DecoyHost:
    """
    Creates a DecoyHost object specified in a YAML file.
    - `path`: path to the config file
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    raise NotImplementedError
    


def random_decoy(network: Network, subnet: Subnet)-> DecoyHost:
    """
    Create a decoy using random parameters. The network and subnet still need to be specified.
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    
    raise NotImplementedError