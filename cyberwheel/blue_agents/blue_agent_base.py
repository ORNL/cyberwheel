from abc import ABC, abstractmethod
from typing import NewType, Tuple

from cyberwheel.reward import RewardMap

BlueAgentResult = NewType("BlueAgentResult", Tuple[str, str, bool])


class BlueAgent(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def act(self) -> BlueAgentResult:
        pass
    
    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        pass
