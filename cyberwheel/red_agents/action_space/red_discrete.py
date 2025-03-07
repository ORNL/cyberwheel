from gymnasium import Space
from gymnasium.spaces import Discrete
from gymnasium.core import ActType

from cyberwheel.red_actions.actions import ARTKillChainPhase

class RedDiscreteActionSpace:
    def __init__(self, actions: list[ARTKillChainPhase], entry_host: str) -> None:
        self._action_space_size: int = len(actions)
        self.num_hosts = 1
        self.num_actions = len(actions)
        self.actions = actions
        self.hosts = [entry_host]

    def select_action(self, action: ActType) -> tuple[ARTKillChainPhase, str]:
        try:
            action = int(action)
        except:
            raise TypeError(
                f"provided action is of type {type(action)} and is unsupported by the chosen ActionSpaceConverter"
            )

        action_index = action % self.num_actions
        host_index = action // self.num_actions

        action_name = self.actions[action_index]
        host_name = self.hosts[host_index]

        return action_name, host_name

    def add_host(self, host_name: str) -> None:
        self._action_space_size += len(self.actions)
        self.hosts += [host_name]
        self.num_hosts += 1

    def get_shape(self) -> tuple[int, ...]:
        return (self._action_space_size,)

    def create_action_space(self, max_size: int) -> Space:
        return Discrete(max_size)

    def reset(self, entry_host: str) -> None:
        self._action_space_size: int = len(self.actions)
        self.num_hosts = 1
        self.hosts = [entry_host]