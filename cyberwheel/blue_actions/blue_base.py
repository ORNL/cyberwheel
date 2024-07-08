from abc import abstractmethod, ABC
from typing import  List, Tuple, Union

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service



class BlueAction(ABC):
    def __init__(self)-> None:
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """
        This method executes a blue action.
        Returns whether the execution succeeded or not
        """
        raise NotImplementedError