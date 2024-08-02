from abc import ABC, abstractmethod
from cyberwheel.network.host import Host

"""
Defines Base class for implementing Red Strategies.
"""

class RedStrategy(ABC):
    @classmethod
    @abstractmethod
    def select_target(cls) -> Host | None:
        return None

    @classmethod
    @abstractmethod
    def get_reward_map(cls) -> dict[str, tuple[int, int]]:
        return {}