from abc import abstractmethod
from typing import Iterable
import yaml
from .alert import Alert

class Detector:
    name = "Detector"
    @abstractmethod
    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        raise NotImplementedError