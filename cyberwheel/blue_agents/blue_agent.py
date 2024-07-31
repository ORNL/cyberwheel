from abc import ABC, abstractmethod

from cyberwheel.reward import RewardMap

class BlueAgentResult():
    def __init__(self, name: str, id: str, success: bool, recurring: int) -> None:
        """
        - `name`: name of the blue action executed
        - `id`: id for a recurring reward
        - `success`: whether this action successfully executed or not
        - `recurring`: an integer describing how this action affected recurring rewards. 
        -1 removes the reward. 0 has no affect. 1 adds a new reward
        """
        self.name = name
        self.id = id
        self.success = success
        self.recurring = recurring


class BlueAgent(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def act(self) -> BlueAgentResult:
        pass
    
    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        pass
