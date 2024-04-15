from abc import ABC, abstractmethod

from cyberwheel.reward.reward import RewardMap

class BlueAgentResult:
    def __init__(self) -> None:
        pass

class BlueAgent(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def act(self) -> BlueAgentResult:
        pass
    
    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        pass
