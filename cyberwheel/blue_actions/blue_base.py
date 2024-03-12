from abc import abstractmethod
from typing import Union, List

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service



class BlueAction:
    def __init__(self, reward=0, recurring_reward=0)-> None:
        self.reward = reward
        self.recurring_reward = recurring_reward

    def calc_recurring_reward(self, n: int)-> int:
        return n + self.recurring_reward
    
    # def set_reward(self, reward: int)-> None:
    #     self.reward = reward
    
    # def set_recurring_reward(self, recurring_reward:)

    @abstractmethod
    def execute(self) -> int:
        """
        This method executes a blue action. 
        It returns the reward gained (negative or positive) by performing this action.
        """
        raise NotImplementedError