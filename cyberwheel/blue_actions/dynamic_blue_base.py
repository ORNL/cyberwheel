

from abc import abstractmethod
from enum import Enum
from typing import  Dict, Tuple, NewType
import uuid

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet





# Helper for generating IDs. Blue actions can use their own ID generation methods as well. 
def generate_id() -> str:
    return uuid.uuid4().hex

class CustomSharedData():
    @abstractmethod
    def clear(self):
        raise NotImplementedError

class DynamicBlueActionReturn():
    def __init__(self, id: str, success: bool, recurring=0) -> None:
        self.id = id
        self.success = success
        self.recurring = recurring

class DynamicBlueAction:
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs)-> None:
        self.network = network
        self.configs = configs

    @abstractmethod
    def execute(self) -> DynamicBlueActionReturn:
        """
        This method executes a blue action. 
        Returns whether the action was successful and the action's id. 
        """
        raise NotImplementedError
    

class StandaloneAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, **kwargs) -> DynamicBlueActionReturn:
        raise NotImplementedError

class HostAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, host: Host, **kwargs) -> DynamicBlueActionReturn:
        raise NotImplementedError
    
class SubnetAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, subnet: Subnet, **kwargs) -> DynamicBlueActionReturn:
        raise NotImplementedError

class RangeAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, i: int,  **kwargs) -> DynamicBlueActionReturn:
        raise NotImplementedError
