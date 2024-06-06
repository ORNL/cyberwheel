

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


class DynamicBlueActionReturn():
    def __init__(self, id: str, success: bool, recurring=0) -> None:
        self.id = id
        self.success = success
        self.recurring = recurring

class DynamicBlueAction:
    def __init__(self, network: Network, configs: Dict[str, any])-> None:
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
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self) -> DynamicBlueActionReturn:
        raise NotImplementedError

class HostAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, host: Host) -> DynamicBlueActionReturn:
        raise NotImplementedError
    
class SubnetAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, subnet: Subnet) -> DynamicBlueActionReturn:
        raise NotImplementedError