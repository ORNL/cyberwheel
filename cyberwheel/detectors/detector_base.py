from abc import abstractmethod
from typing import Iterable
from cyberwheel.detectors.alert import Alert

class Detector:
    name = "Detector"

    def __init__(self) -> None:
        """
        Abstract base class for defining detectors. Should define an `obs()` method
        that takes an iterable of `Alerts` and performs some transformation on the
        iterable and returns the result.
        """
        pass

    @abstractmethod
    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        raise NotImplementedError