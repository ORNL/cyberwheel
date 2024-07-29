from abc import abstractmethod
from typing import Iterable
import yaml

from cyberwheel.network.network_base import Network
from .alert import Alert


def technique_probabilities(filename: str):
    with open(filename, "r") as yaml_file:
        probabilites = yaml.safe_load(yaml_file)
    return probabilites


class Detector:
    @abstractmethod
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        raise NotImplementedError
