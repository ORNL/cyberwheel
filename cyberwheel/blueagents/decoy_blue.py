from typing import Dict, List, Any

from cyberwheel.blue_actions.actions.decoys.deploy_decoy_host import (
    DeployDecoyHost,
    random_decoy,
)
from cyberwheel.blue_actions.actions.decoys.remove_decoy import RemoveDecoyHost
from cyberwheel.blue_actions.blue_base import BlueAction
from cyberwheel.network.host import Host, HostType
from cyberwheel.network.network_base import Network
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet


class DeployedHost:
    def __init__(self, host: Host, subnet: Subnet) -> None:
        self.host = host
        self.subnet = subnet

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, DeployedHost)
            and self.host == __value.host
            and self.subnet == __value.subnet
        )


class DecoyBlueAgent:
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

        # TODO Make host type objects from decoy info

        self.host_types = []
        self.rewards = []
        for decoy_name in decoy_info:
            info = decoy_info[decoy_name]
            reward = info["reward"]
            recurring = info["recurring_reward"]
            type_info = host_defs[info["type"]]
            services = []
            for service_info in type_info["services"]:
                services.append(Service.create_service_from_dict(service_info))
            host_type = HostType(name=decoy_name, services=services, decoy=True)
            self.host_types.append(host_type)
            self.rewards.append((reward, recurring))
        # Keep track of actions that have recurring rewards.
        # Use the base BlueAction class here to allow for
        # a variety of recurring actions.
        self.recurring_actions: List[BlueAction] = []

    def act(self, action):
        # Even if the agent choses to do nothing, the recurring rewards of
        # previous actions still need to be summed.
        rec_rew = self._calc_recurring_reward_sum()
        rew = 0
        # Decide what action to take
        decoy_index = self._get_decoy_type_index(action)
        action_type = self._get_action_type(action)
        subnet_index = self._get_subnet_index(action)

        # Perform the action
        selected_subnet = self.subnets[subnet_index]

        blue_action_str = "no_op no_op"

        # NOOP
        if action_type == 0:
            pass
        # Deploy
        elif action_type == 1:
            decoy_type = self.host_types[decoy_index]
            reward = self.rewards[decoy_index][0]
            recurring_reward = self.rewards[decoy_index][1]
            decoy = DeployDecoyHost(
                self.network,
                selected_subnet,
                decoy_type,
                reward=reward,
                recurring_reward=recurring_reward,
            )
            rew = decoy.execute()
            self.recurring_actions.append(decoy)
            blue_action_str = f"deploy {selected_subnet.name}"
        # TODO Remove
        # Get the host from the right DeployDecoyHost action in self.recurring_actions
        # Remove that host from the network
        # Remove the action from self.recurring_actions
        # NOTE There shouldn't be any conflicts with the observation space here because
        #      the observation space only looks at real hosts
        elif action_type == 2:
            decoy_type = self.host_types[decoy_index]
            for rec_action in self.recurring_actions:
                if (
                    rec_action.host == decoy_type
                    and rec_action.subnet == selected_subnet
                ):
                    removed_host = rec_action.host
                    remove = RemoveDecoyHost(self.network, removed_host)
                    rew = remove.execute()
                    i = self.recurring_actions.index(removed_host)
                    self.recurring_actions.pop(i)
                    break
            blue_action_str = f"remove {selected_subnet.name}"
        else:
            raise ValueError(
                f"The action provided is not within this agent's action space: {action}, {action_type}"
            )

        return rew + rec_rew, blue_action_str

    def _calc_recurring_reward_sum(self) -> int:
        """
        Calculates the sum of all recurring rewards for this agent.
        """
        sum = 0
        for recurring_action in self.recurring_actions:
            sum = recurring_action.calc_recurring_reward(sum)
        return sum

    def _get_subnet_index(self, action: int) -> int:
        return (action - 1) % len(self.subnets)

    def _get_decoy_type_index(self, action: int) -> int:
        """
        Does some math to calculate which decoy host type is to be used.
        Returns an `int` that is the index of a decoy host type in the
        list of decoy host types.

        The list of decoy host types has a length of N where N is the
        number of different host types that can be deployed. N is assumed
        to be the same for each subnet. It also assumes 1 NOOP and no other
        actions besides deploy/remove decoy.

        `_get_decoy_type_index()` converts an integer I in the range (0, 2*N + 1] to be in the range [0, N] (decoy type). If
        I = 0, then it returns -1.

        Pretty much, this just determines which decoy type the RL chose to use.

        NOTE: This just gets the decoy's host type. Whether to deploy or remove the
        decoy is determined in `_get_action_type()`.
        """
        # return (action - 1) % self.num_decoy_types if action else -1
        return ((action - 1) % (self.num_decoy_types * len(self.subnets))) // len(
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
