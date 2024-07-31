from abc import abstractmethod, ABC
from typing import  Dict
import uuid

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet
from cyberwheel.network.service import Service

def generate_id() -> str:
    """
    Returns a UUID4 as string of hex digits. 
    """
    return uuid.uuid4().hex

class CustomSharedData(ABC):
    """
    An abstract base class for defining custom shared data to use with the dynamic blue agent. All custom shared data objects should have
    a `clear()` method that resets the object's member variables to their default value. `clear()` is called whenever the environment resets.
    """
    @abstractmethod
    def clear(self):
        raise NotImplementedError

class BlueActionReturn():
    def __init__(self, id="", success=False, recurring=0) -> None:
        """
        The output of blue actions.

        - `id`: a string that identifies an action with a recurring reward. Should be the empty string otherwise.
        - `success`: specifies if the action was completel successfully.  
        - `recurring`: an integer in the range `[-1,1]` specifying how this actions affects recurring rewards. `-1` means that this action removes a 
        recurring reward. `0` means this action does not affect recurring rewards. `1` means that this action adds a recurring reward.
        """
        self.id = id
        self.success = success
        self.recurring = recurring

class BlueAction(ABC):
    def __init__(self, network: Network, configs: Dict[str, any] = {})-> None:
        """
        Base class for all blue actions. It requires the environment's network.
        Config information can also be supplied here.
        """
        self.network = network
        self.configs = configs

    @abstractmethod
    def execute(self) -> BlueActionReturn:
        """
        This method executes a blue action. 
        Returns whether the action was successful and the action's id. 
        """
        raise NotImplementedError
    

class StandaloneAction(BlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, **kwargs) -> BlueActionReturn:
        raise NotImplementedError

class HostAction(BlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        raise NotImplementedError
    
class SubnetAction(BlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, subnet: Subnet, **kwargs) -> BlueActionReturn:
        raise NotImplementedError
    
    def define_configs(self) -> None:
        self.decoy_info = self.configs["decoy_hosts"]
        self.host_info = self.configs["host_definitions"]
        self.service_info = self.configs["services"]
        self.type = list(self.decoy_info.values())[0]["type"]

    def define_services(self) -> None:
        type_info = self.host_info["host_types"][self.type]
        self.services = set()
        self.cves = set()
        for s in type_info["services"]:
            service = Service.create_service_from_dict(self.service_info[s])
            self.services.add(service)
            self.cves.update(service.vulns)


class RangeAction(BlueAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)
    
    @abstractmethod
    def execute(self, i: int,  **kwargs) -> BlueActionReturn:
        raise NotImplementedError
