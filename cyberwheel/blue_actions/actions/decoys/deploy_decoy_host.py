import json
import random
import yaml

from typing import List, Tuple, Union

from cyberwheel.blue_actions.blue_base import BlueAction
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host, HostType
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet


def get_host_types() -> List[dict[str, any]]:
    with open('resources/metadata/host_definitions.json', 'rb') as f:
        host_defs = json.load(f)
    return host_defs['host_types']

class DeployDecoyHost(BlueAction):
    def __init__(self, network: Network, subnet: Subnet, type: HostType,
                 obs_vec: List, reward: int = 0, recurring_reward: int = 0) -> None:
        """
            A class that allows the blue agent to create a decoy host.
            ### Parameters
            - `network`: the game's network object
            - `subnet`: the subnet this host should be added on
            - `type`: the type of host this decoy will impersonate
            - `reward`: the effect this decoy has on the overall reward upon execution
            - `recurring_reward`: the recurring effect this decoy has on the overall reward
        """
        super().__init__(obs_vec, reward=reward, recurring_reward=recurring_reward)
        self.network: Network = network
        self.subnet: Subnet = subnet
        self.type: HostType = type
        self.host: Host = Host(self.type.name, self.subnet, self.type)  
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, DeployDecoyHost):
            return False
        return True if self.host == __value.host else False
    
    def __str__(self) -> str:
        s = f"Network: {self.network.name}\n"
        s += f"Subnet: {self.subnet.name}\n"
        s += f"Type: {self.type}\n"
        s += f"Host: {self.host}\n"
        return s


    def execute(self) -> Tuple[List[int], int]:
        self.host = self.network.create_decoy_host(self.type.name, self.subnet, self.type)
        return [], self.reward                                                                                                                                                                                                                                              


def deploy_host_from_yaml(decoy_name: str, path: str, network: Network, subnet: Subnet)-> DeployDecoyHost:
    """
    Creates a DecoyHost object specified in a YAML file. This YAML file defines 
    a type of host and what services run on its.
    This should allow for different kinds of decoy hosts to be made in the future.
    - `path`: path to the config file of the typ
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    with open(path, 'r') as r:
        config = yaml.safe_load(r)

    if decoy_name not in config:
        raise KeyError() 
    # name = ""
    # if 'name' in config['host']:
    #     name = config['host']['name']
    host_types = get_host_types()
    for h in host_types: 
        if h['type'] == config[decoy_name]['type']:
            decoy_type = HostType(**h)
            decoy_type.name = decoy_name
            decoy_type.decoy = True
            break

    reward = int(config[decoy_name]['reward'])
    recurring_reward = int(config[decoy_name]['recurring_reward'])
    decoy = DeployDecoyHost(network, subnet, decoy_type, reward=reward, recurring_reward=recurring_reward)
    return decoy

def random_decoy(network: Network, subnet: Subnet)-> DeployDecoyHost:
    """
    Create a decoy using random parameters. The network and subnet still need to be specified.
    - `network`: the network this decoy will be on
    - `subnet`: the subnet this decoy will be on 
    """
    
    host_types = get_host_types()
    selected_type = random.choice(host_types)
    

    decoy_type = HostType(**selected_type)
    return  DeployDecoyHost(network, subnet, decoy_type, reward=-10, recurring_reward=-1)
    
