from abc import abstractmethod
from typing import Union, List

from network.network_base import Network
from network.host import Host
from network.service import Service



class BlueAction:
    @abstractmethod
    def execute(self) -> int:
        """
        This method executes a blue action. 
        It returns the reward gained (negative or positive) by performing this action.
        """
        raise NotImplementedError