import json
import random
import yaml

from typing import List

from blue_actions.blue_base import BlueAction
from network.network_base import Network
from network.host import Host, HostType
from network.service import Service
from network.subnet import Subnet


def get_host_types() -> List[dict[str, any]]:
    with open('cyberwheel/resources/metadata/host_definitions.json', 'rb') as f:
        host_defs = json.load(f)
    return host_defs['host_types']

class DecoyHost(BlueAction):
    def __init__(self, network: Network, subnet: Subnet, type: HostType) -> None:
        """
            A class that allows the blue agent to create a decoy host.
            ### Parameters
            - `network`: the game's network object
            - `subnet`: the subnet this host should be added on
            - `type`: the type of host this decoy will impersonate

            ### Member variables
            - `reward`: the effect this decoy has on the overall reward upon execution
            - `recurring_reward`: the recurring effect this decoy has on the overall reward
        """
        
        self.network: Network = network
        self.subnet: Subnet = subnet
        self.type: str = type
        self.host: Host = Host()
        self.reward: int = 0 
        self.recurring_reward: int = 0  

    def execute(self) -> int:
        self.host = self.network.create_decoy_host(self.name, self.subnet, self.type)
        return self.reward

    def calc_recurring_cost(self, n: int)-> int:
        return n + self.recurring_reward

    def set_reward(self, reward: int)-> None:
        self.reward = reward
    
    def set_recurring_rewawrd(self, recurring_reward: int)-> None:
        self.recurring_reward = recurring_reward

    def check_if_accessed(self) -> Host:
        """
        NOTE: This might be better implemented in the alert stage of the pipeline.\n
        This method can be called to see if the decoy has been accessed and by which host.
        Returns `None` if it hasn't been accessed.
        Returns the `Host` that accessed it
        """
        raise NotImplementedError


def decoy_from_yaml(path: str, network: Network, subnet: Subnet)-> DecoyHost:
    """
    Creates a DecoyHost object specified in a YAML file. This YAML file defines 
    a type of host, what services run on it, and if there are any firewall rules.
    This should allow for different kinds of decoy hosts to be made in the future.
    - `path`: path to the config file of the typ
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    with open(path, 'r') as r:
        config = yaml.load(r)

    host_types = get_host_types()
    for h in host_types: 
        if h['type'] == config['host']['type']:
            decoy_type = HostType(**h)
            break

    
    decoy = DecoyHost(network, subnet, decoy_type)
    decoy.set_reward(int(config['host']['reward']))
    decoy.set_recurring_rewawrd(int(config['host']['recurring_reward']))
    return decoy

def random_decoy(network: Network, subnet: Subnet)-> DecoyHost:
    """
    Create a decoy using random parameters. The network and subnet still need to be specified.
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    
    host_types = get_host_types()
    selected_type = random.choice(host_types)
    

    decoy_type = HostType(**selected_type)
    return  DecoyHost(network, subnet, decoy_type)
    
