import uuid
from typing import Dict, List, Tuple, Any

from cyberwheel.blue_actions.actions import DeployDecoyHost, RemoveDecoyHost
from cyberwheel.blue_agents import BlueAgent, BlueAgentResult
from cyberwheel.network.host import Host, HostType
from cyberwheel.network.network_base import Network
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet
from cyberwheel.reward import RewardMap

class DeployedHost():
    def __init__(self, id: str, host: Host) -> None:
        self.id = id
        self.host = host

    def is_decoy_type(self, type: HostType, subnet: Subnet)-> bool:
        return self.host.name == type.name and self.host.subnet.name == subnet.name


class DecoyBlueAgent(BlueAgent):
    """
    A blue agent that only deploys decoys. Currently, only decoy hosts are
    implemented, so this agent can only deploy or remove decoy hosts
    from a subnet. It is also capable of performing a NOOP as an action.

    Each time the agent deploys a decoy, an initial negative reward is given. This represents
    the extra computation resources and other costs of initially deploying a decoy.

    There is also a negative recurring reward for each decoy that is deployed. This represents
    the maitainence costs, such as energy consumed, and continued use of computational resources.
    The sum of these recurring costs are added to the initial reward.

    Removal of a decoy is also possible. It removes the decoy host from the subnet. Right now,
    the idea is to have this action have an initial reward of 0 but removes the recurring cost
    of the decoy.

    Positive rewards are gained at the detector stage. When a red action is performed against
    a decoy host, the detector will detect it with 100% accuracy. If this happens, then
    a positive reward will be given because the red agent fell for the decoy.
    """

    def __init__(
        self, network: Network, decoy_info: Dict[str, Any], host_defs: Dict[str, Any]
        ) -> None:
        self.network = network
        self.subnets = self.network.get_all_subnets()
        self.decoy_info = decoy_info
        self.num_decoy_types = len(self.decoy_info)
        self.action_space_length = 2 * self.num_decoy_types * len(self.subnets) + 1
        self.host_defs = host_defs
        self._load_host_types()
        self._load_rewards()
        self.recurring_actions: List[Tuple[str, str]] = []
        self.deployed_hosts: List[DeployedHost] = []

    def act(self, action) -> BlueAgentResult:
        """
        Takes the action selected by the RL agent
        
        It returns:
        - The name of the action it took (to index into the reward map)
        - The uuid as a string of hex digits belonging to the action (to differtiate this action from others)
        - Whether the action succeeded or failed
        """
        # Even if the agent choses to do nothing, the recurring rewards of
        # previous actions still need to be summed.
        # Decide what action to take
        decoy_index = self._get_decoy_type_index(action)
        action_type = self._get_action_type(action)
        subnet_index = self._get_subnet_index(action)

        # Perform the action
        selected_subnet = self.subnets[subnet_index]
        successful = False
        id = ""
        action_name = "failed"
        
        # NOOP
        if action_type == 0:
            successful = True
            action_name = "nothing"

        # Deploy Host
        elif action_type == 1:# and (len(self.deployed_hosts) < self.decoy_limit or self.decoy_limit == -1):
            decoy_type = self.host_types[decoy_index]
            id = uuid.uuid4().hex
            decoy_key = list(self.decoy_info.keys())[decoy_index]
            decoy_name = f"{decoy_key}-{id}"
            action_name = decoy_key
            reward = self.rewards[decoy_index][0]
            recurring_reward = self.rewards[decoy_index][1]
            decoy = DeployDecoyHost(decoy_name, self.network, selected_subnet, decoy_type, reward=reward, recurring_reward=recurring_reward) 
            decoy.execute()
            self.deployed_hosts.append(DeployedHost(id, decoy.host))
            successful = True

        # Remove Host
        elif action_type == 2:
            decoy_type = self.host_types[decoy_index]
            action_name = "remove"
            # Check if the host we want to remove is already on the network
            # We can do this by seeing if a host shares the same host name and subnet name
            for deployed_host in self.deployed_hosts:
                if deployed_host.is_decoy_type(decoy_type, selected_subnet):
                    id = deployed_host.id
                    remove = RemoveDecoyHost(self.network, deployed_host.host)
                    remove.execute()
                    self.deployed_hosts.remove(deployed_host)
                    successful = True
                    break
        return action_name, id, successful

    def get_reward_map(self) -> RewardMap:
        return self.reward_map

    def _load_rewards(self)-> None:
        self.rewards = []
        self.reward_map: RewardMap = {}
        for decoy_name in self.decoy_info:
            info = self.decoy_info[decoy_name]
            rewards = (info["reward"], info["recurring_reward"])
            self.rewards.append(rewards)
            self.reward_map[decoy_name] = rewards

        # Add remove and nothing manually for right now
        self.reward_map['remove'] = (-50, 0)
        self.reward_map['nothing'] = (0, 0)

    def _load_host_types(self)-> None:
        self.host_types = []
        for decoy_name in self.decoy_info:
            info = self.decoy_info[decoy_name]
            type_info = self.host_defs[info["type"]]
            services = []
            for service_info in type_info["services"]:
                services.append(Service.create_service_from_dict(service_info))
            host_type = HostType(name=info["type"], services=services, decoy=True)
            self.host_types.append(host_type)

    def _get_subnet_index(self, action: int, i=1) -> int:
        return (action - i) % len(self.subnets)

    def _get_decoy_type_index(self, action: int, i=1) -> int:
        """
        Does some math to calculate which decoy host type is to be used.
        Returns an `int` that is the index of a decoy host type in the
        list of decoy host types.

        The list of decoy host types has a length of N where N is the
        number of different host types that can be deployed. N is assumed
        to be the same for each subnet. It also assumes 1 NOOP and no other
        actions besides deploy/remove decoy. 
        
        `_get_decoy_type_index()` converts an integer I in the range (0, 2*N + 1] to be in the range [0, N]. If
        I = 0, then it returns -1. The resulting integer can then be used to index into the decoy_type list.
        
        NOTE: This just gets the decoy's host type. Whether to deploy or remove the
        decoy is determined in `_get_action_type()`.
        """
        # return (action - 1) % self.num_decoy_types if action else -1
        return ((action - i) % (self.num_decoy_types * len(self.subnets))) // len(
            self.subnets
        )

    def _get_action_type(self, action: int) -> int:
        """
        Determines which type of action to perform.
        """
        # return (action - 1) // self.num_decoy_types + 1 if action else action
        if action == 0:
            return 0
        elif action < (self.num_decoy_types * len(self.subnets) + 1):
            return 1
        else:
            return 2
