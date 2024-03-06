from abc import abstractmethod
from typing import Union, List

from network.network_base import Network
from network.host import Host
from network.service import Service



class BlueAction:
    def __init__(self) -> None:
        pass

    @abstractmethod
    def execute() -> any:
        pass