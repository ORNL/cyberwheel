

from abc import abstractmethod, ABC
from typing import  Dict
import uuid

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet
from cyberwheel.network.service import Service


# Helper for generating IDs. Blue actions can use their own ID generation methods as well.
def generate_id() -> str:
    return uuid.uuid4().hex


class CustomSharedData:
    @abstractmethod
    def clear(self):
        raise NotImplementedError


class DynamicBlueActionReturn:
    def __init__(self, id: str, success: bool, recurring=0) -> None:
        self.id = id
        self.success = success
        self.recurring = recurring

class DynamicBlueAction(ABC):
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


class RangeAction(DynamicBlueAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)

    @abstractmethod
    def execute(self, i: int, **kwargs) -> DynamicBlueActionReturn:
        raise NotImplementedError
