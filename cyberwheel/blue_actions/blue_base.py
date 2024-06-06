from abc import abstractmethod
from typing import  List, Tuple, Union

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service



class BlueAction:
    def __init__(self)-> None:
        pass
    
    @abstractmethod
    def execute(self) -> Tuple[List[int], int, int]:
        """
        This method executes a blue action. 
        It returns how an updated obs_vec that includes how this action affected the network
        and the reward gained (negative or positive) by performing this action.
        """
        raise NotImplementedError