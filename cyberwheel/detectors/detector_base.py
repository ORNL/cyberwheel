from abc import abstractmethod
from typing import Iterable
import yaml

from detectors.alert import Alert

def read_detector_yaml(filename: str):
    with open(filename, 'r') as yaml_file:
        techniques = yaml.safe_load(yaml_file)
    return techniques

class Detector:
    @abstractmethod
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        raise NotImplementedError
