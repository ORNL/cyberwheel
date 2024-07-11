from abc import abstractmethod, ABC
from gym.core import ActType
from gym import Space

from cyberwheel.blue_actions.dynamic_blue_base import DynamicBlueAction
from cyberwheel.network.network_base import Network

class ASReturn:
    def __init__(self, name: str, action: DynamicBlueAction, args=(), kwargs={}) -> None:
        self.name = name
        self.action = action
        self.args = args
        self.kwargs = kwargs

class ActionSpace(ABC):
    """
    A base class for converting the output of `gym.Space.sample()` to a blue action. 
    Must implement:
    - `select_action()`: Method for handling which method the blue agent selects. It should at the least 
      take the `ActType` returned by sampling the action space and use it to select a blue action. The blue 
      action is to be executed by the blue agent. 
    - `add_actions()`: Method for adding an action. Used while parsing the dynamic blue agent's config file to
      add mappings from `ActType` to a blue action. 
    - `get_shape()`: Method for getting the shape of the action space. NOTE: Might be replaced
      by an actual implementation of the action space. I.e. this class also sets up the action space for the env.

    """
    def __init__(self, network: Network) -> None:
        self.network = network
        self.hosts = network.get_hosts()
        self.subnets = network.get_all_subnets()
        self.num_hosts = len(self.hosts)
        self.num_subnets = len(self.subnets)

    @abstractmethod
    def select_action(self, action: ActType, **kwargs)-> ASReturn:
        """
        Selects which action to perform based on the value of `action`. Other information necessary 
        can be passed through `**kwargs`.
        """
        pass
    
    @abstractmethod
    def add_action(self, name: str, action: DynamicBlueAction, **kwargs) -> None:
        """
        Adds an action to this `ActionSpaceConverter`. If using the dynamic blue agent, then the action's
        `action_space_args` from the config file will be passed as `**kwargs`. 
        """
        pass

    @abstractmethod
    def get_shape(self) -> tuple[int, ...]:
        """
        Returns the an action space's shape.
        """
        pass
    
    @abstractmethod
    def create_action_space(self) -> Space:
        pass

    def finalize(self):
        """
        Is called by the dynamic blue agent after it finishes adding actions. By default, it does nothing.
        It can be overwritten to perform any operations necessary to finalize the converter's setup. 
        This may be useful in the situation where all actions need to be known when setting up the converter.
        """
        pass