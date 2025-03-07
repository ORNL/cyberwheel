from abc import ABC, abstractmethod
from cyberwheel.network.host import Host


class RedStrategy(ABC):
    """
    Defines Base class for implementing Red Strategies.
    """
    @classmethod
    @abstractmethod
    def select_target(cls, agent_obj) -> Host | None:
        return None
