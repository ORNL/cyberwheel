import random
from typing import Iterable

from network.network_base import Network
from detectors.detectors.probability_detector import ProbabilityDetector
from detectors.detector_base import read_detector_yaml
from detectors.alert import Alert

class HIDSDetector(ProbabilityDetector):
    """Host-based Intrusion Detection System Detector"""
    def __init__(self, config) -> None:
        # self.network = network
        self.technique_probabilites = read_detector_yaml(config)

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return super().obs(perfect_alert)
