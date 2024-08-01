from abc import ABC, abstractmethod
from cyberwheel.network.host import Host

class RedStrategy(ABC):
    @classmethod
    @abstractmethod
    def select_target(cls) -> Host | None:
        return None

    @classmethod
    @abstractmethod
    def get_reward_map(cls) -> dict[str, tuple[int, int]]:
        return {}