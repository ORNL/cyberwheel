import random
from typing import Iterable

from network.network_base import Network
from ..detector_base import read_detector_yaml, Detector
from ..alert import Alert

class HIDSDetector(Detector):
    def __init__(self, network: Network) -> None:
        self.network = network
        self.technique_probabilites = read_detector_yaml('resources/configs/hids_detector.yaml')

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return super().obs(perfect_alert)
